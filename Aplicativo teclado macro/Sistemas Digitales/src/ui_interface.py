import tkinter as tk
from tkinter import ttk, colorchooser, filedialog, messagebox

# Colores y Estilos
BG_COLOR = "#121212"
PANEL_COLOR = "#1e1e1e"
ACCENT_COLOR = "#0078d7"
TEXT_COLOR = "#ffffff"
SCREEN_BG = "#000000"
SCREEN_TEXT = "#00FF00"

# Presets de atajos
PRESETS = {
    "--- Seleccionar Común ---": "",
    "Copiar": "ctrl+c",
    "Pegar": "ctrl+v",
    "Cortar": "ctrl+x",
    "Guardar": "ctrl+s",
    "Deshacer": "ctrl+z",
    "Seleccionar Todo": "ctrl+a",
    "Cerrar Ventana": "alt+f4",
    "Admin Tareas": "ctrl+shift+esc",
    "Subir Volumen": "volumeup",
    "Bajar Volumen": "volumedown",
    "Silenciar (Mute)": "volumemute",
    "Play/Pause": "playpause",
    "Siguiente Canción": "nexttrack",
    "Anterior Canción": "prevtrack",
    "Tecla Windows": "win",
    "Enter": "enter",
    "Captura Pantalla": "win+shift+s"
}

