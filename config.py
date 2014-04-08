import os
import pickle


class Config:
    def __init__(self, config_path):
        self.config = {}
        self.config_file = os.path.join(config_path, 'config.p')
        if os.path.isfile(self.config_file):
            with open(self.config_file, 'r') as f:
                self.config = pickle.load(f)

    def get(self, value):
        return self.config.get(value, None)

    def set(self, key, value):
        self.config[key] = value

    def save(self):
        with open(self.config_file, 'w+') as f:
            pickle.dump(self.config, f)
