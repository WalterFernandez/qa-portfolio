"""Concurrencia: dos requests sobre el mismo pedido al mismo tiempo.

Defecto que cubren: TOCTOU (time-of-check to time-of-use). Los dos requests leen
el estado (check), los dos lo ven válido y los dos escriben (use). La idempotencia
del pago estaba probada solo en secuencia (test_pago_doble_no_duplica).

Para que la carrera sea reproducible y no dependa de la suerte, una barrera frena
a cada hilo justo después de leer el estado y lo suelta cuando los dos llegaron.

Técnica: transición de estados (ISTQB CTFL v4.0 §4.2.4) con dos requests a la
vez sobre la misma transición. Defecto: MITRE CWE-367. Arreglo: control de
concurrencia optimista (`pedidos._actualizar_si_sigue`).
"""

import sqlite3
import threading

import pytest

from conftest import DATOS_OK, FIRMA_OK, avanzar_hasta
from delivery import pedidos

ESPERA_S = 5


@pytest.fixture
def frenar_en_el_check(monkeypatch):
    """Devuelve una función que activa la barrera para un estado destino o de origen.

    Las dos primeras validaciones hacia `destino` (o que salen de `desde`) son el
    "check" de cada request: se esperan una a la otra antes de seguir. `desde` sirve
    cuando los dos requests van a destinos distintos (cliente y delivery confirman). Los endpoints corren en hilos del
    TestClient, no en los del test: por eso se cuenta, no se mira el hilo.
    """

    def _activar(destino=None, desde=None):
        barrera = threading.Barrier(2, timeout=ESPERA_S)
        llegados = []  # list.append es atómico: cuenta cuántos pasaron el check
        original = pedidos.validar_transicion

        def con_barrera(actual, dest):
            original(actual, dest)
            coincide = dest == destino if destino is not None else actual == desde
            if coincide and len(llegados) < 2:
                llegados.append(1)
                barrera.wait()

        monkeypatch.setattr(pedidos, "validar_transicion", con_barrera)

    return _activar


def _en_paralelo(*llamadas):
    resultados = [None] * len(llamadas)

    def correr(i, f):
        try:
            resultados[i] = f()
        except Exception as exc:  # un 500 del TestClient llega como excepción
            resultados[i] = exc

    hilos = [threading.Thread(target=correr, args=(i, f)) for i, f in enumerate(llamadas)]
    for h in hilos:
        h.start()
    for h in hilos:
        h.join(ESPERA_S * 3)
    return resultados


def test_dos_pagos_simultaneos_no_duplican(crear_cliente, frenar_en_el_check):
    c1, c2 = crear_cliente(), crear_cliente()  # dos apps, una base: como dos procesos
    pid = c1.post("/pedidos", json={"telefono": "1122334455"}).json()["id"]
    c1.put(f"/pedidos/{pid}", json=DATOS_OK)
    c1.post(f"/pedidos/{pid}/firma", json={"imagen": FIRMA_OK})

    frenar_en_el_check(pedidos.Estado.PAGADO)
    r1, r2 = _en_paralelo(
        lambda: c1.post(f"/pedidos/{pid}/pago"),
        lambda: c2.post(f"/pedidos/{pid}/pago"),
    )

    assert [getattr(r, "status_code", r) for r in (r1, r2)] == [200, 200]
    estados = [e["estado"] for e in c1.get(f"/pedidos/{pid}").json()["eventos"]]
    assert estados.count("PAGADO") == 1
    assert estados.count("ASIGNADO") == 1
    al_delivery = c1.get("/mensajes", params={"destino": "delivery", "pedido_id": pid}).json()
    assert len(al_delivery) == 1


def test_dos_cargas_de_datos_simultaneas_no_duplican(crear_cliente, frenar_en_el_check):
    c1, c2 = crear_cliente(), crear_cliente()
    pid = c1.post("/pedidos", json={"telefono": "1122334455"}).json()["id"]

    frenar_en_el_check(pedidos.Estado.DATOS_CARGADOS)
    r1, r2 = _en_paralelo(
        lambda: c1.put(f"/pedidos/{pid}", json=DATOS_OK),
        lambda: c2.put(f"/pedidos/{pid}", json=DATOS_OK),
    )

    codigos = sorted(str(getattr(r, "status_code", repr(r))) for r in (r1, r2))
    assert codigos == ["200", "409"]  # el segundo envío llega tarde: transición inválida
    tarde = next(r for r in (r1, r2) if r.status_code == 409)
    # El 409 informa el estado real (el que dejó el otro request), no el que se leyó.
    assert tarde.json()["detail"]["estado_actual"] == "COTIZADO"
    p = c1.get(f"/pedidos/{pid}").json()
    assert len(p["items"]) == 2
    estados = [e["estado"] for e in p["eventos"]]
    assert estados.count("DATOS_CARGADOS") == 1
    assert estados.count("COTIZADO") == 1
    al_cliente = c1.get("/mensajes", params={"destino": "cliente", "pedido_id": pid}).json()
    assert len(al_cliente) == 2  # el link y una sola cotización


