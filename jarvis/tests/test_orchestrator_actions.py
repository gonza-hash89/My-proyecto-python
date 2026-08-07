"""
Tests de integración del orquestador (FASE 6)

Verifica las acciones nuevas de la Semana 4 usando stubs ligeros
(no inicializa voz, memoria ni abre navegadores):
- Parser de duraciones para temporizadores
- Acciones de notas y tareas (escriben archivos)
- Despacho de intenciones sin handler implementado
"""

import os
import types

import pytest

from orchestrator.orchestrator import Orchestrator


def _make_stub(tmp_path):
    """Instancia de Orchestrator sin __init__ (evita voz/memoria)."""
    inst = object.__new__(Orchestrator)
    inst.config = types.SimpleNamespace(
        base_dir=str(tmp_path),
        data_dir="data",
    )
    inst.speak = lambda text: None
    inst._publish = lambda *a, **k: None
    inst.logger = types.SimpleNamespace(info=lambda *a, **k: None,
                                        warning=lambda *a, **k: None,
                                        debug=lambda *a, **k: None)
    inst.engine = None
    inst._voice_available = False
    inst.is_running = True
    return inst


def _intent(params):
    return types.SimpleNamespace(name="x", confidence=0.9,
                                 parameters=params, raw_text="x")


# ────────── Parser de duraciones ──────────

def test_parse_duration_minutos():
    inst = _make_stub(None)
    assert inst._parse_duration("pon un temporizador de 5 minutos", None) == 300


def test_parse_duration_segundos():
    inst = _make_stub(None)
    assert inst._parse_duration("alarma en 10 segundos", None) == 10


def test_parse_duration_horas():
    inst = _make_stub(None)
    assert inst._parse_duration("temporizador de 2 horas", None) == 7200


def test_parse_duration_palabras():
    inst = _make_stub(None)
    assert inst._parse_duration("pon una hora", None) == 3600
    assert inst._parse_duration("dentro de un minuto", None) == 60


def test_parse_duration_entidad_prioriza():
    inst = _make_stub(None)
    # La entidad extraída manda sobre el texto crudo
    assert inst._parse_duration("texto sin pistas", "15 minutos") == 900


def test_parse_duration_desconocido():
    inst = _make_stub(None)
    assert inst._parse_duration("hola mundo", None) == 0


def test_describe_duration():
    inst = _make_stub(None)
    assert inst._describe_duration(3600) == (1, "hora")
    assert inst._describe_duration(120) == (2, "minutos")
    assert inst._describe_duration(45) == (45, "segundos")


# ────────── Acciones de archivo ──────────

def test_action_take_notes_escribe_archivo(tmp_path):
    inst = _make_stub(tmp_path)
    resp = inst._action_take_notes("anota comprar leche", _intent({"content": "comprar leche"}))
    assert "Nota guardada" in resp

    path = os.path.join(str(tmp_path), "data", "notas.md")
    assert os.path.exists(path)
    with open(path, encoding="utf-8") as f:
        content = f.read()
    assert "comprar leche" in content


def test_action_take_notes_sin_contenido_pregunta(tmp_path):
    inst = _make_stub(tmp_path)
    resp = inst._action_take_notes("anota", _intent({}))
    assert "Pregunta" in resp


def test_action_create_task_escribe_archivo(tmp_path):
    inst = _make_stub(tmp_path)
    resp = inst._action_create_task(
        "crea una tarea para terminar el informe",
        _intent({"task_description": "terminar el informe"}),
    )
    assert "Tarea agregada" in resp

    path = os.path.join(str(tmp_path), "data", "tareas.txt")
    assert os.path.exists(path)
    with open(path, encoding="utf-8") as f:
        content = f.read()
    assert "- [ ] terminar el informe" in content


def test_action_create_task_falla_sin_tarea(tmp_path):
    inst = _make_stub(tmp_path)
    resp = inst._action_create_task("crea una tarea", _intent({}))
    assert "Pregunta" in resp


# ────────── Intenciones sin acción ──────────

def test_intencion_sin_handler_no_rompe(tmp_path):
    inst = _make_stub(tmp_path)
    resp = inst._execute_intent(_intent({"un slot": "x"}), "frase")
    assert resp is not None
    assert "no tengo implementada" in resp
