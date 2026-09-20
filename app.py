import os
import sys
import traceback
import tkinter as tk
from tkinter import ttk, messagebox, filedialog, colorchooser

from config_manager import ConfigManager

try:
    from PIL import Image, ImageTk
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False


STATUS_MESSAGES = {
    "no_existe": "No se encontró un archivo de configuración previo. "
                 "Se usarán valores predeterminados.",
    "sin_permiso_lectura": "No se tienen permisos para leer el archivo de "
                            "configuración. Se usarán valores predeterminados.",
    "corrupto_recuperado_backup": "El archivo de configuración estaba dañado. "
                                   "Se recuperó la última copia de respaldo (config.bak).",
    "corrupto_sin_backup": "El archivo de configuración estaba dañado y no había "
                            "copia de respaldo disponible. Se restauraron los "
                            "valores predeterminados.",
    "error_lectura": "Ocurrió un error inesperado al leer la configuración. "
                      "Se usarán valores predeterminados.",
}

IDIOMAS = [
    ("es/es-ES", "Español (es/es-ES)"),
    ("en/en-US", "English (en/en-US)"),
]

