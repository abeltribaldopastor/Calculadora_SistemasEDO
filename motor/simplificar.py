# -*- coding: utf-8 -*-
"""
simplificar.py — Tubería de simplificación (sección 5) y ayudas para escribir LaTeX.

PROBLEMA: SymPy da resultados correctos pero a menudo ilegibles (sinh(3t) metidos
en e^{Ât}, unidades imaginarias «I» que no se cancelan, términos sin agrupar…).

SOLUCIÓN: pasamos SIEMPRE por una «forma canónica» y desde ella reconstruimos
una forma real y ordenada:

  1) Reescribimos sen, cos, senh y cosh de la variable como EXPONENCIALES
     (complejas si hace falta) y expandimos.
  2) Ahora la expresión es una suma de términos   coef · t^d · e^{λ t}.
     Juntamos los términos con el mismo par (d, λ).        → descomponer()
  3) Reconstruimos en FORMA REAL: cada pareja de conjugados λ = α ± iβ se
     convierte, con la fórmula de Euler, en e^{αt}(P cos βt + Q sen βt);
     y todo se agrupa por exponenciales e^{αt}.              → recomponer()

Así nunca quedan «I» sueltas en un resultado real, nunca salen sinh/cosh y las
comprobaciones «¿esto es 0?» son exactas (basta ver que todos los coef. son 0).
Si una expresión no tiene esa forma (p. ej. log(t) o 1/(1+t)) se usa la tubería
clásica de SymPy: rewrite(exp) → expand → powsimp → trigsimp.
"""
from functools import reduce
from math import gcd

from sympy import (Add, Mul, S, I, exp, sin, cos, sinh, cosh, tanh, expand,
                   expand_complex, simplify, trigsimp, powsimp, factor_terms,
                   conjugate, Matrix, sympify, Rational, N, radsimp, Symbol)
from sympy.printing.latex import LatexPrinter

from .entrada import t

# Colores de la tiza (los mismos que en estilo.css), para usarlos con \color{} en LaTeX.
COLORES = {
    "blanco": "#ebe8df",
    "amarillo": "#e8d79a",
    "azul": "#a9cbd9",
    "menta": "#afd3b8",
    "coral": "#e2aaa3",
}

_TRIG = (sin, cos, sinh, cosh, tanh)


# ===========================================================================
# 1. Forma canónica:  Σ coef · var^d · e^{λ·var}
# ===========================================================================
def _a_exponenciales(expr, var):
    """Cambia sin, cos, sinh, cosh y tanh QUE DEPENDEN de var por exponenciales."""
    return expr.replace(lambda e: isinstance(e, _TRIG) and e.has(var),
                        lambda e: e.rewrite(exp))


def es_cero_constante(c):
    """¿Es 0 esta constante (puede contener c1, c2…, sqrt, I…)?"""
    c = expand(c)
    if c == 0:
        return True
    if c.has(I):
        c = expand(expand_complex(c))
        if c == 0:
            return True
    if c.is_number:
        if simplify(c) == 0:
            return True
        try:
            return abs(complex(N(c, 60))) < 1e-45
        except (TypeError, ValueError):
            return False
    return simplify(c) == 0


def descomponer(expr, var=t):
    """
    Escribe expr como Σ coef·var^d·e^{λ·var}.
    Devuelve un diccionario {(d, λ): coef} (sin coeficientes nulos),
    o None si la expresión no tiene esa forma.
    """
    expr = sympify(expr)
    e = expand(_a_exponenciales(expr, var))
    terminos = {}
    for term in Add.make_args(e):
        if term == 0:
            continue
        coef, dep = term.as_independent(var, as_Add=False)
        d = 0
        lam_ = S.Zero
        for fac in Mul.make_args(dep):
            if fac == 1:
                continue
            if fac == var:
                d += 1
            elif fac.is_Pow and fac.base == var and fac.exp.is_Integer and fac.exp > 0:
                d += int(fac.exp)
            elif isinstance(fac, exp):
                arg = expand(fac.args[0])
                cte, lineal = arg.as_independent(var, as_Add=True)
                k = expand(lineal / var)
                if k.has(var):
                    return None          # p. ej. e^{t²}: no es de la forma buscada
                lam_ += k
                if cte != 0:
                    coef = coef * exp(cte)
            else:
                return None              # p. ej. log(t), 1/(1+t), sqrt(t)…
        clave = (d, expand(lam_))
        terminos[clave] = terminos.get(clave, S.Zero) + coef
    limpio = {}
    for clave, c in terminos.items():
        if not es_cero_constante(c):
            limpio[clave] = expand(c)
    return limpio


