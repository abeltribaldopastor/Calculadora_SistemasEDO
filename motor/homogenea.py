# -*- coding: utf-8 -*-
"""
homogenea.py — PARTE 1: solución homogénea y exponencial matricial e^{Ât}.

Árbol de decisión (sección 3.0, NO se cambia):
    · todos los autovalores distintos (m = n)        → CASO A: autovectores y M̂(t)   (caps. XIX–XX)
    · un único autovalor de multiplicidad n (m = 1)  → CASO B: Cayley-Hamilton       (cap. XXI)
    · repetidos mezclados con distintos (1 < m < n)  → CASO C: matrices constituyentes (cap. XXII)

Cada caso calcula e^{Ât} SOLO con su método. Después, sin mostrarlo, se compara
con (Â·t).exp() de SymPy; si no coincide se añade un aviso visible de error interno.

La función principal es parte1(A, n, pasos) → diccionario con la información.
"""
import random

import mpmath
from sympy import (Matrix, eye, zeros, exp, I, S, roots, Poly, expand, factorial,
                   diff, conjugate, CRootOf, Mul, N, expand_complex, simplify)

from .entrada import t, lam, constantes, ErrorMotor
from .simplificar import (limpiar, limpiar_matriz, simp_cte, es_cero, tex, tex_det,
                          tex_matriz, tex_columna, paso, mcd_lista, mcm_lista,
                          simbolo_tex)


# ===========================================================================
# Utilidades
# ===========================================================================
def _re_im(x):
    a, b = x.as_real_imag()
    return simp_cte(a), simp_cte(b)


def _orden(par):
    """Ordena autovalores: por parte real creciente, después por |β| creciente,
    y en cada pareja conjugada primero α + iβ y justo detrás α − iβ
    (así cada pareja queda junta: i, −i, 2i, −2i…)."""
    a, b = _re_im(par[0])
    return (float(N(a)), abs(float(N(b))), -float(N(b)))


def _forma_cerrada(r):
    return not r.has(CRootOf) and r.count_ops() <= 30


def _tex_autovalor(l):
    return tex(l)


def tex_exp(l):
    """e^{λt} escrito como en la pizarra: e^{3t}, e^{-t}, e^{(4+i)t}."""
    if l.is_Add:
        return r"e^{\left(%s\right)t}" % tex(l)
    return "e^{%s}" % tex(l * t)


def A_menos(l):
    """LaTeX de (Â − λÎ) con λ concreto: Â−2Î, Â+3Î, Â−Î, Â−(4+i)Î…"""
    l = simp_cte(l)
    if l == 0:
        return r"\hat A"
    if l.could_extract_minus_sign():
        signo, val = "+", -l
    else:
        signo, val = "-", l
    if val == 1:
        num = ""
    elif val.is_Add:
        num = r"\left(" + tex(val) + r"\right)"
    else:
        num = tex(val)
    return r"\hat A" + signo + num + r"\hat I"


def _matriz_cte(M):
    return M.applyfunc(simp_cte)


def escalar_vector(v):
    """Multiplica el autovector para que tenga entradas enteras sencillas."""
    coefs = []
    for x in v:
        x = expand(x)
        if x == 0:
            continue
        for term in x.as_ordered_terms():
            c, _ = term.as_coeff_Mul()
            if not c.is_Rational:
                return v
            coefs.append(c)
    if not coefs:
        return v
    den = mcm_lista([int(c.q) for c in coefs])
    num = mcd_lista([abs(int(c.p)) for c in coefs]) or 1
    v = v.applyfunc(lambda x: simp_cte(x * S(den) / num))
    for x in v:
        if x != 0:
            if x.could_extract_minus_sign():
                v = -v
            break
    return v


def autovector(A, l, n):
    """Resuelve (Â − λÎ)v = 0 y devuelve un autovector escalado."""
    B = (A - l * eye(n)).applyfunc(simp_cte)
    base = B.nullspace(simplify=True)
    if not base:
        # Respaldo: buscar el autovector que da SymPy para este mismo λ.
        for val, _, vecs in A.eigenvects(simplify=True):
            if abs(complex(N(val - l, 30))) < 1e-20:
                base = vecs
                break
    if not base:
        raise ErrorMotor("No he podido calcular el autovector de λ = %s." % l)
    return escalar_vector(base[0].applyfunc(simp_cte))


