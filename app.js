/* =====================================================================
   app.js — Interfaz de la pizarra (NO contiene matemáticas).

   Lee el formulario, se lo manda al motor de Python (worker.js) y pinta
   con KaTeX los pasos que devuelve. Todo el cálculo está en motor/*.py.

   ¿Qué puedes tocar sin miedo?
     · TEXTOS (justo debajo): todos los mensajes que ve el usuario.
     · TIEMPO_MAXIMO_MS: tiempo máximo de un cálculo antes de cortarlo.
     · Los colores están en estilo.css (variables de :root).
   ===================================================================== */
"use strict";

// ---------------------------------------------------------------------
// Textos de la interfaz (cámbialos aquí)
// ---------------------------------------------------------------------
const TEXTOS = {
  resolver: "Resolver",
  preparando: "Preparando…",
  reiniciando: "Reiniciando motor…",
  calculando: "Calculando…",
  tiempoAgotado: "El cálculo ha superado los 60 s y se ha detenido. Prueba con un sistema más sencillo.",
  cancelado: "Cálculo cancelado.",
  falloCarga: "No se ha podido cargar el motor de Python",
  archivoLocal: "Has abierto index.html con doble clic y el navegador bloquea la carga de los archivos " +
                "del motor. Sírvela en local con «python -m http.server 8000» y abre http://localhost:8000.",
  pizarraVacia: "Escribe la matriz Â (o elige un ejemplo) y pulsa <b>Resolver</b>.",
  partes: {
    "1": "Parte 1: solución homogénea y $e^{\\hat At}$",
    "2": "Parte 2: solución particular $\\vec y_p(t)$",
    "3": "Parte 3: solución total y condiciones iniciales",
    "V": "Comprobación",
  },
  // lo mismo, en corto, para la barra de las diapositivas
  partesCortas: {
    "1": "Parte 1 · homogénea",
    "2": "Parte 2 · particular",
    "3": "Parte 3 · solución total",
    "V": "Comprobación",
  },
  botonVerificar: "Comprobar<span class=\"largo\"> solución: $\\dot{\\vec y}=\\hat A\\vec y+\\vec f$</span>",
};

const TIEMPO_MAXIMO_MS = 60000;        // 60 s por cálculo
const TIEMPO_TESTS_MS = 240000;        // los 9 tests juntos pueden tardar más

// ---------------------------------------------------------------------
// Estado de la página
// ---------------------------------------------------------------------
const estado = {
  n: 2,
  homogeneo: true,
  modo: "general",
  motorListo: false,
  ocupado: false,
  solucion: null,   // última solución (para «Comprobar»)
  vista: "diapos",  // "diapos" o "scroll" (se recuerda en este navegador)
  pasos: [],        // datos de los pasos que ha mandado el motor
  mostrados: 0,     // cuántos pasos se han visto ya
  elementos: [],    // vista scroll: un <article> por paso
  diapos: [],       // vista diapositivas: un <div> por diapositiva
  diapoDePaso: [],  // primera diapositiva de cada paso
  diapoActual: 0,
  diapoAlPintar: null,
};

const $ = (id) => document.getElementById(id);

// ---------------------------------------------------------------------
// Comunicación con el motor (Web Worker)
// ---------------------------------------------------------------------
let worker = null;
let siguienteId = 1;
const pendientes = new Map();

function crearWorker() {
  worker = new Worker("worker.js");
  worker.onmessage = (ev) => {
    const m = ev.data;
    if (m.tipo === "estado") {
      $("carga-estado").textContent = m.texto;
    } else if (m.tipo === "listo") {
      estado.motorListo = true;
      $("carga").hidden = true;
      actualizarBotones();
      revalidarTodo();
    } else if (m.tipo === "fallo") {
      mostrarFalloCarga(m.error);
    } else if (m.tipo === "respuesta") {
      const p = pendientes.get(m.id);
      if (!p) return;
      pendientes.delete(m.id);
      clearTimeout(p.temporizador);
      if (m.ok) p.resolver(m.resultado);
      else p.rechazar(new Error(m.error));
    }
  };
  worker.onerror = (e) => mostrarFalloCarga(e.message || "error en el worker");
}

/** Manda una petición al motor. Si tarda más de `limite` ms, reinicia el motor. */
function llamar(accion, datos, limite) {
  return new Promise((resolver, rechazar) => {
    const id = siguienteId++;
    const temporizador = limite
      ? setTimeout(() => reiniciarMotor(TEXTOS.tiempoAgotado), limite)
      : null;
    pendientes.set(id, { resolver, rechazar, temporizador });
    worker.postMessage({ id, accion, datos });
  });
}

