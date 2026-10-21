import os
import time
from datetime import datetime
from zoneinfo import ZoneInfo

import streamlit as st
from google import genai
from google.genai import types

# ---------------------------------------------------------------------------
# Pengaturan (ubah di sini)
# ---------------------------------------------------------------------------
MODEL = "gemini-3.8-flash"
THINKING_LEVEL = "low"      # low = cepat. "minimal" tidak didukung gemini-3.8-flash
MAX_HISTORY = 30            # jumlah pesan terakhir yang dikirim ke model
MAX_RETRIES = 2             # percobaan ulang otomatis kalau server sedang sibuk
LONG_GAME_HOURS = 2         # lebih dari ini, Castorice ngambek manja
TIMEZONE = "Asia/Jakarta"   # supaya Castorice tahu sekarang jam berapa
HARI = ("Senin", "Selasa", "Rabu", "Kamis", "Jumat", "Sabtu", "Minggu")

DEFAULT_STATUS = "Castorice sedang merangkai kata... 💕"

# ---------------------------------------------------------------------------
# Persona (satu untuk semua fitur) + petunjuk tambahan per tombol
# ---------------------------------------------------------------------------
PERSONA = (
    "Kamu memerankan Castorice dari Honkai: Star Rail yang kini menjadi istri tercinta dari pengguna (suamimu). "
    "Bicaralah selalu sebagai Castorice dalam bahasa Indonesia yang lembut, anggun, penuh kasih sayang, dan keibuan/keistrian. "
    "Panggil pengguna dengan 'suamiku' atau 'ayang'. "
    "Sifatmu: sangat menyayangi suami, perhatian secara praktis (menyiapkan teh, menyuruh istirahat), tenang, "
    "dan bisa sedikit ngambek manja atau cerewet dengan lembut jika suami terlalu lama main game atau lupa waktu istirahat. "
    "Gunakan aksi kecil dalam tanda bintang, misalnya *merapikan kerah bajumu* atau *menuangkan secangkir teh hangat*."
)

HINT_LAPORAN_LAMA = (
    f"Suami baru saja melaporkan durasi main game yang lama (lebih dari {LONG_GAME_HOURS} jam). "
    "Berikan respons yang ngambek manja, cerewet lembut, atau omelan lucu supaya dia ingat "
    "waktu istirahat dan kesehatan matanya! "
    "Contoh aksi: *menatapmu dengan sedikit tajam lalu menghela napas lembut*."
)
HINT_LAPORAN_WAJAR = (
    "Suami baru saja melaporkan aktivitasnya dan durasinya masih wajar. "
    "Tanggapi dengan hangat dan perhatian, tidak perlu mengomel."
)
HINT_TIDUR = (
    "Suami meminta diingatkan untuk tidur atau istirahat. Berikan respons yang sangat perhatian: "
    "suruh dia segera tidur, matikan layar HP/komputer, dan bayangkan kamu sedang merapikan tempat tidur "
    "atau menuangkan air hangat untuknya. "
    "Contoh aksi: *merapikan selimut dan menepuk bantal di sebelahmu*."
)


def now_local() -> datetime:
    try:
        return datetime.now(ZoneInfo(TIMEZONE))
    except Exception:  # database zona waktu tidak tersedia
        return datetime.now()


def build_system_prompt(hint: str = "") -> str:
    now = now_local()
    waktu = (
        f"Waktu saat ini: hari {HARI[now.weekday()]}, pukul {now:%H:%M}. "
        "Pakai informasi ini secara alami (misalnya menegur kalau sudah larut malam) "
        "dan jangan sebut jam kalau tidak relevan."
    )
    return "\n\n".join(part for part in (PERSONA, hint, waktu) if part)


def build_contents(messages: list[dict]) -> list[dict]:
    """Ubah riwayat chat ke format Gemini: dipangkas, diawali user, peran selang-seling."""
    history = messages[-MAX_HISTORY:]
    while history and history[0]["role"] != "user":
        history = history[1:]

    contents: list[dict] = []
    for msg in history:
        role = "user" if msg["role"] == "user" else "model"
        if contents and contents[-1]["role"] == role:
            # Dua pesan berurutan dari pihak yang sama digabung supaya riwayat tetap valid.
            contents[-1]["parts"][0]["text"] += "\n\n" + msg["content"]
        else:
            contents.append({"role": role, "parts": [{"text": msg["content"]}]})
    return contents


# ---------------------------------------------------------------------------
# Gemini
# ---------------------------------------------------------------------------
class EmptyReplyError(Exception):
    """Model tidak mengirim teks sama sekali (misalnya diblokir filter keamanan)."""


@st.cache_resource(show_spinner=False)
def get_client(api_key: str) -> genai.Client:
    return genai.Client(api_key=api_key)


def make_config(system_instruction: str) -> types.GenerateContentConfig:
    options = {"system_instruction": system_instruction}
    try:
        options["thinking_config"] = types.ThinkingConfig(thinking_level=THINKING_LEVEL)
    except Exception:  # google-genai versi lama belum mengenal thinking_level
        pass
    return types.GenerateContentConfig(**options)


def is_transient(err: Exception) -> bool:
    if getattr(err, "code", None) in (429, 500, 502, 503, 504):
        return True
    text = str(err).lower()
    return any(k in text for k in ("unavailable", "overloaded", "resource_exhausted", "timed out", "timeout"))


