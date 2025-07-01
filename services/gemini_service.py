import os
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv('API_KEY')
if not API_KEY:
    print("Advertencia: La variable de entorno API_KEY no está configurada.")
else:
    genai.configure(api_key=API_KEY)

# Modelo de solo texto
text_model = genai.GenerativeModel('gemini-1.5-flash')

async def suggest_icebreaker(user_name: str, user_interests: list[str] = [], attempt_number: int = 1) -> str:
    if not API_KEY:
        return "Lo siento, la función de IA no está disponible."

    prompt = f"""Eres un asistente de citas experto en iniciar conversaciones con un toque DIVERTIDO y COQUETO. Ayuda a generar un rompehielos para {user_name}.
Los intereses conocidos de {user_name} son: {', '.join(user_interests) if user_interests else 'ninguno'}. Intenta referenciar sutilmente un interés si es posible.
Genera una sugerencia CORTA (máx 5 palabras). No incluyas saludos. Intento #{attempt_number}.
Ejemplos: "¿Escapada o travesura?", "¿Cenas o me cocinas?", "¿Problemas o diversión?"
Genera UN rompehielos. Solo el texto del rompehielos:"""

    try:
        response = await text_model.generate_content_async(prompt)
        return response.text.strip()
    except Exception as e:
        print(f"Error en Gemini API: {e}")
        return "Error al generar sugerencia."

async def suggest_chat_replies(last_message_text: str, own_name: str, chat_partner_name: str) -> list[str]:
    if not API_KEY:
        return ["La IA no está disponible."]

    prompt = f"""Contexto: {chat_partner_name} dijo, "{last_message_text}".
Tarea para {own_name}: 2 respuestas muy cortas (máx 4 palabras cada una), que sean DIVERTIDAS y COQUETAS.
Salida: Solo array JSON de strings.
Ejemplo de salida para "Estoy aburrido/a": ["¿Te aburro yo?", "Tengo ideas traviesas..."]
Genera el array JSON:"""

    try:
        response = await text_model.generate_content_async(
            prompt,
            generation_config=genai.types.GenerationConfig(
                response_mime_type="application/json"
            )
        )
        # La API a menudo envuelve el JSON en ```json ... ```, hay que limpiarlo
        json_text = response.text.strip().replace('```json', '').replace('```', '').strip()
        import json
        return json.loads(json_text)
    except Exception as e:
        print(f"Error en Gemini API para respuestas: {e}")
        return ["Error al generar respuestas."]