"""
WEEK5_PLAN.md - Plan detallado SEMANA 5: Agentes Esenciales

Objetivo: Framework de agentes en jarvis/agents/ + System/Web/Dialog Agent
Resultado: Las intenciones "en desarrollo" de la Semana 4 pasan a ejecución
Dependencias: Semana 4 completa (76 tests verdes, Intent Recognizer híbrido)
Decisiones tomadas: Gemini opcional + degradación; Open-Meteo/CoinGecko; File → Semana 6
"""

# 🎯 SEMANA 5: AGENTES ESENCIALES

**Fechas:** 2026-08-08 al 2026-08-14
**Duración:** 1 semana intensiva
**Objetivo:** Framework de agentes + System/Web/Dialog Agent con acciones reales
**Estado:** ✅ DECISIONES TOMADAS, LISTO PARA COMENZAR

---

## 🧭 CONTEXTO (QUÉ HAY YA)

La Semana 4 dejó listo:

```
✅ Intent Recognizer HÍBRIDO (52 intenciones, ES/EN, <7ms)
✅ 23 acciones reales en el orquestador (legacy 11 + nuevas 12)
✅ 28 intenciones responden "Aún no tengo implementada la acción"
✅ AgentType ya definido en brain/decision.py:
   VOICE, DIALOG, MEMORY, SYSTEM, WEB, FILE, CALENDAR, CREATIVE
✅ core/agent_base.py: clase base Agent (ABC) con process/handle_event/send_message
✅ Mapeo agent_map en ConfidenceBasedStrategy → conecta intenciones con AgentType
❌ jarvis/agents/ NO existe todavía (los agentes no están implementados)
```

**Hueco que cierra la Semana 5:** convertir la capa de INTENCIÓN en capa de
EJECUCIÓN por agente. El orquestador deja de ejecutar acciones "a mano" y
delega en el agente correspondiente.

---

## 🎯 OBJETIVO

```
INTENCIÓN (Semana 4)   +   AGENTE (Semana 5)   =   ACCIÓN REAL
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
├─ recognize(text)        ├─ agents/system.py       ├─ Apagar, abrir apps
├─ intent + entities      ├─ agents/web.py          ├─ Búsqueda real + clima + cripto
└─ DecisionEngine         ├─ agents/dialog.py       ├─ Chatear (Gemini + fallback)
                          └─ agents/file.py         → SEMANA 6 (moviéndose)
```

Regla de oro: **cada agente implementa el contrato de `core/agent_base.py`**
(`process(message) -> dict` y `handle_event(event)`) y se registra en el
orquestador como módulo inicializado.

---

## 🏗️ FASE 0 — FRAMEWORK DE AGENTES (Lunes)

### Entregables
```
jarvis/agents/
├── __init__.py          # Exports + registry de agentes
├── base.py              # AgentBase extendiendo core.agent_base.Agent
├── registry.py          # AgentRegistry: registrar, obtener, listar agentes
└── factory.py           # Crear agentes según AgentType
```

### `registry.py` (interfaz mínima)
```python
class AgentRegistry:
    def register(self, agent: Agent) -> None: ...
    def get(self, agent_type: str) -> Optional[Agent]: ...
    def list(self) -> List[Agent]: ...
    def start_all(self) -> None: ...
    def stop_all(self) -> None: ...
```

### Criterios
- [x] Todo agente hereda de `AgentBase` y respeta el contrato
- [x] El orquestador registra los agentes y les asigna el `event_bus`
- [x] `get_status()` del orquestador muestra los agentes activos

---

## 🖥️ FASE 1 — SYSTEM AGENT (Martes)

### `agents/system.py`
**Intenciones que resuelve** (pasan de "en desarrollo" a reales):
`system_control`, `open_application`, `take_screenshot`, `volume_control`,
`open_folder`, `empty_trash`, `lock_session`

### Capacidades reales (Windows, sin librerías extra)
```
✅ Abrir aplicaciones web y locales (mover lógica de _action_open_app)
✅ Apagar / reiniciar / bloquear / suspender (os.system)
✅ Captura de pantalla (pyautogui, ya disponible)
✅ Subir/bajar/mutar volumen (pycaw o nircmd si está; si no → "en desarrollo")
✅ Abrir carpeta en el Explorador (os.startfile)
✅ Listar procesos (tasklist) y matar procesos (taskkill)
```

### Salida de `process()`
```python
{"status": "success", "data": {"result": "Abriendo notepad"}, "agent": "system_agent"}
```

