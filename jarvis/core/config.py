"""
config.py - Configuración centralizada para Jarvis
Un único lugar donde TODOS los parámetros se configuran
"""

import os
from pathlib import Path
from typing import Optional, Dict, Any
import yaml
from dotenv import load_dotenv


class Config:
    """
    Configuración centralizada con validación.
    Carga desde YAML, .env y variables de entorno.
    """
    
    def __init__(self, config_file: str = "config.yaml"):
        """
        Inicializa la configuración.
        
        Args:
            config_file: Ruta al archivo de configuración YAML
        """
        # Cargar variables de entorno
        load_dotenv()
        
        self.config_file = Path(config_file)
        self.config = {}
        
        # Cargar configuración YAML si existe
        if self.config_file.exists():
            with open(self.config_file, 'r', encoding='utf-8') as f:
                self.config = yaml.safe_load(f) or {}
        
        # Inicializar secciones por defecto
        self._init_defaults()
        self._validate()
    
    def _init_defaults(self):
        """Inicializa valores por defecto para todas las secciones"""
        
        # Logging
        if 'logging' not in self.config:
            self.config['logging'] = {}
        self.logging = self.config['logging']
        self.logging.setdefault('level', 'INFO')
        self.logging.setdefault('file_path', 'logs/jarvis.log')
        self.logging.setdefault('console_output', True)
        self.logging.setdefault('max_file_size', 10 * 1024 * 1024)  # 10 MB
        self.logging.setdefault('backup_count', 5)
        
        # Jarvis
        if 'jarvis' not in self.config:
            self.config['jarvis'] = {}
        self.jarvis = self.config['jarvis']
        self.jarvis.setdefault('name', os.getenv('JARVIS_NAME', 'Jarvis'))
        self.jarvis.setdefault('language', 'es')
        self.jarvis.setdefault('voice_gender', 'male')  # male, female
        self.jarvis.setdefault('voice_speed', 150)
        self.jarvis.setdefault('voice_volume', 1.0)
        
        # APIs
        if 'apis' not in self.config:
            self.config['apis'] = {}
        self.apis = self.config['apis']
        self.apis.setdefault('gemini_api_key', os.getenv('GEMINI_API_KEY', ''))
        self.apis.setdefault('timeout', 30)
        self.apis.setdefault('retry_attempts', 3)
        self.apis.setdefault('retry_delay', 1)  # segundos
        
        # Memory
        if 'memory' not in self.config:
            self.config['memory'] = {}
        self.memory = self.config['memory']
        self.memory.setdefault('db_path', 'data/jarvis_memory.db')
        self.memory.setdefault('max_short_term', 100)  # conversaciones recientes
        self.memory.setdefault('retention_days', 30)
        
        # Agentes
        if 'agents' not in self.config:
            self.config['agents'] = {}
        self.agents = self.config['agents']
        self.agents.setdefault('enabled', ['voice', 'dialog', 'system', 'web'])
        self.agents.setdefault('timeout', 30)
        self.agents.setdefault('max_retries', 3)
        
        # Sistema
        if 'system' not in self.config:
            self.config['system'] = {}
        self.system = self.config['system']
        self.system.setdefault('debug', os.getenv('DEBUG', 'False').lower() == 'true')
        self.system.setdefault('data_dir', 'data')
        self.system.setdefault('plugins_dir', 'plugins')
    
    def _validate(self):
        """Valida la configuración al cargar"""
        # Validar que las claves requeridas existan
        required_keys = ['logging', 'jarvis', 'apis', 'memory', 'agents']
        for key in required_keys:
            if key not in self.config:
                raise ValueError(f"Configuración faltante: {key}")
        
        # Validar API key si es necesaria
        if not self.apis.get('gemini_api_key'):
            print("⚠️  ADVERTENCIA: GEMINI_API_KEY no configurada. Algunas funciones no funcionarán.")
        
        # Crear directorios necesarios
        Path(self.logging['file_path']).parent.mkdir(parents=True, exist_ok=True)
        Path(self.memory['db_path']).parent.mkdir(parents=True, exist_ok=True)
        Path(self.system['data_dir']).mkdir(parents=True, exist_ok=True)
        Path(self.system['plugins_dir']).mkdir(parents=True, exist_ok=True)
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        Obtiene un valor de configuración con notación de punto.
        
        Ejemplo:
            config.get('apis.gemini_api_key')
            config.get('jarvis.name')
        """
        keys = key.split('.')
        value = self.config
        
        for k in keys:
            if isinstance(value, dict):
                value = value.get(k)
                if value is None:
                    return default
            else:
                return default
        
        return value
    
    def set(self, key: str, value: Any):
        """
        Establece un valor de configuración con notación de punto.
        
        Ejemplo:
            config.set('jarvis.name', 'JARVIS')
        """
        keys = key.split('.')
        config = self.config
        
        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]
        
        config[keys[-1]] = value
    
    def to_dict(self) -> Dict[str, Any]:
        """Retorna la configuración como diccionario"""
        return self.config.copy()
    
    def save_to_yaml(self, filepath: str):
        """Guarda la configuración a un archivo YAML"""
        with open(filepath, 'w', encoding='utf-8') as f:
            yaml.dump(self.config, f, allow_unicode=True, default_flow_style=False)


# Instancia global de configuración
_global_config: Optional[Config] = None


def get_config(config_file: str = "config.yaml") -> Config:
    """
    Obtiene la instancia global de configuración.
    La primera llamada inicializa, las siguientes retornan la instancia.
    
    Ejemplo:
        config = get_config()
        api_key = config.apis['gemini_api_key']
    """
    global _global_config
    if _global_config is None:
        _global_config = Config(config_file)
    return _global_config


def reset_config():
    """Reinicia la configuración global (útil para pruebas)"""
    global _global_config
    _global_config = None
