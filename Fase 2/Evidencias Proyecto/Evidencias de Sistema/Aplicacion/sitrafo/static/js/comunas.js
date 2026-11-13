/* Buscador de comunas (RF-CLI-04): agrupa las 346 comunas por region y filtra
   la lista mientras el cliente escribe, sin distinguir tildes ni mayusculas. */
(function () {
  const lista = document.getElementById("id_comuna");
  const buscador = document.getElementById("buscar-comuna");
  const aviso = document.getElementById("comuna-sin-resultados");
  if (!lista || !buscador) return;
  const normalizar = (t) => t.normalize("NFD").replace(/[\u0300-\u036f]/g, "").toLowerCase();

  // Agrupar por region: "Comuna (Region)" -> <optgroup label="Region">
  const vacia = lista.querySelector('option[value=""]');
  const grupos = new Map();
  Array.from(lista.options).forEach((op) => {
    if (!op.value) return;
    const m = op.text.match(/^(.*) \((.*)\)$/);
    if (!m) return;
    op.text = m[1];
    op.dataset.buscar = normalizar(m[1] + " " + m[2]);
    if (!grupos.has(m[2])) {
      const g = document.createElement("optgroup");
      g.label = m[2];
      grupos.set(m[2], g);
    }
    grupos.get(m[2]).appendChild(op);
  });
  lista.innerHTML = "";
  if (vacia) { vacia.text = "Seleccione una comuna"; lista.appendChild(vacia); }
  grupos.forEach((g) => lista.appendChild(g));

  buscador.addEventListener("input", () => {
    const q = normalizar(buscador.value.trim());
    let visibles = 0, primera = null;
    grupos.forEach((g) => {
      let enGrupo = 0;
      Array.from(g.children).forEach((op) => {
        const ok = !q || op.dataset.buscar.includes(q);
        op.hidden = !ok;
        if (ok) { enGrupo++; visibles++; if (!primera) primera = op; }
      });
      g.hidden = enGrupo === 0;
    });
    aviso.classList.toggle("d-none", visibles > 0);
    // Con una busqueda, deja seleccionada la primera coincidencia
    const actual = lista.selectedOptions[0];
    if (q && primera && (!actual || !actual.value || actual.hidden)) {
      primera.selected = true;
    }
  });
})();
