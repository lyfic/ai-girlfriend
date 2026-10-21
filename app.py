import streamlit as st
from google import genai

st.title("🧪 Tes Koneksi Gemini")

api_key = st.text_input("Masukkan API Key:", type="password")

if api_key:
  if st.button("Kirim Tes"):
    try:
      client = genai.Client(api_key=api_key)
      response = client.models.generate_content(
          model="gemini-1.5-flash",
          contents="Halo, balas dengan kata 'Berhasil'",
      )
      st.success(response.text)
    except Exception as e:
      st.error(f"Detail Error: {e}")
      
