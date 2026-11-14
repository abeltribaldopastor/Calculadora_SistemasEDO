/* =====================================================================
   portada.js — Pizarra de bienvenida con dibujos de tiza.

   Sale SOLO al abrir la web (una vez por pestaña: sessionStorage).
   Al tocar la pizarra o pulsar una tecla, un borrador la limpia en
   zigzag (2,4–3,2 s), deja marcas de tiza emborronada y aparece la
   calculadora. Si vuelves a tocar mientras borra, termina al momento.

   ¿Qué puedes tocar sin miedo?
     · TEXTOS_PORTADA: nombre, curso, «Me», «IZI», el meme, la pista.
     · DURACION_BORRADO_MS: lo que tarda el borrador (horizontal / vertical).
     · RESTO_TIZA: cuánto dibujo queda tras borrar (0 = nada, 0.2 = bastante).
     · Las posiciones de cada dibujo están en DIBUJOS (x, y en el
       sistema de coordenadas del SVG: 1600×900 en horizontal y
       900×1600 en vertical).
   ===================================================================== */
"use strict";

const TEXTOS_PORTADA = {
  me: "Me",
  nombre: "Abel Tribaldo Pastor",
  estudios: "Estudiante del Grado en Física · UV · 2.º A",
  izi: "IZI",
  masones: "Masones?",
  pista: "Toca la pizarra o pulsa una tecla para empezar",
};

// lo que tarda el borrador (en vertical hay más pasadas, así que tarda algo más)
const DURACION_BORRADO_MS = { h: 2400, v: 3200 };
const RESTO_TIZA = 0.12;
const CLAVE_SESION = "pizarra.portadaVista";

// ---------------------------------------------------------------------
// Dibujos. Cada uno tiene posición para «h» (horizontal) y «v» (vertical).
// ---------------------------------------------------------------------
const TIZA = "#ebe8df";

function svgTexto(x, y, tam, contenido, extra = "") {
  return `<text x="${x}" y="${y}" font-size="${tam}" ${extra}>${contenido}</text>`;
}

