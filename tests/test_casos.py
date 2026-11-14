# -*- coding: utf-8 -*-
"""
test_casos.py — Los 9 casos obligatorios (sección 8) como tests automáticos.

Para cada caso se comprueba:
    · la ruta elegida (A, B o C)
    · los autovalores y sus multiplicidades
    · que e^{Ât} coincide con la de referencia
    · que la verificación de la sección 6 da 0
    · y, si hay referencia, la solución particular y_p (primitiva y/o ∫ desde t0)

Ejecutar en el ordenador:      pytest tests/
Ejecutar sin pytest:           python tests/test_casos.py
En la web, el botón «Tests» llama a ejecutar_todos() dentro de Pyodide.
"""
import copy
import json
import os
import sys
import time

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if RAIZ not in sys.path:
    sys.path.insert(0, RAIZ)

from sympy import Matrix, sympify, I, E, pi, N  # noqa: E402

from motor.entrada import t  # noqa: E402
from motor.simplificar import es_cero  # noqa: E402
from motor.resolver import resolver  # noqa: E402
from motor.comprobar import comprobar  # noqa: E402

LOCALES = {"t": t, "I": I, "E": E, "pi": pi}


def cargar_casos():
    with open(os.path.join(RAIZ, "ejemplos.json"), encoding="utf-8") as fh:
        return json.load(fh)


def _expr(x):
    return sympify(x, locals=LOCALES)


def _iguales(a, b):
    """Iguales simbólicamente (o, si no se consigue, numéricamente en varios t)."""
    d = _expr(a) - _expr(b)
    if es_cero(d):
        return True
    return all(abs(complex(N(d.subs(t, tv), 30))) < 1e-12 for tv in (0.3, -0.7, 1.1))


def comprobar_caso(caso):
    """Lanza AssertionError con un mensaje claro si algo no cuadra."""
    ref = caso["referencia"]
    r = resolver(caso["datos"])
    assert r["ok"], "el motor falló: %s" % r.get("error")
    assert r["caso"] == ref["ruta"], "ruta %s (esperada %s)" % (r["caso"], ref["ruta"])

    obtenidos = sorted((str(_expr(a["valor"])), a["multiplicidad"]) for a in r["resumen"]["autovalores"])
    esperados = sorted((str(_expr(v)), k) for v, k in ref["autovalores"])
    assert obtenidos == esperados, "autovalores %s (esperados %s)" % (obtenidos, esperados)

    assert r["resumen"]["validada"], "e^{At} no pasó la validación interna"
    n = caso["datos"]["n"]
    for i in range(n):
        for j in range(n):
            assert _iguales(r["resumen"]["eAt"][i][j], ref["eAt"][i][j]), \
                "e^{At}[%d,%d] = %s (esperado %s)" % (i, j, r["resumen"]["eAt"][i][j], ref["eAt"][i][j])

    v = comprobar(r["solucion"])
    assert v["ok"] and v["tipo"] == "simbólica", "la verificación no da 0 (%s)" % v.get("tipo")

    if "y_pvi" in ref:
        for k in range(n):
            assert _iguales(r["solucion"]["y"][k], ref["y_pvi"][k]), "y_%d del PVI" % (k + 1)

    if "yp_general" in ref:
        for k in range(n):
            assert _iguales(r["resumen"]["yp"][k], ref["yp_general"][k]), \
                "y_p[%d] = %s (esperado %s)" % (k, r["resumen"]["yp"][k], ref["yp_general"][k])

    if ref.get("sin_resonancia"):
        assert not any(p["id"] == "P5!" for p in r["pasos"]), "aviso de resonancia indebido"

    if "yp_pvi" in ref or "yp_pvi_fila1" in ref:
        datos = copy.deepcopy(caso["datos"])
        datos.update({"modo": "pvi", "t0": "0", "y0": ["0"] * n})
        r2 = resolver(datos)
        assert r2["ok"], "el motor falló en el PVI: %s" % r2.get("error")
        yp = r2["resumen"]["yp"]
        esperado = ref.get("yp_pvi") or [ref["yp_pvi_fila1"]]
        for k in range(len(esperado)):
            assert _iguales(yp[k], esperado[k]), \
                "y_p PVI[%d] = %s (esperado %s)" % (k, yp[k], esperado[k])
        v2 = comprobar(r2["solucion"])
        assert v2["ok"], "la verificación del PVI no da 0"


def ejecutar_todos():
    """Ejecuta los 9 casos y devuelve una lista de resultados (la usa la web)."""
    resultados = []
    for caso in cargar_casos():
        t_ini = time.time()
        try:
            comprobar_caso(caso)
            ok, msg = True, "correcto"
        except AssertionError as e:
            ok, msg = False, str(e)
        except Exception as e:
            ok, msg = False, "%s: %s" % (type(e).__name__, e)
        resultados.append({"id": caso["id"], "titulo": caso["titulo"], "ok": ok,
                           "mensaje": msg, "segundos": round(time.time() - t_ini, 2)})
    return resultados


# --- pytest: un test por caso ------------------------------------------------
try:
    import pytest

    @pytest.mark.parametrize("caso", cargar_casos(), ids=lambda c: "caso%d" % c["id"])
    def test_caso(caso):
        comprobar_caso(caso)

    @pytest.mark.parametrize("texto,valido", [
        ("a", False), ("2*k", False), ("t", False), ("1/0", False), ("0.5", True),
        ("sqrt(2)", True), ("pi", True), ("-3/4", True), ("2+", False)])
    def test_entradas_A(texto, valido):
        from motor.entrada import validar_celda
        assert validar_celda(texto, "A")["ok"] is valido

    def test_parametro_libre_no_rompe():
        r = resolver({"n": 2, "A": [["a", "1"], ["0", "1"]], "f": ["0", "0"], "modo": "general"})
        assert not r["ok"] and "A_0_0" in r["errores"]

except ImportError:  # en Pyodide no hace falta pytest
    pass


if __name__ == "__main__":
    for res in ejecutar_todos():
        print("%s caso %d (%.2f s): %s" % ("OK " if res["ok"] else "ERR", res["id"],
                                           res["segundos"], res["mensaje"]))
