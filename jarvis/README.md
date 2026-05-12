# 🤖 Jarvis - Asistente de Voz en Python

Un asistente de voz inteligente en español que puede realizar múltiples tareas.

## ✨ Características

- 🎤 Reconocimiento de voz en español
- 🔊 Síntesis de voz (text-to-speech)
- 🕐 Consultar hora y fecha
- 📚 Buscar información en Wikipedia
- 🎵 Reproducir música
- 🌐 Abrir navegadores (YouTube, Google)
- 📸 Tomar capturas de pantalla
- 😂 Contar chistes
- 🖥️ Control del sistema (apagar, reiniciar)
- 📝 Sistema de nombre personalizado

## 📦 Instalación

### 1. Clonar el repositorio
```bash
git clone https://github.com/gonza-hash89/My-proyecto-python.git
cd My-proyecto-python/jarvis
```

### 2. Instalar dependencias
```bash
pip install -r requirements.txt
```

**Nota importante:** En Windows, también necesitas instalar PyAudio:
```bash
pip install pipwin
pipwin install pyaudio
```

## 🚀 Uso

```bash
python jarvis.py
```

### Comandos disponibles:

| Comando | Función |
|---------|----------|
| "hora" | Dice la hora actual |
| "fecha" | Dice la fecha actual |
| "wikipedia [tema]" | Busca en Wikipedia |
| "reproducir música" | Reproduce una canción |
| "pon música" | Reproduce una canción |
| "abrir youtube" | Abre YouTube |
| "abrir google" | Abre Google |
| "cambia tu nombre" | Cambia el nombre de Jarvis |
| "captura de pantalla" | Toma una screenshot |
| "cuéntame un chiste" | Cuenta un chiste |
| "apagar" | Apaga el sistema |
| "reiniciar" | Reinicia el sistema |
| "desconectar" o "salir" | Cierra Jarvis |

## 🔧 Mejoras implementadas

✅ **Ahora Jarvis habla en TODOS los comandos**
✅ **Mejor manejo de errores**
✅ **Docstrings en todas las funciones**
✅ **Archivo requirements.txt para fácil instalación**
✅ **Respuestas más naturales**

## ⚙️ Configuración

### Cambiar voz (Masculina/Femenina):
En `jarvis.py`, línea 10:
```python
engine.setProperty('voice', voices[1].id)  # 1 = Femenina, 0 = Masculina
```

### Cambiar velocidad del habla:
```python
engine.setProperty('rate', 150)  # Velocidad (0-300)
```

### Cambiar volumen:
```python
engine.setProperty('volume', 1)  # Volumen (0-1)
```

## 🐛 Solución de problemas

### "No se escucha el micrófono"
- Verifica que tu micrófono esté conectado
- Comprueba los permisos de micrófono en Windows

### "Error con PyAudio"
```bash
pipwin install pyaudio
```

### "No reconoce comandos"
- Habla claro y lentamente
- Asegúrate de estar en un lugar sin mucho ruido

## 📝 Notas

- El nombre de Jarvis se guarda en `assistant_name.txt`
- Las capturas se guardan en `Documentos/Pictures/captura.png`
- Requiere conexión a internet para Wikipedia y reconocimiento de voz

## 🚀 Próximas mejoras

- [ ] Integración con WhatsApp
- [ ] Control de correo electrónico
- [ ] Automatización de tareas
- [ ] Base de datos de respuestas
- [ ] Interfaz gráfica

## 👨‍💻 Autor

**gonza-hash89** - 2026

## 📄 Licencia

Este proyecto está bajo licencia libre.