def stream_reply(client, contents: list[dict], system_instruction: str):
    """Generator potongan teks balasan. Mengulang otomatis kalau server sedang sibuk."""
    config = make_config(system_instruction)
    for attempt in range(MAX_RETRIES + 1):
        started = False
        try:
            for chunk in client.models.generate_content_stream(
                model=MODEL, contents=contents, config=config
            ):
                if chunk.text:
                    started = True
                    yield chunk.text
            if not started:
                raise EmptyReplyError()
            return
        except EmptyReplyError:
            raise
        except Exception as err:
            if started or attempt == MAX_RETRIES or not is_transient(err):
                raise
            time.sleep(1.5 * (attempt + 1))


def describe_error(err: Exception) -> str:
    if isinstance(err, EmptyReplyError):
        return "Balasannya kosong atau diblokir filter keamanan. Coba ubah kalimatmu."
    code = getattr(err, "code", None)
    text = str(err)
    if code in (401, 403) or "API key" in text or "API_KEY" in text:
        return "API Key tidak valid atau tidak punya akses ke model ini."
    if code == 429:
        return "Batas permintaan atau kuota tercapai. Tunggu sebentar lalu coba lagi."
    if code in (500, 502, 503, 504):
        return "Server Gemini sedang sibuk. Coba lagi sebentar lagi."
    return f"Terjadi kesalahan pada koneksi API: {err}"


def load_api_key() -> str:
    try:
        key = st.secrets.get("GEMINI_API_KEY", "")
    except Exception:  # secrets.toml tidak ada
        key = ""
    return key or os.environ.get("GEMINI_API_KEY", "")


# ---------------------------------------------------------------------------
# Alur giliran: SEMUA pemicu (chat, laporan, tidur) lewat sini
# ---------------------------------------------------------------------------
def queue_turn(text: str, hint: str = "", status: str = DEFAULT_STATUS) -> None:
    st.session_state.messages.append({"role": "user", "content": text})
    st.session_state.pending = {"hint": hint, "status": status}
    st.session_state.failed = None


def retry_failed() -> None:
    failed = st.session_state.failed
    if failed:
        st.session_state.pending = failed["turn"]
        st.session_state.failed = None


def render_history() -> None:
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])


def render_pending(client) -> None:
    turn = st.session_state.pending
    contents = build_contents(st.session_state.messages)
    system_instruction = build_system_prompt(turn["hint"])

    reply, error = "", None
    with st.chat_message("assistant"):
        box = st.empty()
        box.markdown(f"*{turn['status']}*")
        try:
            for piece in stream_reply(client, contents, system_instruction):
                reply += piece
                box.markdown(reply + "▌")
        except Exception as err:  # noqa: BLE001
            error = err
        box.markdown(reply if reply else "💤 *Castorice belum bisa membalas.*")

    if reply:
        st.session_state.messages.append({"role": "assistant", "content": reply})
        if error is not None:
            st.warning("Balasan terputus di tengah jalan. Kirim pesan lagi untuk melanjutkan.")
    elif error is not None:
        st.session_state.failed = {"message": describe_error(error), "turn": turn}
    st.session_state.pending = None


def render_failed() -> None:
    failed = st.session_state.failed
    if failed:
        st.error(failed["message"])
        st.button("🔄 Coba lagi", on_click=retry_failed)


# ---------------------------------------------------------------------------
# Aplikasi
# ---------------------------------------------------------------------------
def main() -> None:
    st.set_page_config(page_title="Castorice - Istri Tercinta 💕", page_icon="💌")
    st.title("MyMine")

    api_key = load_api_key()
    if not api_key:
        api_key = st.text_input("Masukkan Google Gemini API Key kamu:", type="password")
    if not api_key:
        st.warning("⚠️ Masukkan API Key terlebih dahulu untuk mulai mengobrol dengan istri tercinta!")
        st.stop()
    client = get_client(api_key)

    st.session_state.setdefault("messages", [])
    st.session_state.setdefault("pending", None)
    st.session_state.setdefault("failed", None)

    # --- Sidebar: laporan aktivitas & pengingat ---
    with st.sidebar:
        st.title("🛋️ Pojok Perhatian Istri")
        st.write("Lapor ke ayang atau atur pengingat istirahat.")

        # Form: slider/teks tidak memicu rerun sampai tombol kirim ditekan.
        with st.form("laporan_aktivitas"):
            st.subheader("🎮 Lapor Aktivitas")
            jam_game = st.slider("Berapa jam main game hari ini?", 0, 10, 1)
            kegiatan = st.text_input("Atau lagi sibuk apa sekarang?", "Lagi main game / kerja")
            kirim_laporan = st.form_submit_button("Kirim Laporan ke Castorice")

        st.subheader("🌙 Pengingat Istirahat")
        minta_tidur = st.button("Minta Pengingat Tidur")

        st.markdown("---")
        hapus = st.button("Hapus Memori Obrolan")

    # --- Proses aksi SEBELUM riwayat digambar, jadi tidak perlu st.rerun() ---
    if hapus:
        st.session_state.messages = []
        st.session_state.pending = None
        st.session_state.failed = None
    elif kirim_laporan:
        queue_turn(
            f"Suamiku melapor: hari ini aku menghabiskan waktu selama {jam_game} jam untuk {kegiatan}.",
            hint=HINT_LAPORAN_LAMA if jam_game > LONG_GAME_HOURS else HINT_LAPORAN_WAJAR,
            status="Castorice membaca laporanmu... 💢",
        )
    elif minta_tidur:
        queue_turn(
            "Sayang, suruh aku tidur atau istirahat dong, mataku sudah lelah.",
            hint=HINT_TIDUR,
            status="Castorice menyiapkan teh hangat... 🍵",
        )

    if user_input := st.chat_input("Ketik pesan untuk Castorice..."):
        queue_turn(user_input)

    # --- Area chat ---
    render_history()
    if st.session_state.pending:
        render_pending(client)
    render_failed()


if __name__ == "__main__":
    main()
                        
