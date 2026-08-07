"""conftest: añade la carpeta jarvis/ al sys.path para los imports raíz (brain.*, core.*)."""

import sys
from pathlib import Path

JARVIS_DIR = Path(__file__).resolve().parent.parent
if str(JARVIS_DIR) not in sys.path:
    sys.path.insert(0, str(JARVIS_DIR))
