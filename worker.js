/* =====================================================================
   worker.js — Ejecuta el motor de Python (motor/) dentro del navegador.

   Funciona en un «Web Worker» (un hilo aparte) para que la página no se
   congele mientras SymPy calcula. Pasos:
     1) carga Pyodide (Python compilado para el navegador) desde jsDelivr,
     2) carga el paquete SymPy,
     3) descarga los .py de motor/ y los escribe en el disco virtual,
     4) importa motor.resolver y queda esperando mensajes.

   Mensajes que recibe (desde app.js):
     { id, accion: "resolver" | "comprobar" | "validar" | "tests", datos }
   Mensajes que envía:
     { tipo: "estado", texto }            → progreso de la carga
     { tipo: "listo" }                    → el motor ya puede usarse
     { tipo: "fallo", error }             → no se pudo cargar
     { tipo: "respuesta", id, ok, resultado | error }

   Si añades un archivo nuevo a motor/, apúntalo en ARCHIVOS_MOTOR.
   ===================================================================== */
const PYODIDE_URL = "https://cdn.jsdelivr.net/pyodide/v0.27.2/full/";
importScripts(PYODIDE_URL + "pyodide.js");

const ARCHIVOS_MOTOR = [
  "__init__.py", "entrada.py", "simplificar.py", "homogenea.py",
  "particular.py", "comprobar.py", "resolver.py",
];
const CASA = "/home/pyodide";

async function descargar(ruta) {
  const r = await fetch(ruta, { cache: "no-cache" });
  if (!r.ok) throw new Error("No se pudo descargar " + ruta + " (" + r.status + ")");
  return await r.text();
}

async function iniciar() {
  self.postMessage({ tipo: "estado", texto: "Descargando Python (Pyodide)…" });
  const py = await loadPyodide({ indexURL: PYODIDE_URL });

  self.postMessage({ tipo: "estado", texto: "Cargando SymPy…" });
  await py.loadPackage("sympy");

  self.postMessage({ tipo: "estado", texto: "Copiando el motor de cálculo…" });
  py.FS.mkdirTree(CASA + "/motor");
  py.FS.mkdirTree(CASA + "/tests");
  for (const nombre of ARCHIVOS_MOTOR) {
    py.FS.writeFile(CASA + "/motor/" + nombre, await descargar("motor/" + nombre));
  }
  py.FS.writeFile(CASA + "/tests/test_casos.py", await descargar("tests/test_casos.py"));
  py.FS.writeFile(CASA + "/ejemplos.json", await descargar("ejemplos.json"));

  py.runPython(`
import sys
sys.path.insert(0, "${CASA}")
from motor.resolver import resolver_json, comprobar_json, validar_celda_json
`);
  return py;
}

const listo = iniciar();
listo.then(
  () => self.postMessage({ tipo: "listo" }),
  (e) => self.postMessage({ tipo: "fallo", error: String(e && e.message ? e.message : e) })
);

self.onmessage = async (ev) => {
  const { id, accion, datos } = ev.data;
  try {
    const py = await listo;
    let salida;
    if (accion === "resolver") {
      salida = py.globals.get("resolver_json")(JSON.stringify(datos));
    } else if (accion === "comprobar") {
      salida = py.globals.get("comprobar_json")(JSON.stringify(datos));
    } else if (accion === "validar") {
      salida = py.globals.get("validar_celda_json")(JSON.stringify(datos));
    } else if (accion === "tests") {
      salida = py.runPython(`
import sys, json
if "${CASA}/tests" not in sys.path:
    sys.path.insert(0, "${CASA}/tests")
import test_casos
json.dumps(test_casos.ejecutar_todos(), ensure_ascii=False)
`);
    } else {
      throw new Error("Acción desconocida: " + accion);
    }
    self.postMessage({ tipo: "respuesta", id, ok: true, resultado: JSON.parse(salida) });
  } catch (e) {
    self.postMessage({ tipo: "respuesta", id, ok: false, error: String(e && e.message ? e.message : e) });
  }
};
