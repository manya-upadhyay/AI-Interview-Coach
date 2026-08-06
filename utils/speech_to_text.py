import speech_recognition as sr

def recognize_speech():
    recognizer = sr.Recognizer()

    try:
        with sr.Microphone() as source:

            print("🎤 Speak now...")
            recognizer.adjust_for_ambient_noise(source, duration=2)
            print("🎤 Start speaking after this message...")

            audio = recognizer.listen(
                source,
                timeout=15,
                phrase_time_limit=30
            )

        text = recognizer.recognize_google(audio, language="en-IN")
        print("Recognized:", repr(text))
        return text

    except sr.WaitTimeoutError:
        print("No speech detected.")
        return ""

    except sr.UnknownValueError:
        print("Could not understand audio.")
        return ""

    except sr.RequestError as e:
        print("Google Speech API Error:", e)
        return ""

    except Exception as e:
        print("Error:", e)
        return ""