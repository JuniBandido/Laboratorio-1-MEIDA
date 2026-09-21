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

class SettingsWindow(tk.Toplevel):
    def __init__(self, master, config_manager: ConfigManager, current_config: dict, on_saved):
        super().__init__(master)
        self.title("Settings")
        self.resizable(False, False)
        self.config_manager = config_manager
        self.on_saved = on_saved
        self.working_config = dict(current_config)

        self.transient(master)
        self.grab_set()

        self._nueva_foto_origen = None
        self._foto_relativa_actual = ""

        self._build_form()
        self._load_values()

    def _build_form(self):
        pad = {"padx": 8, "pady": 4}
        frame = ttk.Frame(self)
        frame.pack(fill="both", expand=True, padx=12, pady=12)

        row = 0
        ttk.Label(frame, text="Nombre de usuario:").grid(row=row, column=0, sticky="w", **pad)
        self.var_nombre = tk.StringVar()
        ttk.Entry(frame, textvariable=self.var_nombre, width=32).grid(row=row, column=1, sticky="w", **pad)
        row += 1

        ttk.Label(frame, text="Tema de interfaz:").grid(row=row, column=0, sticky="w", **pad)
        self.var_tema = tk.StringVar()
        ttk.Combobox(
            frame, textvariable=self.var_tema, values=["claro", "oscuro"],
            state="readonly", width=29
        ).grid(row=row, column=1, sticky="w", **pad)
        row += 1

        ttk.Label(frame, text="Idioma:").grid(row=row, column=0, sticky="w", **pad)
        self.var_idioma_display = tk.StringVar()
        ttk.Combobox(
            frame, textvariable=self.var_idioma_display,
            values=[d for _, d in IDIOMAS], state="readonly", width=29
        ).grid(row=row, column=1, sticky="w", **pad)
        row += 1

        ttk.Label(frame, text="Tamaño de fuente:").grid(row=row, column=0, sticky="w", **pad)
        self.var_tamano = tk.IntVar()
        tk.Spinbox(frame, from_=8, to=72, textvariable=self.var_tamano, width=10).grid(
            row=row, column=1, sticky="w", **pad
        )
        row += 1

        ttk.Label(frame, text="Color barra de menú:").grid(row=row, column=0, sticky="w", **pad)
        color_frame1 = ttk.Frame(frame)
        color_frame1.grid(row=row, column=1, sticky="w", **pad)
        self.swatch_menu = tk.Label(color_frame1, text="        ", relief="sunken", borderwidth=1)
        self.swatch_menu.pack(side="left")
        ttk.Button(color_frame1, text="Elegir color...", command=self._choose_menu_color).pack(side="left", padx=6)
        self.color_barra_menu = self.config_manager.DEFAULTS["color_barra_menu"]
        row += 1

        ttk.Label(frame, text="Color de letra:").grid(row=row, column=0, sticky="w", **pad)
        color_frame2 = ttk.Frame(frame)
        color_frame2.grid(row=row, column=1, sticky="w", **pad)
        self.swatch_font = tk.Label(color_frame2, text="        ", relief="sunken", borderwidth=1)
        self.swatch_font.pack(side="left")
        ttk.Button(color_frame2, text="Elegir color...", command=self._choose_font_color).pack(side="left", padx=6)
        self.color_letra = self.config_manager.DEFAULTS["color_letra"]
        row += 1

        ttk.Label(frame, text="Foto de perfil:").grid(row=row, column=0, sticky="w", **pad)
        pic_frame = ttk.Frame(frame)
        pic_frame.grid(row=row, column=1, sticky="w", **pad)
        self.lbl_foto = ttk.Label(pic_frame, text="(ninguna)")
        self.lbl_foto.pack(side="left")
        ttk.Button(pic_frame, text="Elegir archivo...", command=self._choose_picture).pack(side="left", padx=6)
        row += 1

        info = ttk.Label(
            frame,
            text="Los cambios se guardan de forma segura (archivo temporal + respaldo).",
            foreground="#555555", font=("Segoe UI", 8),
        )
        info.grid(row=row, column=0, columnspan=2, sticky="w", padx=8, pady=(4, 0))
        row += 1

        btn_frame = ttk.Frame(frame)
        btn_frame.grid(row=row, column=0, columnspan=2, pady=(14, 0))
        ttk.Button(btn_frame, text="Guardar", command=self._on_save).pack(side="left", padx=6)
        ttk.Button(btn_frame, text="Cancelar", command=self.destroy).pack(side="left", padx=6)

    def _load_values(self):
        c = self.working_config
        self.var_nombre.set(c.get("nombre_usuario", ""))
        self.var_tema.set(c.get("tema_interfaz", "claro"))

        idioma_code = c.get("idioma", "es/es-ES")
        display = next((d for code, d in IDIOMAS if code == idioma_code), IDIOMAS[0][1])
        self.var_idioma_display.set(display)

        try:
            self.var_tamano.set(int(c.get("tamaño_fuente", 12)))
        except (ValueError, TypeError):
            self.var_tamano.set(12)

        self.color_barra_menu = c.get("color_barra_menu", "#2c3e50")
        self.color_letra = c.get("color_letra", "#000000")
        self.swatch_menu.configure(bg=self.color_barra_menu)
        self.swatch_font.configure(bg=self.color_letra)

        self._foto_relativa_actual = c.get("foto_perfil", "")
        if self._foto_relativa_actual:
            full = self.config_manager.resolve_profile_picture_path(self._foto_relativa_actual)
            texto = os.path.basename(self._foto_relativa_actual) if full else "(archivo no encontrado)"
            self.lbl_foto.configure(text=texto)
        else:
            self.lbl_foto.configure(text="(ninguna)")

    def _choose_menu_color(self):
        _, hexcode = colorchooser.askcolor(
            color=self.color_barra_menu, title="Color de la barra de menú", parent=self
        )
        if hexcode:
            self.color_barra_menu = hexcode
            self.swatch_menu.configure(bg=hexcode)

    def _choose_font_color(self):
        _, hexcode = colorchooser.askcolor(
            color=self.color_letra, title="Color de letra", parent=self
        )
        if hexcode:
            self.color_letra = hexcode
            self.swatch_font.configure(bg=hexcode)

    def _choose_picture(self):
        path = filedialog.askopenfilename(
            title="Seleccionar foto de perfil",
            filetypes=[("Imágenes", "*.png *.jpg *.jpeg *.gif *.bmp"), ("Todos los archivos", "*.*")],
            parent=self,
        )
        if path:
            self._nueva_foto_origen = path
            self.lbl_foto.configure(text=os.path.basename(path))

    def _on_save(self):
        nombre = self.var_nombre.get().strip()
        if not nombre:
            messagebox.showerror("Datos inválidos", "El nombre de usuario no puede estar vacío.", parent=self)
            return

        try:
            tamano = int(self.var_tamano.get())
            if tamano <= 0:
                raise ValueError
        except (ValueError, tk.TclError):
            messagebox.showerror(
                "Datos inválidos", "El tamaño de fuente debe ser un número entero positivo.", parent=self
            )
            return

        idioma_display = self.var_idioma_display.get()
        idioma_code = next((code for code, d in IDIOMAS if d == idioma_display), "es/es-ES")

        foto_relativa = self._foto_relativa_actual
        if self._nueva_foto_origen:
            nueva_relativa = self.config_manager.import_profile_picture(self._nueva_foto_origen)
            if nueva_relativa is None:
                messagebox.showwarning(
                    "Foto de perfil",
                    "No se pudo copiar la imagen seleccionada (revise permisos o espacio en disco). "
                    "Se conservará la foto anterior.",
                    parent=self,
                )
            else:
                foto_relativa = nueva_relativa

        nueva_config = {
            "nombre_usuario": nombre,
            "tema_interfaz": self.var_tema.get(),
            "idioma": idioma_code,
            "tamaño_fuente": str(tamano),
            "color_barra_menu": self.color_barra_menu,
            "color_letra": self.color_letra,
            "foto_perfil": foto_relativa,
        }

        ok, status = self.config_manager.save(nueva_config)
        if ok:
            messagebox.showinfo("Settings", "Configuración guardada correctamente.", parent=self)
            self.on_saved(nueva_config)
            self.destroy()
        elif status == "sin_permiso_escritura":
            messagebox.showerror(
                "Error al guardar",
                "No se tienen permisos para escribir el archivo de configuración.\n"
                "Los cambios NO se guardaron; el archivo anterior permanece intacto.",
                parent=self,
            )
        else:
            messagebox.showerror(
                "Error al guardar",
                f"No se pudo guardar la configuración.\nDetalle: {status}\n"
                "El archivo anterior permanece intacto.",
                parent=self,
            )

class MainApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Mi Aplicación - Configuración de Usuario")
        self.geometry("580x420")

        self.config_manager = ConfigManager()
        self.current_config, status = self._safe_initial_load()

        self._build_menu()
        self._build_body()
        self._apply_theme()

        if status != "ok":
            self.after(200, lambda: messagebox.showwarning(
                "Configuración", STATUS_MESSAGES.get(status, status)
            ))

    def _safe_initial_load(self):
        try:
            return self.config_manager.load()
        except Exception:
            traceback.print_exc()
            return dict(self.config_manager.DEFAULTS), "error_lectura"

    def _build_menu(self):
        menubar = tk.Menu(self)

        m_archivo = tk.Menu(menubar, tearoff=0)
        for label in ("Nuevo", "Abrir...", "Guardar", "Guardar como..."):
            m_archivo.add_command(label=label, command=lambda l=label: self._simulado(l))
        m_archivo.add_separator()
        m_archivo.add_command(label="Salir", command=self.destroy)
        menubar.add_cascade(label="Archivo", menu=m_archivo)

        m_edicion = tk.Menu(menubar, tearoff=0)
        for label in ("Deshacer", "Rehacer", "Cortar", "Copiar", "Pegar"):
            m_edicion.add_command(label=label, command=lambda l=label: self._simulado(l))
        menubar.add_cascade(label="Edición", menu=m_edicion)

        m_ver = tk.Menu(menubar, tearoff=0)
        for label in ("Zoom +", "Zoom -", "Pantalla completa"):
            m_ver.add_command(label=label, command=lambda l=label: self._simulado(l))
        menubar.add_cascade(label="Ver", menu=m_ver)

        m_settings = tk.Menu(menubar, tearoff=0)
        m_settings.add_command(label="Abrir Settings...", command=self.open_settings)
        menubar.add_cascade(label="Settings", menu=m_settings)

        self.config(menu=menubar)
        self.menubar = menubar

    def _simulado(self, label):
        messagebox.showinfo(label, f"'{label}' es una opción simulada (sin funcionalidad real).")

    def _build_body(self):
        self.body = tk.Frame(self)
        self.body.pack(fill="both", expand=True)

        self.lbl_titulo = tk.Label(self.body, text="Vista previa de configuración", font=("Segoe UI", 14, "bold"))
        self.lbl_titulo.pack(pady=(16, 8))

        self.lbl_usuario = tk.Label(self.body, text="")
        self.lbl_usuario.pack(pady=2)

        self.lbl_tema = tk.Label(self.body, text="")
        self.lbl_tema.pack(pady=2)

        self.lbl_idioma = tk.Label(self.body, text="")
        self.lbl_idioma.pack(pady=2)

        self.foto_canvas = tk.Label(self.body)
        self.foto_canvas.pack(pady=8)

        hint = tk.Label(
            self.body,
            text='Use el menú "Settings" para editar y guardar la configuración.',
            font=("Segoe UI", 9, "italic"),
        )
        hint.pack(pady=(10, 0))
        self.hint_label = hint

        self.status_bar = tk.Label(self, text="", anchor="w", relief="sunken")
        self.status_bar.pack(fill="x", side="bottom")

        self._refresh_body()

    def open_settings(self):
        SettingsWindow(self, self.config_manager, self.current_config, self._on_settings_saved)

    def _on_settings_saved(self, nueva_config):
        self.current_config = nueva_config
        self._apply_theme()
        self._refresh_body()

    def _refresh_body(self):
        c = self.current_config
        self.lbl_usuario.configure(text=f"Usuario: {c.get('nombre_usuario', '')}")
        self.lbl_tema.configure(text=f"Tema: {c.get('tema_interfaz', '')}")
        idioma_display = next((d for code, d in IDIOMAS if code == c.get("idioma")), c.get("idioma", ""))
        self.lbl_idioma.configure(text=f"Idioma: {idioma_display}")
        self.status_bar.configure(text=f"Archivo de configuración: {self.config_manager.config_path}")
        self._load_profile_picture()

    def _load_profile_picture(self):
        rel = self.current_config.get("foto_perfil", "")
        full_path = self.config_manager.resolve_profile_picture_path(rel) if rel else None

        if full_path and PIL_AVAILABLE:
            try:
                img = Image.open(full_path)
                img.thumbnail((96, 96))
                self._photo_ref = ImageTk.PhotoImage(img)
                self.foto_canvas.configure(image=self._photo_ref, text="")
                return
            except Exception:
                pass  # si falla la carga de la imagen, caemos al texto de abajo

        if full_path:
            self.foto_canvas.configure(image="", text=f"Foto: {os.path.basename(full_path)}")
        else:
            self.foto_canvas.configure(image="", text="(sin foto de perfil)")

    def _apply_theme(self):
        c = self.current_config
        tema = c.get("tema_interfaz", "claro")
        color_letra = c.get("color_letra", "#000000")
        color_menu = c.get("color_barra_menu", "#2c3e50")
        try:
            tamano = int(c.get("tamaño_fuente", 12))
        except (ValueError, TypeError):
            tamano = 12

        bg = "#f4f4f4" if tema == "claro" else "#1e1e1e"

        self.body.configure(bg=bg)
        widgets = (self.lbl_titulo, self.lbl_usuario, self.lbl_tema, self.lbl_idioma,
                   self.foto_canvas, self.hint_label)
        for w in widgets:
            w.configure(bg=bg, fg=color_letra)

        self.lbl_titulo.configure(font=("Segoe UI", tamano + 2, "bold"))
        for w in (self.lbl_usuario, self.lbl_tema, self.lbl_idioma):
            w.configure(font=("Segoe UI", tamano))

        try:
            self.menubar.configure(bg=color_menu, fg="#ffffff", activebackground=color_menu)
        except tk.TclError:
            pass

def main():
    try:
        app = MainApp()
        app.mainloop()
    except Exception:
        traceback.print_exc()
        try:
            root = tk.Tk()
            root.withdraw()
            messagebox.showerror(
                "Error fatal",
                "Ocurrió un error inesperado y la aplicación debe cerrarse.\n"
                "Revise la consola para más detalles.",
            )
        except Exception:
            pass
        sys.exit(1)

if __name__ == "__main__":
    main()