/** Mata el worker (cancelar o tiempo agotado) y crea uno nuevo. */
function reiniciarMotor(motivo) {
  worker.terminate();
  for (const [, p] of pendientes) {
    clearTimeout(p.temporizador);
    p.rechazar(new Error(motivo));
  }
  pendientes.clear();
  estado.motorListo = false;
  estado.ocupado = false;
  crearWorker();
  actualizarBotones();
}

function mostrarFalloCarga(error) {
  $("carga").hidden = false;
  $("carga").querySelector(".carga-titulo").textContent = TEXTOS.falloCarga;
  $("carga-estado").textContent =
    location.protocol === "file:" ? TEXTOS.archivoLocal : "(" + error + ")";
  $("boton-resolver").textContent = "—";
}

// ---------------------------------------------------------------------
// Formulario: cuadrícula de Â, vector f(t), t0 e y(t0)
// ---------------------------------------------------------------------
function crearCelda(id, tipo, valor, placeholder) {
  const inp = document.createElement("input");
  inp.className = "celda";
  inp.id = id;
  inp.dataset.tipo = tipo;
  inp.value = valor;
  inp.placeholder = placeholder;
  inp.autocomplete = "off";
  inp.spellcheck = false;
  inp.setAttribute("aria-label", id.replace(/_/g, " "));
  return inp;
}

function valor(id, porDefecto) {
  const el = $(id);
  return el ? el.value : porDefecto;
}

/** (Re)construye las casillas para la dimensión actual, conservando lo escrito. */
function construirFormulario() {
  const n = estado.n;
  const viejoA = {}, viejoF = {}, viejoY = {};
  for (let i = 0; i < 5; i++) {
    viejoF[i] = valor("f_" + i, "");
    viejoY[i] = valor("y0_" + i, "0");
    for (let j = 0; j < 5; j++) viejoA[i + "_" + j] = valor("A_" + i + "_" + j, "");
  }
  const cA = $("cuadricula-A");
  cA.innerHTML = "";
  cA.style.gridTemplateColumns = "repeat(" + n + ", auto)";
  for (let i = 0; i < n; i++)
    for (let j = 0; j < n; j++)
      cA.appendChild(crearCelda("A_" + i + "_" + j, "A", viejoA[i + "_" + j], "0"));

  const cF = $("vector-f");
  cF.innerHTML = "";
  for (let i = 0; i < n; i++) cF.appendChild(crearCelda("f_" + i, "f", viejoF[i], "0"));

  const cY = $("vector-y0");
  cY.innerHTML = "";
  for (let i = 0; i < n; i++) cY.appendChild(crearCelda("y0_" + i, "y0", viejoY[i], "0"));

  $("bloque-f").hidden = estado.homogeneo;
  $("bloque-pvi").hidden = estado.modo !== "pvi";
  actualizarAviso();
}

function leerFormulario() {
  const n = estado.n;
  const A = [], f = [], y0 = [];
  for (let i = 0; i < n; i++) {
    const fila = [];
    for (let j = 0; j < n; j++) fila.push($("A_" + i + "_" + j).value);
    A.push(fila);
    f.push(estado.homogeneo ? "0" : $("f_" + i).value);
    y0.push($("y0_" + i).value);
  }
  const datos = { n, A, f, modo: estado.modo };
  if (estado.modo === "pvi") {
    datos.t0 = $("campo-t0").value;
    datos.y0 = y0;
  }
  return datos;
}

function activarEn(grupo, atributo, valorActivo) {
  for (const b of $(grupo).querySelectorAll("button"))
    b.classList.toggle("activo", b.dataset[atributo] === String(valorActivo));
}

// --- validación en vivo (la hace Python: entrada.validar_celda) ---
const temporizadoresValidacion = new Map();

function programarValidacion(inp) {
  clearTimeout(temporizadoresValidacion.get(inp.id));
  temporizadoresValidacion.set(inp.id, setTimeout(() => validarCelda(inp), 350));
}

async function validarCelda(inp) {
  if (!estado.motorListo) return;
  if (inp.value.trim() === "") { marcarCelda(inp, null); return; }
  const tipo = inp.dataset.tipo === "t0" ? "t0" : inp.dataset.tipo;
  try {
    const r = await llamar("validar", { texto: inp.value, tipo }, 0);
    marcarCelda(inp, r.ok ? null : r.error);
  } catch (e) { /* el motor se reinició: no pasa nada */ }
}

function revalidarTodo() {
  for (const inp of document.querySelectorAll(".celda")) if (inp.value.trim() !== "") validarCelda(inp);
}

