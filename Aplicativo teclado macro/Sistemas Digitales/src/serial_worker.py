import serial
import threading
import time
import keyboard
import os
import pyautogui
import psutil
from datetime import datetime

class SerialWorker:
    def __init__(self, config_manager):
        self.serial_port = None
        self.running = False
        self.config = config_manager
        self.callback = None
        
        # Bandera de Bloqueo de Encoders
        self.encoders_locked = False
        
        # Hilos
        self.read_thread = None
        self.write_thread = None

    def set_callback(self, func):
        self.callback = func

    # Nuevo método para bloquear encoders
    def set_encoders_lock(self, locked):
        self.encoders_locked = locked
        print(f"Estado de bloqueo de encoders: {locked}")

    def connect(self, port, baudrate=9600):
        try:
            self.serial_port = serial.Serial(port, baudrate, timeout=1)
            self.running = True
            
            self.read_thread = threading.Thread(target=self._read_loop, daemon=True)
            self.read_thread.start()
            
            self.write_thread = threading.Thread(target=self._write_loop, daemon=True)
            self.write_thread.start()
            
            print(f"Conectado a {port}")
            return True
        except Exception as e:
            print(f"Error de conexión: {e}")
            return False

    def disconnect(self):
        self.running = False
        if self.serial_port:
            try:
                self.serial_port.close()
            except:
                pass

    def _read_loop(self):
        """Escucha al Arduino"""
        while self.running and self.serial_port and self.serial_port.is_open:
            try:
                if self.serial_port.in_waiting > 0:
                    line = self.serial_port.readline().decode('utf-8', errors='ignore').strip()
                    if line:
                        print(f"Arduino dice: {line}")
                        self._execute_action(line)
                        if self.callback:
                            self.callback(line)
            except Exception as e:
                print(f"Error lectura: {e}")
            time.sleep(0.01)

    def _write_loop(self):
        """Envía Hora y RAM al Arduino"""
        while self.running:
            if self.serial_port and self.serial_port.is_open:
                try:
                    now = datetime.now().strftime("%H:%M")
                    ram = psutil.virtual_memory().percent
                    # Mensaje formato: "20:30|RAM: 45%"
                    mensaje = f"{now}|RAM: {ram}%\n"
                    self.serial_port.write(mensaje.encode('utf-8'))
                except Exception as e:
                    print(f"Error enviando datos: {e}")
            time.sleep(2)

    def _execute_action(self, key_id):
        # 1. Verificar bloqueo de Encoders
        if self.encoders_locked:
            if "ENC_" in key_id:
                print(f"Ignorando {key_id} (Bloqueo activo)")
                return

        # 2. Ejecutar Acción
        key_data = self.config.get_key_data(key_id)
        action_type = key_data["type"]
        value = key_data["value"]

        if not value: return

        try:
            if action_type == "hotkey":
                if value in ["volumeup", "volumedown", "volumemute", "playpause", "nexttrack", "prevtrack"]:
                    pyautogui.press(value)
                else:
                    keyboard.send(value)
            elif action_type == "write":
                keyboard.write(value)
            elif action_type == "open":
                if os.path.exists(value):
                    os.startfile(value)
        except Exception as e:
            print(f"Error acción: {e}")