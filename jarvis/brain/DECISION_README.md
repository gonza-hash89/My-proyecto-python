"""
decision_README.md - Guía completa del Motor de Decisiones

El corazón estratégico de Jarvis: Cómo se toman las decisiones
"""

# 🧠 Motor de Decisiones de Jarvis

## Visión General

El motor de decisiones es el **corazón estratégico** de Jarvis. No es solo un sistema que responde preguntas — es un sistema que **piensa**, **evalúa** y **decide** qué hacer y en qué orden.

```
Usuario dice algo
        ↓
Intent Recognizer detecta intención(es)
        ↓
Decision Engine evalúa con múltiples reglas
        ↓
Elige mejor acción según:
  • Confianza
  • Contexto
  • Prioridades
  • Historial reciente
        ↓
Agente ejecuta decisión
        ↓
Resultado se registra en memoria
```

## 🏗️ Arquitectura

### Componentes Principales

```
┌─────────────────────────────────────────────────────────────┐
│                     DECISION ENGINE                          │
│                                                               │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐       │
│  │   Intent     │  │  Decision    │  │  Decision    │       │
│  │  (entrada)   │  │ (estructura) │  │  Context     │       │
│  └──────────────┘  └──────────────┘  └──────────────┘       │
│                                                               │
│  ┌────────────────────────────────────────────────────┐      │
│  │          DECISION RULES (Reglas de Evaluación)    │      │
│  ├────────────────────────────────────────────────────┤      │
│  │ • ConfidenceRule      → Confianza de la intención │      │
│  │ • RecencyRule         → Qué tan reciente es       │      │
│  │ • ContextRelevanceRule → Relevancia al contexto   │      │
│  │ • PriorityRule        → Nivel de prioridad        │      │
│  │ • AgentAvailabilityRule → Disponibilidad agente  │      │
│  └────────────────────────────────────────────────────┘      │
│                                                               │
│  ┌────────────────────────────────────────────────────┐      │
│  │     DECISION STRATEGIES (Estrategias)             │      │
│  ├────────────────────────────────────────────────────┤      │
│  │ • ConfidenceBasedStrategy   (por defecto)        │      │
│  │ • ContextAwareStrategy      (sensible contexto)  │      │
│  │ • [Futuras: PriorityFirst, HistoryBased...]     │      │
│  └────────────────────────────────────────────────────┘      │
│                                                               │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐       │
│  │   Historial  │  │   Pending    │  │   Context    │       │
│  │  de Decisión │  │   Decisions  │  │   Actual     │       │
│  └──────────────┘  └──────────────┘  └──────────────┘       │
└─────────────────────────────────────────────────────────────┘
```

## 📊 Estructuras de Datos

### Intent (Intención)

Representa lo que el usuario **quiere hacer**.

```python
@dataclass
class Intent:
    id: str                              # ID único
    name: str                            # "play_music", "search", etc.
    confidence: float                    # 0.0 - 1.0 (qué tan seguro)
    parameters: Dict[str, Any]           # {"query": "reggaeton"}
    raw_text: str                        # Texto original del usuario
    timestamp: datetime                  # Cuándo se reconoció
```

**Ejemplo:**
```python
intent = Intent(
    id="intent_001",
    name="play_music",
    confidence=0.95,
    parameters={"genre": "reggaeton", "priority": "normal"},
    raw_text="Reproduce música reggaeton"
)
```

### Decision (Decisión)

Representa lo que Jarvis **decide hacer**.

```python
@dataclass
class Decision:
    id: str                              # ID único
    intent: Intent                       # La intención que originó esto
    selected_agent: AgentType           # Qué agente la ejecutará
    priority: IntentPriority            # CRITICAL, HIGH, NORMAL, etc.
    confidence: float                   # Confianza en esta decisión
    reasoning: str                      # POR QUÉ se tomó esta decisión
    dependencies: List[str]             # Otras decisiones que espera
    actions: List[str]                  # Acciones específicas a ejecutar
    status: str                         # "pending", "executing", "completed"
```

**Ejemplo:**
```python
decision = Decision(
    id="dec_001_xyz",
    intent=intent,
    selected_agent=AgentType.DIALOG,
    priority=IntentPriority.NORMAL,
    confidence=0.92,
    reasoning="Intención con 95% confianza, contexto favorable",
    actions=["play_music"]
)
```

### DecisionContext (Contexto)

El **estado actual** en el que se toman decisiones.

```python
@dataclass
class DecisionContext:
    user_id: str                        # Usuario actual
    session_id: str                     # Sesión actual
    previous_intents: List[Intent]      # Historial de intenciones
    active_decisions: List[Decision]    # Decisiones en ejecución
    system_state: Dict[str, Any]        # Estado del sistema
    available_agents: List[AgentType]   # Agentes disponibles
    constraints: Dict[str, Any]         # Restricciones actuales
```

