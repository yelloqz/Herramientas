import os
import streamlit as st
from google import genai

st.set_page_config(page_title="Gemini 3.8 Flash Chat", page_icon="🤖", layout="centered")

st.title("🤖 Chatbot con Gemini 3.8 Flash")
st.caption("Chat unimodal básico utilizando la API de Interacciones (client.interactions.create).")

# --- Barra lateral para configuración ---
with st.sidebar:
    st.header("Configuración")
    api_key = st.text_input(
        "Gemini API Key",
        type="password",
        value="",
        help="Obtén tu clave en Google AI Studio"
    )

    if st.button("Limpiar conversación", use_container_width=True):
        st.session_state.messages = []
        st.session_state.previous_interaction_id = None
        st.rerun()

# Validar que exista la API Key
if not api_key:
    st.info("Por favor, ingresa tu API Key en la barra lateral para continuar.")
    st.stop()

# Instanciar el cliente
client = genai.Client(api_key=api_key)

# --- Estado de sesión de Streamlit ---
if "messages" not in st.session_state:
    st.session_state.messages = []

if "previous_interaction_id" not in st.session_state:
    st.session_state.previous_interaction_id = None

# Mostrar el historial en pantalla
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# --- Captura y procesamiento del mensaje ---
if prompt := st.chat_input("Escribe tu consulta..."):
    # 1. Mostrar y guardar el mensaje del usuario
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # 2. Generar respuesta con client.interactions.create
    with st.chat_message("assistant"):
        try:
            with st.spinner("Pensando..."):
                params = {
                    "model": "gemini-3.8-flash",
                    "input": prompt,
                }
                if st.session_state.previous_interaction_id:
                    params["previous_interaction_id"] = st.session_state.previous_interaction_id

                interaction = client.interactions.create(**params)
                bot_response = interaction.output_text
                st.session_state.previous_interaction_id = interaction.id
                st.markdown(bot_response)
                
                st.session_state.messages.append({"role": "assistant", "content": bot_response})

        except Exception as e:
            st.error(f"Error de conexión con la API de Gemini: {e}")

    # 3. Guardar respuesta en el historial visual
    st.session_state.messages.append({"role": "assistant", "content": bot_response})