function marcarCelda(inp, error) {
  inp.classList.toggle("invalida", !!error);
  inp.title = error || "";
  actualizarAviso();
}

function actualizarAviso() {
  const mensajes = [];
  for (const inp of document.querySelectorAll(".celda.invalida")) {
    if (inp.closest("[hidden]")) continue;
    if (inp.title && !mensajes.includes(inp.title)) mensajes.push(inp.title);
  }
  const aviso = $("aviso-entrada");
  aviso.hidden = mensajes.length === 0;
  aviso.textContent = mensajes.join(" · ");
}

// ---------------------------------------------------------------------
// Pintar en la pizarra
//
// Los pasos que manda el motor se guardan en estado.pasos (datos) y se
// pintan de una de dos formas:
//   · VISTA DIAPOSITIVAS: un paso por pantalla (si no cabe, se parte en
//     varias). Se pasa con las flechas, el teclado o deslizando el dedo.
//   · VISTA SCROLL: la de siempre, los pasos uno debajo de otro.
// ---------------------------------------------------------------------
/** Escapa HTML pero deja pasar <b>, </b> y <br> (los usa el motor). */
function textoSeguro(t) {
  return String(t)
    .replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;")
    .replace(/&lt;(\/?)b&gt;/g, "<$1b>").replace(/&lt;br\s*\/?&gt;/g, "<br>");
}

function renderizarDolares(el) {
  if (window.renderMathInElement) {
    renderMathInElement(el, {
      delimiters: [{ left: "$", right: "$", display: false }],
      throwOnError: false, strict: "ignore",
    });
  }
}

function formula(tex) {
  const div = document.createElement("div");
  div.className = "formula";
  try {
    katex.render(tex, div, { displayMode: true, throwOnError: false, strict: "ignore" });
  } catch (e) {
    div.textContent = tex;
  }
  return div;
}

// Recuadro «a mano alzada» para la solución final (dos trazos ligeramente distintos).
const BORDE_TIZA =
  '<svg class="borde-tiza" viewBox="0 0 100 100" preserveAspectRatio="none" aria-hidden="true">' +
  '<path vector-effect="non-scaling-stroke" d="M1.5,2.5 C25,0.8 60,3.2 98.2,1.6 C99.4,30 97.8,65 98.6,97.8 C70,99.2 35,96.9 1.2,98.4 C0.4,70 2.4,35 1.5,2.5 Z"/>' +
  '<path vector-effect="non-scaling-stroke" style="opacity:.45" d="M3,1.2 C40,2.6 72,0.4 99.3,3.1 C98.4,40 99.6,72 97.4,99.2 C60,97.6 28,99.6 0.6,97.1 C2,60 0.3,30 3,1.2"/>' +
  "</svg>";

/** ¿Empieza una parte nueva en el paso i? */
function empiezaParte(i) {
  const p = estado.pasos[i];
  if (!TEXTOS.partes[p.parte]) return false;
  return i === 0 || String(estado.pasos[i - 1].parte) !== String(p.parte);
}

/** Cabecera de un paso (título de parte si toca + id, título y referencia). */
function cabeceraPaso(art, p, conParte, continuacion) {
  if (conParte) {
    const h = document.createElement("h2");
    h.className = "titulo-parte titulo-tiza";
    h.innerHTML = textoSeguro(TEXTOS.partes[p.parte]);
    renderizarDolares(h);
    art.appendChild(h);
  }
  const cab = document.createElement("div");
  cab.className = "paso-cabecera";
  cab.innerHTML =
    '<span class="paso-id">' + textoSeguro(p.id || "") + "</span>" +
    '<h3 class="titulo-tiza">' + textoSeguro(p.titulo || "") + "</h3>" +
    (continuacion ? '<span class="continua">(continuación)</span>' : "") +
    (p.ref ? '<span class="ref">→ ' + textoSeguro(p.ref) + "</span>" : "");
  renderizarDolares(cab);
  art.appendChild(cab);
}

function articuloVacio(p) {
  const art = document.createElement("article");
  art.className = "paso grano " + (p.color || "blanco") + (p.clase ? " " + p.clase : "");
  return art;
}

function textoPaso(p) {
  const tx = document.createElement("p");
  tx.className = "texto";
  tx.innerHTML = textoSeguro(p.texto);
  renderizarDolares(tx);
  return tx;
}