const DIBUJOS = {
  h: {
    ancho: 1600, alto: 900, pasadas: 5,
    cara: { x: 90, y: 120, tam: 470 },
    escudo: { x: 1210, y: 40, tam: 340 },
    adr: { x: 690, y: 445, ancho: 300, giro: -3 },
    masones: { x: 1060, y: 535, tam: 56, giro: -7,
               flecha: "M1052,500 C1030,488 1010,500 996,526", punta: "M996,526 l2,-17 M996,526 l15,-6" },
    me: { x: 690, y: 255, tam: 110 },
    flecha: "M680,225 C620,190 575,215 545,262",          // desde «Me» hasta la cara
    punta: "M545,262 l4,-34 M545,262 l30,-14",
    nombre: { x: 650, y: 345, tam: 58 },
    estudios: { x: 652, y: 395, tam: 36 },
    izi: { x: 1150, y: 720, tam: 120, giro: -9 },
    extras: [
      // ∫ e^x dx = ? tachado
      `<path d="M150,712 C140,700 128,708 130,725 L124,780 C122,796 110,800 102,788" />`,
      svgTexto(150, 760, 54, "e<tspan baseline-shift='super' font-size='34'>x</tspan> dx = ?", "transform='rotate(-3 150 760)'"),
      `<path d="M100,745 C200,738 280,752 345,742" />`,
      // dy/dt = Ây
      svgTexto(700, 120, 50, "dy/dt = Ây", "transform='rotate(-4 700 120)'"),
      // λ² − 4λ + 3 = 0
      svgTexto(110, 868, 40, "λ<tspan baseline-shift='super' font-size='24'>2</tspan> − 4λ + 3 = 0", "transform='rotate(2 110 868)'"),
      // matriz 2x2 suelta
      `<path d="M470,690 C455,720 455,775 470,805 M570,690 C585,720 585,775 570,805" />`,
      svgTexto(488, 738, 40, "1&#160;&#160;2"),
      svgTexto(488, 790, 40, "2&#160;&#160;1"),
      // Σ y marcas de conteo
      svgTexto(1040, 860, 64, "Σ", "transform='rotate(8 1040 860)'"),
      `<path d="M1430,760 l-6,62 M1448,760 l-5,62 M1466,760 l-6,62 M1484,760 l-5,62 M1418,800 L1500,780" />`,
      // monigote
      `<circle cx="1500" cy="560" r="20" /><path d="M1500,580 L1497,640 M1497,600 L1470,620 M1497,600 L1528,612 M1497,640 L1478,690 M1497,640 L1520,688" />`,
      // e^{iπ} + 1 = 0
      svgTexto(760, 830, 42, "e<tspan baseline-shift='super' font-size='26'>iπ</tspan> + 1 = 0", "transform='rotate(-2 760 830)'"),
    ],
  },
  v: {
    ancho: 900, alto: 1600, pasadas: 8,
    cara: { x: 200, y: 400, tam: 500 },
    escudo: { x: 560, y: 50, tam: 300 },
    adr: { x: 490, y: 1250, ancho: 320, giro: -3 },
    masones: { x: 560, y: 1535, tam: 52, giro: -4,
               flecha: "M552,1500 C540,1488 548,1470 566,1456", punta: "M566,1456 l-16,3 M566,1456 l1,15" },
    me: { x: 430, y: 1040, tam: 110 },
    flecha: "M420,1005 C380,970 400,935 420,900",
    punta: "M420,900 l-22,24 M420,900 l12,30",
    nombre: { x: 450, y: 1135, tam: 62, centrado: true },
    estudios: { x: 450, y: 1190, tam: 34, centrado: true },
    izi: { x: 70, y: 250, tam: 120, giro: -10 },
    extras: [
      `<path d="M108,1294 C98,1282 86,1290 88,1306 L82,1358 C80,1374 68,1378 60,1366" />`,
      svgTexto(108, 1340, 50, "e<tspan baseline-shift='super' font-size='32'>x</tspan> dx = ?", "transform='rotate(-3 108 1340)'"),
      `<path d="M58,1326 C160,1318 230,1332 292,1322" />`,
      svgTexto(520, 420, 44, "dy/dt = Ây", "transform='rotate(-5 520 420)'"),
      svgTexto(120, 1490, 64, "Σ", "transform='rotate(8 120 1490)'"),
      `<path d="M262,1440 l-6,58 M278,1440 l-5,58 M294,1440 l-6,58 M310,1440 l-5,58 M250,1478 L324,1460" />`,
      `<circle cx="120" cy="480" r="18" /><path d="M120,498 L118,552 M118,516 L94,534 M118,516 L146,526 M118,552 L100,598 M118,552 L140,596" />`,
    ],
  },
};

/** Camino del borrador: zigzag con pasadas onduladas que se solapan. */
function caminoBorrador(d) {
  const W = d.ancho, H = d.alto, n = d.pasadas, fila = H / n;
  let r = 0.37;                                    // pseudoaleatorio fijo (siempre igual)
  const azar = () => (r = (r * 9301 + 49297) % 233280 / 233280) - 0.5;
  const tramos = 4;                                // ondulaciones por pasada
  let x = -0.06 * W, y = fila * 0.5;
  let c = `M${x.toFixed(0)},${y.toFixed(0)}`;
  for (let i = 0; i < n; i++) {
    const derecha = i % 2 === 0;
    const yc = fila * (i + 0.5);
    for (let k = 1; k <= tramos; k++) {
      const xf = derecha ? -0.06 * W + 1.12 * W * k / tramos : 1.06 * W - 1.12 * W * k / tramos;
      const yf = yc + azar() * fila * 0.35;
      const xm = (x + xf) / 2, ym = (y + yf) / 2 + azar() * fila * 0.5;
      c += ` Q${xm.toFixed(0)},${ym.toFixed(0)} ${xf.toFixed(0)},${yf.toFixed(0)}`;
      x = xf; y = yf;
    }
    if (i < n - 1) {                               // giro corto hacia la fila de abajo
      const yn = fila * (i + 1.5);
      const xg = derecha ? x + 0.02 * W : x - 0.02 * W;
      c += ` Q${xg.toFixed(0)},${((y + yn) / 2).toFixed(0)} ${x.toFixed(0)},${yn.toFixed(0)}`;
      y = yn;
    }
  }
  return { d: c, grosor: fila * 1.32 };
}

