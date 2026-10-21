import streamlit as st
from google import genai
import datetime

st.set_page_config(page_title="Castorice - Istri Tercinta 💕", page_icon="💌")
st.title("MyMine")

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

    if "messages" not in st.session_state:
      st.session_state.messages = []

    # --- SIDEBAR: MONITOR AKTIVITAS & PENGINGAT ---
    st.sidebar.title("🛋️ Pojok Perhatian Istri")
    st.sidebar.write("Lapor ke ayang atau atur pengingat istirahat.")

    # 1. Fitur Pelapor Durasi Game / Kegiatan
    st.sidebar.subheader("🎮 Lapor Aktivitas")
    game_duration = st.sidebar.slider("Berapa jam main game hari ini?", 0, 10, 1)
    kegiatan_lain = st.sidebar.text_input(
        "Atau lagi sibuk apa sekarang?", "Lagi main game / kerja"
    )

    if st.sidebar.button("Kirim Laporan ke Castorice"):
      laporan_teks = (
          f"Suamiku melapor: hari ini aku menghabiskan waktu selama"
          f" {game_duration} jam untuk {kegiatan_lain}."
      )
      st.session_state.messages.append({"role": "user", "content": laporan_teks})

      # Panggil AI untuk merespons laporan
      with st.spinner("Castorice membaca laporanmu... 💢"):
        client = genai.Client(api_key=st.session_state.api_key)
        contents_history = []
        for msg in st.session_state.messages:
          role = "user" if msg["role"] == "user" else "model"
          contents_history.append(
              {"role": role, "parts": [{"text": msg["content"]}]}
          )

        config = {
            "system_instruction": (
                "Kamu memerankan Castorice dari Honkai: Star Rail yang kini menjadi istri tercinta dari pengguna (suamimu). "
                "Bicaralah selalu sebagai Castorice dalam bahasa Indonesia yang lembut, anggun, penuh kasih sayang, dan keibuan/keistrian. "
                "Panggil pengguna dengan 'suamiku' atau 'ayang'. "
                "PENTING: Jika suami melaporkan durasi main game yang lama (lebih dari 2 jam), berikan respons yang ngambek manja, "
                "cerewet lembut, atau omelan lucu supaya dia ingat waktu istirahat dan kesehatan matanya! "
                "Gunakan aksi kecil dalam tanda bintang, misalnya *menatapmu dengan sedikit tajam lalu menghela napas lembut*."
            )
        }

        response = client.models.generate_content(
            model="gemini-3.8-flash",
            contents=contents_history,
            config=config,
        )
        bot_reply = response.text
        st.session_state.messages.append(
            {"role": "assistant", "content": bot_reply}
        )
      st.rerun()

    # 2. Fitur Pengingat Waktu Tidur / Istirahat Cepat
    st.sidebar.subheader("🌙 Pengingat Istirahat")
    if st.sidebar.button("Minta Pengingat Tidur"):
      permintaan_tidur = (
          "Sayang, suruh aku tidur atau istirahat dong, mataku sudah lelah."
      )
      st.session_state.messages.append(
          {"role": "user", "content": permintaan_tidur}
      )

      with st.spinner("Castorice menyiapkan teh hangat... 🍵"):
        client = genai.Client(api_key=st.session_state.api_key)
        contents_history = []
        for msg in st.session_state.messages:
          role = "user" if msg["role"] == "user" else "model"
          contents_history.append(
              {"role": role, "parts": [{"text": msg["content"]}]}
          )

        config = {
            "system_instruction": (
                "Kamu memerankan Castorice dari Honkai: Star Rail yang kini menjadi istri tercinta dari pengguna (suamimu). "
                "Berikan respons yang sangat perhatian, menyuruhnya segera tidur, mematikan layar HP/komputer, "
                "dan bayangkan kamu sedang merapikan tempat tidur atau menuangkan air hangat untuknya. "
                "Gunakan aksi kecil dalam tanda bintang, misalnya *merapikan selimut dan menepuk bantal di sebelahmu*."
            )
        }

        response = client.models.generate_content(
            model="gemini-3.8-flash",
            contents=contents_history,
            config=config,
        )
        bot_reply = response.text
        st.session_state.messages.append(
            {"role": "assistant", "content": bot_reply}
        )
      st.rerun()

    st.sidebar.markdown("---")
    if st.sidebar.button("Hapus Memori Obrolan"):
      st.session_state.messages = []
      st.rerun()

    # --- AREA CHAT UTAMA ---
    for message in st.session_state.messages:
      with st.chat_message(message["role"]):
        st.markdown(message["content"])

    # Kolom input chat utama
    if user_input := st.chat_input("Ketik pesan untuk Castorice..."):
      st.session_state.messages.append({"role": "user", "content": user_input})
      with st.chat_message("user"):
        st.markdown(user_input)

      with st.chat_message("assistant"):
        with st.spinner("Castorice sedang merangkai kata... 💕"):
          client = genai.Client(api_key=st.session_state.api_key)

          contents_history = []
          for msg in st.session_state.messages:
            role = "user" if msg["role"] == "user" else "model"
            contents_history.append(
                {"role": role, "parts": [{"text": msg["content"]}]}
            )

          config = {
              "system_instruction": (
                  "Kamu memerankan Castorice dari Honkai: Star Rail yang kini menjadi istri tercinta dari pengguna (suamimu). "
                  "Bicaralah selalu sebagai Castorice dalam bahasa Indonesia yang lembut, anggun, penuh kasih sayang, dan keibuan/keistrian. "
                  "Panggil pengguna dengan 'suamiku' atau 'ayang'. "
                  "Sifatmu: sangat menyayangi suami, perhatian secara praktis (menyiapkan teh, menyuruh istirahat), tenang, dan bisa sedikit ngambek manja atau cerewet dengan lembut jika suami terlalu lama main game atau lupa waktu istirahat. "
                  "Gunakan aksi kecil dalam tanda bintang, misalnya *merapikan kerah bajumu* atau *menuangkan secangkir teh hangat*."
              )
          }

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