function tablaTests(res) {
  const tabla = document.createElement("table");
  tabla.className = "tabla-tests";
  for (const x of res) {
    const fila = tabla.insertRow();
    fila.insertCell().textContent = x.ok ? "✔" : "✘";
    fila.cells[0].className = x.ok ? "bien" : "mal";
    fila.insertCell().textContent = x.id + ". " + x.titulo;
    fila.insertCell().textContent = x.ok ? x.segundos + " s" : x.mensaje;
  }
  return tabla;
}

/** Paso completo (vista scroll). */
function crearPaso(i) {
  const p = estado.pasos[i];
  const art = articuloVacio(p);
  cabeceraPaso(art, p, empiezaParte(i), false);
  if (p.texto) art.appendChild(textoPaso(p));
  for (const tex of p.latex || []) art.appendChild(formula(tex));
  if (p.tabla) art.appendChild(tablaTests(p.tabla));
  if (p.clase === "final") art.insertAdjacentHTML("beforeend", BORDE_TIZA);
  return art;
}

// --- avisos de fórmulas demasiado anchas -----------------------------
function esMovilVertical() {
  return window.matchMedia("(orientation: portrait) and (max-width: 700px)").matches;
}

/** Marca las fórmulas que no caben y, en móvil vertical, sugiere girarlo. */
function marcarDesbordes(raiz) {
  let alguna = false;
  for (const f of raiz.querySelectorAll(".formula")) {
    const desborda = f.scrollWidth > f.clientWidth + 4;
    f.classList.toggle("desborda", desborda);
    alguna = alguna || desborda;
  }
  return alguna;
}

function actualizarPistaGirar() {
  let hay = false;
  if (esMovilVertical()) {
    if (estado.vista === "diapos") {
      const d = estado.diapos[estado.diapoActual];
      hay = !!d && marcarDesbordes(d);
    } else {
      for (const art of $("pasos").querySelectorAll(".paso:not([hidden])")) {
        if (marcarDesbordes(art)) hay = true;
      }
    }
  }
  $("pista-girar").hidden = !hay;
}

// --- vista scroll ----------------------------------------------------
function pintarScroll() {
  const cont = $("pasos");
  cont.className = "pasos";
  cont.innerHTML = "";
  estado.elementos = [];
  for (let i = 0; i < estado.pasos.length; i++) {
    const art = crearPaso(i);
    art.hidden = i >= estado.mostrados;
    cont.appendChild(art);
    estado.elementos.push(art);
  }
  for (const art of estado.elementos) if (!art.hidden) marcarDesbordes(art);
}

// --- vista diapositivas ----------------------------------------------
/** Construye las diapositivas. Un paso que no cabe se reparte en varias:
    la primera lleva título y texto; las siguientes, «(continuación)». */
function construirDiapos() {
  const cont = $("pasos");
  cont.className = "pasos modo-diapos";
  cont.innerHTML = "";
  estado.diapos = [];
  estado.diapoDePaso = [];
  const alto = cont.clientHeight;

  const nuevaDiapo = (i, art) => {
    const d = document.createElement("div");
    d.className = "diapo midiendo";
    d.dataset.paso = i;
    d.appendChild(art);
    cont.appendChild(d);
    estado.diapos.push(d);
    return d;
  };
  const cabe = (d) => d.scrollHeight <= alto + 1;

  for (let i = 0; i < estado.pasos.length; i++) {
    const p = estado.pasos[i];
    estado.diapoDePaso[i] = estado.diapos.length;

    let art = articuloVacio(p);
    cabeceraPaso(art, p, empiezaParte(i), false);
    if (p.texto) art.appendChild(textoPaso(p));
    if (p.tabla) art.appendChild(tablaTests(p.tabla));
    let d = nuevaDiapo(i, art);
    let formulasEnDiapo = 0;

    for (const tex of p.latex || []) {
      const f = formula(tex);
      art.appendChild(f);
      if (!cabe(d) && formulasEnDiapo > 0) {
        // no cabe: pasa a una diapositiva nueva («continuación»)
        f.remove();
        if (p.clase === "final") art.insertAdjacentHTML("beforeend", BORDE_TIZA);
        art = articuloVacio(p);
        cabeceraPaso(art, p, false, true);
        art.appendChild(f);
        d = nuevaDiapo(i, art);
        formulasEnDiapo = 0;
      }
      formulasEnDiapo++;
    }
    if (p.clase === "final") art.insertAdjacentHTML("beforeend", BORDE_TIZA);
  }
  for (const d of estado.diapos) d.classList.remove("midiendo");
  construirListaSaltar();
}