def _parte_real(c):
    c = expand(c)
    if c.has(I):
        c = expand(expand_complex(c))
    if c.is_number and not c.is_Rational:
        c = expand(radsimp(c))
    return c


def recomponer(terminos, var=t):
    """
    Inversa de descomponer(), pero en FORMA REAL:
    las parejas λ = α ± iβ se juntan en e^{αt}(P cos βt + Q sen βt)
    y todo se agrupa por exponenciales e^{αt}.
    """
    if not terminos:
        return S.Zero
    grupos = {}       # α -> {(d, tipo, β): coeficiente}
    vistos = set()
    for (d, l), c in terminos.items():
        if (d, l) in vistos:
            continue
        a, b = [expand(x) for x in l.as_real_imag()]
        g = grupos.setdefault(a, {})
        if b == 0:
            vistos.add((d, l))
            g[(d, "uno", S.Zero)] = g.get((d, "uno", S.Zero), S.Zero) + _parte_real(c)
        else:
            if b.is_positive:
                lp, lm, beta = l, expand(conjugate(l)), b
            else:
                lp, lm, beta = expand(conjugate(l)), l, -b
            cp = terminos.get((d, lp), S.Zero)
            cm = terminos.get((d, lm), S.Zero)
            vistos.add((d, lp))
            vistos.add((d, lm))
            # c₊e^{iβt} + c₋e^{-iβt} = (c₊ + c₋) cos βt + i(c₊ − c₋) sen βt   (Euler)
            g[(d, "cos", beta)] = g.get((d, "cos", beta), S.Zero) + _parte_real(cp + cm)
            g[(d, "sin", beta)] = g.get((d, "sin", beta), S.Zero) + _parte_real(I * (cp - cm))
    resultado = S.Zero
    for a, g in grupos.items():
        contenido = S.Zero
        for (d, tipo, beta), c in g.items():
            if es_cero_constante(c):
                continue
            if c.free_symbols:
                c = factor_terms(c)
            fun = S.One if tipo == "uno" else (cos(beta * var) if tipo == "cos" else sin(beta * var))
            contenido += c * var**d * fun
        resultado += exp(a * var) * contenido
    return resultado


# ===========================================================================
# 2. La tubería que se aplica a TODO lo que se muestra
# ===========================================================================
def limpiar_clasico(expr, var=t):
    """Tubería clásica (para expresiones que no son Σ coef·t^d·e^{λt})."""
    e = sympify(expr).rewrite([sinh, cosh, tanh], exp)
    if e.has(I):
        e = simplify(expand_complex(e))
    e = powsimp(expand(e))
    if e.has(sin, cos):
        e = trigsimp(e)
    return e


def limpiar(expr, var=t):
    """Deja una expresión escalar limpia, real y agrupada por exponenciales."""
    expr = sympify(expr)
    if expr == 0:
        return S.Zero
    if not expr.has(var):
        e = expand(expr)
        if e.has(I):
            e = expand(expand_complex(e))
        if e.is_number and not e.is_Rational:
            e = simplify(e)
        return e
    try:
        terminos = descomponer(expr, var)
    except Exception:
        terminos = None
    if terminos is None:
        return limpiar_clasico(expr, var)
    r = recomponer(terminos, var)
    if r.has(I):
        r2 = simplify(expand_complex(r))
        if not r2.has(I):
            r = r2
    return r


def limpiar_matriz(M, var=t):
    return M.applyfunc(lambda x: limpiar(x, var))


def simp_cte(x):
    """Simplifica una constante (entradas de matrices numéricas, autovectores…)."""
    x = expand(sympify(x))
    if x.is_Rational:
        return x
    if x.has(I):
        x = expand(expand_complex(x))
    if x.is_number:
        x = expand(radsimp(x))
    return x


def es_cero(expr, var=t):
    """¿Es idénticamente 0 esta expresión (simbólicamente)?"""
    expr = sympify(expr)
    if expr == 0:
        return True
    try:
        terminos = descomponer(expr, var)
    except Exception:
        terminos = None
    if terminos is not None:
        return len(terminos) == 0
    return simplify(expr) == 0


def matriz_es_cero(M, var=t):
    return all(es_cero(x, var) for x in M)


def claves(expr, var=t):
    """Conjunto de pares (d, λ) que aparecen en la forma canónica (o None)."""
    d = descomponer(expr, var)
    return None if d is None else set(d.keys())


