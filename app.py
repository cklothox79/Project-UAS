import streamlit as st
import folium
from streamlit_folium import st_folium
from datetime import date
from utils.isdp_api import get_forecast

st.set_page_config(page_title="Cuaca Perjalanan", page_icon="🌦️", layout="wide")

# ----- Header -----
st.title("🌦️ Cuaca Perjalanan")
st.caption(
    "Lihat prakiraan suhu, hujan, awan, kelembapan, dan angin setiap jam "
    "untuk lokasi dan tanggal yang kamu pilih."
)

# ----- Input -----
col1, col2 = st.columns([2,1])
with col1:
    kota = st.text_input("Masukkan nama kota (opsional):")
with col2:
    tgl_perjalanan = st.date_input(
        "Pilih tanggal perjalanan:",
        value=date.today(),
        min_value=date.today()
    )

st.markdown("### 📍 Klik lokasi di peta atau masukkan koordinat")

# ----- Peta -----
m = folium.Map(location=[-2.5, 118], zoom_start=5)
st_map = st_folium(m, height=400, width=700)

# Koordinat hasil klik
clicked_lat = None
clicked_lon = None
if st_map and st_map.get("last_clicked"):
    clicked_lat = st_map["last_clicked"]["lat"]
    clicked_lon = st_map["last_clicked"]["lng"]
    st.success(f"Koordinat terpilih: {clicked_lat:.4f}, {clicked_lon:.4f}")

# ----- Ambil Data -----
if clicked_lat and clicked_lon:
    if st.button("Ambil Prakiraan Cuaca"):
        with st.spinner("Mengambil data prakiraan BMKG..."):
            data = get_forecast(clicked_lat, clicked_lon)

        if not data:
            st.error("Gagal mengambil prakiraan.")
        else:
            forecasts = data.get("data", {}).get("forecasts", [])
            if not forecasts:
                st.warning("Data prakiraan tidak ditemukan.")
            else:
                st.markdown(f"### 🌍 Prakiraan Cuaca {tgl_perjalanan}")
                # tampilkan 12 jam pertama
                for jam in forecasts[:12]:
                    time = jam.get("time")
                    suhu = jam.get("t")
                    hujan = jam.get("weather", "-")
                    kelembapan = jam.get("hu")
                    angin = jam.get("ws")
                    arah_angin = jam.get("wd")
                    st.write(
                        f"⏰ {time} | 🌡️ {suhu}°C | 💧 {kelembapan}% | "
                        f"💨 {angin} km/j ({arah_angin}) | ☁️ {hujan}"
                    )

else:
    st.info("Silakan klik lokasi di peta untuk mendapatkan prakiraan.")