/** Menú «Saltar a…», con los pasos agrupados por partes. */
function construirListaSaltar() {
  const lista = $("lista-saltar");
  lista.innerHTML = "";
  for (let i = 0; i < estado.pasos.length; i++) {
    const p = estado.pasos[i];
    if (empiezaParte(i)) {
      const h = document.createElement("h4");
      h.innerHTML = textoSeguro(TEXTOS.partes[p.parte]);
      lista.appendChild(h);
    }
    const b = document.createElement("button");
    b.type = "button";
    b.dataset.diapo = estado.diapoDePaso[i];
    b.innerHTML = '<span class="id">' + textoSeguro(p.id || "") + "</span><span>" +
      textoSeguro(p.titulo || "") + "</span>";
    lista.appendChild(b);
  }
  renderizarDolares(lista);
}

function irADiapo(k, direccion) {
  const n = estado.diapos.length;
  if (n === 0) return;
  k = Math.max(0, Math.min(n - 1, k));
  const anterior = estado.diapos[estado.diapoActual];
  if (anterior) anterior.classList.remove("actual", "entra-derecha", "entra-izquierda");
  estado.diapoActual = k;
  const d = estado.diapos[k];
  d.classList.add("actual");
  if (direccion) {
    void d.offsetWidth;
    d.classList.add(direccion > 0 ? "entra-derecha" : "entra-izquierda");
  }
  d.scrollTop = 0;
  const paso = Number(d.dataset.paso);
  estado.mostrados = Math.max(estado.mostrados, paso + 1);
  actualizarNav();
  actualizarPistaGirar();
}

function actualizarNav() {
  const n = estado.diapos.length;
  const k = estado.diapoActual;
  $("nav-diapos").hidden = estado.vista !== "diapos" || n === 0;
  if (n === 0) return;
  $("nav-contador").textContent = (k + 1) + " / " + n;
  const p = estado.pasos[Number(estado.diapos[k].dataset.paso)];
  $("nav-parte").textContent = TEXTOS.partesCortas[p.parte] || "";
  $("diapo-anterior").disabled = k === 0;
  $("diapo-siguiente").disabled = k === n - 1;
  for (const b of $("lista-saltar").querySelectorAll("button")) {
    b.classList.toggle("actual", Number(b.dataset.diapo) === estado.diapoDePaso[Number(estado.diapos[k].dataset.paso)]);
  }
}

// --- cambiar de vista y repintar -------------------------------------
function pintar() {
  document.querySelector(".pizarra").classList.toggle("vista-diapos", estado.vista === "diapos");
  $("boton-vista").innerHTML = '<span class="largo">Vista: </span>' +
    (estado.vista === "diapos" ? "diapositivas" : "scroll");
  const vacia = estado.pasos.length === 0;
  if (vacia) {
    const cont = $("pasos");
    cont.className = "pasos";
    cont.innerHTML = '<p class="pizarra-vacia" id="pizarra-vacia">' + TEXTOS.pizarraVacia + "</p>";
    estado.elementos = [];
    estado.diapos = [];
    $("nav-diapos").hidden = true;
    $("pista-girar").hidden = true;
  } else if (estado.vista === "diapos") {
    construirDiapos();
    const paso = Math.max(0, estado.mostrados - 1);
    irADiapo(estado.diapoAlPintar ?? estado.diapoDePaso[paso] ?? 0, 0);
    estado.diapoAlPintar = null;
  } else {
    $("nav-diapos").hidden = true;
    pintarScroll();
    actualizarPistaGirar();
  }
  actualizarBotones();
}

function cambiarVista() {
  if (estado.vista === "diapos") {
    // al pasar a scroll se ve todo hasta el paso donde estabas
    const d = estado.diapos[estado.diapoActual];
    const pasoActual = d ? Number(d.dataset.paso) : 0;
    estado.vista = "scroll";
    guardarVista();
    pintar();
    const art = estado.elementos[pasoActual];
    if (art) art.scrollIntoView({ block: "start", behavior: "smooth" });
  } else {
    estado.vista = "diapos";
    guardarVista();
    pintar();
  }
}

function guardarVista() {
  try { localStorage.setItem("pizarra.vista", estado.vista); } catch (e) { /* da igual */ }
}
function leerVista() {
  try { return localStorage.getItem("pizarra.vista") === "scroll" ? "scroll" : "diapos"; } catch (e) { return "diapos"; }
}

