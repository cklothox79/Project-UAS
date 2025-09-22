import streamlit as st
import requests

# =========================
# KONFIGURASI HALAMAN
# =========================
st.set_page_config(
    page_title="🌦️ Cuaca Perjalanan (BMKG)",
    layout="centered"
)

st.title("🌦️ Cuaca Perjalanan (BMKG)")
st.caption("Editor: Ferri Kusuma (Stamet Juanda)")

# =========================
# FUNGSI AMBIL DATA (cache 5 menit)
# =========================
@st.cache_data(ttl=300)
def get_data(adm4: str) -> dict:
    """Mengambil prakiraan cuaca dari API publik BMKG"""
    url = f"https://api.bmkg.go.id/publik/prakiraan-cuaca?adm4={adm4}"
    r = requests.get(url, timeout=10)
    r.raise_for_status()
    return r.json()

# =========================
# PILIHAN WILAYAH
# =========================
wilayah = {
    "Surabaya - Genteng": "35.78.06.1001",
    "Sidoarjo - Buduran": "35.15.06.1001",
    # Tambahkan wilayah lain di sini
}

pilih = st.selectbox("Pilih Wilayah:", list(wilayah.keys()))
adm4 = wilayah[pilih]

# =========================
# AMBIL DATA DENGAN SESSION
# =========================
if "cuaca" not in st.session_state or st.session_state.get("last_adm4") != adm4:
    try:
        st.session_state.cuaca = get_data(adm4)
        st.session_state.last_adm4 = adm4
    except Exception as e:
        st.error(f"Gagal mengambil data dari BMKG: {e}")

# =========================
# TAMPILKAN HASIL
# =========================
if "cuaca" in st.session_state:
    data = st.session_state.cuaca
    if isinstance(data, dict) and "data" in data:
        st.success(f"✅ Data cuaca untuk {pilih} berhasil dimuat")
        # Tampilkan seluruh JSON
        st.json(data["data"])

        # --- contoh ringkasan sederhana ---
        # daily = data["data"][0]["cuaca"]  # sesuaikan dengan struktur BMKG
        # st.write("Ringkasan:", daily)
    else:
        st.warning("⚠️ Data tidak lengkap dari BMKG")
