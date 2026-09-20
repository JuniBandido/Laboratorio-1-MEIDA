import os
import shutil
import time

class ConfigError(Exception):
    pass


class ConfigManager:
    DEFAULTS = {
        "nombre_usuario": "Usuario",
        "tema_interfaz": "claro",
        "idioma": "es/es-ES",
        "tamaño_fuente": "12",
        "color_barra_menu": "#2c3e50",
        "color_letra": "#000000",
        "foto_perfil": "",
    }

    def __init__(self, base_dir=None):
        directorio_por_defecto = os.path.join(os.getcwd(), "mi_app_config")
        self.base_dir = base_dir or directorio_por_defecto
        
        self.profile_pics_dir = os.path.join(self.base_dir, "profile_pics")
        self.config_path = os.path.join(self.base_dir, "config.txt")
        self.backup_path = os.path.join(self.base_dir, "config.bak")
        self.tmp_path = os.path.join(self.base_dir, "config.tmp")

        self._ensure_dirs()