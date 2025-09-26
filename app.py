import streamlit as st
import pandas as pd
from utils.isdp_api import get_forecast   # Pastikan utils/isdp_api.py sudah dibuat

# =======================
# Aplikasi Cuaca Perjalanan
# =======================

st.set_page_config(page_title="Cuaca Perjalanan – BMKG API ISDP", layout="wide")
st.title("🌦️ Cuaca Perjalanan – BMKG API ISDP")

st.markdown(
    """
    Aplikasi ini menampilkan prakiraan cuaca berdasarkan **API ISDP BMKG**.
    Pilih kode wilayah (Provinsi, Kota/Kab, Kecamatan, Desa) sesuai kode BIG/Permendagri.
    """
)

# --- Input Kode Wilayah ---
with st.sidebar:
    st.header("📍 Pilih Wilayah (Kode BIG)")
    adm1 = st.text_input("Kode Provinsi (adm1)", "61")
    adm2 = st.text_input("Kode Kota/Kab (adm2)", "61.12")
    adm3 = st.text_input("Kode Kecamatan (adm3)", "61.12.01")
    adm4 = st.text_input("Kode Desa (adm4)", "61.12.01.2001")
    st.caption("Gunakan format kode sesuai [kodewilayah.id](https://kodewilayah.id/)")

# --- Tombol Ambil Data ---
if st.button("Ambil Prakiraan Cuaca"):
    with st.spinner("Mengambil data prakiraan dari BMKG..."):
        data = get_forecast(adm1=adm1, adm2=adm2, adm3=adm3, adm4=adm4)

    if not data:
        st.error("Gagal mengambil prakiraan atau data tidak ditemukan.")
    else:
        # ========================
        # Tampilkan Lokasi
        # ========================
        lokasi = data.get("lokasi", {})
        st.subheader(
            f"📍 {lokasi.get('desa','')} – {lokasi.get('kecamatan','')} "
            f"({lokasi.get('kotkab','')}, {lokasi.get('provinsi','')})"
        )

        # ========================
        # Parsing Data Prakiraan
        # ========================
        cuaca_data = []
        for item in data.get("data", []):
            if "cuaca" in item and item["cuaca"]:
                # cuaca adalah list bersarang (list dalam list)
                for jam in item["cuaca"][0]:
                    cuaca_data.append({
                        "Waktu Lokal": jam.get("local_datetime"),
                        "Suhu (°C)": jam.get("t"),
                        "Kelembapan (%)": jam.get("hu"),
                        "Awan (%)": jam.get("tcc"),
                        "Kecepatan Angin (kt)": jam.get("ws"),
                        "Cuaca": jam.get("weather_desc"),
                        "Icon": jam.get("image")
                    })

        if cuaca_data:
            df = pd.DataFrame(cuaca_data)
            # urutkan waktu jika diperlukan
            df = df.sort_values("Waktu Lokal").reset_index(drop=True)

            # ========================
            # Tabel Prakiraan
            # ========================
            st.markdown("### 🕒 Prakiraan Jam-an")
            st.dataframe(df, use_container_width=True)

            # ========================
            # Grafik Suhu
            # ========================
            st.markdown("### 🌡️ Grafik Suhu")
            st.line_chart(
                data=df.set_index("Waktu Lokal")["Suhu (°C)"],
                use_container_width=True
            )

            # ========================
            # Grafik Kelembapan
            # ========================
            st.markdown("### 💧 Grafik Kelembapan")
            st.line_chart(
                data=df.set_index("Waktu Lokal")["Kelembapan (%)"],
                use_container_width=True
            )
        else:
            st.warning("Tidak ada data jam-an yang bisa ditampilkan.")