// --- gestos y teclado (vista diapositivas) ---------------------------
function activarGestos() {
  const cont = $("pasos");
  let inicio = null;

  cont.addEventListener("touchstart", (e) => {
    if (estado.vista !== "diapos" || e.touches.length !== 1) { inicio = null; return; }
    const t = e.touches[0];
    // si el dedo empieza sobre una fórmula que se puede desplazar, el gesto es suyo
    const f = e.target.closest(".formula");
    const formulaDesplazable = f && f.scrollWidth > f.clientWidth + 4;
    inicio = formulaDesplazable ? null : { x: t.clientX, y: t.clientY, t: Date.now() };
  }, { passive: true });

  cont.addEventListener("touchend", (e) => {
    if (!inicio) return;
    const t = e.changedTouches[0];
    const dx = t.clientX - inicio.x, dy = t.clientY - inicio.y;
    const rapido = Date.now() - inicio.t < 700;
    inicio = null;
    if (rapido && Math.abs(dx) > 50 && Math.abs(dx) > 1.6 * Math.abs(dy)) {
      irADiapo(estado.diapoActual + (dx < 0 ? 1 : -1), dx < 0 ? 1 : -1);
    }
  }, { passive: true });

  document.addEventListener("keydown", (e) => {
    if (estado.vista !== "diapos" || estado.diapos.length === 0) return;
    if (document.documentElement.classList.contains("con-portada")) return;
    const tag = (e.target.tagName || "").toLowerCase();
    if (tag === "input" || tag === "textarea" || e.altKey || e.ctrlKey || e.metaKey) return;
    if (e.key === "ArrowRight" || e.key === "PageDown") {
      e.preventDefault(); irADiapo(estado.diapoActual + 1, 1);
    } else if (e.key === "ArrowLeft" || e.key === "PageUp") {
      e.preventDefault(); irADiapo(estado.diapoActual - 1, -1);
    } else if (e.key === "Home") {
      e.preventDefault(); irADiapo(0, -1);
    } else if (e.key === "End") {
      e.preventDefault(); irADiapo(estado.diapos.length - 1, 1);
    }
  });

  $("diapo-anterior").addEventListener("click", () => irADiapo(estado.diapoActual - 1, -1));
  $("diapo-siguiente").addEventListener("click", () => irADiapo(estado.diapoActual + 1, 1));
  $("lista-saltar").addEventListener("click", (e) => {
    const b = e.target.closest("button[data-diapo]");
    if (!b) return;
    const k = Number(b.dataset.diapo);
    irADiapo(k, k >= estado.diapoActual ? 1 : -1);
    $("saltar").open = false;
  });
  document.addEventListener("click", (e) => {
    if (!e.target.closest("#saltar")) $("saltar").open = false;
  });

  // al cambiar el tamaño (o girar el móvil) se rehacen las diapositivas
  let temporizador = null;
  window.addEventListener("resize", () => {
    clearTimeout(temporizador);
    temporizador = setTimeout(() => {
      if (estado.vista === "diapos" && estado.diapos.length) {
        const d = estado.diapos[estado.diapoActual];
        const paso = d ? Number(d.dataset.paso) : 0;
        const primera = estado.diapoDePaso[paso];
        const desplazamiento = estado.diapoActual - primera;   // dentro del mismo paso
        construirDiapos();
        const ultimaDelPaso = (estado.diapoDePaso[paso + 1] ?? estado.diapos.length) - 1;
        irADiapo(Math.min(estado.diapoDePaso[paso] + desplazamiento, ultimaDelPaso), 0);
      } else {
        actualizarPistaGirar();
      }
    }, 200);
  });
}

// --- operaciones sobre los pasos --------------------------------------
function limpiarPizarra() {
  estado.pasos = [];
  estado.mostrados = 0;
  estado.diapoActual = 0;
  estado.solucion = null;
  pintar();
}

/** Añade pasos. En diapositivas salta al primero nuevo; en scroll los
    revela todos si revelarTodos es true. */
function anadirPasos(pasos, revelarTodos) {
  const primeroNuevo = estado.pasos.length;
  estado.pasos.push(...pasos);
  if (revelarTodos) estado.mostrados = estado.pasos.length;
  if (estado.vista === "diapos") {
    construirDiapos();
    if (primeroNuevo === 0) irADiapo(0, 0);
    else irADiapo(estado.diapoDePaso[primeroNuevo] ?? 0, 1);
  } else {
    pintarScroll();
    actualizarPistaGirar();
  }
  actualizarBotones();
}

function siguientePaso() {
  if (estado.mostrados >= estado.elementos.length) return;
  const el = estado.elementos[estado.mostrados++];
  el.hidden = false;
  el.classList.remove("escribiendo");
  void el.offsetWidth;                 // reinicia la animación de «escritura»
  el.classList.add("escribiendo");
  el.scrollIntoView({ block: "nearest", behavior: "smooth" });
  actualizarPistaGirar();
  actualizarBotones();
}