---

## 🌐 FASE 2 — WEB AGENT (Miércoles)

### `agents/web.py`
**Intenciones que resuelve:**
`search_info`, `news_query`, `weather_query`, `get_exchange_rate`, `crypto_price`,
`check_investments`

### Capacidades reales
```
✅ Búsqueda en internet de VERDAD (requests + parse de resultados)
   - API pública: Wikipedia (ya instalada) + DuckDuckGo HTML (sin key)
   - Fallback: abrir Google con la query (como hoy)
✅ Noticias: resumir titulares vía RSS público (feedparser) o Google News RSS
✅ Clima: Open-Meteo API (gratis, sin key) → temperatura real
✅ Cripto: CoinGecko API (gratis, sin key) → precio real de monedas
```

### Decisiones tomadas (confirmadas)
- [x] ✅ **Open-Meteo y CoinGecko INTEGRADOS** (gratis, sin keys) → Jarvis responde el
      clima y el precio de cripto con datos reales, no solo abre el buscador
- [x] ✅ Búsqueda web real: Wikipedia + DuckDuckGo HTML (sin key); fallback a Google
- [x] ✅ Noticias: RSS público (feedparser) como resumen; fallback a Google News
- [x] ✅ El resto (inversiones, tipo de cambio) se mantiene "abrir buscador" esta semana

---

## 💬 FASE 3 — DIALOG AGENT (Jueves)

### `agents/dialog.py`
**Intenciones que resuelve:**
`tell_joke`, `change_name`, `help_query`, `smalltalk` (respuestas conversacionales),
`translate_text` (si es factible)

### Capacidades reales
```
✅ Gemini API (google-generativeai) CON API key opcional
   - Si hay clave en config → respuestas generativas con contexto de sesión
   - Si NO hay clave → respuestas por plantilla local (chistes, ayuda, saludos)
✅ help_query: genera el manual de comandos desde INTENT_CATALOG
✅ translate_text: fallback a MyMemory API gratuita (sin key) o "en desarrollo"
```

### Seguridad
- La API key se lee de variable de entorno o `config`, NUNCA se commitea
- Sin clave → el agente funciona en modo plantillas (degradación elegante)

### Decisiones tomadas (confirmadas)
- [x] ✅ **Gemini API OPCIONAL con degradación elegante**: si hay key → respuestas
      generativas con contexto de sesión; si no hay key → plantillas locales
      (chistes, ayuda, saludos). Jarvis nunca crashea por falta de API.

---

## 📁 FILE AGENT → MOVIDO A SEMANA 6

**Decisión tomada:** el File Agent (notas, tareas, recordatorios) se implementa en
**Semana 6** junto con el Voice Agent mejorado, para no recargar la Semana 5.

```
Razón:
✅ Notas/tareas ya funcionan en el orquestador (desde Semana 4)
✅ Moverlas a un agente es refactor de código existente, no funcionalidad nueva
✅ La Semana 5 se concentra en 3 agentes NUEVOS hechos con calidad y tests
✅ En Semana 6: agents/file.py + Voice mejorado + email/calendar si aplica
```

Las intenciones `take_notes`, `create_task`, `read_file`, `list_folder`,
`reminder_set` siguen como "en desarrollo" esta semana (sin regresión).

---

## 🔌 FASE 4 — INTEGRACIÓN ORCHESTRATOR (Viernes-Sábado)

### Cambios en `orchestrator/orchestrator.py`
```
✅ _execute_intent delega en agents/<tipo>.process() según el AgentType
   del mapeo en decision.py (ya existe agent_map)
✅ Los 3 agentes se inicializan en run() y aparecen en _get_module_list()
✅ _execute_intent mantiene fallback: si el agente no está activo → "en desarrollo"
✅ Probar las intenciones antes "en desarrollo" → ahora responden real
```

### Mapeo intención → agente (base para `_execute_intent`)
| Agente | Intenciones |
|--------|-------------|
| system_agent | system_control, open_application, take_screenshot, volume_control, open_folder, empty_trash, lock_session |
| web_agent | search_info, news_query, weather_query, get_exchange_rate, crypto_price, check_investments |
| dialog_agent | tell_joke, change_name, help_query, smalltalk, translate_text |
| (Semana 6) | file_agent: take_notes, create_task, read_file, list_folder, reminder_set |
| (Semanas 6+) | email, calendar, luces, saldo, transferencias, llamadas |

