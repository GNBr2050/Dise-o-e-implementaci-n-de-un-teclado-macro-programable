import json
import os

CONFIG_FILE = "profiles.json"

DEFAULT_PROFILE = {
    "default": {
        "KEY_1": {"type": "hotkey", "value": "ctrl+c", "color": "#4CAF50"},
        "KEY_2": {"type": "hotkey", "value": "ctrl+v", "color": "#2196F3"},
        "KEY_3": {"type": "write", "value": "Hola Mundo", "color": "#FF9800"},
        "ENC_A_DER": {"type": "hotkey", "value": "volumeup", "color": "#E91E63"},
        "ENC_A_IZQ": {"type": "hotkey", "value": "volumedown", "color": "#E91E63"},
        # El resto se llenará dinámicamente si falta
    }
}

class ConfigManager:
    def __init__(self):
        self.profiles = self.load_data()
        self.current_profile = "default"

    def load_data(self):
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, 'r') as f:
                    return json.load(f)
            except:
                return DEFAULT_PROFILE
        return DEFAULT_PROFILE

    def save_data(self):
        with open(CONFIG_FILE, 'w') as f:
            json.dump(self.profiles, f, indent=4)

    def get_key_data(self, key_id):
        return self.profiles[self.current_profile].get(key_id, {"type": "hotkey", "value": "", "color": "#333"})

    def update_key(self, key_id, action_type, value, color):
        if self.current_profile not in self.profiles:
            self.profiles[self.current_profile] = {}
        
        self.profiles[self.current_profile][key_id] = {
            "type": action_type,
            "value": value,
            "color": color
        }
        self.save_data()