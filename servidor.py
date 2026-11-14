"""
servidor.py — Sirve la pizarra en http://localhost:8000 (lo arranca «Abrir pizarra.bat»).

Es lo mismo que «python -m http.server 8000», con dos diferencias:
  · le dice al navegador que NO guarde copias viejas de los archivos
    (así, cada vez que cambias algo, carga la versión nueva sin Ctrl+F5);
  · con «python servidor.py --movil» también se puede abrir desde el
    móvil, si está conectado al MISMO Wi-Fi que el PC
    (lo arranca «Abrir pizarra en el movil.bat»).
"""
import functools
import http.server
import os
import socket
import sys

PUERTO = 8000
CARPETA = os.path.dirname(os.path.abspath(__file__))


class SinCache(http.server.SimpleHTTPRequestHandler):
    def end_headers(self):
        self.send_header("Cache-Control", "no-cache, must-revalidate")
        super().end_headers()

    def log_message(self, formato, *args):
        pass  # sin mensajes por cada archivo


def ip_local():
    """IP del PC dentro de la red Wi-Fi de casa (p. ej. 192.168.1.35)."""
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("8.8.8.8", 80))   # no envía nada: solo sirve para saber qué IP usaría
        return s.getsockname()[0]
    except OSError:
        return None
    finally:
        s.close()


if __name__ == "__main__":
    movil = "--movil" in sys.argv
    direccion = "0.0.0.0" if movil else "127.0.0.1"
    manejador = functools.partial(SinCache, directory=CARPETA)
    with http.server.ThreadingHTTPServer((direccion, PUERTO), manejador) as servidor:
        print(f"Pizarra en este PC:  http://localhost:{PUERTO}")
        if movil:
            ip = ip_local()
            if ip:
                print()
                print("  En el MOVIL (conectado al mismo Wi-Fi que el PC), abre Safari y escribe:")
                print()
                print(f"      http://{ip}:{PUERTO}")
                print()
            else:
                print("No he encontrado la IP del PC en la red Wi-Fi. ¿Está conectado?")
        print("Cierra esta ventana para apagarla.")
        servidor.serve_forever()