function construirSVG(d) {
  const izi = d.izi, adr = d.adr, mas = d.masones;
  const anclaN = d.nombre.centrado ? "middle" : "start";
  const camino = caminoBorrador(d);
  const altoAdr = adr.ancho * 426 / 700;           // proporción de arte/adr-tiza.png
  return `
<svg class="portada-svg" viewBox="0 0 ${d.ancho} ${d.alto}" preserveAspectRatio="xMidYMid meet" aria-hidden="true">
  <defs>
    <filter id="filtro-tiza" x="-5%" y="-5%" width="110%" height="110%">
      <feTurbulence type="fractalNoise" baseFrequency="0.85" numOctaves="2" seed="4" result="ruido"/>
      <feDisplacementMap in="SourceGraphic" in2="ruido" scale="2.4" xChannelSelector="R" yChannelSelector="G" result="temblor"/>
      <feTurbulence type="fractalNoise" baseFrequency="1.4" numOctaves="1" seed="9" result="grano"/>
      <feColorMatrix in="grano" type="matrix" values="0 0 0 0 0  0 0 0 0 0  0 0 0 0 0  3 0 0 0 -0.55" result="mascara"/>
      <feComposite in="temblor" in2="mascara" operator="in"/>
    </filter>
    <!-- borde irregular de la pasada del borrador -->
    <filter id="filtro-pasada" x="-10%" y="-10%" width="120%" height="120%">
      <feTurbulence type="fractalNoise" baseFrequency="0.035 0.12" numOctaves="2" seed="11" result="r"/>
      <feDisplacementMap in="SourceGraphic" in2="r" scale="${(camino.grosor * 0.28).toFixed(0)}" xChannelSelector="R" yChannelSelector="G"/>
    </filter>
    <!-- marca de polvo de tiza que deja el borrador (rayado en el sentido del movimiento) -->
    <filter id="filtro-polvo" x="-10%" y="-10%" width="120%" height="120%">
      <feTurbulence type="fractalNoise" baseFrequency="0.006 0.09" numOctaves="3" seed="5" result="vetas"/>
      <feDisplacementMap in="SourceGraphic" in2="vetas" scale="${(camino.grosor * 0.3).toFixed(0)}" xChannelSelector="R" yChannelSelector="G" result="d"/>
      <feColorMatrix in="vetas" type="matrix" values="0 0 0 0 1  0 0 0 0 1  0 0 0 0 1  2.2 0 0 0 -0.75" result="a"/>
      <feComposite in="d" in2="a" operator="in"/>
    </filter>
    <mask id="mascara-borrado" maskUnits="userSpaceOnUse" x="0" y="0" width="${d.ancho}" height="${d.alto}">
      <rect width="${d.ancho}" height="${d.alto}" fill="#fff"/>
      <path class="pasada" d="${camino.d}" fill="none" stroke-dasharray="0 1000000" stroke="#000" stroke-opacity="${1 - RESTO_TIZA}"
            stroke-width="${camino.grosor.toFixed(0)}" stroke-linecap="round" stroke-linejoin="round" filter="url(#filtro-pasada)"/>
    </mask>
  </defs>

  <!-- marcas del borrador (debajo de los dibujos) -->
  <path class="polvo" d="${camino.d}" fill="none" stroke-dasharray="0 1000000" stroke="${TIZA}" stroke-opacity="0.075"
        stroke-width="${(camino.grosor * 0.95).toFixed(0)}" stroke-linecap="round" stroke-linejoin="round" filter="url(#filtro-polvo)"/>

  <g class="dibujos" mask="url(#mascara-borrado)">
    <image href="arte/cara-tiza.png" x="${d.cara.x}" y="${d.cara.y}" width="${d.cara.tam}" height="${d.cara.tam}"/>
    <image href="arte/escudo-tiza.png" x="${d.escudo.x}" y="${d.escudo.y}" width="${d.escudo.tam}" height="${d.escudo.tam}"/>
    <image href="arte/adr-tiza.png" x="${adr.x}" y="${adr.y}" width="${adr.ancho}" height="${altoAdr.toFixed(0)}"
           transform="rotate(${adr.giro} ${adr.x + adr.ancho / 2} ${adr.y + altoAdr / 2})"/>
    <g class="trazos" filter="url(#filtro-tiza)" fill="${TIZA}" stroke="${TIZA}">
      <g fill="none" stroke-width="5" stroke-linecap="round" stroke-linejoin="round">
        <path d="${d.flecha}"/><path d="${d.punta}"/>
      </g>
      <g fill="none" stroke-width="4" stroke-linecap="round" stroke-linejoin="round">
        <path d="${mas.flecha}"/><path d="${mas.punta}"/>
      </g>
      <g stroke="none">
        ${svgTexto(d.me.x, d.me.y, d.me.tam, TEXTOS_PORTADA.me, "font-weight='700'")}
        ${svgTexto(d.nombre.x, d.nombre.y, d.nombre.tam, TEXTOS_PORTADA.nombre, `font-weight='700' text-anchor='${anclaN}'`)}
        ${svgTexto(d.estudios.x, d.estudios.y, d.estudios.tam, TEXTOS_PORTADA.estudios, `text-anchor='${anclaN}' opacity='.85'`)}
        ${svgTexto(mas.x, mas.y, mas.tam, TEXTOS_PORTADA.masones, `transform='rotate(${mas.giro} ${mas.x} ${mas.y})'`)}
        <g transform="rotate(${izi.giro} ${izi.x} ${izi.y})">
          ${svgTexto(izi.x, izi.y, izi.tam, TEXTOS_PORTADA.izi, "font-weight='700' letter-spacing='6'")}
          <path d="M${izi.x - 8},${izi.y + 22} C${izi.x + 60},${izi.y + 14} ${izi.x + 140},${izi.y + 26} ${izi.x + 200},${izi.y + 16}
                   M${izi.x + 10},${izi.y + 40} C${izi.x + 80},${izi.y + 32} ${izi.x + 150},${izi.y + 42} ${izi.x + 190},${izi.y + 34}"
                fill="none" stroke="${TIZA}" stroke-width="4" stroke-linecap="round"/>
        </g>
      </g>
      <g class="garabatos" fill="none" stroke-width="3.5" stroke-linecap="round" stroke-linejoin="round" opacity=".8">
        ${d.extras.filter((e) => !e.startsWith("<text")).join("\n")}
      </g>
      <g class="garabatos" stroke="none" opacity=".8">
        ${d.extras.filter((e) => e.startsWith("<text")).join("\n")}
      </g>
    </g>
  </g>
</svg>`;
}

