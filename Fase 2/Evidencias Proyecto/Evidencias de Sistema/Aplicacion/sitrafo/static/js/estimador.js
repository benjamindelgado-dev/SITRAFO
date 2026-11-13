(function () {
  const CLAVE = JSON.parse(document.getElementById("clave-api").textContent);
  const CODIGO = JSON.parse(document.getElementById("codigo-modelo").textContent);
  const form = document.getElementById("form-estimar");
  const error = document.getElementById("estimar-error");
  const resultado = document.getElementById("estimar-resultado");
  const texto = (id, valor) => { document.getElementById(id).textContent = valor; };

  const numero = (valor, decimales) => Number(valor).toLocaleString("es-CL",
    { minimumFractionDigits: decimales, maximumFractionDigits: decimales });
  const fecha = (iso) => new Date(iso + "T12:00:00").toLocaleDateString("es-CL");

  function primerError(datos) {
    if (datos.detail) return datos.detail;
    const item = datos.items && (Array.isArray(datos.items) ? datos.items.find((i) => i && Object.keys(i).length) : datos.items);
    if (typeof item === "string") return item;
    if (item) return Object.values(item).flat()[0];
    return "No fue posible estimar el precio.";
  }

  form.addEventListener("submit", async (evento) => {
    evento.preventDefault();
    error.hidden = true;
    resultado.hidden = true;
    const cantidad = Number.parseInt(form.cantidad.value, 10);
    if (!cantidad || cantidad < 1) {
      error.textContent = "Ingrese una cantidad de al menos una unidad.";
      error.hidden = false;
      return;
    }
    try {
      const resp = await fetch(form.dataset.api, {
        method: "POST",
        headers: { "X-API-Key": CLAVE, "Content-Type": "application/json", "Accept": "application/json" },
        body: JSON.stringify({ items: [{ modelo: CODIGO, cantidad: cantidad }] }),
      });
      const datos = await resp.json();
      if (!resp.ok) throw new Error(primerError(datos));

      const item = datos.items[0];
      if (item.disponible) {
        texto("e-unitario", numero(item.precio_unitario_uf, 2) + " UF");
        texto("e-total", numero(item.subtotal_uf, 2) + " UF");
        const partes = [];
        if (datos.total_clp !== null) partes.push("$" + numero(datos.total_clp, 0));
        if (datos.total_usd !== null) partes.push("US$" + numero(datos.total_usd, 2));
        texto("e-equivalente", partes.length ? partes.join(" · ") : "No disponible");
      } else {
        texto("e-unitario", "Segun especificacion");
        texto("e-total", "Se confirma en la cotizacion");
        texto("e-equivalente", "—");
      }
      texto("e-entrega", fecha(datos.plazo.fecha_entrega_estimada) + " (" +
            datos.plazo.dias_habiles + " dias habiles)");
      texto("e-validez", fecha(datos.valida_hasta));
      texto("e-avisos", datos.avisos.join(" "));
      // El enlace usa la ruta del portal actual con el modelo y la cantidad
      const url = new URL(item.solicitar_presupuesto);
      document.getElementById("e-solicitar").href = url.pathname + url.search;
      resultado.hidden = false;
    } catch (e) {
      error.textContent = e.message;
      error.hidden = false;
    }
  });
})();
