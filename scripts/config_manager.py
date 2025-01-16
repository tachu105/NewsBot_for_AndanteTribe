import os
import yaml

class ConfigManager:
    # ---------------------
    # コンストラクタ
    # ---------------------
    def __init__(self, config_file_path):
        self.config_file_path = config_file_path

    # ---------------------
    # config.yaml を読み込んで Python の辞書として返す
    # ---------------------
    def load_config(self):
        if not os.path.exists(self.config_file_path):
            raise FileNotFoundError(f"Config file not found: {self.config_file_path}")
        with open(self.config_file_path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)