// ---------------------------------------------------------------------
// El borrador (dibujo SVG: taco de madera con fieltro manchado de tiza)
// ---------------------------------------------------------------------
const SVG_BORRADOR = `
<svg viewBox="0 0 220 84" xmlns="http://www.w3.org/2000/svg" aria-hidden="true">
  <defs>
    <linearGradient id="madera" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0" stop-color="#c99a63"/><stop offset=".45" stop-color="#a87841"/><stop offset="1" stop-color="#7d5428"/>
    </linearGradient>
    <linearGradient id="canto" x1="0" y1="0" x2="1" y2="0">
      <stop offset="0" stop-color="#000" stop-opacity=".25"/><stop offset=".08" stop-color="#000" stop-opacity="0"/>
      <stop offset=".92" stop-color="#000" stop-opacity="0"/><stop offset="1" stop-color="#000" stop-opacity=".3"/>
    </linearGradient>
    <linearGradient id="fieltro" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0" stop-color="#4a4844"/><stop offset="1" stop-color="#2f2e2b"/>
    </linearGradient>
    <filter id="polvo-fieltro" x="0" y="0" width="100%" height="100%">
      <feTurbulence type="fractalNoise" baseFrequency=".9" numOctaves="2" seed="2" result="n"/>
      <feColorMatrix in="n" type="matrix" values="0 0 0 0 .92  0 0 0 0 .91  0 0 0 0 .87  3.2 0 0 0 -1.35"/>
      <feComposite in2="SourceGraphic" operator="in"/>
    </filter>
    <filter id="vetas" x="0" y="0" width="100%" height="100%">
      <feTurbulence type="fractalNoise" baseFrequency=".008 .35" numOctaves="2" seed="7" result="v"/>
      <feColorMatrix in="v" type="matrix" values="0 0 0 0 .25  0 0 0 0 .15  0 0 0 0 .05  2.4 0 0 0 -1"/>
      <feComposite in2="SourceGraphic" operator="in"/>
    </filter>
  </defs>
  <ellipse cx="112" cy="76" rx="98" ry="7" fill="#000" opacity=".35"/>
  <!-- fieltro -->
  <rect x="10" y="44" width="200" height="26" rx="5" fill="url(#fieltro)"/>
  <rect x="10" y="44" width="200" height="26" rx="5" fill="#fff" filter="url(#polvo-fieltro)" opacity=".85"/>
  <rect x="10" y="62" width="200" height="8" rx="4" fill="#e9e6dd" opacity=".35"/>
  <!-- taco de madera -->
  <rect x="6" y="8" width="208" height="40" rx="9" fill="url(#madera)"/>
  <rect x="6" y="8" width="208" height="40" rx="9" fill="#fff" filter="url(#vetas)"/>
  <rect x="6" y="8" width="208" height="40" rx="9" fill="url(#canto)"/>
  <path d="M16,12 H204" stroke="#fff" stroke-opacity=".35" stroke-width="2" stroke-linecap="round"/>
  <path d="M10,46 H210" stroke="#3b2612" stroke-opacity=".6" stroke-width="2"/>
  <!-- huellas de dedos con tiza -->
  <ellipse cx="70" cy="24" rx="12" ry="6" fill="#e9e6dd" opacity=".12"/>
  <ellipse cx="150" cy="30" rx="15" ry="5" fill="#e9e6dd" opacity=".1"/>
</svg>`;