---

## 🧪 FASE 5 — TESTS Y CIERRE (Domingo)

### Tests nuevos (`jarvis/tests/`)
```
test_agents_framework.py   # registry: registrar/obtener/listar/start/stop
test_system_agent.py       # acciones simuladas (mock de os.startfile/shutdown)
test_web_agent.py          # search_info, clima Open-Meteo, cripto (mock de requests)
test_dialog_agent.py       # help_query genera manual; fallback sin API key
test_orchestrator_agents.py# orquestador delega en agentes (stub, sin __init__)
```

### Verificación end-to-end
- [ ] `python -m pytest jarvis/tests -q` → suite completa verde
- [ ] Smoke: `process_input` de una intención antes "en desarrollo" → responde real
- [ ] Cobertura nuevos módulos ≥ 90%

---

## 📦 ENTREGABLES SEMANA 5

```
jarvis/agents/
├── __init__.py          (exports + registry)
├── base.py              (AgentBase)
├── registry.py          (AgentRegistry)
├── factory.py           (crear por AgentType)
├── system.py            (SystemAgent)
├── web.py               (WebAgent)
└── dialog.py            (DialogAgent)

jarvis/tests/
├── test_agents_framework.py
├── test_system_agent.py
├── test_web_agent.py
├── test_dialog_agent.py
└── test_orchestrator_agents.py

WEEK5_PLAN.md            (este documento)
WEEK5_TASKS.md           (checklist de progreso, como Semana 4)
```

---

## 📈 MÉTRICAS ESPERADAS

| Métrica | Meta | Estado |
|---------|------|--------|
| Agentes implementados | 3 (System, Web, Dialog) | 📝 |
| Intenciones con acción real | +10 (de 23 → ~33) | 📝 |
| Intenciones "en desarrollo" | ~19 | 📝 |
| Framework tests | 12+ | 📝 |
| Suite total pytest | 90+ | 📝 |
| Cobertura módulos nuevos | 90%+ | 📝 |
| Código nuevo | 1,200-1,500 líneas | 📝 |

---

## 🔁 COMMITS PLANIFICADOS (5)

1. `🏗️ Semana 5: Fase 0 framework de agentes (registry)`
2. `🖥️ Semana 5: Fase 1 System Agent`
3. `🌐 Semana 5: Fase 2 Web Agent (Open-Meteo + CoinGecko)`
4. `💬 Semana 5: Fase 3 Dialog Agent (Gemini + fallback)`
5. `✅ Semana 5: Fase 4-5 integración orquestador + tests + docs`

---

## 🎯 CRITERIO DE TERMINADO

- [ ] `jarvis/agents/` con 3 agentes reales (System, Web, Dialog)
- [ ] Las ~10 intenciones objetivo pasan de "en desarrollo" a acción real
- [ ] Clima (Open-Meteo) y cripto (CoinGecko) responden con datos reales sin key
- [ ] Dialog responde con Gemini si hay key; degrada a plantillas si no la hay
- [ ] Los agentes se inicializan con el orquestador y aparecen en get_status()
- [ ] Fallback elegante: sin API key / sin internet → degradación, no crash
- [ ] Suite completa verde (90+ tests) y cobertura ≥ 90% en módulos nuevos
- [ ] `git push` final (con confirmación explícita del usuario)

---

## ✅ DECISIONES TOMADAS (confirmadas)

| # | Decisión | Elección |
|---|----------|----------|
| 1 | Dialog Agent | **Gemini API opcional** con degradación elegante a plantillas |
| 2 | Web Agent | **Open-Meteo + CoinGecko integrados** (gratis, sin keys) |
| 3 | File Agent | **Movido a Semana 6** (junto a Voice mejorado) |
| 4 | Email/Calendario | **Semana 6+** (requieren OAuth) |

---

## 🎊 DESPUÉS DE SEMANA 5

**JARVIS será:**

```
✅ Ejecutor real
   └─ System, Web y Dialog agentes activos

✅ Autónomo en el PC
   └─ Abre, apaga, busca, responde y sabe el clima/cripto

✅ Preparado para Semana 6
   └─ File Agent, Voice mejorado, email, calendar
```

---

**Commits esperados:** 5
**Líneas totales:** ~1,200-1,500
**Tiempo estimado:** 1 semana intensiva
**Dificultad:** ⭐⭐⭐ (Intermedia)

**¿VAMOS? 🚀**
