# -*- coding: utf-8 -*-
"""
particular.py — PARTE 2: solución particular y_p(t) (solo si f ≠ 0).

Fórmula de los apuntes (cap. XX, ec. (285)):
    y(t) = e^{Ât} [ y0 + ∫_0^t ds e^{−Âs} f(s) ]
y para t0 arbitrario:
    y(t) = e^{Â(t−t0)} y(t0) + e^{Ât} ∫_{t0}^{t} ds e^{−Âs} f(s)

Pasos que se muestran (en verde menta):
    P1 fórmula · P2 e^{−Âs} (sin invertir: t → −s) · P3 g(s) = e^{−Âs} f(s)
    P4 integrar componente a componente · P5 multiplicar por e^{Ât}
    P6 solución total (homogénea + particular, en recuadros de colores)
"""
from sympy import (Matrix, S, exp, symbols, linsolve, Integral, integrate, factorial,
                   expand, re, I)

from .entrada import t, s
from .simplificar import (limpiar, limpiar_matriz, descomponer, claves, simp_cte, es_cero,
                          tex, tex_matriz, paso, color, es_cero_constante)


# ===========================================================================
# Integración
# ===========================================================================
def _primitiva_basica(d, l, x):
    """∫ x^d e^{l x} dx (sin constante), por partes repetidas."""
    if l == 0:
        return x**(d + 1) / (d + 1)
    total = S.Zero
    for k in range(d + 1):
        total += (-1)**k * factorial(d) / factorial(d - k) * x**(d - k) / l**(k + 1)
    return exp(l * x) * total


def primitiva(g, x=s):
    """
    Primitiva de g respecto de x (sin constante).
    Devuelve (F, True) o (Integral sin evaluar, False) si SymPy no sabe integrarla.
    """
    if g == 0:
        return S.Zero, True
    terminos = descomponer(g, x)
    if terminos is not None:
        F = S.Zero
        for (d, l), c in terminos.items():
            F += c * _primitiva_basica(d, l, x)
        return limpiar(F, x), True
    try:
        F = integrate(g, x)
    except Exception:
        F = Integral(g, x)
    if F.has(Integral):
        return F, False
    return limpiar(F, x), True


# ===========================================================================
# Términos homogéneos y resonancia
# ===========================================================================
def _grupo(l):
    a, b = l.as_real_imag()
    return (simp_cte(a), abs(simp_cte(b)))


def absorber_homogeneos(E, yp, n):
    """
    Busca en y_p términos que sean solución homogénea, es decir, de la forma e^{Ât}·k.
    Se hace por «familias» de autovalores (λ y su conjugado juntos).
    Devuelve (yp_sin_ellos, k, h) o (yp, None, None) si no hay nada que absorber.
    """
    phi = set()
    for x in E:
        cl = claves(x)
        if cl is None:
            return yp, None, None
        phi |= cl
    desc = [descomponer(x) for x in yp]
    if any(d is None for d in desc):
        return yp, None, None
    grupos = {_grupo(l) for d in desc for (dd, l) in d if (dd, l) in phi}
    ks = symbols("k1:%d" % (n + 1))
    kv = Matrix(ks)
    total_k = Matrix.zeros(n, 1)
    for gr in grupos:
        parte = Matrix([sum((c * t**dd * exp(l * t) for (dd, l), c in d.items()
                             if (dd, l) in phi and _grupo(l) == gr), S.Zero) for d in desc])
        resto = parte - E * kv
        ecuaciones = []
        for x in resto:
            dx = descomponer(x)
            if dx is None:
                ecuaciones = None
                break
            ecuaciones += [expand(c) for c in dx.values()]
        if ecuaciones is None:
            continue
        sol = linsolve(ecuaciones, ks) if ecuaciones else None
        if not sol:
            continue
        valores = list(sol)[0]
        libres = set().union(*[v.free_symbols for v in valores]) & set(ks)
        valores = Matrix([simp_cte(re(v.subs({k: 0 for k in libres}))) for v in valores])
        if all(v == 0 for v in valores):
            continue
        # comprobación: con estos valores el grupo desaparece de verdad
        if all(es_cero(x) for x in (parte - E * valores)):
            total_k += valores
    if all(v == 0 for v in total_k):
        return yp, None, None
    h = limpiar_matriz(E * total_k)
    return limpiar_matriz(yp - h), total_k, h


