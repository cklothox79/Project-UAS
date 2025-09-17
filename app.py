# app.py - Cuaca Perjalanan (BMKG API)
import streamlit as st
import requests
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime
import math

st.set_page_config(page_title="Cuaca Perjalanan (BMKG)", layout="wide")

# ----- Header -----
st.markdown("<h1 style='font-size:36px;'>🌤️ Cuaca Perjalanan (BMKG)</h1>", unsafe_allow_html=True)
st.markdown("<p style='font-size:18px; color:gray;'><em>Editor: Ferri Kusuma (Stamet Juanda)</em></p>", unsafe_allow_html=True)

# ----- Sidebar -----
st.sidebar.header("Input Lokasi (adm4)")
adm4_code = st.sidebar.text_input("📝 Kode Wilayah adm4 (Kelurahan/Kecamatan)", value="31.71.03.1001")
st.sidebar.caption("Cth: 31.71.03.1001 = Penjaringan, Jakarta Utara")

use_taf = st.sidebar.checkbox("🔁 Generate simplified TAF (EDUCATIONAL/INFORMAL)", value=False)
if use_taf:
    st.sidebar.caption("Hanya ilustrasi — **bukan** TAF resmi!")

st.sidebar.markdown("---")
st.sidebar.caption("Aplikasi: prakicu.streamlit.app (versi BMKG)")

# ----- Fungsi ambil data BMKG -----
@st.cache_data(show_spinner=False)
def get_weather_bmkg(adm4_code: str):
    url = f"https://api.bmkg.go.id/publik/prakiraan-cuaca?adm4={adm4_code}"
    r = requests.get(url, timeout=15)
    if r.status_code == 200:
        return r.json()
    return None

# ----- Konversi arah angin -----
def parse_wind_dir(wd: str):
    arah_map = {
        "Utara": 0, "Timur Laut": 45, "Timur": 90, "Tenggara": 135,
        "Selatan": 180, "Barat Daya": 225, "Barat": 270, "Barat Laut": 315
    }
    return arah_map.get(wd, 0)

def parse_wind_speed(ws: str):
    try:
        return float(ws.split()[0]) / 3.6  # km/jam → m/s
    except:
        return 0.0

# ----- Ambil data -----
if adm4_code:
    data = get_weather_bmkg(adm4_code)
    if data and "data" in data:
        lokasi = data.get("lokasi", {})
        st.markdown(f"### 📍 Lokasi: {lokasi.get('kecamatan','?')}, {lokasi.get('kabupaten','?')}")

        df = pd.DataFrame(data["data"])
        df["jamCuaca"] = pd.to_datetime(df["jamCuaca"])
        df["Arah Angin (°)"] = df["wd"].apply(parse_wind_dir)
        df["Kecepatan Angin (m/s)"] = df["ws"].apply(parse_wind_speed)

        # ----- Cuaca ekstrem detection -----
        ekstrem = df[df["kodeCuaca"] >= 80]
        st.markdown("### ⚠️ Peringatan Cuaca Ekstrem")
        if not ekstrem.empty:
            daftar = "\n".join(f"• {t.strftime('%Y-%m-%d %H:%M')} → {c}" for t, c in zip(ekstrem["jamCuaca"], ekstrem["cuaca"]))
            st.warning(f"Cuaca ekstrem diperkirakan pada:\n\n{daftar}")
        else:
            st.success("✅ Tidak ada cuaca ekstrem yang terdeteksi.")

        # ----- Grafik suhu & kelembapan -----
        st.markdown("### 📈 Grafik Suhu & Kelembapan")
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=df["jamCuaca"], y=df["tempC"], name="Suhu (°C)"))
        fig.add_trace(go.Scatter(x=df["jamCuaca"], y=df["humidity"], name="RH (%)", yaxis="y2"))

        fig.update_layout(
            xaxis=dict(title="Waktu (WIB)"),
            yaxis=dict(title="Suhu (°C)"),
            yaxis2=dict(title="RH (%)", overlaying="y", side="right"),
            height=480
        )
        st.plotly_chart(fig, use_container_width=True)

        # ----- Windrose -----
        st.markdown("### 🧭 Arah & Kecepatan Angin")
        fig_angin = go.Figure()
        fig_angin.add_trace(go.Barpolar(
            r=df["Kecepatan Angin (m/s)"],
            theta=df["Arah Angin (°)"],
            name="Angin per jam",
            marker_color="#1f77b4",
            opacity=0.8
        ))
        fig_angin.update_layout(
            polar=dict(angularaxis=dict(direction="clockwise", rotation=90)),
            height=520
        )
        st.plotly_chart(fig_angin, use_container_width=True)

        # ----- Tabel -----
        st.markdown("### 📊 Tabel Data Cuaca")
        st.dataframe(df[["jamCuaca", "tempC", "humidity", "cuaca", "wd", "ws"]], use_container_width=True)
        csv = df.to_csv(index=False).encode("utf-8")
        st.download_button("📥 Unduh Data (CSV)", data=csv, file_name="cuaca_bmkg.csv", mime="text/csv")

        # ----- TAF sederhana -----
        if use_taf:
            st.markdown("### 📝 Simplified TAF (EDUCATIONAL)")
            first = df.iloc[0]
            taf = f"TAF XXXX {datetime.utcnow().strftime('%d%H%MZ')} " \
                  f"{df['jamCuaca'].min().strftime('%d%H%M')}/{df['jamCuaca'].max().strftime('%d%H%M')} " \
                  f"{parse_wind_dir(first['wd']):03d}{int(parse_wind_speed(first['ws'])*1.94):02d}KT " \
                  f"{first['cuaca'].upper()} " \
                  f"TEMP {first['tempC']}C RH {first['humidity']}% ="
            st.code(taf)
    else:
        st.error("❌ Data BMKG tidak tersedia untuk kode adm4 ini.")
