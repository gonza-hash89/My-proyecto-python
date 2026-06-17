"""
utils.py - Utilidades comunes para todos los componentes
Decorados, validadores, helpers que se reutilizan
"""

import asyncio
import functools
from typing import Any, Callable, TypeVar, Optional, List
from datetime import datetime, timedelta
import time


F = TypeVar('F', bound=Callable[..., Any])


# ============================================================================
# DECORADORES
# ============================================================================

def retry(max_attempts: int = 3, delay: float = 1, backoff: float = 2):
    """
    Decorador para reintentar una función automáticamente.
    
    Args:
        max_attempts: Máximo número de intentos
        delay: Tiempo de espera inicial (segundos)
        backoff: Multiplicador de delay entre intentos
    
    Ejemplo:
        @retry(max_attempts=3, delay=1)
        async def call_api():
            # código que puede fallar
            pass
    """
    def decorator(func: F) -> F:
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            current_delay = delay
            
            for attempt in range(max_attempts):
                try:
                    return await func(*args, **kwargs)
                except Exception as e:
                    if attempt == max_attempts - 1:
                        raise
                    
                    print(f"Intento {attempt + 1}/{max_attempts} falló. Reintentando en {current_delay}s...")
                    await asyncio.sleep(current_delay)
                    current_delay *= backoff
        
        return wrapper
    return decorator


def timeout(seconds: float):
    """
    Decorador para establecer timeout a una función.
    
    Args:
        seconds: Tiempo máximo en segundos
    
    Ejemplo:
        @timeout(30)
        async def long_operation():
            pass
    """
    def decorator(func: F) -> F:
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            try:
                return await asyncio.wait_for(
                    func(*args, **kwargs),
                    timeout=seconds
                )
            except asyncio.TimeoutError:
                raise TimeoutError(f"{func.__name__} excedió el timeout de {seconds}s")
        
        return wrapper
    return decorator


def log_execution(logger_func: Callable):
    """
    Decorador que loguea la ejecución de una función.
    
    Args:
        logger_func: Función de logger a usar
    
    Ejemplo:
        @log_execution(logger.info)
        async def my_function():
            pass
    """
    def decorator(func: F) -> F:
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            func_name = func.__name__
            logger_func(f"Iniciando {func_name}...")
            
            start_time = time.time()
            try:
                result = await func(*args, **kwargs)
                elapsed = time.time() - start_time
                logger_func(f"✅ {func_name} completado en {elapsed:.2f}s")
                return result
            except Exception as e:
                elapsed = time.time() - start_time
                logger_func(f"❌ {func_name} falló después de {elapsed:.2f}s: {str(e)}")
                raise
        
        return wrapper
    return decorator


# ============================================================================
# VALIDADORES
# ============================================================================

def validate_not_empty(value: Any, field_name: str = "field") -> bool:
    """
    Valida que un valor no esté vacío.
    
    Args:
        value: Valor a validar
        field_name: Nombre del campo (para mensajes)
    
    Returns:
        True si es válido
    
    Raises:
        ValueError si es inválido
    """
    if not value:
        raise ValueError(f"{field_name} no puede estar vacío")
    return True


def validate_type(value: Any, expected_type: type, field_name: str = "field") -> bool:
    """
    Valida el tipo de un valor.
    
    Args:
        value: Valor a validar
        expected_type: Tipo esperado
        field_name: Nombre del campo
    
    Returns:
        True si es válido
    
    Raises:
        TypeError si el tipo no coincide
    """
    if not isinstance(value, expected_type):
        raise TypeError(
            f"{field_name} debe ser {expected_type.__name__}, "
            f"pero se recibió {type(value).__name__}"
        )
    return True


def validate_in_range(value: float, min_val: float, max_val: float, field_name: str = "field") -> bool:
    """
    Valida que un número esté en un rango.
    
    Args:
        value: Valor a validar
        min_val: Valor mínimo (inclusive)
        max_val: Valor máximo (inclusive)
        field_name: Nombre del campo
    
    Returns:
        True si es válido
    
    Raises:
        ValueError si está fuera de rango
    """
    if not (min_val <= value <= max_val):
        raise ValueError(
            f"{field_name} debe estar entre {min_val} y {max_val}, "
            f"pero se recibió {value}"
        )
    return True


def validate_regex(value: str, pattern: str, field_name: str = "field") -> bool:
    """
    Valida que un string coincida con una expresión regular.
    
    Args:
        value: String a validar
        pattern: Expresión regular
        field_name: Nombre del campo
    
    Returns:
        True si es válido
    
    Raises:
        ValueError si no coincide
    """
    import re
    if not re.match(pattern, value):
        raise ValueError(
            f"{field_name} no cumple el patrón requerido: {pattern}"
        )
    return True