def terminos_seculares(yp, E, f, autov):
    """
    Términos seculares: potencias de t que multiplican exponenciales/senos/cosenos
    y que NO estaban en f ni son de la parte homogénea. Devuelve la lista de
    autovalores responsables (sin repetir conjugados).
    """
    phi = set()
    for x in E:
        cl = claves(x)
        if cl is None:
            return []
        phi |= cl
    fk = set()
    for x in f:
        cl = claves(x)
        if cl is None:
            return []
        fk |= cl
    responsables = []
    for x in yp:
        cl = claves(x)
        if cl is None:
            return []
        for d, l in cl:
            if d < 1 or (d, l) in phi:
                continue
            if any(lf == l and df >= d for df, lf in fk):
                continue
            for lv, _ in autov:
                if es_cero_constante(lv - l):
                    gr = _grupo(lv)
                    if gr not in [g for g, _ in responsables]:
                        responsables.append((gr, lv))
    return [lv for _, lv in responsables]


# ===========================================================================
# Pasos P1–P6
# ===========================================================================
def _fila_por_columna(M, v, var):
    """LaTeX del producto matriz·vector «fila por columna», sin simplificar."""
    filas = []
    for i in range(M.rows):
        sumandos = []
        for j in range(M.cols):
            if M[i, j] == 0 or v[j] == 0:
                continue
            sumandos.append(r"\left(%s\right)\left(%s\right)" % (tex(M[i, j]), tex(v[j])))
        filas.append("+".join(sumandos) if sumandos else "0")
    return r"\begin{pmatrix}" + r" \\ ".join(filas) + r"\end{pmatrix}"


