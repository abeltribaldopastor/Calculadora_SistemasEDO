# -*- coding: utf-8 -*-
"""
Motor de cálculo de la «Pizarra de sistemas de EDOs» (Abel Tribaldo).

Resuelve   dy/dt = Â·y(t) + f(t)   con Â constante (n = 2…5), paso a paso,
siguiendo los métodos de los apuntes de Mètodes Matemàtics I (caps. XIX–XXII).

Es Python puro + SymPy: funciona igual en el ordenador y en el navegador (Pyodide).

Uso rápido:
    from motor.resolver import resolver
    r = resolver({"n": 2, "A": [["1", "2"], ["2", "1"]], "f": ["0", "0"],
                  "modo": "pvi", "t0": "0", "y0": ["1", "0"]})
    print(r["caso"], r["ok"])

Módulos:
    entrada.py     → leer y validar lo que escribe el usuario
    simplificar.py → dejar las expresiones limpias + ayudas para escribir LaTeX
    homogenea.py   → Parte 1: casos A, B y C (e^{Ât})
    particular.py  → Parte 2: pasos P1–P6 (solución particular)
    comprobar.py   → verificación de la solución
    resolver.py    → función principal resolver(datos)
"""