def test_firma_que_llega_tarde_no_pisa_un_pedido_pagado(crear_cliente, monkeypatch):
    """Orden fijo: la firma lee COTIZADO y se frena; el pago termina entero; la firma sigue."""
    c1, c2 = crear_cliente(), crear_cliente()
    pid = c1.post("/pedidos", json={"telefono": "1122334455"}).json()["id"]
    c1.put(f"/pedidos/{pid}", json=DATOS_OK)
    c1.post(f"/pedidos/{pid}/firma", json={"imagen": FIRMA_OK})

    llego, seguir = threading.Event(), threading.Event()
    original = pedidos.validar_transicion

    def frenar_la_firma(actual, destino):
        original(actual, destino)
        # La primera validación hacia PAGADO es la de la firma: el pago arranca después.
        if destino == pedidos.Estado.PAGADO and not llego.is_set():
            llego.set()
            seguir.wait(ESPERA_S)

    monkeypatch.setattr(pedidos, "validar_transicion", frenar_la_firma)
    otra = "data:image/png;base64,OTRA="
    resultado = []
    hilo = threading.Thread(
        target=lambda: resultado.append(
            c2.post(f"/pedidos/{pid}/firma", json={"imagen": otra})
        ),
    )
    hilo.start()
    assert llego.wait(ESPERA_S)
    assert c1.post(f"/pedidos/{pid}/pago").status_code == 200
    seguir.set()
    hilo.join(ESPERA_S * 2)

    assert resultado[0].status_code == 409
    con = sqlite3.connect(c1.app.state.cfg.db_path)
    firma = con.execute("SELECT firma FROM pedidos WHERE id = ?", (pid,)).fetchone()[0]
    con.close()
    assert firma == FIRMA_OK  # la firma del pago queda intacta


# --- Task 7: confirmaciones y cancelación -----------------------------------


def _pedido_en(c, estado):
    """Pedido nuevo llevado por la API hasta `estado` (COTIZADO, o ASIGNADO en adelante)."""
    pid = c.post("/pedidos", json={"telefono": "1122334455"}).json()["id"]
    c.put(f"/pedidos/{pid}", json=DATOS_OK)
    c.post(f"/pedidos/{pid}/firma", json={"imagen": FIRMA_OK})
    if estado == "COTIZADO":
        return pid
    c.post(f"/pedidos/{pid}/pago")
    if estado != "ASIGNADO":
        avanzar_hasta(c, pid, estado)
    return pid


def _codigos(*respuestas):
    return sorted(str(getattr(r, "status_code", repr(r))) for r in respuestas)


def test_confirmaciones_simultaneas_cierran_una_sola_vez(crear_cliente, frenar_en_el_check):
    """Cliente y delivery confirman en el mismo instante desde EN_PUERTA.

    Los dos leen EN_PUERTA y uno gana el UPDATE condicional. El otro no debe recibir
    409, porque su confirmación es legítima: relee y confirma sobre el estado nuevo.
    """
    c1, c2 = crear_cliente(), crear_cliente()
    pid = _pedido_en(c1, "EN_PUERTA")

    frenar_en_el_check(desde=pedidos.Estado.EN_PUERTA)
    r1, r2 = _en_paralelo(
        lambda: c1.post(f"/pedidos/{pid}/recibido"),
        lambda: c2.post(f"/pedidos/{pid}/entregado"),
    )

    assert _codigos(r1, r2) == ["200", "200"]
    p = c1.get(f"/pedidos/{pid}").json()
    assert p["estado"] == "CERRADO"
    assert (p["recibido_cliente"], p["entregado_delivery"]) == (True, True)
    estados = [e["estado"] for e in p["eventos"]]
    assert [estados.count(e) for e in ("RECIBIDO", "ENTREGADO", "CERRADO")] == [1, 1, 1]


def test_la_misma_confirmacion_dos_veces_a_la_vez_da_un_409(crear_cliente, frenar_en_el_check):
    c1, c2 = crear_cliente(), crear_cliente()
    pid = _pedido_en(c1, "EN_PUERTA")

    frenar_en_el_check(desde=pedidos.Estado.EN_PUERTA)
    r1, r2 = _en_paralelo(
        lambda: c1.post(f"/pedidos/{pid}/recibido"),
        lambda: c2.post(f"/pedidos/{pid}/recibido"),
    )

    assert _codigos(r1, r2) == ["200", "409"]
    p = c1.get(f"/pedidos/{pid}").json()
    assert p["estado"] == "RECIBIDO"
    assert [e["estado"] for e in p["eventos"]].count("RECIBIDO") == 1