function verTodos() {
  while (estado.mostrados < estado.elementos.length) {
    estado.elementos[estado.mostrados++].hidden = false;
  }
  actualizarPistaGirar();
  actualizarBotones();
}

function actualizarBotones() {
  const hay = estado.pasos.length > 0;
  const quedan = estado.mostrados < estado.pasos.length;
  $("boton-siguiente").disabled = !quedan;
  $("boton-todos").disabled = !quedan;
  $("boton-verificar").disabled = !estado.solucion || !estado.motorListo || estado.ocupado;
  $("contador").textContent = hay ? "Paso " + Math.min(estado.mostrados, estado.pasos.length) + " de " + estado.pasos.length : "";

  const br = $("boton-resolver");
  br.disabled = !estado.motorListo || estado.ocupado;
  br.textContent = estado.ocupado ? TEXTOS.calculando
    : estado.motorListo ? TEXTOS.resolver : TEXTOS.preparando;
  $("boton-cancelar").hidden = !estado.ocupado;
  $("boton-tests").disabled = !estado.motorListo || estado.ocupado;
}

/** En diapositivas, coloca la pizarra entera en la pantalla. */
function enfocarPizarra() {
  const marco = document.querySelector(".pizarra-marco");
  const r = marco.getBoundingClientRect();
  if (r.top < -2 || r.bottom > window.innerHeight + 2) {
    marco.scrollIntoView({ behavior: "smooth", block: "start" });
  }
}

function avisoEnPizarra(titulo, texto) {
  anadirPasos([{ parte: "", id: "!", color: "coral", clase: "aviso", titulo, texto, latex: [], ref: "" }], true);
}

// ---------------------------------------------------------------------
// Acciones principales
// ---------------------------------------------------------------------
async function resolver() {
  if (!estado.motorListo || estado.ocupado) return;
  const datos = leerFormulario();
  limpiarPizarra();
  estado.ocupado = true;
  actualizarBotones();
  try {
    const r = await llamar("resolver", datos, TIEMPO_MAXIMO_MS);
    for (const inp of document.querySelectorAll(".celda.invalida")) marcarCelda(inp, null);
    if (r.errores) {
      for (const [id, msg] of Object.entries(r.errores)) {
        const inp = id === "t0" ? $("campo-t0") : $(id);
        if (inp) marcarCelda(inp, msg);
      }
    }
    const pasos = r.pasos || [];
    if (r.ok) {
      estado.solucion = r.solucion;
      estado.mostrados = 0;
      anadirPasos(pasos, false);
      if (estado.vista === "scroll") siguientePaso();
      else enfocarPizarra();
    } else {
      anadirPasos(pasos, true);
      avisoEnPizarra("No se puede continuar", r.error || "Error desconocido.");
      if (r.detalle) console.error(r.detalle);
    }
  } catch (e) {
    avisoEnPizarra("Cálculo interrumpido", e.message);
  } finally {
    estado.ocupado = false;
    actualizarBotones();
  }
}

async function verificar() {
  if (!estado.solucion || estado.ocupado) return;
  estado.ocupado = true;
  actualizarBotones();
  try {
    const r = await llamar("comprobar", estado.solucion, TIEMPO_MAXIMO_MS);
    if (estado.vista === "scroll") verTodos();
    if (r.pasos) anadirPasos(r.pasos, true);
    else avisoEnPizarra("No se pudo comprobar", r.error || "");
    if (estado.vista === "scroll") {
      const ult = estado.elementos[estado.elementos.length - 1];
      if (ult) ult.scrollIntoView({ block: "center", behavior: "smooth" });
    }
  } catch (e) {
    avisoEnPizarra("Comprobación interrumpida", e.message);
  } finally {
    estado.ocupado = false;
    actualizarBotones();
  }
}

async function ejecutarTests() {
  if (!estado.motorListo || estado.ocupado) return;
  estado.ocupado = true;
  actualizarBotones();
  limpiarPizarra();
  try {
    const res = await llamar("tests", {}, TIEMPO_TESTS_MS);
    const bien = res.filter((x) => x.ok).length;
    anadirPasos([{
      parte: "", id: "T", color: bien === res.length ? "amarillo" : "coral",
      titulo: "Tests: " + bien + " de " + res.length + " casos correctos",
      texto: "Los mismos 9 casos de tests/test_casos.py, ejecutados aquí con Pyodide.",
      latex: [], ref: "sección 8", tabla: res,
    }], true);
  } catch (e) {
    avisoEnPizarra("Tests interrumpidos", e.message);
  } finally {
    estado.ocupado = false;
    actualizarBotones();
  }
}

