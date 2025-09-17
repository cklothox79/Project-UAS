import streamlit as st
import requests
import pandas as pd
import folium
from streamlit_folium import st_folium
import pytz

# -----------------------------
# Fungsi ambil data wilayah BMKG
# -----------------------------
@st.cache_data
def get_wilayah_bmkg():
    url = "https://api.bmkg.go.id/publik/wilayah"
    r = requests.get(url, timeout=10)
    if r.status_code == 200:
        return r.json()
    return None

# -----------------------------
# Fungsi ambil prakiraan cuaca BMKG
# -----------------------------
def get_prakiraan_bmkg(adm4_code: str):
    url = f"https://api.bmkg.go.id/publik/prakiraan-cuaca?adm4={adm4_code}"
    r = requests.get(url, timeout=10)
    if r.status_code == 200:
        return r.json()
    return None

# -----------------------------
# Aplikasi Streamlit
# -----------------------------
st.set_page_config(page_title="Cuaca Perjalanan (BMKG)", layout="wide")

st.title("🌦️ Cuaca Perjalanan (BMKG)")
st.write("Editor: Ferri Kusuma (Stamet Juanda)")

# Ambil daftar wilayah
wilayah_data = get_wilayah_bmkg()

if wilayah_data:
    # Dropdown provinsi
    provinsi_list = sorted(set([w["provinsi"] for w in wilayah_data]))
    provinsi = st.selectbox("Pilih Provinsi:", provinsi_list)

    # Filter kabupaten/kota
    kabupaten_list = sorted(set([w["kotkab"] for w in wilayah_data if w["provinsi"] == provinsi]))
    kabupaten = st.selectbox("Pilih Kabupaten/Kota:", kabupaten_list)

    # Filter kecamatan
    kecamatan_list = sorted(set([w["kecamatan"] for w in wilayah_data if w["kotkab"] == kabupaten]))
    kecamatan = st.selectbox("Pilih Kecamatan:", kecamatan_list)

    # Filter kelurahan (adm4)
    kelurahan_list = [w for w in wilayah_data if w["kecamatan"] == kecamatan]
    kelurahan_names = [w["kelurahan"] for w in kelurahan_list]
    kelurahan = st.selectbox("Pilih Kelurahan:", kelurahan_names)

    # Ambil adm4 code
    adm4_code = None
    lat, lon = -2.5, 118.0  # fallback tengah Indonesia
    for w in kelurahan_list:
        if w["kelurahan"] == kelurahan:
            adm4_code = w["kode"]
            lat = float(w["lat"])
            lon = float(w["lon"])
            break

    if adm4_code:
        # Ambil data prakiraan cuaca
        prakiraan = get_prakiraan_bmkg(adm4_code)

        if prakiraan and "data" in prakiraan:
            st.subheader(f"Prakiraan Cuaca: {kelurahan}, {kecamatan}, {kabupaten}, {provinsi}")

            df = pd.DataFrame(prakiraan["data"])

            # Normalisasi kolom waktu → pilih yang tersedia
            if "jamCuaca" in df.columns:
                waktu_col = "jamCuaca"
            elif "local_datetime" in df.columns:
                waktu_col = "local_datetime"
            elif "tanggal" in df.columns:
                waktu_col = "tanggal"
            else:
                waktu_col = None

            if waktu_col:
                df["waktu_lokal"] = pd.to_datetime(df[waktu_col])
                # Convert ke WIB
                tz = pytz.timezone("Asia/Jakarta")
                df["waktu_lokal"] = df["waktu_lokal"].dt.tz_convert(tz)
                df["waktu_lokal"] = df["waktu_lokal"].dt.strftime("%d-%m-%Y %H:%M")
            else:
                st.warning("Kolom waktu tidak ditemukan di data BMKG.")
                df["waktu_lokal"] = None

            # Tampilkan tabel
            st.dataframe(df)

            # -----------------------------
            # Peta lokasi
            # -----------------------------
            m = folium.Map(location=[lat, lon], zoom_start=11)
            folium.Marker(
                [lat, lon],
                popup=f"{kelurahan}, {kecamatan}",
                tooltip="Lokasi"
            ).add_to(m)
            st_map = st_folium(m, width=700, height=450)

            # Tambahkan keterangan
            st.caption("⏰ Waktu ditampilkan dalam zona lokal Indonesia (WIB)")
            st.caption("ℹ️ Data prakiraan cuaca diambil dari BMKG (api.bmkg.go.id)")
        else:
            st.error("Data prakiraan cuaca tidak tersedia untuk wilayah ini.")
else:
    st.error("Gagal mengambil daftar wilayah dari BMKG.")

