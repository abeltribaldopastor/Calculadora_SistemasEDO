# Pizarra de sistemas de EDOs

**Autor:** Abel Tribaldo

Calculadora web que resuelve **paso a paso y de forma exacta** sistemas lineales de
ecuaciones diferenciales de primer orden con coeficientes constantes:

$$\frac{d\vec y}{dt} = \hat A\,\vec y(t) + \vec f(t),\qquad n = 2,\dots,5$$

Explica cada paso como en una pizarra de clase y sigue los métodos del temario de
*Mètodes Matemàtics I* (Universitat de València), caps. XIX–XXII:

| Autovalores                         | Método                                     |
|-------------------------------------|--------------------------------------------|
| Todos distintos                     | **Caso A**: autovectores y matriz fundamental |
| Uno solo, de multiplicidad *n*      | **Caso B**: Cayley-Hamilton (serie truncada) |
| Repetidos mezclados con distintos   | **Caso C**: matrices constituyentes Ẑᵢⱼ      |

Si el sistema no es homogéneo, calcula la solución particular con la fórmula
$\vec y_p = e^{\hat At}\int ds\, e^{-\hat As}\vec f(s)$ (ec. 285). Es una herramienta de apoyo
al estudio, no un sustituto de hacer los ejercicios.

---

## Cómo está hecha

```
index.html, estilo.css, app.js   → la interfaz (solo dibuja; no hay matemáticas aquí)
                                   app.js: vista de diapositivas (por defecto) y vista scroll
portada.js                       → pizarra de bienvenida con dibujos (solo al abrir la web)
arte/                            → dibujos a tiza de la portada (cara y escudo)
worker.js                        → carga Python (Pyodide) en el navegador y ejecuta motor/
motor/                           → TODA la matemática, en Python + SymPy
tests/test_casos.py              → los 9 casos de prueba
ejemplos.json                    → los 9 ejemplos de la web (y sus resultados de referencia)
```

La web es **estática**: no hay servidor. Python se ejecuta en el navegador de cada visitante
gracias a [Pyodide](https://pyodide.org). La primera visita tarda 10–30 s en descargar
Python y SymPy; después el navegador lo guarda en caché.

### El motor (`motor/`)

| Archivo          | Qué hace                                                        |
|------------------|-----------------------------------------------------------------|
| `entrada.py`     | Lee y valida lo que escribe el usuario. Define `t`, `s`, `λ`, `c₁…cₙ`. |
| `simplificar.py` | Deja las expresiones limpias (sin `I`, sin `sinh`) y ayuda a escribir LaTeX. |
| `homogenea.py`   | Parte 1: polinomio característico, casos A, B y C, $e^{\hat At}$. |
| `particular.py`  | Parte 2: pasos P1–P6 de la solución particular, resonancia.      |
| `comprobar.py`   | Comprueba que $\dot{\vec y}-\hat A\vec y-\vec f=\vec 0$.          |
| `resolver.py`    | `resolver(datos)`: junta todo y devuelve la lista de pasos.     |

Cada paso que devuelve el motor es un diccionario como este (el JavaScript solo lo pinta):

```json
{ "parte": 1, "id": "1.5", "color": "azul", "titulo": "Autovectores",
  "texto": "Resolvemos $(\\hat A-\\lambda_1\\hat I)\\vec v_1=\\vec 0$…",
  "latex": ["\\vec v_1 = …"], "ref": "ec. (291), cap. XX" }
```

Para cambiar una explicación, busca el texto en `motor/*.py` y edítalo. Los colores
válidos son `blanco`, `amarillo`, `azul`, `menta` y `coral`.

---

## Probar el motor en tu ordenador (sin navegador)

```bash
pip install sympy pytest
```

Desde la carpeta del proyecto:

```bash
python -c "from motor.resolver import resolver; r = resolver({'n': 2, 'A': [['1','2'],['2','1']], 'f': ['0','0'], 'modo': 'pvi', 't0': '0', 'y0': ['1','0']}); print(r['caso'], r['solucion']['y'])"
```

Pasar los tests:

```bash
pytest tests/
```

o, sin pytest:

```bash
python tests/test_casos.py
```

Si cambias algo en `motor/`, vuelve a pasar los tests antes de publicar.

---

## Probar la web en local

Abrir `index.html` con doble clic **no funciona**: el navegador no deja que la página
descargue los archivos `.py` del disco. Hay que servirla con un pequeño servidor:

```bash
python -m http.server 8000
```

y abrir <http://localhost:8000>. El botón discreto **Tests** del pie de página ejecuta los
mismos 9 casos dentro del navegador.

## Privacidad

Sin cookies, sin analítica y sin rastreadores. Todo el cálculo se hace en el navegador de
quien visita la página. Solo se descargan Pyodide/SymPy y KaTeX (jsDelivr) y las fuentes
(Google Fonts).

© 2026 Abel Tribaldo
