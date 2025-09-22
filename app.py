import streamlit as st
import requests
import geopandas as gpd
from streamlit_folium import st_folium
import folium

st.set_page_config(page_title="🌏 Peta Seismisitas BMKG", layout="wide")
st.title("🌏 Peta Seismisitas BMKG")
st.caption("Data real-time dari portal Satu Peta MKG (BMKG) – format WFS/GeoJSON")

# ==========================
# Fungsi ambil GeoJSON BMKG
# ==========================
@st.cache_data(ttl=3600)
def get_seismisitas():
    # Endpoint contoh (lihat Link di portal)
    # Ganti typeName sesuai nama layer aslinya di capabilities
    url = "https://gis.bmkg.go.id/arcgis/services/Seismisitas/MapServer/WFSServer"
    params = {
        "service": "WFS",
        "version": "1.0.0",
        "request": "GetFeature",
        "typeName": "Seismisitas",   # cek nama layer di 'Link'
        "outputFormat": "geojson"
    }
    r = requests.get(url, params=params, timeout=30)
    r.raise_for_status()
    # WFS bisa langsung dibaca ke GeoDataFrame
    gdf = gpd.read_file(r.text)
    return gdf

try:
    gdf = get_seismisitas()
except Exception as e:
    st.error(f"Gagal mengambil data WFS BMKG: {e}")
    st.stop()

st.success(f"✅ Data berhasil dimuat. Total titik: {len(gdf)}")

# ==========================
# Peta interaktif Folium
# ==========================
m = folium.Map(location=[-2,118], zoom_start=4, tiles="CartoDB positron")
for _, row in gdf.iterrows():
    lat, lon = row.geometry.y, row.geometry.x
    folium.CircleMarker(
        location=[lat, lon],
        radius=4,
        popup=f"Magnitude: {row.get('magnitude','-')} | Date: {row.get('date','-')}",
        color="red",
        fill=True
    ).add_to(m)

st_folium(m, width=800, height=500)
