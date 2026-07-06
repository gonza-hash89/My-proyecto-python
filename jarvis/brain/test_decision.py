"""
test_decision.py - Pruebas y ejemplos del motor de decisiones

Demuestra cómo funciona el motor de decisiones de Jarvis en diferentes escenarios.
"""

from datetime import datetime
from jarvis.brain.decision import (
    DecisionEngine,
    Intent,
    DecisionContext,
    IntentPriority,
    AgentType,
    resolve_conflicts,
    can_execute_in_parallel,
)
from jarvis.core.logger import JarvisLogger, init_logger
from jarvis.core.config import get_config


def init_test_environment():
    """Inicializa el ambiente de pruebas"""
    init_logger()
    logger = JarvisLogger.get_logger("test_decision")
    logger.info("🧪 Iniciando pruebas del motor de decisiones")
    return logger


def test_basic_intent_recognition():
    """
    TEST 1: Reconocimiento básico de intención
    
    Escenario: El usuario dice "Reproduce música"
    Esperado: Se reconoce la intención y se asigna al agente correcto
    """
    print("\n" + "="*80)
    print("TEST 1: Reconocimiento básico de intención")
    print("="*80)
    
    logger = JarvisLogger.get_logger("test_decision")
    engine = DecisionEngine()
    
    # Crear una intención
    intent = Intent(
        id="intent_001",
        name="play_music",
        confidence=0.95,
        parameters={"query": "reggaeton", "priority": "normal"},
        raw_text="Reproduce música reggaeton"
    )
    
    logger.info(f"📝 Intención creada: {intent.name} (confianza: {intent.confidence:.2%})")
    
    # Tomar decisión
    decision = engine.decide([intent])
    
    if decision:
        print(f"\n✅ DECISIÓN TOMADA:")
        print(f"   Intent: {decision.intent.name}")
        print(f"   Agente: {decision.selected_agent.value}")
        print(f"   Prioridad: {decision.priority.name}")
        print(f"   Confianza: {decision.confidence:.2%}")
        print(f"   Acciones: {decision.actions}")
        logger.info(f"Decision ID: {decision.id}")
    else:
        print("\n❌ No se pudo tomar decisión")
        logger.error("Failed to make decision")


def test_multiple_intents_conflict():
    """
    TEST 2: Conflicto de múltiples intenciones
    
    Escenario: El usuario dice algo ambiguo
    - "Busca información sobre música" (search)
    - "Reproduce música" (play_music)
    Esperado: Se elige la intención con mayor confianza
    """
    print("\n" + "="*80)
    print("TEST 2: Conflicto de múltiples intenciones")
    print("="*80)
    
    logger = JarvisLogger.get_logger("test_decision")
    engine = DecisionEngine()
    
    # Crear múltiples intenciones con diferentes confianzas
    intents = [
        Intent(
            id="intent_002a",
            name="play_music",
            confidence=0.92,
            parameters={"priority": "normal"},
            raw_text="Toca música"
        ),
        Intent(
            id="intent_002b",
            name="search",
            confidence=0.65,
            parameters={"query": "música", "priority": "normal"},
            raw_text="Busca música"
        ),
    ]
    
    print(f"\n📝 Intenciones detectadas:")
    for i in intents:
        print(f"   - {i.name}: {i.confidence:.2%} confianza")
    
    # Tomar decisión
    decision = engine.decide(intents)
    
    if decision:
        print(f"\n✅ DECISIÓN GANADORA:")
        print(f"   Intent: {decision.intent.name}")
        print(f"   Confianza final: {decision.confidence:.2%}")
        print(f"   Razón: {decision.reasoning[:100]}...")
    else:
        print("\n❌ No se pudo resolver conflicto")


def test_priority_levels():
    """
    TEST 3: Niveles de prioridad
    
    Escenario: El usuario dice múltiples cosas con diferentes urgencias
    Esperado: La intención CRÍTICA se ejecuta primero
    """
    print("\n" + "="*80)
    print("TEST 3: Niveles de prioridad")
    print("="*80)
    
    logger = JarvisLogger.get_logger("test_decision")
    engine = DecisionEngine()
    
    # Crear intenciones con diferentes prioridades
    intents = [
        Intent(
            id="intent_003a",
            name="play_music",
            confidence=0.88,
            parameters={"priority": "normal"},
            raw_text="Reproduce música"
        ),
        Intent(
            id="intent_003b",
            name="shutdown",
            confidence=0.95,
            parameters={"priority": "critical"},
            raw_text="APAGAR SISTEMA AHORA"
        ),
        Intent(
            id="intent_003c",
            name="search",
            confidence=0.85,
            parameters={"priority": "low"},
            raw_text="Busca algo cuando puedas"
        ),
    ]
    
    print(f"\n📝 Intenciones con prioridades:")
    for i in intents:
        print(f"   - {i.name}: {i.confidence:.2%} | Prioridad: {i.parameters['priority']}")
    
    # Tomar decisiones
    decisions = []
    for intent in intents:
        decision = engine.decide([intent])
        if decision:
            decisions.append(decision)
    
    # Mostrar orden de ejecución esperado
    print(f"\n✅ ORDEN DE EJECUCIÓN:")
    sorted_decisions = sorted(
        decisions,
        key=lambda d: d.priority.value,
        reverse=True
    )
    for i, d in enumerate(sorted_decisions, 1):
        print(f"   {i}. {d.intent.name} ({d.priority.name}) - {d.confidence:.2%}")