def parte2(A, E, f, n, modo, t0, autov, caso, info1, pasos):
    pvi = modo == "pvi"
    nota = (r"En <b>solución general</b> usamos la <b>primitiva sin constante</b> evaluada en "
            r"$s=t$: cualquier término homogéneo que aparezca se absorbe en las constantes $c_i$."
            if not pvi else
            r"En el <b>PVI</b> usamos la integral definida de $t_0$ a $t$, con lo que "
            r"$\vec y_p(t_0)=\vec 0$.")
    pasos.append(paso(
        2, "P1", "menta", "Fórmula de los apuntes",
        r"Generalizando la solución de la EDO lineal de primer orden (ec. (284)) al caso "
        r"matricial: " + nota,
        [r"\vec y(t)=e^{\hat At}\left[\vec y_0+\int_0^t ds\,e^{-\hat As}\vec f(s)\right]",
         r"\vec y(t)=e^{\hat A(t-t_0)}\vec y(t_0)+\underbrace{e^{\hat At}\int_{t_0}^{t}ds\,"
         r"e^{-\hat As}\vec f(s)}_{\vec y_p(t)}"],
        "ec. (285), cap. XX"))

    Es = limpiar_matriz(E.subs(t, -s), s)
    pasos.append(paso(
        2, "P2", "menta", r"$e^{-\hat As}$ sin invertir",
        r"Por las propiedades de la exponencial, $\left(e^{t\hat A}\right)^{-1}=e^{-t\hat A}$: "
        r"basta con sustituir $t\to-s$ en la $e^{\hat At}$ de la Parte 1.",
        [r"e^{-\hat As}=" + tex_matriz(Es, s)], "propiedades de $e^{\\hat At}$, cap. XX"))

    fs = f.subs(t, s)
    g = limpiar_matriz(Es * fs, s)
    lineas = [r"\vec f(s)=" + tex(fs)]
    if n <= 3:
        lineas.append(r"\vec g(s)=e^{-\hat As}\vec f(s)=" + _fila_por_columna(Es, fs, s))
        lineas.append(r"\vec g(s)=" + tex(g))
    else:
        lineas.append(r"\vec g(s)=e^{-\hat As}\vec f(s)=" + tex(g))
    pasos.append(paso(
        2, "P3", "menta", r"Producto $\vec g(s)=e^{-\hat As}\,\vec f(s)$",
        r"Sustituimos $t\to s$ en $\vec f$ ($s$ es la variable muda de integración) y "
        r"multiplicamos fila por columna:", lineas, "ec. (285), cap. XX"))

    Ivec = Matrix.zeros(n, 1)
    lineas = []
    sin_resolver = []
    for k in range(n):
        F, ok = primitiva(g[k], s)
        if not ok:
            sin_resolver.append(k + 1)
        if pvi:
            if ok:
                val = limpiar(F.subs(s, t) - F.subs(s, t0))
                lineas.append(r"I_{%d}(t)=\int_{%s}^{t}ds\,\left(%s\right)=\Big[%s\Big]_{s=%s}^{s=t}=%s"
                              % (k + 1, tex(t0), tex(g[k]), tex(F), tex(t0), tex(val)))
            else:
                val = Integral(g[k], (s, t0, t))
                lineas.append(r"I_{%d}(t)=%s" % (k + 1, tex(val)))
        else:
            val = limpiar(F.subs(s, t)) if ok else F.subs(s, t)
            if g[k] == 0:
                lineas.append(r"I_{%d}(t)=0" % (k + 1))
            else:
                lineas.append(r"I_{%d}(t)=\int ds\,\left(%s\right)\Big|_{s=t}=%s"
                              % (k + 1, tex(g[k]), tex(val)))
        Ivec[k] = val
    pasos.append(paso(
        2, "P4", "menta", "Integramos componente a componente",
        (r"Primitivas sin constante, evaluadas en $s=t$:" if not pvi
         else r"Integrales definidas de $t_0=%s$ a $t$:" % tex(t0)),
        lineas, "ec. (285), cap. XX"))
    if sin_resolver:
        pasos.append(paso(
            2, "P4!", "coral", "Integral sin resolver",
            r"SymPy no consigue integrar en forma cerrada la(s) componente(s) %s. Se deja "
            r"indicada la integral; el resto del cálculo sigue con ella."
            % ", ".join(str(k) for k in sin_resolver), [], "", clase="aviso"))

    yp = limpiar_matriz(E * Ivec)
    lineas = []
    if n <= 3 and not sin_resolver:
        lineas.append(r"\vec y_p(t)=e^{\hat At}\,\vec I(t)=" + _fila_por_columna(E, Ivec, t))
    lineas.append(r"\vec y_p(t)=" + tex(yp))
    pasos.append(paso(
        2, "P5", "menta", r"Multiplicamos por $e^{\hat At}$ por la izquierda",
        r"Al multiplicar, las exponenciales opuestas se cancelan "
        r"($e^{\lambda t}e^{-\lambda t}=1$):", lineas, "ec. (285), cap. XX"))

    k_abs = None
    if not pvi and not sin_resolver:
        yp2, k_abs, h = absorber_homogeneos(E, yp, n)
        if k_abs is not None:
            pasos.append(paso(
                2, "P5'", "menta", "Absorbemos un término homogéneo",
                r"Una parte de $\vec y_p$ es combinación de columnas de $e^{\hat At}$, es decir, "
                r"es solución de la homogénea. La absorbemos en las constantes: "
                r"$\vec c\to\vec c+\vec k$.",
                [r"e^{\hat At}\vec k=" + tex(h) + r",\qquad\vec k=" + tex(k_abs),
                 r"\vec y_p(t)=" + tex(yp2)], "ec. (285), cap. XX"))
            yp = yp2

    if not sin_resolver:
        sec = terminos_seculares(yp, E, f, autov)
        if sec:
            lista = ", ".join(r"$\lambda=%s$" % tex(l) + (r" (y su conjugado)" if l.has(I) else "")
                              for l in sec)
            pasos.append(paso(
                2, "P5!", "coral", "Aviso de resonancia",
                r"$\vec y_p(t)$ contiene términos seculares (potencias de $t$ multiplicando "
                r"exponenciales, senos o cosenos que no estaban en $\vec f$). Proceden de: "
                + lista + ".", [], "cap. XX", clase="aviso"))

    # P6: solución total con recuadros de colores
    c = info1["c"]
    if caso == "A":
        hom_tex = r"\hat M(t)\,\vec c"
    else:
        hom_tex = r"e^{\hat At}\,\vec c"
    yh = info1["yh_general"]
    lineas = [r"\vec y(t)=" + color("azul", r"\boxed{" + hom_tex + "}") + "+"
              + color("menta", r"\boxed{\vec y_p(t)}")]
    for k in range(n):
        lineas.append(r"y_{%d}(t)=%s+%s" % (
            k + 1, color("azul", r"\boxed{" + tex(yh[k]) + "}"),
            color("menta", r"\boxed{" + tex(yp[k]) + "}")))
    pasos.append(paso(
        2, "P6", "menta", "Solución total",
        r"Homogénea (recuadro azul) más particular (recuadro verde)%s:"
        % (r"; en el PVI las constantes se fijan en la Parte 3" if pvi else ""),
        lineas, "ecs. (285) y (279)"))
    return {"yp": yp, "sin_resolver": bool(sin_resolver), "k_absorbido": k_abs}
