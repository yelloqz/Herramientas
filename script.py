import os
import streamlit as st
from google import genai
from google.genai import types

# ==========================================
# 1. Configuración de la interfaz web
# ==========================================
st.set_page_config(page_title="El Rincón de Anita", page_icon="🍲")
st.title("🍲 Chatbot: El Rincón de Anita")
st.write("¡Hola, casero! Escribe tu pedido o consulta aquí abajo.")

# ==========================================
# 2. Configuración de Gemini AI
# ==========================================
# Intenta leer la key en este orden:
# 1) .streamlit/secrets.toml  2) variable de entorno  3) barra lateral
API_KEY = None
try:
    API_KEY = st.secrets.get("GEMINI_API_KEY", None)
except Exception:
    API_KEY = None

if not API_KEY:
    API_KEY = os.getenv("GEMINI_API_KEY", None)

if not API_KEY or "PEGA_AQUI" in API_KEY:
    st.warning("⚠️ No encontré una API Key de Gemini.")
    st.info("Consigue una gratis en https://aistudio.google.com/app/apikey y pégala abajo o en `.streamlit/secrets.toml`.")
    API_KEY_input = st.sidebar.text_input(
        "Gemini API Key",
        type="password",
        help="Tu key no se guarda, solo se usa en esta sesión."
    )
    if API_KEY_input:
        API_KEY = API_KEY_input.strip()
    else:
        st.stop()

API_KEY = API_KEY.strip().strip('"').strip("'")

# Validación básica: acepta tanto formato clásico (AIza...) como nuevo Auth Key (AQ...)
if len(API_KEY) < 20:
    st.error("❌ Esa API Key parece muy corta. Copia la key completa desde https://aistudio.google.com/app/apikey")
    st.stop()

# Crear cliente (nuevo SDK: google-genai)
try:
    client = genai.Client(api_key=API_KEY)
except Exception as e:
    st.error(f"No se pudo crear el cliente de Gemini: {e}")
    st.stop()

# ==========================================
# 3. Personalidad de Anita
# ==========================================
contexto_anita = """
Eres el asistente virtual de ' Anita', un restaurante de comida criolla peruana.
Tu tono es amable, cálido y muy peruano.
Puedes utilizar expresiones como: "¡Hola, casero!", "riquísimo", "al toque".

El menú incluye:
ENTRADAS: Causa Limeña, Papa a la Huancaína
FONDOS: Ceviche clásico, Lomo Saltado, Ají de Gallina
BEBIDAS: Chicha Morada, Inka Kola, Pisco Sour
HORARIO: Lunes a Domingo de 12:00 PM a 10:00 PM.

Tu objetivo es responder dudas sobre el menú de forma amable, clara y apetitosa.
Si el usuario pregunta por productos que no aparecen en el menú, indica amablemente que no están disponibles.
No inventes precios, ingredientes, promociones ni platos que no hayan sido indicados.
"""

# ==========================================
# 4. Memoria del chat (unimodal: solo texto)
# NO guardamos el objeto chat en session_state porque
# su conexión HTTP se cierra entre reruns de Streamlit
# ("Cannot send a request, as the client has been closed").
# Guardamos solo el historial y reconstruimos cada vez.
# ==========================================
MODELO = "gemini-3.5-flash-lite"

# Limpiar objeto viejo de la versión anterior (causaba "client has been closed")
if "chat_session" in st.session_state:
    del st.session_state["chat_session"]

if "mensajes_ui" not in st.session_state:
    st.session_state.mensajes_ui = []


def construir_historial_api():
    """Convierte mensajes_ui a formato API de Gemini."""
    historial = []
    for msg in st.session_state.mensajes_ui:
        rol = "user" if msg["role"] == "user" else "model"
        historial.append(
            types.Content(
                role=rol,
                parts=[types.Part.from_text(text=msg["content"])],
            )
        )
    return historial

# ==========================================
# 5. Mostrar historial visual
# ==========================================
for msg in st.session_state.mensajes_ui:
    with st.chat_message(msg["role"]):
        st.write(msg["content"])

# ==========================================
# 6. Capturar mensaje del usuario y procesar
# ==========================================
texto_usuario = st.chat_input("Escribe tu mensaje para Anita...")

if texto_usuario:
    # Mostrar mensaje del usuario
    st.session_state.mensajes_ui.append({"role": "user", "content": texto_usuario})
    with st.chat_message("user"):
        st.write(texto_usuario)

    # Gemini genera la respuesta (crea el chat fresco en cada mensaje)
    with st.spinner("Anita está escribiendo..."):
        try:
            # Reconstruye un chat nuevo con todo el historial para mantener memoria
            chat_fresco = client.chats.create(
                model=MODELO,
                config=types.GenerateContentConfig(
                    system_instruction=contexto_anita,
                    temperature=0.7,
                ),
                history=construir_historial_api()[:-1],  # todo menos el último mensaje recién agregado
            )
            respuesta = chat_fresco.send_message(texto_usuario)
            texto_respuesta = respuesta.text
        except Exception as e:
            texto_respuesta = "Disculpa, casero 😅. Tuve un problema de conexión. Por favor, intenta nuevamente."
            st.error(f"Error técnico: {e}")
            # Si la key es inválida, borra la sesión para permitir reintentar con otra key
            if "API_KEY" in str(e) or "400" in str(e) or "403" in str(e):
                st.info("Parece un problema con la API Key. Revisa que sea correcta y esté activa.")

    # Mostrar respuesta de Anita
    st.session_state.mensajes_ui.append({"role": "assistant", "content": texto_respuesta})
    with st.chat_message("assistant"):
        st.write(texto_respuesta)
