"""
main.py - Punto de entrada de Jarvis
Configura los paths e inicia el orquestador
"""

import sys
import os

# Agregar la carpeta jarvis al path de Python
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'jarvis'))

# Ahora importar el orquestador
from orchestrator.orchestrator import Orchestrator

if __name__ == "__main__":
    orchestrator = Orchestrator()
    orchestrator.run()
