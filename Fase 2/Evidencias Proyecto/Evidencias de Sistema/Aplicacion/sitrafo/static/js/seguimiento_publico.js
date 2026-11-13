(function () {
  const CLAVE = JSON.parse(document.getElementById("clave-api").textContent);
  const form = document.getElementById("form-seguimiento");
  const mensaje = document.getElementById("mensaje");
  const resultado = document.getElementById("resultado");

  const fecha = (texto) => texto ? new Date(texto).toLocaleDateString("es-CL") : "";
  const fechaHora = (texto) => new Date(texto).toLocaleString("es-CL",
    { dateStyle: "short", timeStyle: "short" });

  function fila(textoIzq, textoDer, claseEstado) {
    const li = document.createElement("li");
    const izq = document.createElement("span");
    izq.textContent = textoIzq;
    li.appendChild(izq);
    if (textoDer) {
      const der = document.createElement("span");
      der.textContent = textoDer;
      der.className = claseEstado ? "estado " + claseEstado : "texto-nota sin-salto";
      li.appendChild(der);
    }
    return li;
  }

  function llenar(id, elementos) {
    const lista = document.getElementById(id);
    lista.replaceChildren(...elementos);
  }

  function mostrar(datos) {
    document.getElementById("r-numero").textContent = datos.numero;
    document.getElementById("r-fecha").textContent = "pedido del " + fecha(datos.fecha_pedido);
    document.getElementById("r-avance").textContent = datos.avance_pct + "%";
    document.getElementById("r-barra").style.width = datos.avance_pct + "%";
    document.getElementById("r-estado").textContent = datos.anulado ? "Anulado" : datos.estado.nombre;

    const e = datos.entrega;
    let entrega = "Por definir";
    if (e.fecha_estimada) {
      entrega = fecha(e.fecha_estimada + "T12:00:00");
      if (datos.etapa_actual === "entregado") entrega += " (entregado)";
      else if (e.atrasado) entrega += " (atrasado)";
      else entrega += " · " + e.dias_habiles_restantes + " dias habiles";
    }
    document.getElementById("r-entrega").textContent = entrega;

    llenar("r-etapas", datos.etapas.map((et) => {
      const li = fila(et.nombre,
        et.completada ? "Completada" : et.actual ? "En curso" : "Pendiente",
        et.completada ? "estado--bien" : et.actual ? "estado--espera" : "");
      if (et.completada) li.classList.add("terminada");
      return li;
    }));
    llenar("r-productos", datos.productos.length
      ? datos.productos.map((p) => fila(p.cantidad + " × " + p.modelo + " (" + p.orden_trabajo + ")",
          p.estado + " · " + Math.round(p.avance_pct) + "%"))
      : [fila("La fabricacion aun no se ha planificado.")]);
    llenar("r-historial", datos.historial.slice().reverse().map((h) =>
      fila(h.documento + " · " + h.estado, fechaHora(h.fecha_hora))));

    mensaje.hidden = true;
    resultado.hidden = false;
  }

  async function consultar(numero, codigo) {
    resultado.hidden = true;
    mensaje.hidden = true;
    const url = form.dataset.api + encodeURIComponent(numero) +
                "/?codigo=" + encodeURIComponent(codigo);
    try {
      const resp = await fetch(url, { headers: { "X-API-Key": CLAVE, "Accept": "application/json" } });
      const datos = await resp.json();
      if (!resp.ok) throw new Error(datos.detail || "No fue posible consultar el pedido.");
      mostrar(datos);
    } catch (error) {
      mensaje.textContent = error.message;
      mensaje.hidden = false;
    }
  }

  form.addEventListener("submit", (evento) => {
    evento.preventDefault();
    const numero = form.numero.value.trim();
    const codigo = form.codigo.value.trim();
    if (!numero || !codigo) {
      mensaje.textContent = "Ingrese el numero de la orden y el codigo de seguimiento.";
      mensaje.hidden = false;
      return;
    }
    consultar(numero, codigo);
  });

  if (form.numero.value && form.codigo.value) consultar(form.numero.value.trim(), form.codigo.value.trim());
})();
