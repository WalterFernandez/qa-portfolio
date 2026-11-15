"""Smoke test: la app levanta e informa el estado de los defectos sembrados."""


def test_salud_informa_defectos_apagados(cliente):
    r = cliente.get("/salud")
    assert r.status_code == 200
    assert r.json() == {"estado": "ok", "defectos": {"zona_horaria": False, "contrato": False}}


def test_salud_refleja_defecto_encendido(crear_cliente):
    r = crear_cliente(defecto_contrato=True).get("/salud")
    assert r.json()["defectos"]["contrato"] is True
