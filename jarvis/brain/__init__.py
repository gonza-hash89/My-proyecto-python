"""
brain package - El cerebro de Jarvis

Módulos principales:
- memory.py: Sistema de memoria (short + long term) ✅
- intent.py: Reconocedor de intenciones (próximamente)
- decision.py: Motor de decisiones ✅

El cerebro está construido con 3 capas:
  1. MEMORIA: Almacena y recuerda información
  2. INTENCIÓN: Reconoce qué quiere el usuario
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
]