// ---------------------------------------------------------------------
// Mostrar, redibujar al girar y borrar
// ---------------------------------------------------------------------
const portada = {
  el: null, dibujos: null, borrador: null, lienzo: null,
  orientacion: null, borrando: false, acabarYa: false,
};

function leerSesion() {
  try { return sessionStorage.getItem(CLAVE_SESION) === "1"; } catch (e) { return false; }
}
function guardarSesion() {
  try { sessionStorage.setItem(CLAVE_SESION, "1"); } catch (e) { /* sin almacenamiento: da igual */ }
}

function dibujarPortada() {
  if (portada.borrando) return;
  const o = window.innerWidth >= window.innerHeight ? "h" : "v";
  if (o === portada.orientacion) return;
  portada.orientacion = o;
  portada.dibujos.innerHTML = construirSVG(DIBUJOS[o]);
}

function iniciarPortada() {
  portada.el = document.getElementById("portada");
  if (!portada.el) return;
  if (leerSesion()) {
    portada.el.remove();
    document.documentElement.classList.remove("con-portada");
    return;
  }
  portada.dibujos = document.getElementById("portada-dibujos");
  portada.borrador = document.getElementById("portada-borrador");
  portada.borrador.innerHTML = SVG_BORRADOR;
  portada.lienzo = document.getElementById("portada-polvo");
  if (!portada.lienzo) {                                   // por si el navegador tenía un index.html antiguo
    portada.lienzo = document.createElement("canvas");
    portada.lienzo.className = "portada-polvo";
    portada.el.appendChild(portada.lienzo);
  }
  document.getElementById("portada-pista").textContent = TEXTOS_PORTADA.pista;
  document.documentElement.classList.add("con-portada");
  dibujarPortada();
  window.addEventListener("resize", dibujarPortada);

  const empezar = (e) => {
    if (e.type === "keydown" && ["Shift", "Control", "Alt", "Meta", "Tab"].includes(e.key)) return;
    e.preventDefault();
    if (portada.borrando) portada.acabarYa = true;   // segundo toque: termina ya
    else borrarPortada();
  };
  portada.el.addEventListener("pointerdown", empezar);
  document.addEventListener("keydown", empezar, { capture: true });
  portada.quitarEscuchas = () => {
    portada.el.removeEventListener("pointerdown", empezar);
    document.removeEventListener("keydown", empezar, { capture: true });
    window.removeEventListener("resize", dibujarPortada);
  };
  portada.el.focus({ preventScroll: true });
}

function terminarPortada() {
  if (portada.terminando) return;
  portada.terminando = true;
  guardarSesion();
  portada.quitarEscuchas();
  portada.el.classList.add("desvaneciendo");
  setTimeout(() => {
    portada.el.remove();
    document.documentElement.classList.remove("con-portada");
    document.dispatchEvent(new CustomEvent("portada-cerrada"));
  }, 950);
}

