# -*- coding: utf-8 -*-
"""
resolver.py — Función principal del motor:  resolver(datos: dict) -> dict

Entrada (lo que manda la interfaz), por ejemplo:
    {"n": 2, "A": [["1","2"],["2","1"]], "f": ["0","0"],
     "modo": "pvi", "t0": "0", "y0": ["1","0"]}

Salida:
    {"ok": True, "caso": "A", "pasos": [...], "solucion": {...}, "resumen": {...}}
  o {"ok": False, "error": "mensaje en español", "errores": {...}, "pasos": [...]}

Para probarlo sin navegador:
    python -c "from motor.resolver import resolver; print(resolver({...})['caso'])"

También hay versiones «_json» (texto JSON → texto JSON) que usa worker.js.
"""
import json
import traceback

from sympy import Matrix

from .entrada import t, leer_datos, validar_celda, ErrorEntrada, ErrorMotor
from .simplificar import limpiar_matriz, simp_cte, tex, tex_matriz, paso, color
from .homogenea import parte1
from .particular import parte2
from .comprobar import comprobar

NOMBRE_CASO = {"A": "autovalores distintos", "B": "Cayley-Hamilton",
               "C": "matrices constituyentes"}


def _planteamiento(d, pasos):
    n, A, f = d["n"], d["A"], d["f"]
    lineas = [r"\frac{d\vec y}{dt}=\hat A\,\vec y(t)" + ("" if d["homogeneo"] else r"+\vec f(t)"),
              r"\hat A=" + tex(A) + ("" if d["homogeneo"] else r",\qquad\vec f(t)=" + tex(f))]
    if d["modo"] == "pvi":
        lineas.append(r"\vec y(%s)=%s" % (tex(d["t0"]), tex(d["y0"])))
    texto = ("Sistema %s de %d ecuaciones lineales con coeficientes constantes. Buscamos %s."
             % ("homogéneo" if d["homogeneo"] else "no homogéneo", n,
                "la solución del problema de valores iniciales" if d["modo"] == "pvi"
                else "la solución general"))
    pasos.append(paso(1, "1.0", "blanco", "Planteamiento", texto, lineas, "cap. XIX"))


def _parte3(d, info1, yp, pasos):
    """Condiciones iniciales (si es PVI) y solución final recuadrada."""
    n, t0, y0 = d["n"], d["t0"], d["y0"]
    E = info1["E"]
    if d["modo"] == "pvi":
        if info1["caso"] == "A":
            M = info1["M"]
            Mt0 = M.subs(t, t0).applyfunc(simp_cte)
            Minv = info1["M0inv"] if t0 == 0 else Mt0.inv().applyfunc(simp_cte)
            cvec = (Minv * y0).applyfunc(simp_cte)
            yh = limpiar_matriz(M * cvec)
            lineas = []
            if t0 != 0:
                lineas.append(r"\hat M(t_0)=" + tex(Mt0) + r",\qquad \hat M^{-1}(t_0)=" + tex_matriz(Minv))
                Et = limpiar_matriz(M * Minv)
                lineas.append(r"e^{\hat A(t-t_0)}=\hat M(t)\,\hat M^{-1}(t_0)=" + tex_matriz(Et))
            lineas.append(r"\vec c=\hat M^{-1}(t_0)\,\vec y(t_0)=" + tex_matriz(Minv)
                          + tex(y0) + "=" + tex(cvec))
            lineas.append(r"\vec y_h(t)=\hat M(t)\,\vec c=" + tex(yh))
            texto = (r"Como $\vec y_p(t_0)=\vec 0$, la condición inicial solo afecta a la parte "
                     r"homogénea: $\vec y(t_0)=\hat M(t_0)\vec c$.")
        else:
            Et = limpiar_matriz(E.subs(t, t - t0)) if t0 != 0 else E
            yh = limpiar_matriz(Et * y0)
            lineas = []
            if t0 != 0:
                lineas.append(r"e^{\hat A(t-t_0)}=" + tex_matriz(Et))
            lineas.append(r"\vec y_h(t)=e^{\hat A(t-t_0)}\,\vec y(t_0)=" + tex(yh))
            texto = (r"Como $\vec y_p(t_0)=\vec 0$, la condición inicial solo afecta a la parte "
                     r"homogénea, que es $e^{\hat A(t-t_0)}\vec y(t_0)$ (en $t=t_0$ vale "
                     r"$\hat I\,\vec y(t_0)$).")
        pasos.append(paso(3, "3.1", "blanco", "Condiciones iniciales", texto, lineas,
                          "ec. (279), cap. XIX"))
    else:
        yh = info1["yh_general"]

    y = limpiar_matriz(yh + yp)
    lineas = [r"\vec y(t)=" + tex(y)]
    for k in range(n):
        lineas.append(r"y_{%d}(t)=%s" % (k + 1, tex(y[k])))
    pasos.append(paso(
        3, "3.2", "amarillo", "Solución final",
        "Forma matricial y variable por variable%s:" % (
            "" if d["modo"] == "pvi" else r" ($c_1,\dots,c_{%d}$ constantes arbitrarias)" % n),
        lineas, "caps. XIX–XXII", clase="final"))
    return y


