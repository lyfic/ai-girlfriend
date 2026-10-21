import streamlit as st
from google import genai

st.set_page_config(page_title="My Virtual Girlfriend 💕", page_icon="💌")
st.title("Kegagalan")

# Cek API Key dari Secrets Streamlit, jika kosong sediakan input manual
api_key = ""
if "GEMINI_API_KEY" in st.secrets:
  api_key = st.secrets["GEMINI_API_KEY"]

if not api_key:
  api_key = st.text_input(
      "Masukkan Google Gemini API Key kamu:", type="password"
  )

if not api_key:
  st.warning(
      "⚠️ Masukkan API Key terlebih dahulu untuk mulai ngobrol dengan ayang!"
  )
else:
  try:
    # Simpan API key di session state agar aman
    st.session_state.api_key = api_key

    if "messages" not in st.session_state:
      st.session_state.messages = []

    # Tampilkan riwayat chat di layar
    for message in st.session_state.messages:
      with st.chat_message(message["role"]):
        st.markdown(message["content"])

    # Kolom input chat
    if user_input := st.chat_input("Ketik pesan mesra atau bilang mau main game..."):
      st.session_state.messages.append({"role": "user", "content": user_input})
      with st.chat_message("user"):
        st.markdown(user_input)

      with st.chat_message("assistant"):
        with st.spinner("Lagi ngetik balasan buat kamu... 💕"):
          # Buat client baru setiap ada request agar koneksi tidak tertutup (closed)
          client = genai.Client(api_key=st.session_state.api_key)

          # Ubah riwayat chat Streamlit ke format yang bisa dibaca Gemini
          contents_history = []
          for msg in st.session_state.messages:
            role = "user" if msg["role"] == "user" else "model"
            contents_history.append({"role": role, "parts": [{"text": msg["content"]}]})

          # Konfigurasi kepribadian pacar virtual
          config = {
              "system_instruction": (
                  "Kamu adalah pacar virtual pengguna yang sangat penyayang, "
                  "perhatian, manja, dan suportif. Gunakan bahasa gaul/akrab "
                  "dengan panggilan sayang (seperti 'sayang', 'ayang'). Ingatkan "
                  "dia jika waktunya tidur atau belajar, dan komentari kalau "
                  "dia terlalu lama main game!"
              )
          }

          # Kirim seluruh riwayat percakapan agar konteksnya tetap nyambung
          response = client.models.generate_content(
              model="gemini-2.5-flash",
              contents=contents_history,
              config=config,
          )

          bot_reply = response.text
          st.markdown(bot_reply)

      st.session_state.messages.append(
          {"role": "assistant", "content": bot_reply}
      )

  except Exception as e:
    st.error(f"Terjadi kesalahan pada koneksi API: {e}")
