// Sistema demo: helpers compartidos por las páginas (sin frameworks).

// Llama a la API. Si la respuesta no es 2xx, lanza un Error con `status` y `detail`.
async function api(metodo, ruta, body) {
  const opciones = { method: metodo, headers: {} };
  if (body !== undefined) {
    opciones.headers["Content-Type"] = "application/json";
    opciones.body = JSON.stringify(body);
  }
  let r;
  try {
    r = await fetch(ruta, opciones);
  } catch (e) {
    const err = new Error("sin_conexion");
    err.status = 0;
    throw err;
  }
  const datos = await r.json().catch(() => null);
  if (!r.ok) {
    const err = new Error("api_" + r.status);
    err.status = r.status;
    err.detail = datos && datos.detail;
    throw err;
  }
  return datos;
}

// Id del pedido: último tramo de la URL (/cliente/pedido/7 -> 7).
function idDelPedido() {
  return location.pathname.split("/").filter(Boolean).pop();
}

// Formato de pesos. Si el valor no es un número finito, se muestra tal cual
// (así el defecto de contrato se ve como "NaN" en vez de esconderse).
function pesos(n) {
  if (typeof n === "number" && Number.isFinite(n)) {
    return "$ " + n.toLocaleString("es-AR");
  }
  return String(n);
}

// Traduce un error de la API a un texto para la persona. Siempre incluye el código
// del error entre corchetes: lo leen las pruebas automáticas y sirve para reportar.
function textoDeError(err) {
  if (err.status === 0) return "No hay conexión con el servidor. [sin_conexion]";
  const d = err.detail;
  if (Array.isArray(d)) {
    // 422 de validación de FastAPI: lista de campos con problemas.
    const campos = d.map((x) => (x.loc || []).slice(1).join(".")).filter(Boolean);
    return "Revisá los datos: " + (campos.join(", ") || "formato inválido") + ". [422]";
  }
  const codigo = (d && d.error) || "error_" + err.status;
  const textos = {
    pedido_no_encontrado: "No encontramos ese pedido.",
    transicion_invalida: "Esa acción ya no corresponde: el pedido está en " + (d && d.estado_actual) + ".",
    firma_requerida: "Firmá antes de pagar.",
    no_cancelable: d && d.mensaje,
    plato_repetido: "Hay un plato repetido en el pedido.",
    plato_inexistente: "Uno de los platos ya no existe.",
    // Errores del navegador, no de la API:
    sin_geolocalizacion: "Este navegador no permite obtener la ubicación.",
    ubicacion_no_disponible: "No pudimos obtener tu ubicación. Marcá el punto en el mapa.",
  };
  return (textos[codigo] || "Algo salió mal.") + " [" + codigo + "]";
}

function mostrarError(err) {
  const caja = document.querySelector('[data-testid="msg-error"]');
  caja.textContent = textoDeError(err);
  caja.hidden = false;
}

function limpiarError() {
  const caja = document.querySelector('[data-testid="msg-error"]');
  caja.textContent = "";
  caja.hidden = true;
}

// Nombres legibles de los estados (el código exacto se muestra igual, para las pruebas).
const ESTADOS = {
  INICIADO: "Iniciado",
  LINK_ENVIADO: "Esperando tus datos",
  DATOS_CARGADOS: "Datos cargados",
  COTIZADO: "Cotizado: falta firmar y pagar",
  PAGADO: "Pagado",
  ASIGNADO: "Asignado a un delivery",
  RETIRADO: "Retirado del local",
  EN_CAMINO: "En camino",
  EN_PUERTA: "En la puerta",
  RECIBIDO: "Recibido por el cliente",
  ENTREGADO: "Entregado por el delivery",
  CERRADO: "Cerrado",
  CANCELADO: "Cancelado",
};

// Consulta el pedido cada `ms` y llama a `alCambiar` solo si cambió algo relevante,
// para no pisar lo que la persona está escribiendo en un formulario.
// Devuelve `aplicar(pedido)`: después de una acción propia se usa la respuesta
// de la API directamente, sin esperar a la próxima consulta.
function seguirPedido(id, ms, alCambiar) {
  let ultimo = null;
  function aplicar(p) {
    const clave = [p.estado, p.recibido_cliente, p.entregado_delivery].join("|");
    if (clave !== ultimo) {
      ultimo = clave;
      alCambiar(p);
    }
  }
  async function consultar() {
    try {
      aplicar(await api("GET", "/pedidos/" + id));
    } catch (err) {
      mostrarError(err);
      if (err.status === 404) return; // no tiene sentido seguir consultando
    }
    setTimeout(consultar, ms);
  }
  consultar();
  return aplicar;
}