## 🎯 Prioridades

Las intenciones pueden tener diferentes **niveles de urgencia**:

```python
class IntentPriority(Enum):
    CRITICAL = 5       # ¡AHORA! (apagar PC, emergencia)
    HIGH = 4           # Importante, ejecutar pronto
    NORMAL = 3         # Ejecución normal
    LOW = 2            # Puede esperar
    BACKGROUND = 1     # Segundo plano
```

**Ejemplo de uso:**
```python
intent = Intent(
    name="shutdown",
    confidence=0.98,
    parameters={"priority": "critical"}  # ← Prioridad máxima
)
```

## 🤖 Agentes Disponibles

El motor de decisiones puede asignar tareas a estos agentes:

```python
class AgentType(Enum):
    VOICE = "voice_agent"           # Síntesis de voz
    DIALOG = "dialog_agent"         # Generación de respuestas
    MEMORY = "memory_agent"         # Gestión de memoria
    SYSTEM = "system_agent"         # Control del PC
    WEB = "web_agent"               # Búsqueda en internet
    FILE = "file_agent"             # Gestión de archivos
    CALENDAR = "calendar_agent"     # Gestión de agenda
    CREATIVE = "creative_agent"     # Tareas creativas
```

## ⚙️ Reglas de Decisión

Las reglas evalúan cada intención y generan un **puntaje**:

### 1. ConfidenceRule
**Regla:** La confianza del intent es crucial

```python
rule = ConfidenceRule("confidence", weight=0.5)
score, reason = rule.evaluate(intent, context)
# Si intent.confidence = 0.95, score = 0.95
```

### 2. RecencyRule
**Regla:** Las intenciones recientes son más relevantes

```python
rule = RecencyRule("recency", weight=0.2)
score, reason = rule.evaluate(intent, context)
# Si el intent es muy nuevo, score alto
# Si es viejo, score decae: 1.0 / (1.0 + tiempo_segundos/60)
```

### 3. ContextRelevanceRule
**Regla:** Intenciones relevantes al contexto reciente

```python
rule = ContextRelevanceRule("context", weight=0.2)
score, reason = rule.evaluate(intent, context)
# Si hay intenciones similares recientes, score sube
```

### 4. PriorityRule
**Regla:** Intenciones críticas siempre ganan

```python
rule = PriorityRule("priority", weight=0.3)
score, reason = rule.evaluate(intent, context)
# CRITICAL: 1.0, HIGH: 0.8, NORMAL: 0.6, LOW: 0.4, BACKGROUND: 0.2
```

### 5. AgentAvailabilityRule
**Regla:** Verifica que el agente esté disponible

```python
rule = AgentAvailabilityRule(AgentType.VOICE)
score, reason = rule.evaluate(intent, context)
# 1.0 si disponible, 0.0 si no
```

## 🧩 Estrategias de Decisión

### ConfidenceBasedStrategy (Predeterminada)

Evalúa cada intención con todas las reglas y elige la de **mayor puntaje ponderado**.

```
Score Final = (ConfidenceScore × 0.5) +
              (RecencyScore × 0.2) +
              (ContextScore × 0.2) +
              (PriorityScore × 0.3) +
              ... / suma_de_pesos
```

**Ventajas:**
- Rápida y eficiente
- Predecible
- Fácil de ajustar pesos

**Ejemplo:**
```python
engine = DecisionEngine(strategy="confidence_based")
decision = engine.decide([intent1, intent2, intent3])
```

### ContextAwareStrategy

Considera el **historial y estado del sistema** de forma más profunda.

**Ventajas:**
- Más inteligente
- Aprende del contexto
- Futuro: machine learning

**Ejemplo:**
```python
engine = DecisionEngine(strategy="context_aware")
decision = engine.decide([intent], context)
```

## 📖 Cómo Usar el Motor

### 1. Uso Básico

```python
from jarvis.brain.decision import DecisionEngine, Intent

# Crear motor de decisiones
engine = DecisionEngine()

# Crear una intención
intent = Intent(
    id="intent_001",
    name="play_music",
    confidence=0.95,
    parameters={"genre": "rock"},
    raw_text="Reproduce música rock"
)

# Tomar decisión
decision = engine.decide([intent])

if decision:
    print(f"Agente asignado: {decision.selected_agent.value}")
    print(f"Confianza: {decision.confidence:.2%}")
    print(f"Razón: {decision.reasoning}")
```

### 2. Con Múltiples Intenciones

```python
intents = [
    Intent("i1", "play_music", 0.92),
    Intent("i2", "search", 0.65),
    Intent("i3", "open", 0.78),
]

decision = engine.decide(intents)
# → Se elige la intención con mejor puntaje ponderado
```

