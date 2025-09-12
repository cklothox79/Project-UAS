import streamlit as st
import folium
from streamlit_folium import st_folium
import matplotlib.pyplot as plt
import numpy as np

# ===================== #
# Judul Aplikasi
# ===================== #
st.set_page_config(page_title="TAFOR Generator", layout="wide")
st.title("🛫 Generator TAFOR Otomatis")

# ===================== #
# Sidebar
# ===================== #
st.sidebar.header("⚙️ Pengaturan")

# Pilihan basemap
basemap_option = st.sidebar.radio(
    "🗺️ Pilih Tampilan Peta",
    ("OpenStreetMap", "Stamen Terrain", "Stamen Toner", "Esri Satelit")
)

# Input lokasi awal peta
default_location = [-7.379, 112.787]  # Juanda (contoh)
zoom_start = 8

# ===================== #
# Buat Peta Folium
# ===================== #
m = folium.Map(location=default_location, zoom_start=zoom_start, control_scale=True)

if basemap_option == "OpenStreetMap":
    folium.TileLayer("OpenStreetMap").add_to(m)
elif basemap_option == "Stamen Terrain":
    folium.TileLayer("Stamen Terrain", attr="Stamen").add_to(m)
elif basemap_option == "Stamen Toner":
    folium.TileLayer("Stamen Toner", attr="Stamen").add_to(m)
elif basemap_option == "Esri Satelit":
    folium.TileLayer(
        tiles="https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
        attr="Esri &mdash; Source: Esri, i-cubed, USDA, USGS, AEX, GeoEye",
        name="Esri Satellite",
        overlay=False,
        control=True,
    ).add_to(m)

# Marker lokasi default
folium.Marker(
    location=default_location,
    popup="Bandara Juanda",
    tooltip="Klik untuk pilih lokasi"
).add_to(m)

# Tampilkan peta
st_map = st_folium(m, width=700, height=450)

# ===================== #
# Input Manual TAFOR
# ===================== #
st.subheader("✍️ Input Parameter TAFOR")

location = st.text_input("Lokasi Bandara", "Juanda (WARR)")
valid_time = st.text_input("Periode Valid (contoh: 1200/1306)", "1200/1306")
wind = st.text_input("Angin (ddffGggKT)", "09010KT")
visibility = st.text_input("Visibilitas (meter atau km)", "6000")
weather = st.text_input("Cuaca (kode ICAO)", "SHRA")
clouds = st.text_input("Awan (kode ICAO)", "BKN020")

# Tombol generate
if st.button("🚀 Generate TAFOR"):
    tafor_text = f"TAF {location} {valid_time} {wind} {visibility} {weather} {clouds}"
    st.code(tafor_text, language="yaml")

# ===================== #
# Windrose (Visualisasi)
# ===================== #
st.subheader("🌬️ Distribusi Angin (Windrose)")

angles = np.linspace(0, 2*np.pi, 16, endpoint=False)
values = np.random.rand(16) * 100  # data dummy

fig, ax = plt.subplots(subplot_kw={'projection': 'polar'}, figsize=(4,4))
bars = ax.bar(angles, values, width=0.35, bottom=0.0)

# Styling agar lebih eye-catching
for bar in bars:
    bar.set_alpha(0.7)
    bar.set_facecolor(plt.cm.viridis(np.random.rand()))

ax.set_theta_zero_location("N")
ax.set_theta_direction(-1)

st.pyplot(fig)
