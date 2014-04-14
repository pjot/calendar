'''
Module that simplifies storing and reading values from a config file
'''
import os
import pickle


class Config(object):
    '''
    Class that simplifies storing and reading values from a config file
    '''
    def __init__(self, config_path):
        '''
        Create a new Config object using the supplied path.

        :param config_path: Path to config file
        :type config_path: str
        '''
        self.config = {}
        self.config_file = os.path.join(config_path, 'config.p')
        if os.path.isfile(self.config_file):
            with open(self.config_file, 'r') as config_file:
                self.config = pickle.load(config_file)

    def get(self, key):
        '''
        Get a value from the config

        :param key: Name of key
        :type key: str
        '''
        return self.config.get(key, None)

    def set(self, key, value):
        '''
        Set a value in the config

        :param key: Name of Key
        :type key: str

        :param value: Value
        :type value: Anything
        '''
        self.config[key] = value

    def save(self):
        '''
        Save the config to disk
        '''
        with open(self.config_file, 'w+') as config_file:
            pickle.dump(self.config, config_file)