def _frenar_el_primero(monkeypatch, destino):
    """Frena el primer request que valida hacia `destino`, justo después de su check.

    Devuelve (llego, seguir): el test espera `llego`, hace pasar al otro request
    entero y después da `seguir`. Así el orden de la carrera es fijo.
    """
    llego, seguir = threading.Event(), threading.Event()
    original = pedidos.validar_transicion

    def frenar(actual, dest):
        original(actual, dest)
        if dest == destino and not llego.is_set():
            llego.set()
            seguir.wait(ESPERA_S)

    monkeypatch.setattr(pedidos, "validar_transicion", frenar)
    return llego, seguir


def _en_un_hilo(f):
    resultado = []
    hilo = threading.Thread(target=lambda: resultado.append(f()))
    hilo.start()
    return hilo, resultado


def test_pago_que_se_adelanta_a_la_cancelacion(crear_cliente, monkeypatch):
    """La cancelación lee COTIZADO y se frena; el pago termina; la cancelación sigue.

    El 409 tiene que ser el mismo `no_cancelable` que si el pago hubiera llegado
    antes, no un `transicion_invalida` suelto del UPDATE condicional.
    """
    c1, c2 = crear_cliente(), crear_cliente()
    pid = _pedido_en(c1, "COTIZADO")

    llego, seguir = _frenar_el_primero(monkeypatch, pedidos.Estado.CANCELADO)
    hilo, resultado = _en_un_hilo(
        lambda: c2.post(f"/pedidos/{pid}/cancelar", json={"por": "cliente"})
    )
    assert llego.wait(ESPERA_S)
    assert c1.post(f"/pedidos/{pid}/pago").status_code == 200
    seguir.set()
    hilo.join(ESPERA_S * 2)

    assert resultado[0].status_code == 409
    assert resultado[0].json()["detail"] == {
        "error": "no_cancelable",
        "estado_actual": "ASIGNADO",
        "mensaje": "No se puede cancelar un pedido que ya fue pagado",
    }
    p = c1.get(f"/pedidos/{pid}").json()
    assert p["estado"] == "ASIGNADO"
    assert p["cancelado_por"] is None
    assert "CANCELADO" not in [e["estado"] for e in p["eventos"]]


def test_cancelacion_que_se_adelanta_al_pago(crear_cliente, monkeypatch):
    """El pago lee COTIZADO (firmado) y se frena; la cancelación termina; el pago sigue."""
    c1, c2 = crear_cliente(), crear_cliente()
    pid = _pedido_en(c1, "COTIZADO")

    llego, seguir = _frenar_el_primero(monkeypatch, pedidos.Estado.PAGADO)
    hilo, resultado = _en_un_hilo(lambda: c2.post(f"/pedidos/{pid}/pago"))
    assert llego.wait(ESPERA_S)
    assert c1.post(f"/pedidos/{pid}/cancelar", json={"por": "servicio"}).status_code == 200
    seguir.set()
    hilo.join(ESPERA_S * 2)

    assert resultado[0].status_code == 409
    assert resultado[0].json()["detail"]["estado_actual"] == "CANCELADO"
    p = c1.get(f"/pedidos/{pid}").json()
    assert p["estado"] == "CANCELADO"
    assert "PAGADO" not in [e["estado"] for e in p["eventos"]]
    al_delivery = c1.get("/mensajes", params={"destino": "delivery", "pedido_id": pid}).json()
    assert al_delivery == []


def test_la_conexion_se_puede_usar_desde_otro_hilo(tmp_path):
    """FastAPI abre la conexión (dependencia `obtener_ctx`) en un hilo del threadpool y
    corre el endpoint en otro. Con `check_same_thread=True` (el default de sqlite3),
    dos requests a la vez daban 500 al azar. Lo encontró el panel del Paso 10, que
    pide /pedidos y /mensajes en paralelo. Cada conexión sigue siendo de un solo
    request: se usa desde un hilo por vez, nunca desde dos al mismo tiempo.
    """
    from delivery import db

    con = db.conectar(tmp_path / "hilos.db")
    errores = []

    def usar():
        try:
            con.execute("SELECT 1").fetchone()
        except Exception as exc:
            errores.append(exc)

    t = threading.Thread(target=usar)
    t.start()
    t.join(ESPERA_S)
    con.close()
    assert errores == []