# ===========================================================================
# Paso común: polinomio característico
# ===========================================================================
def polinomio_y_autovalores(A, n, pasos):
    M = lam * eye(n) - A
    p = expand(A.charpoly(lam).as_expr())
    raices = roots(Poly(p, lam))
    total = sum(raices.values())

    pasos.append(paso(
        1, "1.1", "blanco", "Polinomio característico",
        r"Con el convenio de los apuntes, $p(\lambda)=|\lambda\hat I-\hat A|$:",
        [r"p(\lambda)=|\lambda\hat I-\hat A|=" + tex_det(M) + "=" + tex(p)],
        "cap. XXI"))

    if total < n or not all(_forma_cerrada(r) for r in raices):
        pasos.append(paso(
            1, "1.2", "coral", "Raíces sin forma cerrada manejable",
            r"Las raíces de $p(\lambda)$ no tienen una forma cerrada manejable "
            r"(cúbica o quíntica irreducible, radicales enormes…). Con los métodos "
            r"exactos de los apuntes no se puede seguir: detengo el cálculo.",
            [], "cap. XXI", clase="aviso"))
        raise ErrorMotor("Los autovalores no tienen una forma cerrada manejable; "
                         "el cálculo exacto se detiene.")

    autov = sorted(((simp_cte(r), k) for r, k in raices.items()), key=_orden)
    factores = []
    for l, k in autov:
        base = r"\left(" + tex(expand(lam - l)) + r"\right)"
        factores.append(base + ("^{%d}" % k if k > 1 else ""))
    lineas = [r"p(\lambda)=" + tex(p) + "=" + "".join(factores)]
    lista = [r"\lambda_{%d}=%s\quad(k_{%d}=%d)" % (i, _tex_autovalor(l), i, k)
             for i, (l, k) in enumerate(autov, 1)]
    lineas.append(r",\qquad ".join(lista))
    pasos.append(paso(
        1, "1.2", "amarillo", "Autovalores y multiplicidades",
        r"Factorizamos $p(\lambda)=(\lambda-\lambda_1)^{k_1}\cdots(\lambda-\lambda_m)^{k_m}$ "
        r"con $\sum_i k_i=n=%d$. Hay $m=%d$ autovalores distintos:" % (n, len(autov)),
        lineas, "cap. XXI"))
    return p, autov


