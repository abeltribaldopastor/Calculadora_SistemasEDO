# -*- coding: utf-8 -*-
"""
entrada.py — Lectura y validación de los datos que escribe el usuario.

Aquí se definen también los SÍMBOLOS comunes a todo el motor:
    t      → variable independiente (real)
    s      → variable muda de integración (real)
    lam    → λ, la variable del polinomio característico
    c1…cn  → constantes arbitrarias (reales)

Reglas de entrada (sección 2 del enunciado):
    · Â: enteros, fracciones (1/2), decimales (0.5 → 1/2) y constantes exactas
      (sqrt(2), pi). NO se admiten parámetros libres (a, k, omega…).
    · f(t): expresiones que solo dependen de t: 1, t, t^2, exp(2*t), e^(-2t),
      cos(2t), t*exp(t)…
    · t0 e y(t0): números.
"""
import re

from sympy import Symbol, symbols, E, pi, I, S, Expr, Matrix, zoo, oo, nan, latex
from sympy.parsing.sympy_parser import (
    parse_expr,
    standard_transformations,
    implicit_multiplication_application,
    convert_xor,
    rationalize,
)

# ---------------------------------------------------------------------------
# Símbolos comunes
# ---------------------------------------------------------------------------
t = Symbol("t", real=True)
s = Symbol("s", real=True)
lam = Symbol("lambda")


def constantes(n):
    """Devuelve [c1, c2, …, cn] como símbolos reales."""
    return list(symbols("c1:%d" % (n + 1), real=True))


# ---------------------------------------------------------------------------
# Errores con mensaje en español
# ---------------------------------------------------------------------------
class ErrorMotor(Exception):
    """Error «previsto» del cálculo: su mensaje se enseña tal cual al usuario."""


class ErrorEntrada(ErrorMotor):
    """Error en lo que ha escrito el usuario. `errores` = {celda: mensaje}."""

    def __init__(self, mensaje, errores=None):
        super().__init__(mensaje)
        self.errores = errores or {}


# ---------------------------------------------------------------------------
# Lector de expresiones
# ---------------------------------------------------------------------------
# standard + multiplicación implícita (2t → 2*t) + ^ como potencia (t^2)
# + decimales a racional exacto (0.5 → 1/2).
TRANSFORMACIONES = standard_transformations + (
    implicit_multiplication_application,
    convert_xor,
    rationalize,
)

# Nombres que entiende el lector además de las funciones de SymPy.
NOMBRES = {"t": t, "e": E, "E": E, "pi": pi}

# Solo dejamos pasar letras, números, espacios y + - * / ^ ( ) .
# (así no se puede colar código raro dentro de una celda).
_PERMITIDOS = re.compile(r"^[0-9A-Za-z\s+\-*/^().]*$")


def leer_expresion(texto, permitir_t):
    """
    Convierte el texto de una celda en una expresión de SymPy.
    Lanza ErrorEntrada (con mensaje en español) si no es válida.
    Una celda vacía vale 0.
    """
    texto = "" if texto is None else str(texto)
    # Pequeños arreglos para escritura «a mano»: coma decimal, signos tipográficos…
    texto = (texto.replace(",", ".").replace("·", "*").replace("−", "-")
             .replace("×", "*").strip())
    if texto == "":
        return S.Zero
    if len(texto) > 200:
        raise ErrorEntrada("La expresión es demasiado larga (máximo 200 caracteres).")
    if not _PERMITIDOS.match(texto):
        raise ErrorEntrada("Hay caracteres no permitidos. Usa números, letras, "
                           "+ - * / ^ y paréntesis.")
    try:
        expr = parse_expr(texto, local_dict=dict(NOMBRES),
                          transformations=TRANSFORMACIONES, evaluate=True)
    except Exception:
        raise ErrorEntrada("No entiendo «%s». Revisa los paréntesis y los operadores." % texto)

    if not isinstance(expr, Expr):
        raise ErrorEntrada("«%s» no es una expresión matemática válida." % texto)
    if expr.has(zoo, oo, -oo, nan):
        raise ErrorEntrada("«%s» no es un número finito (¿una división entre 0?)." % texto)
    if expr.has(I):
        raise ErrorEntrada("No se admiten números complejos en los datos: el sistema es real.")

    libres = set(expr.free_symbols)
    if permitir_t:
        libres.discard(t)
        if libres:
            nombres = ", ".join(sorted(str(x) for x in libres))
            raise ErrorEntrada("f(t) solo puede depender de t, pero aparece «%s»." % nombres)
    else:
        if t in libres and len(libres) == 1:
            raise ErrorEntrada("Aquí debe ir un número constante: no puede depender de t.")
        if libres:
            nombres = ", ".join(sorted(str(x) for x in libres))
            raise ErrorEntrada(
                "«%s» es un parámetro libre. No se admiten parámetros en Â: la "
                "clasificación en casos A, B y C depende de las multiplicidades de los "
                "autovalores, y con parámetros cambia según su valor. Escribe un número." % nombres)
        if expr.is_real is False:
            raise ErrorEntrada("«%s» no es un número real." % texto)
    return expr