// ---------------------------------------------------------------------
// Ejemplos precargados (ejemplos.json)
// ---------------------------------------------------------------------
async function cargarEjemplos() {
  try {
    const r = await fetch("ejemplos.json", { cache: "no-cache" });
    const lista = await r.json();
    const cont = $("ejemplos");
    for (const ej of lista) {
      const b = document.createElement("button");
      b.type = "button";
      b.innerHTML = '<span class="ruta">' + textoSeguro(ej.referencia.ruta) + "</span>" +
        textoSeguro(ej.id + ". " + ej.titulo) +
        ' <span class="tipo-ej">(' + textoSeguro(ej.etiqueta) + ")</span>";
      b.addEventListener("click", () => cargarEjemplo(ej.datos));
      cont.appendChild(b);
    }
  } catch (e) {
    $("ejemplos").textContent = "(no se pudieron cargar los ejemplos)";
  }
}

function cargarEjemplo(d) {
  estado.n = d.n;
  estado.homogeneo = (d.f || []).every((x) => String(x).trim() === "0" || String(x).trim() === "");
  estado.modo = d.modo || "general";
  activarEn("selector-n", "n", estado.n);
  activarEn("selector-tipo", "tipo", estado.homogeneo ? "homogeneo" : "no_homogeneo");
  activarEn("selector-modo", "modo", estado.modo);
  construirFormulario();
  for (let i = 0; i < d.n; i++) {
    for (let j = 0; j < d.n; j++) $("A_" + i + "_" + j).value = d.A[i][j];
    $("f_" + i).value = d.f ? d.f[i] : "0";
    $("y0_" + i).value = d.y0 ? d.y0[i] : "0";
  }
  $("campo-t0").value = d.t0 || "0";
  for (const inp of document.querySelectorAll(".celda")) marcarCelda(inp, null);
  if (estado.vista === "scroll" && window.matchMedia("(max-width: 900px)").matches) $("titulo-pizarra").scrollIntoView({ behavior: "smooth", block: "start" });
  resolver();
}

// ---------------------------------------------------------------------
// Arranque
// ---------------------------------------------------------------------
function iniciar() {
  // fórmulas fijas de la interfaz (atributo data-tex)
  for (const el of document.querySelectorAll("[data-tex]")) {
    try { katex.render(el.dataset.tex, el, { throwOnError: false }); } catch (e) { /* se queda el texto */ }
  }
  $("boton-verificar").innerHTML = TEXTOS.botonVerificar;
  renderizarDolares($("boton-verificar"));

  construirFormulario();

  $("selector-n").addEventListener("click", (e) => {
    const b = e.target.closest("button[data-n]");
    if (!b) return;
    estado.n = Number(b.dataset.n);
    activarEn("selector-n", "n", estado.n);
    construirFormulario();
  });
  $("selector-tipo").addEventListener("click", (e) => {
    const b = e.target.closest("button[data-tipo]");
    if (!b) return;
    estado.homogeneo = b.dataset.tipo === "homogeneo";
    activarEn("selector-tipo", "tipo", b.dataset.tipo);
    construirFormulario();
  });
  $("selector-modo").addEventListener("click", (e) => {
    const b = e.target.closest("button[data-modo]");
    if (!b) return;
    estado.modo = b.dataset.modo;
    activarEn("selector-modo", "modo", estado.modo);
    construirFormulario();
  });

  // validación en vivo de cualquier casilla + Intro para resolver
  document.querySelector(".panel").addEventListener("input", (e) => {
    if (e.target.classList.contains("celda")) programarValidacion(e.target);
  });
  document.querySelector(".panel").addEventListener("keydown", (e) => {
    if (e.key === "Enter" && e.target.classList.contains("celda")) resolver();
  });
  $("campo-t0").dataset.tipo = "t0";

  $("boton-resolver").addEventListener("click", resolver);
  $("boton-cancelar").addEventListener("click", () => reiniciarMotor(TEXTOS.cancelado));
  $("boton-siguiente").addEventListener("click", siguientePaso);
  $("boton-todos").addEventListener("click", verTodos);
  $("boton-limpiar").addEventListener("click", limpiarPizarra);
  $("boton-verificar").addEventListener("click", verificar);
  $("boton-tests").addEventListener("click", ejecutarTests);
  $("boton-vista").addEventListener("click", cambiarVista);
  activarGestos();

  estado.vista = leerVista();
  pintar();

  cargarEjemplos();
  if (location.protocol === "file:") {
    mostrarFalloCarga("");
    return;
  }
  crearWorker();
  actualizarBotones();
}

document.addEventListener("DOMContentLoaded", iniciar);
