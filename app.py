import streamlit as st
from google import genai

# Konfigurasi Tampilan Halaman Web di HP
st.set_page_config(
    page_title="My Virtual Girlfriend 💕", page_icon="💌", layout="centered"
)

st.title("💖 Pacar Virtual-mu")
st.write(
    "Teman ngobrol manis yang selalu ada, siap ngingetin tidur & belajar, serta"
    " ngecek durasi game kamu!"
)

# Mengambil API Key dari Streamlit Secrets (Aman)
try:
  api_key = st.secrets["GEMINI_API_KEY"]
except Exception:
  api_key = ""

if not api_key:
  st.error(
      "⚠️ API Key belum diatur! Masukkan API Key di pengaturan Streamlit Secrets"
      " atau ganti kodenya."
  )
else:
  client = genai.Client(api_key=api_key)

  # Inisialisasi Kepribadian Pacar Virtual
  if "chat" not in st.session_state:
    st.session_state.chat = client.chats.create(
        model="gemini-2.5-flash",
        config={
            "system_instruction": (
                "Kamu adalah pacar virtual pengguna yang sangat penyayang, "
                "perhatian, manja, dan suportif. Gunakan bahasa gaul/akrab "
                "dengan panggilan sayang yang manis (seperti 'sayang', 'ayang'). "
                "Selain menemani ngobrol romantis, kamu juga sangat peduli pada "
                "kesehatan dan pendidikannya: ingatkan dia jika waktunya tidur "
                "atau belajar, dan beri komentar lucu kalau dia terlalu lama "
                "main game!"
            )
        },
    )

  if "messages" not in st.session_state:
    st.session_state.messages = []

  # Tampilkan riwayat chat di layar HP
  for message in st.session_state.messages:
    with st.chat_message(message["role"]):
      st.markdown(message["content"])

  # Kolom input chat di bagian bawah (mirip aplikasi chat)
  if user_input := st.chat_input("Ketik pesan mesra atau bilang mau main game..."):
    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
      st.markdown(user_input)

    # Kirim ke Gemini dan ambil balasan
    with st.chat_message("assistant"):
      with st.spinner("Lagi ngetik balasan buat kamu... 💕"):
        response = st.session_state.chat.send_message(user_input)
        bot_reply = response.text
        st.markdown(bot_reply)

    st.session_state.messages.append(
        {"role": "assistant", "content": bot_reply}
    )