### 3. Con Contexto Personalizado

```python
from jarvis.brain.decision import DecisionContext, AgentType

context = DecisionContext(
    user_id="user_001",
    session_id="session_xyz",
    previous_intents=[...],  # Historial
    available_agents=[AgentType.VOICE, AgentType.DIALOG]
)

decision = engine.decide([intent], context)
```

### 4. Resolver Conflictos

```python
from jarvis.brain.decision import resolve_conflicts

decisions = [dec1, dec2, dec3]  # Múltiples decisiones válidas
winner = resolve_conflicts(decisions)
# → Elige por: Prioridad, Confianza, Recencia
```

### 5. Verificar Paralelismo

```python
from jarvis.brain.decision import can_execute_in_parallel

if can_execute_in_parallel(decision1, decision2):
    # Ejecutar en paralelo (diferentes agentes)
    executor.execute_parallel(decision1, decision2)
else:
    # Ejecutar secuencial
    executor.execute_sequential(decision1, decision2)
```

### 6. Acceder al Historial

```python
# Obtener últimas 10 decisiones
history = engine.get_decision_history(limit=10)

# Exportar a JSON
engine.export_decision_history("decisions.json")

# Ver decisiones pendientes
pending = engine.get_pending_decisions()
```

## 🧪 Pruebas

Ejecuta la suite completa de pruebas:

```bash
python jarvis/brain/test_decision.py
```

**Incluye 8 escenarios:**
1. ✅ Reconocimiento básico de intención
2. ✅ Conflicto de múltiples intenciones
3. ✅ Niveles de prioridad
4. ✅ Umbral de confianza
5. ✅ Contexto de decisión
6. ✅ Resolución de conflictos
7. ✅ Ejecución en paralelo
8. ✅ Historial de decisiones

## 📊 Configuración

En `jarvis/core/config.py`:

```python
@dataclass
class DecisionConfig:
    """Configuración del motor de decisiones"""
    enabled: bool = True
    strategy: str = "confidence_based"  # o "context_aware"
    max_retries: int = 3
    timeout: int = 30  # segundos
    confidence_threshold: float = 0.5   # Mínimo 50% de confianza
```

**Cambiar configuración:**
```python
from jarvis.core.config import get_config

config = get_config()
config.decision.confidence_threshold = 0.7  # Más exigente
config.decision.strategy = "context_aware"
```

## 🔍 Logging y Trazabilidad

Cada decisión está **completamente documentada**:

```
2026-07-06 15:35:42 | Jarvis.decision_engine | INFO | Processing 3 intent(s)
2026-07-06 15:35:42 | Jarvis.decision_engine | DEBUG | Intent 'play_music' scored: 92.34%
  rules: confidence: 0.95 (weight: 0.5) | recency: 0.88 | priority: 0.90
2026-07-06 15:35:42 | Jarvis.decision_engine | INFO | Decision made: dialog_agent
```

**Ver logs:**
```bash
tail -f logs/jarvis.log
grep "decision_engine" logs/jarvis.log
```

## 🎓 Conceptos Avanzados

### Umbrales de Confianza

```python
# Solo aceptar decisiones con 80%+ de confianza
engine.config.confidence_threshold = 0.8

# Si está por debajo, se rechaza
decision = engine.decide([low_confidence_intent])
# → None (rechazado)
```

### Dependencias entre Decisiones

```python
# Una decisión puede depender de otra
decision_1 = Decision(..., id="dec_001")
decision_2 = Decision(
    ..., 
    id="dec_002",
    dependencies=["dec_001"]  # Espera a dec_001
)
```

### Estado de Decisiones

```python
decision.status = "pending"      # Pendiente de ejecutar
decision.status = "executing"    # Ejecutando
decision.status = "completed"    # Completada
```

## 🚀 Futuras Mejoras

- [ ] Machine Learning: Aprender pesos óptimos de reglas
- [ ] Predicción: Anticipar siguientes intenciones
- [ ] Aprendizaje del usuario: Preferencias personalizadas
- [ ] Multi-intención: Ejecutar varias en paralelo
- [ ] Retroalimentación: Mejorar con cada decisión
- [ ] Explicabilidad: IA interpretable al usuario

## 📝 Filosofía de Diseño

```
"Mejor lento y bien, que rápido y mal"

Principios:
✓ Cada decisión es RAZONADA (no aleatoria)
✓ Cada decisión es TRAZABLE (logging completo)
✓ Cada decisión es FLEXIBLE (múltiples estrategias)
✓ Cada decisión es CONFIABLE (validaciones exhaustivas)
✓ Cada decisión es EDUCATIVA (código legible y documentado)
```

---

**Última actualización:** 2026-07-06  
**Versión:** 1.0 (SEMANA 2 completa ✅)