// --- polvo de tiza que cae del borrador (canvas) ---
function crearPolvo() {
  const cv = portada.lienzo;
  const dpr = Math.min(2, window.devicePixelRatio || 1);
  cv.width = innerWidth * dpr; cv.height = innerHeight * dpr;
  const ctx = cv.getContext("2d");
  ctx.scale(dpr, dpr);
  const motas = [];
  return {
    soltar(x, y, cuantas) {
      for (let i = 0; i < cuantas; i++) {
        motas.push({
          x: x + (Math.random() - 0.5) * 30, y: y + (Math.random() - 0.5) * 10,
          vx: (Math.random() - 0.5) * 0.6, vy: Math.random() * 0.4 + 0.2,
          r: Math.random() * 1.6 + 0.5, vida: 1,
        });
      }
    },
    pintar() {
      ctx.clearRect(0, 0, innerWidth, innerHeight);
      for (let i = motas.length - 1; i >= 0; i--) {
        const m = motas[i];
        m.x += m.vx; m.y += m.vy; m.vy += 0.035; m.vida -= 0.018;
        if (m.vida <= 0) { motas.splice(i, 1); continue; }
        ctx.globalAlpha = m.vida * 0.55;
        ctx.fillStyle = TIZA;
        ctx.beginPath(); ctx.arc(m.x, m.y, m.r, 0, 6.283); ctx.fill();
      }
      return motas.length;
    },
  };
}

const suave = (t) => t < 0.5 ? 2 * t * t : 1 - Math.pow(-2 * t + 2, 2) / 2;

function borrarPortada() {
  if (portada.borrando) return;
  portada.borrando = true;
  portada.el.classList.add("borrando");
  try {
    animarBorrado();
  } catch (e) {
    // pase lo que pase, la portada nunca se queda pillada
    console.error("Animación de borrado:", e);
    portada.borrador.hidden = true;
    terminarPortada();
  }
}

function animarBorrado() {
  const sinMovimiento = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  if (sinMovimiento) { terminarPortada(); return; }

  const svg = portada.dibujos.querySelector("svg");
  const pasada = svg.querySelector(".pasada");
  const polvo = svg.querySelector(".polvo");
  const largo = pasada.getTotalLength();
  for (const p of [pasada, polvo]) {
    p.style.strokeDasharray = largo + " " + largo;
    p.style.strokeDashoffset = largo;
  }
  // tamaño del borrador en pantalla: un poco menos que el ancho de una pasada
  const d = DIBUJOS[portada.orientacion];
  const escala = svg.getScreenCTM().a;
  const largoBorrador = (d.alto / d.pasadas) * 1.15 * escala;
  const b = portada.borrador;
  b.style.width = largoBorrador + "px";
  b.style.height = (largoBorrador * 84 / 220) + "px";
  b.hidden = false;

  const motas = crearPolvo();
  const t0 = performance.now();
  let anterior = null;

  function fotograma(ahora) {
    try { paso(ahora); } catch (e) {
      console.error("Animación de borrado:", e);
      b.hidden = true;
      terminarPortada();
    }
  }

  function paso(ahora) {
    let t = Math.min(1, (ahora - t0) / DURACION_BORRADO_MS[portada.orientacion]);
    if (portada.acabarYa) t = 1;
    const s = suave(t);
    const recorrido = largo * s;
    pasada.style.strokeDashoffset = largo - recorrido;
    polvo.style.strokeDashoffset = largo - recorrido;

    // posición y giro del borrador (perpendicular al movimiento, con algo de vaivén)
    const ctm = svg.getScreenCTM();
    const p = pasada.getPointAtLength(Math.min(largo, recorrido));
    const q = pasada.getPointAtLength(Math.min(largo, recorrido + 4));
    const x = ctm.a * p.x + ctm.e, y = ctm.d * p.y + ctm.f;
    const angulo = Math.atan2(q.y - p.y, q.x - p.x) * 180 / Math.PI;
    const vaiven = Math.sin(ahora / 70) * 4;
    b.style.transform = `translate(${x}px, ${y}px) translate(-50%, -50%) rotate(${angulo + 90 + vaiven}deg)`;

    if (anterior && t < 1) {
      const v = Math.hypot(x - anterior.x, y - anterior.y);
      motas.soltar(x, y, Math.min(6, Math.round(v / 6)));
    }
    anterior = { x, y };
    motas.pintar();

    if (t < 1) {
      requestAnimationFrame(fotograma);
    } else {
      b.classList.add("levantando");                // el borrador se aparta
      setTimeout(() => { b.hidden = true; }, 350);
      terminarPortada();
      const seguir = () => { if (motas.pintar() > 0 && portada.el.isConnected) requestAnimationFrame(seguir); };
      requestAnimationFrame(seguir);
    }
  }
  requestAnimationFrame(fotograma);
}

document.addEventListener("DOMContentLoaded", iniciarPortada);
