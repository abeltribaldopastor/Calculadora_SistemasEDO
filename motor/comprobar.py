# -*- coding: utf-8 -*-
"""
comprobar.py — Botón «Comprobar solución» (sección 6).

Se comprueba simbólicamente que  dy/dt − Â·y − f(t) = 0  (y que y(t0) = y0 en el PVI).
Si la simplificación simbólica no llega a 0, se hace una comprobación NUMÉRICA en
5 valores aleatorios de t (y de las constantes c_i) con tolerancia 1e-9, y se dice
en la pizarra qué tipo de comprobación se ha superado.

comprobar(solucion) recibe el diccionario "solucion" que devuelve resolver()
(todo en texto, para que viaje como JSON) y devuelve {"ok", "tipo", "pasos"}.
"""
import random

from sympy import Matrix, sympify, N, E, pi, I

from .entrada import t, constantes
from .simplificar import limpiar, es_cero, tex, paso


def _leer(texto, locales):
    return sympify(texto, locals=locales)


def _numerico(exprs, cs, rnd):
    """¿Son ≈ 0 todas las expresiones en 5 puntos aleatorios? (tolerancia 1e-9)"""
    for _ in range(5):
        sub = {t: rnd.uniform(-1.5, 1.5)}
        for c in cs:
            sub[c] = rnd.uniform(-2, 2)
        for x in exprs:
            if x.has(t) or any(x.has(c) for c in cs):
                val = complex(N(x.subs(sub), 30))
            else:
                val = complex(N(x, 30))
            if abs(val) > 1e-9:
                return False
    return True


def comprobar(solucion):
    try:
        n = int(solucion["n"])
        cs = constantes(n)
        locales = {"t": t, "E": E, "pi": pi, "I": I}
        locales.update({str(c): c for c in cs})
        A = Matrix([[_leer(x, locales) for x in fila] for fila in solucion["A"]])
        f = Matrix([_leer(x, locales) for x in solucion["f"]])
        y = Matrix([_leer(x, locales) for x in solucion["y"]])
    except Exception as e:
        return {"ok": False, "error": "No puedo leer la solución a comprobar (%s)." % e}

    residuo = (y.diff(t) - A * y - f).applyfunc(limpiar)
    simbolica = all(es_cero(x) for x in residuo)
    lineas = [r"\frac{d\vec y}{dt}-\hat A\vec y-\vec f(t)=" + tex(residuo)]

    ini_ok_sim = True
    ini = None
    if solucion.get("modo") == "pvi":
        t0 = _leer(solucion["t0"], locales)
        y0 = Matrix([_leer(x, locales) for x in solucion["y0"]])
        ini = (y.subs(t, t0) - y0).applyfunc(limpiar)
        ini_ok_sim = all(es_cero(x) for x in ini)
        lineas.append(r"\vec y(t_0)-\vec y_0=" + tex(ini))

    rnd = random.Random()
    if simbolica and ini_ok_sim:
        ok, tipo = True, "simbólica"
        texto = r"✔ La resta se simplifica exactamente a $\vec 0$: comprobación <b>simbólica</b> superada."
    else:
        todo = list(residuo) + (list(ini) if ini is not None else [])
        ok = _numerico(todo, cs, rnd)
        tipo = "numérica" if ok else "fallida"
        texto = (r"La simplificación simbólica no llega a $\vec 0$, así que evaluamos en 5 valores "
                 r"aleatorios de $t$ y de las $c_i$ (tolerancia $10^{-9}$): "
                 + (r"✔ comprobación <b>numérica</b> superada." if ok else
                    r"✘ <b>la solución NO cumple el sistema</b>."))
    return {"ok": ok, "tipo": tipo,
            "pasos": [paso("V", "V.1", "amarillo" if ok else "coral",
                           r"Comprobación: $\dot{\vec y}=\hat A\vec y+\vec f$", texto, lineas, "sección 6")]}