# ===========================================================================
# 3. Escribir LaTeX con la notación de los apuntes
# ===========================================================================
class _Impresora(LatexPrinter):
    """Igual que la de SymPy, pero escribe e^{αt}(…) con la exponencial DELANTE."""

    def _print_Mul(self, expr):
        coef, resto = expr.as_coeff_Mul()
        if resto.is_Mul and len(resto.args) == 2:
            a, b = resto.args
            if isinstance(b, exp):
                a, b = b, a
            if isinstance(a, exp) and b.is_Add:
                if coef == 1:
                    pre = ""
                elif coef == -1:
                    pre = "- "
                else:
                    pre = self._print(coef) + " "
                return pre + self._print(a) + r"\left(" + self._print(b) + r"\right)"
        return super()._print_Mul(expr)


_IMPRESORA = _Impresora({"mat_delim": "("})


def tex(expr):
    """LaTeX de una expresión o matriz (matrices con paréntesis, como en los apuntes)."""
    return _IMPRESORA.doprint(expr)


def tex_det(M):
    """Determinante escrito con barras verticales."""
    filas = [" & ".join(tex(M[i, j]) for j in range(M.cols)) for i in range(M.rows)]
    return r"\begin{vmatrix}" + r" \\ ".join(filas) + r"\end{vmatrix}"


def _denominador_comun(M):
    """Si TODOS los coeficientes numéricos de la matriz tienen el mismo denominador q>1, devuelve q."""
    qs = set()
    for x in M:
        if x == 0:
            continue
        for term in Add.make_args(expand(x)):
            c, _ = term.as_coeff_Mul()
            if not c.is_Rational:
                return 1
            qs.add(int(c.q))
    if len(qs) == 1:
        q = qs.pop()
        return q if q > 1 else 1
    return 1


def tex_matriz(M, var=t):
    """
    LaTeX de una matriz sacando factores comunes «naturales»:
      · una exponencial común e^{αt} (p. ej. e^{2t}(…) en el caso B),
      · un denominador común (p. ej. ½(…) o ⅓(…)).
    """
    prefijo = ""
    no_nulos = [x for x in M if x != 0]
    if not no_nulos:
        return tex(M)
    try:
        descs = [descomponer(x, var) for x in no_nulos]
    except Exception:
        descs = [None]
    if all(d for d in descs):
        alfas = {expand(l.as_real_imag()[0]) for d in descs for (_, l) in d}
        if len(alfas) == 1:
            a = alfas.pop()
            if a != 0:
                M = M.applyfunc(lambda x: limpiar(x * exp(-a * var), var))
                prefijo = tex(exp(a * var))
    if not any(x.free_symbols - {var} for x in M):
        q = _denominador_comun(M)
        if q > 1:
            M = M.applyfunc(lambda x: limpiar(expand(x * q), var))
            prefijo = r"\frac{1}{%d}" % q + prefijo
    return prefijo + tex(M)


def tex_columna(simbolos_tex):
    """Vector columna con elementos ya escritos en LaTeX."""
    return r"\begin{pmatrix}" + r" \\ ".join(simbolos_tex) + r"\end{pmatrix}"


def color(nombre, contenido):
    return r"{\color{%s}{%s}}" % (COLORES[nombre], contenido)


# ===========================================================================
# 4. Pasos de la pizarra
# ===========================================================================
def paso(parte, id_, color_, titulo, texto="", latex=None, ref="", clase=None):
    """
    Crea un paso de la pizarra (el JS solo lo pinta).
      parte  : 1, 2, 3 (o "V" para la verificación)
      color_ : "blanco", "amarillo", "azul", "menta" o "coral"
      texto  : explicación en español; las fórmulas en línea van entre $…$
      latex  : lista de fórmulas en modo display
      ref    : ecuación o capítulo de los apuntes, p. ej. "ec. (318), cap. XXI"
      clase  : opcional ("final" = solución recuadrada, "aviso" = aviso en coral)
    """
    d = {"parte": parte, "id": id_, "color": color_, "titulo": titulo,
         "texto": texto, "latex": list(latex or []), "ref": ref}
    if clase:
        d["clase"] = clase
    return d


def mcd_lista(enteros):
    return reduce(gcd, enteros, 0)


def mcm_lista(enteros):
    return reduce(lambda a, b: a * b // gcd(a, b), enteros, 1)


def simbolo_tex(nombre):
    """Símbolo no conmutativo cuyo LaTeX es exactamente `nombre` (para Ẑ_ij, etc.)."""
    return Symbol(nombre, commutative=False)


def racional(x):
    return Rational(x)