# ===========================================================================
# CASO A: autovalores distintos → autovectores y M̂(t)
# ===========================================================================
def caso_A(A, n, autov, pasos):
    pasos.append(paso(
        1, "1.3", "coral", "Diagnóstico: CASO A",
        r"Todos los autovalores son distintos $\Rightarrow$ $\hat A$ es diagonalizable. "
        r"Aplicamos el método de autovectores.", [], "caps. XIX–XX"))
    pasos.append(paso(
        1, "1.4", "blanco", "¿Por qué autovalores y autovectores?",
        r"Proponemos soluciones de la forma $\vec y_i(t)=e^{\lambda_i t}\vec v_i$. "
        r"Al sustituir en $\dot{\vec y}=\hat A\vec y$ y simplificar $e^{\lambda_i t}\neq0$ "
        r"queda un problema de autovalores: $\lambda_i$ son los autovalores de $\hat A$ y "
        r"$\vec v_i$ sus autovectores.",
        [r"\lambda_i e^{\lambda_i t}\vec v_i=\hat A\,e^{\lambda_i t}\vec v_i"
         r"\;\Longrightarrow\;\hat A\vec v_i=\lambda_i\vec v_i"],
        "ej. 1, cap. XX"))

    columnas = []
    terminos = []
    idx_c = 1
    sub = 1
    hay_complejos = False
    for i, (l, k) in enumerate(autov, 1):
        a, b = _re_im(l)
        if b.is_negative:
            continue        # se trata junto con su conjugado α + iβ
        v = autovector(A, l, n)
        B = (A - l * eye(n)).applyfunc(simp_cte)
        lineas = [r"(\hat A-\lambda_{%d}\hat I)\vec v_{%d}=%s\,\vec v_{%d}=\vec 0"
                  % (i, i, tex(B), i),
                  r"\vec v_{%d}=%s" % (i, tex(v))]
        texto = r"Para $\lambda_{%d}=%s$ resolvemos $(\hat A-\lambda_{%d}\hat I)\vec v_{%d}=\vec 0$ " \
                r"(escalamos el autovector para que tenga entradas sencillas):" % (i, tex(l), i, i)
        if b != 0:
            texto += r" Para el conjugado $\lambda_{%d}=%s$ basta con tomar $\vec v_{%d}=\vec v_{%d}^{\,*}$." \
                     % (i + 1, tex(simp_cte(conjugate(l))), i + 1, i)
        pasos.append(paso(1, "1.5.%d" % sub, "azul", r"Autovector de $\lambda_{%d}$" % i,
                          texto, lineas, "ec. (291), cap. XX"))
        sub += 1

        z = exp(l * t) * v
        if b == 0:
            col = limpiar_matriz(z)
            columnas.append(col)
            terminos.append(r"c_{%d}\,%s%s" % (idx_c, tex_exp(l), tex(v)))
            idx_c += 1
        else:
            hay_complejos = True
            zc = z.applyfunc(conjugate)
            u = limpiar_matriz((z + zc) / 2)
            w = limpiar_matriz((z - zc) / (2 * I))
            columnas += [u, w]
            terminos.append(r"c_{%d}%s+c_{%d}%s" % (idx_c, tex_matriz(u), idx_c + 1, tex_matriz(w)))
            idx_c += 2
            pasos.append(paso(
                1, "1.5.%d" % sub, "azul", "Pareja compleja: fórmula de Euler",
                r"Tomamos solo $\lambda_{%d}=%s$ y su $\vec v_{%d}$. Desarrollamos con Euler, "
                r"$e^{(\alpha+i\beta)t}=e^{\alpha t}(\cos\beta t+i\sin\beta t)$, y separamos "
                r"$\vec u(t)=\mathrm{Re}$ y $\vec w(t)=\mathrm{Im}$. Estas dos columnas "
                r"<b>reales</b> e independientes sustituyen a las dos columnas complejas "
                r"conjugadas de $\hat M(t)$; equivale a exigir $c^-=(c^+)^*$ para que la "
                r"solución sea real." % (i, tex(l), i),
                [r"%s%s=\vec u(t)+i\,\vec w(t)" % (tex_exp(l), tex(v)),
                 r"\vec u(t)=%s,\qquad \vec w(t)=%s" % (tex_matriz(u), tex_matriz(w))],
                "ecs. (311)–(312), cap. XX"))
            sub += 1

    M = Matrix.hstack(*columnas)
    c = constantes(n)
    pasos.append(paso(
        1, "1.6", "azul", "Solución general y matriz fundamental",
        r"Superponemos las $n=%d$ soluciones independientes. En forma matricial, "
        r"$\vec y(t)=\hat M(t)\,\vec c$, donde las columnas de $\hat M(t)$ son esas soluciones%s:"
        % (n, " (reales)" if hay_complejos else ""),
        [r"\vec y_h(t)=" + "+".join(terminos),
         r"\hat M(t)=" + tex(M),
         r"\vec y_h(t)=\hat M(t)\,\vec c,\qquad \vec c=" + tex(Matrix(c))],
        "ecs. (291) y (278), caps. XIX–XX"))

    M0 = _matriz_cte(M.subs(t, 0))
    if M0.det() == 0:
        raise ErrorMotor("Error interno: M̂(0) no es invertible.")
    M0inv = _matriz_cte(M0.inv())
    E = limpiar_matriz(M * M0inv)
    pasos.append(paso(
        1, "1.7", "azul", "Exponencial matricial",
        r"Como $e^{\hat A\cdot0}=\hat I$, la exponencial es la matriz fundamental "
        r"«normalizada» en $t=0$:",
        [r"\hat M(0)=" + tex(M0) + r",\qquad \hat M^{-1}(0)=" + tex_matriz(M0inv),
         r"e^{\hat At}=\hat M(t)\,\hat M^{-1}(0)=" + tex_matriz(E)],
        "ecs. (279) y (288), cap. XX"))
    return {"caso": "A", "E": E, "M": M, "M0inv": M0inv}


def _sub(i):
    return "".join("₀₁₂₃₄₅₆₇₈₉"[int(d)] for d in str(i))


