import streamlit as st
from google import genai

st.title("💖 Pacar Virtual-mu")

api_key = st.text_input("Masukkan Google Gemini API Key:", type="password")

if api_key:
  if st.button("Mulai Ngobrol"):
    try:
      # Menggunakan model terbaru yang didukung oleh library google-genai
      client = genai.Client(api_key=api_key)
      response = client.models.generate_content(
          model="gemini-2.0-flash",
          contents=(
              "Katakan halo dengan manis sebagai pacar virtual yang manja!"
          ),
      )
      st.success(response.text)
    except Exception as e:
      st.error(f"Error: {e}")
      