def test_confidence_threshold():
    """
    TEST 4: Umbral de confianza
    
    Escenario: Se detectan intenciones pero con poca confianza
    Esperado: Si está debajo del threshold, se rechaza
    """
    print("\n" + "="*80)
    print("TEST 4: Umbral de confianza")
    print("="*80)
    
    logger = JarvisLogger.get_logger("test_decision")
    config = get_config()
    print(f"\n⚙️  Umbral de confianza configurado: {config.decision.confidence_threshold:.2%}")
    
    engine = DecisionEngine()
    
    # Crear intenciones con confianza baja
    intents = [
        Intent(
            id="intent_004a",
            name="play_music",
            confidence=0.45,  # DEBAJO del threshold (0.5)
            parameters={"priority": "normal"},
            raw_text="Algo sobre música"
        ),
        Intent(
            id="intent_004b",
            name="search",
            confidence=0.52,  # ENCIMA del threshold
            parameters={"priority": "normal"},
            raw_text="Busca algo"
        ),
    ]
    
    print(f"\n📝 Intenciones detectadas:")
    for i in intents:
        status = "✅ ACEPTADA" if i.confidence >= config.decision.confidence_threshold else "❌ RECHAZADA"
        print(f"   - {i.name}: {i.confidence:.2%} {status}")
    
    # Tomar decisiones
    print(f"\n⚡ Procesando decisiones:")
    for intent in intents:
        decision = engine.decide([intent])
        if decision:
            print(f"   ✅ {intent.name}: DECISIÓN TOMADA")
        else:
            print(f"   ❌ {intent.name}: RECHAZADA (confianza insuficiente)")


def test_decision_context():
    """
    TEST 5: Contexto de decisión
    
    Escenario: El contexto afecta cómo se toman las decisiones
    Esperado: Las intenciones similares recientes son más relevantes
    """
    print("\n" + "="*80)
    print("TEST 5: Contexto de decisión")
    print("="*80)
    
    logger = JarvisLogger.get_logger("test_decision")
    engine = DecisionEngine()
    
    # Crear contexto con historial
    context = DecisionContext(
        user_id="user_001",
        session_id="session_001",
        previous_intents=[
            Intent("intent_005a", "play_music", 0.90, raw_text="Reproduce reggaeton"),
            Intent("intent_005b", "play_music", 0.88, raw_text="Sigue con más reggaeton"),
        ],
        available_agents=list(AgentType)
    )
    
    print(f"\n📝 Historial de intenciones recientes:")
    for i in context.previous_intents:
        print(f"   - {i.name}: {i.confidence:.2%}")
    
    # Nueva intención similar
    new_intent = Intent(
        id="intent_005c",
        name="play_music",
        confidence=0.85,
        parameters={"priority": "normal"},
        raw_text="Más música"
    )
    
    print(f"\n🎵 Nueva intención: {new_intent.name} ({new_intent.confidence:.2%})")
    
    # Tomar decisión con contexto
    decision = engine.decide([new_intent], context)
    
    if decision:
        print(f"\n✅ DECISIÓN CON CONTEXTO:")
        print(f"   Intención: {decision.intent.name}")
        print(f"   Confianza final: {decision.confidence:.2%}")
        print(f"   Agente: {decision.selected_agent.value}")


def test_resolve_conflicts():
    """
    TEST 6: Resolver conflictos entre decisiones
    
    Escenario: Hay múltiples decisiones válidas en conflicto
    Esperado: Se elige la más importante
    """
    print("\n" + "="*80)
    print("TEST 6: Resolver conflictos entre decisiones")
    print("="*80)
    
    logger = JarvisLogger.get_logger("test_decision")
    engine = DecisionEngine()
    
    # Crear decisiones en conflicto
    intent1 = Intent("i1", "play_music", 0.92, parameters={"priority": "high"})
    intent2 = Intent("i2", "search", 0.90, parameters={"priority": "critical"})
    intent3 = Intent("i3", "open", 0.88, parameters={"priority": "normal"})
    
    dec1 = engine.decide([intent1])
    dec2 = engine.decide([intent2])
    dec3 = engine.decide([intent3])
    
    decisions = [dec1, dec2, dec3]
    
    print(f"\n⚔️ Decisiones en conflicto:")
    for d in decisions:
        print(f"   - {d.intent.name}: {d.priority.name} | {d.confidence:.2%}")
    
    # Resolver conflicto
    winner = resolve_conflicts(decisions)
    print(f"\n🏆 DECISIÓN GANADORA:")
    print(f"   Intent: {winner.intent.name}")
    print(f"   Prioridad: {winner.priority.name}")
    print(f"   Confianza: {winner.confidence:.2%}")