# ===========================================================================
# CASO B: un único autovalor → Cayley-Hamilton y serie truncada
# ===========================================================================
def caso_B(A, n, autov, pasos):
    l1 = autov[0][0]
    pasos.append(paso(
        1, "1.3", "coral", "Diagnóstico: CASO B",
        r"Todos los autovalores son iguales ($\lambda_1=%s$ con multiplicidad $%d$) "
        r"$\Rightarrow$ aplicamos el teorema de Cayley-Hamilton." % (tex(l1), n),
        [], "cap. XXI"))
    pasos.append(paso(
        1, "1.4", "blanco", "El truco de los apuntes",
        r"Como $\lambda_1\hat I$ conmuta con cualquier matriz, podemos separar la exponencial "
        r"y desarrollar en serie de Taylor la segunda parte:",
        [r"e^{\hat At}=e^{\lambda_1 t\hat I}\cdot e^{(\hat A-\lambda_1\hat I)t}"
         r"=e^{\lambda_1 t}\sum_{k=0}^{\infty}\frac{(\hat A-\lambda_1\hat I)^k t^k}{k!}"],
        "ec. (317), cap. XXI"))

    Nm = A - l1 * eye(n)
    potencias = [eye(n)]
    P = Nm
    q = 1
    while not P.is_zero_matrix and q <= n:
        potencias.append(P)
        P = (P * Nm).applyfunc(simp_cte)
        q += 1
    # Ahora N^q = 0 y potencias = [I, N, …, N^{q-1}]
    lineas = [r"p(\hat A)=(%s)^{%d}=\hat 0" % (A_menos(l1), n)]
    if q == 1:
        lineas.append(r"\hat N=%s=\hat 0" % A_menos(l1))
        texto = (r"Cayley-Hamilton: $p(\hat A)=\hat 0$. Definimos $\hat N=\hat A-\lambda_1\hat I$. "
                 r"Aquí $\hat N=\hat 0$, es decir, $\hat A=\lambda_1\hat I$: la serie se reduce a $\hat I$.")
    else:
        lineas.append(r"\hat N=%s=%s" % (A_menos(l1), tex(Nm)))
        for k in range(2, q):
            lineas.append(r"\hat N^{%d}=%s" % (k, tex(potencias[k])))
        lineas.append(r"\hat N^{%d}=\hat 0" % q)
        texto = (r"Cayley-Hamilton: $p(\hat A)=(\hat A-\lambda_1\hat I)^{n}=\hat 0$. "
                 r"Definimos $\hat N=\hat A-\lambda_1\hat I$ y calculamos sus potencias. "
                 r"Los apuntes garantizan que la serie se corta en orden $n-1=%d$ «o puede que antes»: "
                 r"aquí la primera potencia nula es $\hat N^{%d}$%s."
                 % (n - 1, q, " (justo la que predice el teorema)" if q == n else " (antes de lo previsto)"))
    pasos.append(paso(1, "1.5", "azul", r"Cayley-Hamilton: potencias de $\hat N$", texto, lineas,
                      "cap. XXI"))

    corchete = zeros(n, n)
    for k, Pk in enumerate(potencias):
        corchete += Pk * t**k / factorial(k)
    corchete = corchete.applyfunc(expand)
    E = limpiar_matriz(exp(l1 * t) * corchete)
    gen = [r"\hat I", r"(\hat A-\lambda_1\hat I)t"] + [
        r"\frac{(\hat A-\lambda_1\hat I)^{%d}t^{%d}}{%d!}" % (k, k, k) for k in range(2, n)]
    expl = [r"\hat I"]
    for k in range(1, len(potencias)):
        expl.append(tex(potencias[k]) + (r"\frac{t^{%d}}{%d!}" % (k, k) if k > 1 else "t"))
    pasos.append(paso(
        1, "1.6", "azul", "Serie truncada",
        r"Sustituimos en la serie: todas las potencias a partir de $\hat N^{%d}$ son nulas." % q,
        [r"e^{\hat At}=e^{\lambda_1 t}\left[" + "+".join(gen[:n]) + r"\right]",
         r"e^{\hat At}=e^{%s}\left[" % tex(l1 * t) + "+".join(expl) + r"\right]",
         r"e^{\hat At}=e^{%s}%s=%s" % (tex(l1 * t), tex(corchete), tex(E))],
        "ec. (318), cap. XXI"))
    if q > 1:
        pasos.append(paso(
            1, "1.7", "blanco", "Nota didáctica",
            r"La degeneración no da exponenciales distintas: en su lugar aparecen funciones "
            r"independientes nuevas del tipo $t^j e^{\lambda_1 t}$ (aquí hasta $t^{%d}e^{%s}$)."
            % (q - 1, tex(l1 * t)), [], "cap. XXI"))
    return {"caso": "B", "E": E, "N": Nm, "q": q}