def resolver(datos):
    pasos = []
    try:
        d = leer_datos(datos)
    except ErrorEntrada as e:
        return {"ok": False, "error": str(e), "errores": e.errores, "pasos": []}
    try:
        n = d["n"]
        _planteamiento(d, pasos)
        info1 = parte1(d["A"], n, pasos)
        if d["homogeneo"]:
            yp = Matrix.zeros(n, 1)
            info2 = None
        else:
            info2 = parte2(d["A"], info1["E"], d["f"], n, d["modo"], d["t0"],
                           info1["autovalores"], info1["caso"], info1, pasos)
            yp = info2["yp"]
        y = _parte3(d, info1, yp, pasos)
    except ErrorMotor as e:
        return {"ok": False, "error": str(e), "pasos": pasos}
    except Exception as e:  # nunca dejamos que la interfaz se rompa
        return {"ok": False, "pasos": pasos,
                "error": "Error interno inesperado (%s: %s)." % (type(e).__name__, e),
                "detalle": traceback.format_exc()}

    solucion = {
        "n": n,
        "A": [[str(d["A"][i, j]) for j in range(n)] for i in range(n)],
        "f": [str(x) for x in d["f"]],
        "y": [str(x) for x in y],
        "modo": d["modo"],
        "t0": str(d["t0"]),
        "y0": [str(x) for x in d["y0"]] if d["y0"] is not None else None,
    }
    resumen = {
        "caso": info1["caso"],
        "metodo": NOMBRE_CASO[info1["caso"]],
        "autovalores": [{"valor": str(l), "latex": tex(l), "multiplicidad": k}
                        for l, k in info1["autovalores"]],
        "eAt": [[str(info1["E"][i, j]) for j in range(n)] for i in range(n)],
        "yp": [str(x) for x in yp] if info2 else None,
        "validada": info1["validada"],
    }
    return {"ok": True, "caso": info1["caso"], "pasos": pasos,
            "solucion": solucion, "resumen": resumen}


# ---------------------------------------------------------------------------
# Versiones JSON (las usa worker.js: texto entra, texto sale)
# ---------------------------------------------------------------------------
def resolver_json(texto):
    return json.dumps(resolver(json.loads(texto)), ensure_ascii=False)


def comprobar_json(texto):
    try:
        r = comprobar(json.loads(texto))
    except Exception as e:
        r = {"ok": False, "error": "Error interno al comprobar (%s)." % e}
    return json.dumps(r, ensure_ascii=False)


def validar_celda_json(texto):
    d = json.loads(texto)
    return json.dumps(validar_celda(d.get("texto", ""), d.get("tipo", "A")), ensure_ascii=False)
