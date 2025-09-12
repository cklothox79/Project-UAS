import streamlit as st
import folium
from streamlit_folium import st_folium

# ========================
# KONFIGURASI APLIKASI
# ========================
st.set_page_config(
    page_title="Sistem Informasi Dini BMKG",
    page_icon="🌦️",
    layout="wide"
)

# ========================
# HEADER
# ========================
st.markdown(
    """
    <h1 style='text-align: center; color: #2C3E50;'>🌦️ Sistem Informasi Dini BMKG</h1>
    <p style='text-align: center; font-size:18px;'>
        Aplikasi ini dibuat untuk memberikan informasi cepat dan interaktif terkait cuaca ekstrem 
        dan bencana hidrometeorologis di Indonesia.
    </p>
    """,
    unsafe_allow_html=True
)

# ========================
# SIDEBAR
# ========================
with st.sidebar:
    st.header("🔎 Menu Navigasi")
    menu = st.radio(
        "Pilih halaman:",
        ["Beranda", "Peta Interaktif", "Data & Statistik", "Tentang Aplikasi"]
    )

# ========================
# BERANDA
# ========================
if menu == "Beranda":
    st.subheader("📌 Selamat Datang")
    st.write(
        """
        Sistem ini merupakan bagian dari penelitian kelompok IV pada mata kuliah **Kapita Selekta Meteorologi**.  
        Fokus penelitian adalah **Respon Masyarakat terhadap Sistem Informasi Dini BMKG dalam Menghadapi Bencana Hidrometeorologis**.
        """
    )
    st.info("Gunakan menu di sebelah kiri untuk menjelajah fitur aplikasi.")

# ========================
# PETA INTERAKTIF
# ========================
elif menu == "Peta Interaktif":
    st.markdown("<h3 style='font-size:20px; margin-top:20px;'>🗺️ Pilih Lokasi di Peta</h3>", unsafe_allow_html=True)

    default_location = [-2.5, 117.0]  # Pusat Indonesia
    m = folium.Map(location=default_location, zoom_start=5, tiles="OpenStreetMap")

    # Tambahkan pilihan layer dengan attribution
    folium.TileLayer(
        "Stamen Terrain",
        name="Terrain",
        attr="Map tiles by Stamen Design, CC BY 3.0 — Map data © OpenStreetMap contributors"
    ).add_to(m)

    folium.TileLayer(
        "Stamen Toner",
        name="Toner",
        attr="Map tiles by Stamen Design, CC BY 3.0 — Map data © OpenStreetMap contributors"
    ).add_to(m)

    folium.TileLayer(
        "CartoDB positron",
        name="Carto",
        attr="Map tiles by Carto, CC BY 3.0 — Map data © OpenStreetMap contributors"
    ).add_to(m)

    # Layer control
    folium.LayerControl().add_to(m)

    # Tampilkan peta di Streamlit
    map_data = st_folium(m, width=800, height=500)

    # Ambil lokasi klik
    if map_data and map_data.get("last_clicked"):
        st.success(f"Lokasi dipilih: {map_data['last_clicked']}")

# ========================
# DATA & STATISTIK
# ========================
elif menu == "Data & Statistik":
    st.subheader("📊 Data & Statistik Responden")
    st.write(
        """
        Bagian ini menampilkan data kuesioner masyarakat terkait sistem informasi dini BMKG.  
        Analisis akan mencakup faktor usia, pekerjaan, dan respon terhadap informasi cuaca ekstrem.
        """
    )
    st.warning("📌 Data kuesioner akan diintegrasikan di tahap berikutnya.")

# ========================
# TENTANG APLIKASI
# ========================
elif menu == "Tentang Aplikasi":
    st.subheader("ℹ️ Tentang Aplikasi")
    st.write(
        """
        Aplikasi ini dikembangkan oleh **Kelompok IV (Ferri Kusuma, Hani Gunawan, Ibnu Khaldun)**  
        dalam rangka tugas akhir mata kuliah Kapita Selekta Meteorologi di bawah bimbingan  
        **Dr. Giarno**.  

        **Tujuan utama:**  
        - Memberikan informasi dini terkait bencana hidrometeorologis.  
        - Mempermudah masyarakat dalam memahami sistem informasi BMKG.  
        - Menyediakan sarana analisis respon masyarakat.  
        """
    )
    st.success("Versi awal aplikasi sudah siap digunakan 🚀")