# ===========================================================================
# CASO C: degeneración mixta → matrices constituyentes Ẑ_ij
# ===========================================================================
def _Z(i, j):
    return simbolo_tex(r"\hat Z_{%d%d}" % (i, j))


def caso_C(A, n, autov, pasos):
    pasos.append(paso(
        1, "1.3", "coral", "Diagnóstico: CASO C",
        r"Hay autovalores repetidos junto a otros distintos $\Rightarrow$ aplicamos el "
        r"método de las matrices constituyentes $\hat Z_{ij}$.", [], "cap. XXII"))

    # --- Cayley-Hamilton: p(Â) = 0̂ -------------------------------------------
    nombres = []
    mats = []
    prod = eye(n)
    for l, k in autov:
        B = (A - l * eye(n)).applyfunc(simp_cte)
        nombres.append(r"(%s)%s" % (A_menos(l), "^{%d}" % k if k > 1 else ""))
        mats.append(tex(B) + ("^{%d}" % k if k > 1 else ""))
        prod = (prod * B**k).applyfunc(simp_cte)
    pasos.append(paso(
        1, "1.4", "blanco", "Cayley-Hamilton",
        r"Toda matriz anula su polinomio característico:",
        [r"p(\hat A)=" + "".join(nombres) + "=" + "".join(mats) + "=" + tex(prod)],
        "cap. XXI (cf. ec. (323))"))

    complejos = any(_re_im(l)[1] != 0 for l, _ in autov)
    pasos.append(paso(
        1, "1.5", "blanco", "Fórmula de las matrices constituyentes",
        r"Para cualquier función $f$ que admita desarrollo en serie, con $m$ autovalores "
        r"distintos de multiplicidades $k_i$:"
        r" <br>Convenio de los apuntes: en (325) <b>no</b> hay factor $1/j!$; los factoriales "
        r"quedan dentro de las $\hat Z_{ij}$.",
        [r"f(\hat A)=\sum_{i=1}^{m}\sum_{j=0}^{k_i-1}\left.\frac{d^jf(\lambda)}{d\lambda^j}"
         r"\right|_{\lambda=\lambda_i}\hat Z_{ij},\qquad \frac{d^j}{d\lambda^j}e^{\lambda t}=t^je^{\lambda t}"],
        "ec. (325), cap. XXII"))

    mu = [l for l, k in autov for _ in range(k)]
    incog = [(i, j, l) for i, (l, k) in enumerate(autov, 1) for j in range(k)]
    fs = []
    for sidx in range(n):
        f = S.One
        for r in range(sidx):
            f = f * (lam - mu[r])
        fs.append(f)

    def tex_f(sidx):
        if sidx == 0:
            return "1"
        return "".join(r"\left(" + tex(expand(lam - mu[r])) + r"\right)" for r in range(sidx))

    pasos.append(paso(
        1, "1.6", "blanco", "Funciones de prueba",
        r"Por Cayley-Hamilton, con una matriz $%d\times%d$ solo se pueden construir $n=%d$ "
        r"matrices independientes; por eso necesitamos exactamente $%d$ funciones de prueba, y "
        r"ninguna puede ser el polinomio característico completo (daría $\hat 0$). Escribimos la "
        r"lista de autovalores repetidos según su multiplicidad y vamos multiplicando factores:"
        % (n, n, n, n),
        [r"(\mu_1,\dots,\mu_{%d})=(%s)" % (n, ",\\,".join(tex(x) for x in mu)),
         r",\quad ".join(r"f_{%d}(\lambda)=%s" % (sidx, tex_f(sidx)) for sidx in range(n))],
        "ecs. (327)–(328), cap. XXII"))

    # --- f_s(Â) y su desarrollo ------------------------------------------------
    fsA = []
    C = zeros(n, n)
    lineas = []
    for sidx in range(n):
        Mf = eye(n)
        for r in range(sidx):
            Mf = (Mf * (A - mu[r] * eye(n))).applyfunc(simp_cte)
        fsA.append(Mf)
        desarrollo = S.Zero
        for u, (i, j, l) in enumerate(incog):
            C[sidx, u] = simp_cte(diff(fs[sidx], lam, j).subs(lam, l))
            desarrollo += C[sidx, u] * _Z(i, j)
        nombre_A = "".join(r"(%s)" % A_menos(mu[r]) for r in range(sidx)) or r"\hat I"
        lineas.append(r"f_{%d}(\hat A)=%s=%s=%s" % (sidx, nombre_A, tex(Mf), tex(desarrollo)))
    pasos.append(paso(
        1, "1.7", "azul", "Aplicamos (325) a cada función de prueba",
        r"Las derivadas se evalúan en cada $\lambda_i$; los ceros vienen de las raíces de cada $f_s$:",
        lineas, "ec. (325), cap. XXII"))

    vec_Z = tex_columna([tex(_Z(i, j)) for i, j, _ in incog])
    vec_f = tex_columna([r"f_{%d}(\hat A)" % sidx for sidx in range(n)])
    pasos.append(paso(
        1, "1.8", "azul", "Sistema triangular",
        r"Ordenando las incógnitas como $\hat Z_{10},\dots,\hat Z_{1,k_1-1},\hat Z_{20},\dots$ "
        r"el sistema es triangular superior:",
        [tex(C) + vec_Z + "=" + vec_f], "ec. (329), cap. XXII"))

    # --- resolución de abajo arriba ------------------------------------------
    Zs = [None] * n
    lineas = []
    for u in reversed(range(n)):
        i, j, l = incog[u]
        rhs = fsA[u]
        rhs_tex = r"f_{%d}(\hat A)" % u
        for v in range(u + 1, n):
            if C[u, v] != 0:
                rhs = rhs - C[u, v] * Zs[v]
                iv, jv, _ = incog[v]
                rhs_tex += "-" + tex(C[u, v] * _Z(iv, jv)) if not (C[u, v] * _Z(iv, jv)).could_extract_minus_sign() \
                    else "+" + tex(-C[u, v] * _Z(iv, jv))
        Zs[u] = (rhs / C[u, u]).applyfunc(simp_cte)
        izq = rhs_tex if C[u, u] == 1 else r"\frac{1}{%s}\left[%s\right]" % (tex(C[u, u]), rhs_tex)
        lineas.append(r"%s=%s=%s" % (tex(_Z(i, j)), izq, tex(Zs[u])))
    pasos.append(paso(
        1, "1.9", "azul", "Matrices constituyentes",
        r"Resolvemos recursivamente de abajo arriba:", lineas, "ecs. (330)–(331), cap. XXII"))

    # --- comprobaciones ------------------------------------------------------
    suma0 = zeros(n, n)
    sumaA = zeros(n, n)
    t0_tex, tA_tex = [], []
    for u, (i, j, l) in enumerate(incog):
        if j == 0:
            suma0 += Zs[u]
            sumaA += l * Zs[u]
            t0_tex.append(tex(_Z(i, 0)))
            tA_tex.append(tex(l * _Z(i, 0)))
        elif j == 1:
            sumaA += Zs[u]
            tA_tex.append(tex(_Z(i, 1)))
    suma0 = suma0.applyfunc(simp_cte)
    sumaA = sumaA.applyfunc(simp_cte)
    ok0 = suma0 == eye(n)
    okA = sumaA == A.applyfunc(simp_cte)
    pasos.append(paso(
        1, "1.10", "blanco" if ok0 and okA else "coral", "Comprobaciones",
        r"Con $f=1$ debe salir $\hat I$ y con $f=\lambda$ debe salir $\hat A$ "
        r"($\hat Z_{i1}=\hat 0$ si $k_i=1$): %s" % ("✔ se cumplen." if ok0 and okA else "✘ ¡NO se cumplen!"),
        [r"\textstyle\sum_i\hat Z_{i0}=" + "+".join(t0_tex) + "=" + tex(suma0),
         r"\textstyle\sum_i(\lambda_i\hat Z_{i0}+\hat Z_{i1})=" + "+".join(tA_tex).replace("+-", "-")
         + "=" + tex(sumaA)],
        "ec. (325), cap. XXII"))

    # --- e^{Ât} ----------------------------------------------------------------
    Ec = zeros(n, n)
    formula = S.Zero
    for u, (i, j, l) in enumerate(incog):
        Ec += t**j * exp(l * t) * Zs[u]
        formula += t**j * exp(l * t) * _Z(i, j)
    E = limpiar_matriz(Ec)
    E0 = E.subs(t, 0).applyfunc(simp_cte)
    texto = r"Con $f(\lambda)=e^{\lambda t}$ la derivada $j$-ésima es $t^je^{\lambda t}$:"
    if complejos:
        texto += (r" Calculamos con complejos, pero cada pareja conjugada se combina con "
                  r"Euler para mostrar $e^{\hat At}$ en <b>forma real</b>.")
    pasos.append(paso(
        1, "1.11", "azul", "Exponencial matricial",
        texto,
        [r"e^{\hat At}=" + tex(formula),
         r"e^{\hat At}=" + tex_matriz(E),
         r"e^{\hat A\cdot 0}=" + tex(E0) + (r"=\hat I\;\checkmark" if E0 == eye(n) else r"\neq\hat I")],
        "ec. (325), cap. XXII"))
    return {"caso": "C", "E": E, "Z": Zs, "incog": incog}