def test_parallel_execution():
    """
    TEST 7: Determinar si las decisiones pueden ejecutarse en paralelo
    
    Escenario: Múltiples decisiones pueden ejecutarse simultáneamente
    Esperado: Se identifican qué decisiones son independientes
    """
    print("\n" + "="*80)
    print("TEST 7: Ejecución en paralelo")
    print("="*80)
    
    logger = JarvisLogger.get_logger("test_decision")
    engine = DecisionEngine()
    
    # Crear decisiones
    intent1 = Intent("i1", "play_music", 0.90)
    intent2 = Intent("i2", "search", 0.88)
    intent3 = Intent("i3", "open", 0.85)
    
    dec1 = engine.decide([intent1])
    dec2 = engine.decide([intent2])
    dec3 = engine.decide([intent3])
    
    print(f"\n📋 Decisiones:")
    print(f"   1. {dec1.selected_agent.value}")
    print(f"   2. {dec2.selected_agent.value}")
    print(f"   3. {dec3.selected_agent.value}")
    
    # Verificar paralelismo
    print(f"\n🔄 Compatibilidad de ejecución:")
    print(f"   Dec1 & Dec2: {'✅ PARALELO' if can_execute_in_parallel(dec1, dec2) else '❌ SECUENCIAL'}")
    print(f"   Dec2 & Dec3: {'✅ PARALELO' if can_execute_in_parallel(dec2, dec3) else '❌ SECUENCIAL'}")
    print(f"   Dec1 & Dec3: {'✅ PARALELO' if can_execute_in_parallel(dec1, dec3) else '❌ SECUENCIAL'}")


def test_decision_history():
    """
    TEST 8: Historial de decisiones
    
    Escenario: Se registra todo lo que Jarvis decide
    Esperado: Historial completo y trazable
    """
    print("\n" + "="*80)
    print("TEST 8: Historial de decisiones")
    print("="*80)
    
    logger = JarvisLogger.get_logger("test_decision")
    engine = DecisionEngine()
    
    # Hacer varias decisiones
    intents = [
        Intent("i1", "play_music", 0.90),
        Intent("i2", "search", 0.85),
        Intent("i3", "time", 0.95),
    ]
    
    print(f"\n⏱️ Procesando {len(intents)} intenciones...")
    for intent in intents:
        decision = engine.decide([intent])
        if decision:
            print(f"   ✅ {intent.name}")
    
    # Mostrar historial
    history = engine.get_decision_history()
    print(f"\n📚 HISTORIAL DE DECISIONES ({len(history)} decisiones):")
    for i, dec in enumerate(history, 1):
        print(f"   {i}. {dec.intent.name} → {dec.selected_agent.value} ({dec.confidence:.2%})")
    
    # Exportar historial
    history_file = "decision_history.json"
    engine.export_decision_history(history_file)
    print(f"\n💾 Historial exportado a: {history_file}")


def run_all_tests():
    """Ejecuta todas las pruebas"""
    logger = init_test_environment()
    
    print("\n" + "█"*80)
    print("█" + " "*78 + "█")
    print("█" + "  🤖 PRUEBAS DEL MOTOR DE DECISIONES DE JARVIS".center(78) + "█")
    print("█" + " "*78 + "█")
    print("█"*80)
    
    try:
        test_basic_intent_recognition()
        test_multiple_intents_conflict()
        test_priority_levels()
        test_confidence_threshold()
        test_decision_context()
        test_resolve_conflicts()
        test_parallel_execution()
        test_decision_history()
        
        print("\n" + "█"*80)
        print("█" + " "*78 + "█")
        print("█" + "  ✅ TODAS LAS PRUEBAS COMPLETADAS".center(78) + "█")
        print("█" + " "*78 + "█")
        print("█"*80 + "\n")
        
        logger.info("✅ Todas las pruebas completadas exitosamente")
        
    except Exception as e:
        logger.error(f"❌ Error durante las pruebas: {e}", exc_info=True)
        print(f"\n❌ ERROR: {e}")


if __name__ == "__main__":
    run_all_tests()
