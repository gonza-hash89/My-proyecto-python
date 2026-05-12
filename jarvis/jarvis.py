import pyttsx3
import datetime
import speech_recognition as sr
import wikipedia
import webbrowser as wb
import os
import random
import pyautogui
import pyjokes

engine = pyttsx3.init()
voices = engine.getProperty('voices')
engine.setProperty('voice', voices[1].id)
engine.setProperty('rate', 150)
engine.setProperty('volume', 1)


def speak(audio) -> None:
    """Hace que Jarvis hable"""
    engine.say(audio)
    engine.runAndWait()


def time() -> None:
    """Dice la hora actual"""
    current_time = datetime.datetime.now().strftime("%I:%M:%S %p")
    speak("La hora actual es")
    speak(current_time)
    print("La hora actual es", current_time)


def date() -> None:
    """Dice la fecha actual"""
    now = datetime.datetime.now()
    speak("La fecha actual es")
    speak(f"{now.day} de {now.strftime('%B')} de {now.year}")
    print(f"La fecha actual es {now.day}/{now.month}/{now.year}")


def wishme() -> None:
    """Saludo inicial según la hora"""
    speak("Bienvenido de nuevo, señor!")
    print("Bienvenido de nuevo, señor!")

    hour = datetime.datetime.now().hour
    if 4 <= hour < 12:
        speak("Buenos días!")
        print("Buenos días!")
    elif 12 <= hour < 16:
        speak("Buenas tardes!")
        print("Buenas tardes!")
    elif 16 <= hour < 24:
        speak("Buenas noches!")
        print("Buenas noches!")
    else:
        speak("Buenas noches, hasta mañana.")

    assistant_name = load_name()
    speak(f"{assistant_name} a su servicio. ¿En qué le puedo ayudar?")
    print(f"{assistant_name} a su servicio. ¿En qué le puedo ayudar?")


def screenshot() -> None:
    """Toma una captura de pantalla"""
    img = pyautogui.screenshot()
    img_path = os.path.expanduser("~\\Pictures\\captura.png")
    img.save(img_path)
    speak(f"Captura guardada en {img_path}.")
    print(f"Captura guardada en {img_path}.")


def takecommand() -> str:
    """Escucha y reconoce comando de voz"""
    r = sr.Recognizer()
    with sr.Microphone() as source:
        print("Escuchando...")
        r.pause_threshold = 1

        try:
            audio = r.listen(source, timeout=5)
        except sr.WaitTimeoutError:
            speak("Tiempo agotado. Por favor intente de nuevo.")
            return None

    try:
        print("Reconociendo...")
        query = r.recognize_google(audio, language="es-ES")
        print(query)
        return query.lower()
    except sr.UnknownValueError:
        speak("Lo siento, no entendí eso.")
        return None
    except sr.RequestError:
        speak("El servicio de reconocimiento de voz no está disponible.")
        return None
    except Exception as e:
        speak(f"Ocurrió un error: {e}")
        print(f"Error: {e}")
        return None


def play_music(song_name=None) -> None:
    """Reproduce música de la carpeta Música"""
    song_dir = os.path.expanduser("~\\Music")
    songs = os.listdir(song_dir)

    if song_name:
        songs = [song for song in songs if song_name.lower() in song.lower()]

    if songs:
        song = random.choice(songs)
        os.startfile(os.path.join(song_dir, song))
        speak(f"Reproduciendo {song}.")
        print(f"Reproduciendo {song}.")
    else:
        speak("No se encontró ninguna canción.")
        print("No se encontró ninguna canción.")


def set_name() -> None:
    """Permite cambiar el nombre de Jarvis"""
    speak("¿Cómo le gustaría llamarme?")
    name = takecommand()
    if name:
        with open("assistant_name.txt", "w") as file:
            file.write(name)
        speak(f"De acuerdo, a partir de ahora me llamaré {name}.")
        print(f"Nombre cambiado a: {name}")
    else:
        speak("Lo siento, no pude escuchar eso.")


def load_name() -> str:
    """Carga el nombre de Jarvis desde archivo"""
    try:
        with open("assistant_name.txt", "r") as file:
            return file.read().strip()
    except FileNotFoundError:
        return "Jarvis"


def search_wikipedia(query):
    """Busca información en Wikipedia"""
    try:
        speak("Buscando en Wikipedia...")
        wikipedia.set_lang("es")
        result = wikipedia.summary(query, sentences=2)
        speak(result)
        print(result)
    except wikipedia.exceptions.DisambiguationError:
        speak("Hay varios resultados. Por favor sea más específico.")
        print("Error: Múltiples resultados encontrados")
    except Exception:
        speak("No encontré nada en Wikipedia.")
        print("Error: No se encontró información")


if __name__ == "__main__":
    wishme()

    while True:
        query = takecommand()
        if not query:
            continue

        if "hora" in query:
            time()

        elif "fecha" in query:
            date()

        elif "wikipedia" in query:
            query = query.replace("wikipedia", "").strip()
            search_wikipedia(query)

        elif "reproducir música" in query or "pon música" in query:
            song_name = query.replace("reproducir música", "").replace("pon música", "").strip()
            play_music(song_name)
            speak("Música activada.")

        elif "abrir youtube" in query:
            speak("Abriendo YouTube.")
            wb.open("youtube.com")

        elif "abrir google" in query:
            speak("Abriendo Google.")
            wb.open("google.com")

        elif "cambia tu nombre" in query:
            set_name()

        elif "captura de pantalla" in query:
            screenshot()
            speak("Captura de pantalla tomada, por favor revísela.")

        elif "cuéntame un chiste" in query or "dime un chiste" in query:
            joke = pyjokes.get_joke(language="es")
            speak(joke)
            print(joke)

        elif "apagar" in query:
            speak("Apagando el sistema, hasta luego!")
            os.system("shutdown /s /f /t 1")
            break

        elif "reiniciar" in query:
            speak("Reiniciando el sistema, por favor espere!")
            os.system("shutdown /r /f /t 1")
            break

        elif "desconectar" in query or "salir" in query:
            speak("Desconectándome. ¡Que tenga un buen día!")
            break

        else:
            speak("Comando no reconocido. Por favor intente de nuevo.")
            print("Comando no reconocido")