# ===========================================================================
# Validación interna (no se muestra salvo que falle)
# ===========================================================================
def validar_exponencial(A, E, n):
    """Compara E con (Â·t).exp() de SymPy. Devuelve (ok, diferencia)."""
    try:
        R = (A * t).exp()
        D = (E - R)
        if all(es_cero(x) for x in D):
            return True, None
        D = limpiar_matriz(D)
    except Exception:
        D = None
    # Respaldo numérico independiente (mpmath.expm) por si la simplificación no llega a 0.
    rnd = random.Random(2026)
    for _ in range(4):
        tv = rnd.uniform(-1.2, 1.2)
        num = mpmath.expm(mpmath.matrix([[complex(N(A[i, j] * tv, 30)) for j in range(n)]
                                         for i in range(n)]))
        for i in range(n):
            for j in range(n):
                val = complex(N(E[i, j].subs(t, tv), 30))
                if abs(val - complex(num[i, j])) > 1e-9 * (1 + abs(val)):
                    return False, D
    return True, None


# ===========================================================================
# Función principal de la Parte 1
# ===========================================================================
def parte1(A, n, pasos):
    p, autov = polinomio_y_autovalores(A, n, pasos)
    m = len(autov)
    if m == n:
        info = caso_A(A, n, autov, pasos)
    elif m == 1:
        info = caso_B(A, n, autov, pasos)
    else:
        info = caso_C(A, n, autov, pasos)

    ok, D = validar_exponencial(A, info["E"], n)
    if not ok:
        pasos.append(paso(
            1, "1.E", "coral", r"ERROR INTERNO: discrepancia en $e^{\hat At}$",
            r"La $e^{\hat At}$ obtenida con el método del caso no coincide con la exponencial "
            r"de referencia de SymPy. No oculto la discrepancia; la diferencia es:",
            [tex(D)] if D is not None else [], "sección 5", clase="aviso"))
    info.update({"p": p, "autovalores": autov, "validada": ok})

    c = Matrix(constantes(n))
    if info["caso"] == "A":
        yh = limpiar_matriz(info["M"] * c)
        lineas = [r"\vec y_h(t)=\hat M(t)\,\vec c=" + tex(yh)]
    else:
        yh = limpiar_matriz(info["E"] * c)
        lineas = [r"\vec y_h(t)=e^{\hat At}\,\vec c=" + tex(yh)]
    pasos.append(paso(
        1, "1.F", "azul", "Solución homogénea",
        r"Con constantes arbitrarias $c_1,\dots,c_{%d}$:" % n, lineas,
        "ecs. (278)–(279), cap. XIX"))
    info["yh_general"] = yh
    info["c"] = c
    return info