class MacroPadUI:
    def __init__(self, root):
        self.root = root
        self.root.title("MacroPad Control Center")
        self.root.geometry("1000x700") # Un poco más alto para el checkbox
        self.root.configure(bg=BG_COLOR)

        # Importación diferida para evitar ciclos circulares si fuera necesario, 
        # pero aquí asumimos que main inyecta las dependencias o se instancian correctamente.
        from config_manager import ConfigManager
        from serial_worker import SerialWorker

        self.config = ConfigManager()
        self.worker = SerialWorker(self.config)
        self.worker.set_callback(self.update_virtual_screen)
        self.selected_key = None

        self._setup_styles()
        self._build_layout()

    def _setup_styles(self):
        style = ttk.Style()
        style.theme_use('clam')
        style.configure("TFrame", background=BG_COLOR)
        style.configure("TLabel", background=PANEL_COLOR, foreground=TEXT_COLOR)
        style.configure("TCombobox", fieldbackground="#333", background="#333", foreground="white")

    def _build_layout(self):
        # 1. BARRA SUPERIOR
        top_bar = tk.Frame(self.root, bg=PANEL_COLOR, height=60, pady=10)
        top_bar.pack(fill="x", side="top")
        
        tk.Label(top_bar, text="🔌 Puerto:", bg=PANEL_COLOR, fg="#aaa").pack(side="left", padx=(20, 5))
        self.entry_port = tk.Entry(top_bar, width=8, bg="#333", fg="white", insertbackground="white")
        self.entry_port.insert(0, "COM3")
        self.entry_port.pack(side="left", padx=5)
        
        self.btn_connect = tk.Button(top_bar, text="CONECTAR", bg="#4CAF50", fg="white", font=("Segoe UI", 9, "bold"), 
                                     command=self._toggle_connection, relief="flat", padx=15, pady=2)
        self.btn_connect.pack(side="left", padx=15)

        tk.Label(top_bar, text="MacroPad Pro", bg=PANEL_COLOR, fg="#555", font=("Segoe UI", 12, "bold")).pack(side="right", padx=20)

        # 2. CONTENEDOR PRINCIPAL
        main_container = tk.Frame(self.root, bg=BG_COLOR)
        main_container.pack(fill="both", expand=True, padx=20, pady=20)

        # --- IZQUIERDA: DISPOSITIVO VISUAL ---
        left_panel = tk.LabelFrame(main_container, text=" Vista Previa ", bg=BG_COLOR, fg="#888", font=("Segoe UI", 10))
        left_panel.pack(side="left", fill="both", expand=True, padx=(0, 10))

        # A. PANTALLA OLED VIRTUAL
        oled_frame = tk.Frame(left_panel, bg=BG_COLOR)
        oled_frame.pack(pady=15)
        self.canvas_oled = tk.Canvas(oled_frame, width=160, height=80, bg=SCREEN_BG, highlightthickness=2, highlightbackground="#444")
        self.canvas_oled.pack()
        self.oled_text_header = self.canvas_oled.create_text(80, 20, text="ESPERANDO...", fill=SCREEN_TEXT, font=("Consolas", 10))
        self.oled_text_value = self.canvas_oled.create_text(80, 50, text="--", fill="white", font=("Consolas", 16, "bold"))

        # B. MATRIZ DE BOTONES (NUEVA DISTRIBUCIÓN 4x3)
        grid_frame = tk.Frame(left_panel, bg=BG_COLOR)
        grid_frame.pack(pady=10)

        self.btn_map = {}
        
        # --- AQUÍ ESTÁ EL CAMBIO SOLICITADO ---
        # 4 Columnas, 3 Filas
        layout = [
            ["KEY_1", "KEY_2", "KEY_3", "KEY_4"], # Fila 1
            ["KEY_5", "KEY_6", "KEY_7", "KEY_8"], # Fila 2
            ["KEY_*", "KEY_9", "KEY_0", "KEY_#"]  # Fila 3
        ]
        
        for r, row in enumerate(layout):
            for c, key_id in enumerate(row):
                lbl = key_id.replace("KEY_", "")
                btn = tk.Button(grid_frame, text=lbl, width=6, height=2, 
                                font=("Segoe UI", 12, "bold"), bg="#333", fg="white",
                                relief="flat", cursor="hand2",
                                command=lambda k=key_id: self._select_key(k))
                btn.grid(row=r, column=c, padx=5, pady=5)
                self.btn_map[key_id] = btn

        # C. ENCODERS
        enc_frame = tk.Frame(left_panel, bg=BG_COLOR)
        enc_frame.pack(pady=15)
        self._create_enc_group(enc_frame, "Izquierdo (A)", ["ENC_A_IZQ", "ENC_A_DER", "BTN_A_PRESS"], 0)
        tk.Frame(enc_frame, width=30, bg=BG_COLOR).grid(row=0, column=1)
        self._create_enc_group(enc_frame, "Derecho (B)", ["ENC_B_IZQ", "ENC_B_DER", "BTN_B_PRESS"], 2)

        # D. CHECKBOX BLOQUEO ENCODERS
        self.var_lock_enc = tk.BooleanVar(value=False)
        chk_lock = tk.Checkbutton(left_panel, text="🔒 BLOQUEAR ENCODERS", 
                                  variable=self.var_lock_enc,
                                  command=self._toggle_lock_encoders,
                                  bg=BG_COLOR, fg="#FF5555", selectcolor="#333",
                                  activebackground=BG_COLOR, activeforeground="#FF5555",
                                  font=("Segoe UI", 10, "bold"))
        chk_lock.pack(pady=(5, 15))

        # --- DERECHA: EDITOR ---
        right_panel = tk.Frame(main_container, bg=PANEL_COLOR, width=320)
        right_panel.pack(side="right", fill="y")
        right_panel.pack_propagate(False)

        tk.Label(right_panel, text="EDITAR ACCIÓN", bg=PANEL_COLOR, fg="white", font=("Segoe UI", 14, "bold")).pack(pady=(25, 5))
        self.lbl_selected = tk.Label(right_panel, text="Selecciona tecla...", bg=PANEL_COLOR, fg="#00a8ff", font=("Segoe UI", 11))
        self.lbl_selected.pack(pady=(0, 20))

        # Campos de Edición
        self._create_label(right_panel, "Tipo de Acción")
        self.combo_type = ttk.Combobox(right_panel, values=["hotkey", "write", "open"], state="readonly")
        self.combo_type.pack(fill="x", padx=25, pady=5)
        self.combo_type.set("hotkey")
        self.combo_type.bind("<<ComboboxSelected>>", self._on_type_change)

        self._create_label(right_panel, "Atajos Rápidos (Presets)")
        self.combo_presets = ttk.Combobox(right_panel, values=list(PRESETS.keys()), state="readonly")
        self.combo_presets.pack(fill="x", padx=25, pady=5)
        self.combo_presets.bind("<<ComboboxSelected>>", self._apply_preset)

        self._create_label(right_panel, "Comando / Valor")
        self.entry_value = tk.Entry(right_panel, bg="#333", fg="white", relief="flat", font=("Consolas", 10))
        self.entry_value.pack(fill="x", padx=25, pady=5, ipady=4)
        
        self.btn_browse = tk.Button(right_panel, text="📂 Buscar Archivo...", command=self._browse_file, bg="#444", fg="white", relief="flat")

        self._create_label(right_panel, "Color Visual")
        self.btn_color = tk.Button(right_panel, text="", bg="#333", command=self._pick_color, relief="flat", height=2)
        self.btn_color.pack(fill="x", padx=25, pady=5)

        tk.Button(right_panel, text="💾 GUARDAR CAMBIOS", bg=ACCENT_COLOR, fg="white", font=("Segoe UI", 11, "bold"), 
                  command=self._save_key, height=2, relief="flat").pack(side="bottom", fill="x", padx=25, pady=30)
        
        self._refresh_grid_colors()

    def _create_label(self, parent, text):
        tk.Label(parent, text=text, bg=PANEL_COLOR, fg="#aaa", anchor="w").pack(fill="x", padx=25, pady=(15, 0))

    def _create_enc_group(self, parent, title, keys, col):
        frame = tk.Frame(parent, bg=BG_COLOR)
        frame.grid(row=0, column=col)
        tk.Label(frame, text=title, bg=BG_COLOR, fg="#888", font=("Segoe UI", 9)).pack(pady=5)
        sub_frame = tk.Frame(frame, bg=BG_COLOR)
        sub_frame.pack()
        
        # Botones pequeños para simular encoder
        for i, (sym, k) in enumerate([("⏪", keys[0]), ("🔴", keys[2]), ("⏩", keys[1])]):
            btn = tk.Button(sub_frame, text=sym, width=4, bg="#333", fg="white", command=lambda x=k: self._select_key(x))
            btn.pack(side="left", padx=2)
            self.btn_map[k] = btn

    def _toggle_connection(self):
        if not self.worker.running:
            port = self.entry_port.get()
            if self.worker.connect(port):
                self.btn_connect.config(text="DESCONECTAR", bg="#e81123")
                self.canvas_oled.itemconfig(self.oled_text_header, text="CONECTADO", fill="#00FF00")
            else:
                messagebox.showerror("Error", "No se pudo conectar al Arduino")
        else:
            self.worker.disconnect()
            self.btn_connect.config(text="CONECTAR", bg="#4CAF50")
            self.canvas_oled.itemconfig(self.oled_text_header, text="DESCONECTADO", fill="#FF0000")

    def _toggle_lock_encoders(self):
        is_locked = self.var_lock_enc.get()
        self.worker.set_encoders_lock(is_locked)
        state_text = "ENC. LOCK" if is_locked else "ENC. OPEN"
        color = "#FF5555" if is_locked else "#00FF00"
        self.canvas_oled.itemconfig(self.oled_text_value, text=state_text, fill=color)

    def update_virtual_screen(self, key_id):
        friendly = key_id.replace("KEY_", "TECLA ").replace("ENC_", "").replace("_", " ")
        self.canvas_oled.itemconfig(self.oled_text_value, text=friendly)
        if key_id in self.btn_map:
            orig = self.btn_map[key_id].cget("bg")
            self.btn_map[key_id].config(bg="#FFFFFF")
            self.root.after(150, lambda: self.btn_map[key_id].config(bg=orig))

    def _select_key(self, key_id):
        self.selected_key = key_id
        self.lbl_selected.config(text=key_id, fg="#ffffff")
        data = self.config.get_key_data(key_id)
        self.combo_type.set(data["type"])
        self._on_type_change(None)
        self.entry_value.delete(0, tk.END)
        self.entry_value.insert(0, data["value"])
        self.btn_color.config(bg=data["color"])

    def _on_type_change(self, event):
        if self.combo_type.get() == "open":
            self.btn_browse.pack(fill="x", padx=25, pady=5, after=self.entry_value)
            self.combo_presets.config(state="disabled")
        else:
            self.btn_browse.pack_forget()
            self.combo_presets.config(state="readonly")

    def _apply_preset(self, event):
        val = PRESETS.get(self.combo_presets.get(), "")
        if val:
            self.entry_value.delete(0, tk.END)
            self.entry_value.insert(0, val)
            self.combo_type.set("hotkey")

    def _browse_file(self):
        f = filedialog.askopenfilename()
        if f:
            self.entry_value.delete(0, tk.END)
            self.entry_value.insert(0, f)

    def _pick_color(self):
        c = colorchooser.askcolor()[1]
        if c: self.btn_color.config(bg=c)

    def _save_key(self):
        if self.selected_key:
            self.config.update_key(self.selected_key, self.combo_type.get(), self.entry_value.get(), self.btn_color.cget("bg"))
            self._refresh_grid_colors()

    def _refresh_grid_colors(self):
        for k, btn in self.btn_map.items():
            btn.config(bg=self.config.get_key_data(k)["color"])