def validar_celda(texto, tipo):
    """
    Validación «en vivo» de una sola celda (la usa la interfaz mientras se escribe).
    tipo: "A", "f", "y0" o "t0".
    Devuelve {"ok": True, "latex": ...} o {"ok": False, "error": "..."}.
    """
    try:
        expr = leer_expresion(texto, permitir_t=(tipo == "f"))
        return {"ok": True, "latex": latex(expr)}
    except ErrorEntrada as e:
        return {"ok": False, "error": str(e)}


def leer_datos(datos):
    """
    Lee el diccionario que manda la interfaz y devuelve otro con objetos de SymPy:
        n, A (Matrix), f (Matrix), homogeneo (bool), modo ("general"/"pvi"),
        t0 (número), y0 (Matrix o None)
    Si hay celdas inválidas lanza ErrorEntrada con todas ellas en `errores`.
    """
    if not isinstance(datos, dict):
        raise ErrorEntrada("Datos de entrada mal formados.")
    try:
        n = int(datos.get("n", 0))
    except (TypeError, ValueError):
        raise ErrorEntrada("La dimensión n debe ser 2, 3, 4 o 5.")
    if n not in (2, 3, 4, 5):
        raise ErrorEntrada("La dimensión n debe ser 2, 3, 4 o 5.")

    errores = {}
    filas = datos.get("A") or []
    if len(filas) != n or any(len(f) != n for f in filas):
        raise ErrorEntrada("La matriz Â debe ser de %d×%d." % (n, n))

    A = Matrix.zeros(n, n)
    for i in range(n):
        for j in range(n):
            try:
                A[i, j] = leer_expresion(filas[i][j], permitir_t=False)
            except ErrorEntrada as e:
                errores["A_%d_%d" % (i, j)] = str(e)

    f_txt = datos.get("f") or ["0"] * n
    if len(f_txt) != n:
        raise ErrorEntrada("El vector f(t) debe tener %d componentes." % n)
    f = Matrix.zeros(n, 1)
    for i in range(n):
        try:
            f[i] = leer_expresion(f_txt[i], permitir_t=True)
        except ErrorEntrada as e:
            errores["f_%d" % i] = str(e)

    modo = datos.get("modo", "general")
    if modo not in ("general", "pvi"):
        raise ErrorEntrada("El modo debe ser «general» o «pvi».")

    t0 = S.Zero
    y0 = None
    if modo == "pvi":
        try:
            t0 = leer_expresion(datos.get("t0", "0"), permitir_t=False)
        except ErrorEntrada as e:
            errores["t0"] = str(e)
        y0_txt = datos.get("y0") or []
        if len(y0_txt) != n:
            raise ErrorEntrada("El vector y(t0) debe tener %d componentes." % n)
        y0 = Matrix.zeros(n, 1)
        for i in range(n):
            if str(y0_txt[i]).strip() == "":
                errores["y0_%d" % i] = "Falta el valor inicial."
                continue
            try:
                y0[i] = leer_expresion(y0_txt[i], permitir_t=False)
            except ErrorEntrada as e:
                errores["y0_%d" % i] = str(e)

    if errores:
        raise ErrorEntrada("Hay %d casilla(s) con errores: corrígelas (están en coral)."
                           % len(errores), errores)

    return {"n": n, "A": A, "f": f, "homogeneo": all(x == 0 for x in f),
            "modo": modo, "t0": t0, "y0": y0}
