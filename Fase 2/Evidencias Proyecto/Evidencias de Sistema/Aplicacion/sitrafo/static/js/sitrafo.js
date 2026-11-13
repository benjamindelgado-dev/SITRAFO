/* Comportamientos comunes del portal.

   La politica de seguridad de contenido (CSP) del sitio no admite JavaScript
   escrito dentro de las plantillas (atributos onclick, onchange, onsubmit ni
   bloques <script> en linea) ni atributos style. Esos comportamientos se
   declaran con atributos data-* y este archivo los conecta:

   - data-confirmar="mensaje": en un boton o formulario, pide confirmacion
     antes de enviar.
   - data-autoenviar: en un select, envia su formulario al cambiar el valor.
   - data-avance="40": en una barra de avance, fija su ancho en porcentaje. */
(function () {
  document.addEventListener("click", (evento) => {
    const boton = evento.target.closest("button[data-confirmar], a[data-confirmar]");
    if (boton && !window.confirm(boton.dataset.confirmar)) {
      evento.preventDefault();
      evento.stopPropagation();
    }
  });

  document.addEventListener("submit", (evento) => {
    const formulario = evento.target;
    if (formulario.matches("form[data-confirmar]") &&
        !window.confirm(formulario.dataset.confirmar)) {
      evento.preventDefault();
    }
  });

  document.addEventListener("change", (evento) => {
    const campo = evento.target;
    if (campo.matches("[data-autoenviar]") && campo.form) {
      campo.form.submit();
    }
  });

  const fijarAvance = (barra) => {
    const valor = Math.max(0, Math.min(100, Number.parseFloat(String(barra.dataset.avance).replace(",", ".")) || 0));
    barra.style.width = valor + "%";
  };
  document.querySelectorAll("[data-avance]").forEach(fijarAvance);
})();
