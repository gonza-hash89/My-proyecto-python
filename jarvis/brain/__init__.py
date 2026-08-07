"""
brain package - El cerebro de Jarvis

Módulos:
- memory.py: Sistema de memoria (short + long term) ✅
- decision.py: Motor de decisiones ✅
- intent_data.py: Catálogo de 50+ intenciones bilingües ES/EN (Semana 4) ✅
- intent_patterns.py: Matcher de patrones regex <5ms (Semana 4) ✅
- intent_entities.py: Extracción de entidades/slots (Semana 4) ✅
- intent_ml.py: Modelo ML TF-IDF char + LinearSVC (Semana 4) ✅
- intent_processor.py: Reconocedor híbrido patrones + ML (Semana 4) ✅

El cerebro está construido con 3 capas:
  1. MEMORIA: Almacena y recuerda información
  2. INTENCIÓN: Reconoce qué quiere el usuario (híbrido regex + ML)
  3. DECISIÓN: Decide qué hacer y en qué orden
"""

from .decision import (
    DecisionEngine,
    Decision,
    Intent,
    DecisionContext,
    IntentPriority,
    AgentType,
    DecisionRule,
    DecisionStrategy,
    ConfidenceBasedStrategy,
    ContextAwareStrategy,
    ConfidenceRule,
    RecencyRule,
    ContextRelevanceRule,
    PriorityRule,
    AgentAvailabilityRule,
    resolve_conflicts,
    can_execute_in_parallel,
)

# Subsistema de intenciones (Semana 4)
from .intent_data import (
    INTENT_CATALOG,
    CATEGORIES,
    get_intent,
    get_all_intents,
    get_intents_by_category,
    get_categories,
    catalog_stats,
    generate_training_data,
    get_training_data,
    training_stats,
)
from .intent_patterns import PatternMatcher, PatternMatch, detect_language
from .intent_entities import EntityExtractor
from .intent_ml import IntentMLModel
from .intent_processor import IntentProcessor, IntentResult, get_processor

__all__ = [
    # Motor de decisiones
    "DecisionEngine",
    "Decision",
    "Intent",
    "DecisionContext",

    # Enums
    "IntentPriority",
    "AgentType",

    # Reglas
    "DecisionRule",
    "ConfidenceRule",
    "RecencyRule",
    "ContextRelevanceRule",
    "PriorityRule",
    "AgentAvailabilityRule",

    # Estrategias
    "DecisionStrategy",
    "ConfidenceBasedStrategy",
    "ContextAwareStrategy",

    # Utilidades
    "resolve_conflicts",
    "can_execute_in_parallel",

    # Datos de intenciones
    "INTENT_CATALOG",
    "CATEGORIES",
    "get_intent",
    "get_all_intents",
    "get_intents_by_category",
    "get_categories",
    "catalog_stats",
    "generate_training_data",
    "get_training_data",
    "training_stats",

    # Reconocimiento de intenciones
    "PatternMatcher",
    "PatternMatch",
    "detect_language",
    "EntityExtractor",
    "IntentMLModel",
    "IntentProcessor",
    "IntentResult",
    "get_processor",
]
