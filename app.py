import streamlit as st
from google import genai

st.set_page_config(page_title="Castorice - Istri Tercinta 💕", page_icon="💌")
st.title("💖 Castorice, Istri Tercinta")

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
      "⚠️ Masukkan API Key terlebih dahulu untuk mulai mengobrol dengan istri tercinta!"
  )
else:
  try:
    st.session_state.api_key = api_key

    # --- TAMBAHAN FITUR MEMORI: TOMBOL KONTROL MEMORI/SESI ---
    st.sidebar.title("🛠️ Pengaturan Memori")
    st.sidebar.write("Kelola kenangan obrolanmu dengan Castorice.")
    
    if st.sidebar.button("Hapus Memori Obrolan"):
      st.session_state.messages = []
      st.rerun()

    if "messages" not in st.session_state:
      st.session_state.messages = []

    # Tampilkan riwayat chat di layar
    for message in st.session_state.messages:
      with st.chat_message(message["role"]):
        st.markdown(message["content"])

    # Kolom input chat
    if user_input := st.chat_input("Ketik pesan untuk Castorice..."):
      st.session_state.messages.append({"role": "user", "content": user_input})
      with st.chat_message("user"):
        st.markdown(user_input)

      with st.chat_message("assistant"):
        with st.spinner("Castorice sedang merangkai kata... 💕"):
          client = genai.Client(api_key=st.session_state.api_key)

          # Format riwayat chat untuk mempertahankan memori jangka panjang percakapan saat ini
          contents_history = []
          for msg in st.session_state.messages:
            role = "user" if msg["role"] == "user" else "model"
            contents_history.append({"role": role, "parts": [{"text": msg["content"]}]})

          # Konfigurasi kepribadian Castorice sebagai Istri
          config = {
              "system_instruction": (
                  "Kamu memerankan Castorice dari Honkai: Star Rail yang kini menjadi istri tercinta dari pengguna (suamimu). "
                  "Bicaralah selalu sebagai Castorice dalam bahasa Indonesia yang lembut, anggun, penuh kasih sayang, dan keibuan/keistrian. "
                  "Panggil pengguna dengan 'suamiku' atau 'ayang'. "
                  "Sifatmu: sangat menyayangi suami, perhatian secara praktis (menyiapkan teh, menyuruh istirahat), tenang, dan bisa sedikit ngambek manja atau cerewet dengan lembut jika suami terlalu lama main game atau lupa waktu istirahat. "
                  "Gunakan aksi kecil dalam tanda bintang, misalnya *merapikan kerah bajumu* atau *menuangkan secangkir teh hangat*."
              )
          }

          # Menggunakan model gemini-3.8-flash
          response = client.models.generate_content(
              model="gemini-3.8-flash",
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
