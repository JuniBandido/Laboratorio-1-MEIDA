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

    def _ensure_dirs(self):
        try:
            os.makedirs(self.base_dir, exist_ok=True)
            os.makedirs(self.profile_pics_dir, exist_ok=True)
        except PermissionError:
            pass
        except OSError:
            pass

    @staticmethod
    def _parse_line(line):
        line = line.strip("\n").strip("\r")
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            return None
        if "=" not in line:
            return None
        key, _, value = line.partition("=")
        key = key.strip()
        value = value.strip()
        if not key:
            return None
        return key, value

    def _parse_content(self, text):
        data = {}
        for raw_line in text.splitlines():
            parsed = self._parse_line(raw_line)
            if parsed:
                k, v = parsed
                data[k] = v
        return data

    def _validate(self, data):
        result = dict(self.DEFAULTS)
        for key in self.DEFAULTS:
            if key in data and data[key] != "":
                result[key] = data[key]

        if result["tema_interfaz"] not in ("claro", "oscuro"):
            result["tema_interfaz"] = self.DEFAULTS["tema_interfaz"]

        if result["idioma"] not in ("es/es-ES", "en/en-US"):
            result["idioma"] = self.DEFAULTS["idioma"]

        try:
            int(result["tamaño_fuente"])
        except (ValueError, TypeError):
            result["tamaño_fuente"] = self.DEFAULTS["tamaño_fuente"]

        for color_key in ("color_barra_menu", "color_letra"):
            val = result.get(color_key, "")
            if not (isinstance(val, str) and val.startswith("#") and len(val) in (4, 7)):
                result[color_key] = self.DEFAULTS[color_key]

        return result

    def load(self):
        if not os.path.exists(self.config_path):
            return dict(self.DEFAULTS), "no_existe"

        try:
            with open(self.config_path, "r", encoding="utf-8") as f:
                content = f.read()
        except PermissionError:
            return dict(self.DEFAULTS), "sin_permiso_lectura"
        except UnicodeDecodeError:
            recovered = self._try_recover_from_backup()
            if recovered is not None:
                return recovered, "corrupto_recuperado_backup"
            return dict(self.DEFAULTS), "corrupto_sin_backup"
        except OSError:
            return dict(self.DEFAULTS), "error_lectura"

        try:
            raw_data = self._parse_content(content)
            if not raw_data:
                raise ConfigError("Archivo vacío o sin pares clave=valor válidos")
            data = self._validate(raw_data)
            return data, "ok"
        except Exception:
            recovered = self._try_recover_from_backup()
            if recovered is not None:
                return recovered, "corrupto_recuperado_backup"
            return dict(self.DEFAULTS), "corrupto_sin_backup"

    def _try_recover_from_backup(self):
        if not os.path.exists(self.backup_path):
            return None
        try:
            with open(self.backup_path, "r", encoding="utf-8") as f:
                content = f.read()
            raw_data = self._parse_content(content)
            if not raw_data:
                return None
            return self._validate(raw_data)
        except Exception:
            return None

    def save(self, config_dict):
        data = self._validate(config_dict)
        lines = [
            "# Archivo de configuración de usuario",
            "# Formato: clave=valor  |  Codificación: UTF-8",
            "# Generado automáticamente por la aplicación. Editar con cuidado.",
            "",
        ]
        for key in self.DEFAULTS:
            lines.append(f"{key}={data[key]}")
        content = "\n".join(lines) + "\n"

        try:
            self._ensure_dirs()

            with open(self.tmp_path, "w", encoding="utf-8", newline="\n") as f:
                f.write(content)
                f.flush()
                os.fsync(f.fileno())

            if os.path.exists(self.config_path):
                try:
                    shutil.copy2(self.config_path, self.backup_path)
                except OSError:
                    pass

            os.replace(self.tmp_path, self.config_path)
            return True, "ok"

        except PermissionError:
            self._cleanup_tmp()
            return False, "sin_permiso_escritura"
        except OSError as e:
            self._cleanup_tmp()
            return False, f"error_escritura: {e}"

    def _cleanup_tmp(self):
        try:
            if os.path.exists(self.tmp_path):
                os.remove(self.tmp_path)
        except OSError:
            pass

    def import_profile_picture(self, source_path):
        try:
            if not os.path.isfile(source_path):
                return None
            ext = os.path.splitext(source_path)[1].lower()
            if ext not in (".png", ".jpg", ".jpeg", ".gif", ".bmp"):
                ext = ".png"
            dest_name = f"perfil_{int(time.time())}{ext}"
            dest_path = os.path.join(self.profile_pics_dir, dest_name)
            shutil.copy2(source_path, dest_path)
            return os.path.join("profile_pics", dest_name)
        except OSError:
            return None

    def resolve_profile_picture_path(self, relative_path):
        if not relative_path:
            return None
        full_path = os.path.join(self.base_dir, relative_path)
        return full_path if os.path.exists(full_path) else None