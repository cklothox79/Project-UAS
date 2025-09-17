import streamlit as st
import requests
import pandas as pd
import folium
from streamlit_folium import st_folium
import pytz

st.set_page_config(page_title="Cuaca Perjalanan BMKG", layout="wide")

st.title("🌦️ Cuaca Perjalanan (BMKG)")
st.caption("Editor: Ferri Kusuma (Stamet Juanda)")

# --- Daftar wilayah manual (adm4 BMKG) ---
wilayah_lookup = {
    "Jakarta Pusat - Kemayoran": "31.71.03.1001",
    "Surabaya - Genteng": "35.78.06.1001",
    "Bandung - Cicendo": "32.73.08.1001",
    "Sidoarjo - Buduran": "35.15.06.1001"
}

pilihan = st.selectbox("Pilih Wilayah:", list(wilayah_lookup.keys()))
kode_wilayah = wilayah_lookup[pilihan]

if st.button("Ambil Data Cuaca"):
    url = f"https://api.bmkg.go.id/publik/prakiraan-cuaca?adm4={kode_wilayah}"

    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()

        if "data" not in data or not data["data"]:
            st.error("Data cuaca tidak tersedia untuk wilayah ini.")
        else:
            lokasi_info = data.get("lokasi", {})
            kecamatan = lokasi_info.get("kecamatan", "-")
            kabupaten = lokasi_info.get("kabupaten/kota") or lokasi_info.get("kota") or lokasi_info.get("provinsi", "-")
            lokasi = f"{kecamatan}, {kabupaten}"

            # Ambil dataframe cuaca
            df = pd.DataFrame(data["data"])

            # Konversi jamCuaca ke waktu lokal WIB
            if "jamCuaca" in df.columns:
                df["jamCuaca"] = pd.to_datetime(df["jamCuaca"])
                tz = pytz.timezone("Asia/Jakarta")
                df["jamLokal"] = df["jamCuaca"].dt.tz_convert(tz).dt.strftime("%d-%m-%Y %H:%M WIB")

            st.subheader(f"📍 Lokasi: {lokasi}")
            st.dataframe(df)

            # Peta lokasi
            if "lokasi" in data and "lat" in data["lokasi"] and "lon" in data["lokasi"]:
                m = folium.Map(location=[data["lokasi"]["lat"], data["lokasi"]["lon"]], zoom_start=12)
                folium.Marker(
                    [data["lokasi"]["lat"], data["lokasi"]["lon"]],
                    popup=f"{lokasi}",
                    tooltip="Lokasi Cuaca"
                ).add_to(m)
                st_folium(m, width=700, height=400)

            st.caption("🛈 Data diambil dari BMKG (api.bmkg.go.id)")

    except Exception as e:
        st.error(f"Gagal mengambil data dari BMKG: {e}")