# ============================================================================
# HELPERS DE FECHA/HORA
# ============================================================================

def get_current_time_str() -> str:
    """
    Retorna la hora actual como string formateado.
    
    Returns:
        String con formato "HH:MM:SS"
    """
    return datetime.now().strftime("%H:%M:%S")


def get_current_date_str() -> str:
    """
    Retorna la fecha actual como string formateado.
    
    Returns:
        String con formato "DD/MM/YYYY"
    """
    return datetime.now().strftime("%d/%m/%Y")


def format_duration(seconds: float) -> str:
    """
    Formatea duración en segundos a string legible.
    
    Args:
        seconds: Duración en segundos
    
    Returns:
        String formateado (ej: "1h 30m 45s")
    """
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    
    parts = []
    if hours:
        parts.append(f"{hours}h")
    if minutes:
        parts.append(f"{minutes}m")
    if secs or not parts:
        parts.append(f"{secs}s")
    
    return " ".join(parts)


def is_within_hours(hours: float) -> bool:
    """
    Verifica si estamos dentro de un rango de horas desde ahora.
    
    Args:
        hours: Número de horas
    
    Returns:
        True si el tiempo actual es menor que hours
    """
    return datetime.now() < (datetime.now() + timedelta(hours=hours))


# ============================================================================
# HELPERS DE ARCHIVO
# ============================================================================

def ensure_directory(path: str) -> bool:
    """
    Asegura que un directorio existe, lo crea si es necesario.
    
    Args:
        path: Ruta del directorio
    
    Returns:
        True si existe o fue creado
    """
    from pathlib import Path
    Path(path).mkdir(parents=True, exist_ok=True)
    return True


def file_exists(path: str) -> bool:
    """
    Verifica si un archivo existe.
    
    Args:
        path: Ruta del archivo
    
    Returns:
        True si existe
    """
    from pathlib import Path
    return Path(path).exists() and Path(path).is_file()


def read_file(path: str, encoding: str = "utf-8") -> str:
    """
    Lee un archivo completo.
    
    Args:
        path: Ruta del archivo
        encoding: Codificación (default: utf-8)
    
    Returns:
        Contenido del archivo
    
    Raises:
        FileNotFoundError si no existe
    """
    from pathlib import Path
    return Path(path).read_text(encoding=encoding)


def write_file(path: str, content: str, encoding: str = "utf-8") -> bool:
    """
    Escribe contenido a un archivo.
    
    Args:
        path: Ruta del archivo
        content: Contenido a escribir
        encoding: Codificación (default: utf-8)
    
    Returns:
        True si fue exitoso
    """
    from pathlib import Path
    ensure_directory(str(Path(path).parent))
    Path(path).write_text(content, encoding=encoding)
    return True


# ============================================================================
# HELPERS GENERALES
# ============================================================================

def chunk_list(lst: List[Any], chunk_size: int) -> List[List[Any]]:
    """
    Divide una lista en chunks de tamaño especificado.
    
    Args:
        lst: Lista a dividir
        chunk_size: Tamaño de cada chunk
    
    Returns:
        Lista de listas (chunks)
    
    Ejemplo:
        chunks = chunk_list([1, 2, 3, 4, 5], 2)
        # [[1, 2], [3, 4], [5]]
    """
    return [lst[i:i + chunk_size] for i in range(0, len(lst), chunk_size)]


def flatten_dict(d: dict, parent_key: str = '', sep: str = '.') -> dict:
    """
    Aplana un diccionario anidado.
    
    Args:
        d: Diccionario a aplanar
        parent_key: Clave padre (para recursión)
        sep: Separador entre niveles
    
    Returns:
        Diccionario aplainado
    
    Ejemplo:
        d = {'a': {'b': 1, 'c': 2}}
        flatten_dict(d)  # {'a.b': 1, 'a.c': 2}
    """
    items = []
    for k, v in d.items():
        new_key = f"{parent_key}{sep}{k}" if parent_key else k
        if isinstance(v, dict):
            items.extend(flatten_dict(v, new_key, sep=sep).items())
        else:
            items.append((new_key, v))
    return dict(items)


def merge_dicts(*dicts: dict) -> dict:
    """
    Fusiona múltiples diccionarios (últimos sobrescriben).
    
    Args:
        *dicts: Diccionarios a fusionar
    
    Returns:
        Diccionario fusionado
    
    Ejemplo:
        merged = merge_dicts({'a': 1}, {'b': 2}, {'a': 3})
        # {'a': 3, 'b': 2}
    """
    result = {}
    for d in dicts:
        result.update(d)
    return result
