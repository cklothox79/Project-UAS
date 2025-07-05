import streamlit as st
import xarray as xr
import matplotlib.pyplot as plt
import cartopy.crs as ccrs
import cartopy.feature as cfeature
import pandas as pd
from datetime import datetime

st.set_page_config(page_title="Prakiraan Cuaca DKI Jakarta", layout="wide")
st.title("📡 GFS Viewer Provinsi DKI Jakarta (Realtime via NOMADS)")
st.header("Web Hasil Pembelajaran Pengelolaan Informasi Meteorologi")
st.markdown("**YANTI MALA**  \n*UAS PIM M8TB 2025*")

@st.cache_data
def load_dataset(run_date, run_hour):
    base_url = f"https://nomads.ncep.noaa.gov/dods/gfs_0p25_1hr/gfs{run_date}/gfs_0p25_1hr_{run_hour}z"
    ds = xr.open_dataset(base_url)
    return ds

st.sidebar.title("⚙️ Pengaturan")
today = datetime.utcnow()
run_date = st.sidebar.date_input("Tanggal Run GFS (UTC)", today.date())
run_hour = st.sidebar.selectbox("Jam Run GFS (UTC)", ["00", "06", "12", "18"])
forecast_hour = st.sidebar.slider("Jam ke depan", 0, 240, 0, step=1)
parameter = st.sidebar.selectbox("Parameter", [
    "Curah Hujan per jam (pratesfc)",
    "Suhu Permukaan (tmp2m)",
    "Angin Permukaan (ugrd10m & vgrd10m)",
    "Tekanan Permukaan Laut (prmslmsl)"
])

if st.sidebar.button("🔎 Tampilkan Visualisasi"):
    try:
        ds = load_dataset(run_date.strftime("%Y%m%d"), run_hour)
        if forecast_hour >= len(ds.time):
            st.error("Data untuk jam ke-{} belum tersedia.".format(forecast_hour))
            st.stop()
        st.success("Dataset berhasil dimuat.")
    except Exception as e:
        st.error(f"Gagal memuat data: {e}")
        st.stop()

    is_contour = False
    is_vector = False

    if "pratesfc" in parameter:
        var = ds["pratesfc"][forecast_hour, :, :] * 3600
        label = "Curah Hujan (mm/jam)"
        cmap = "Blues"
    elif "tmp2m" in parameter:
        var = ds["tmp2m"][forecast_hour, :, :] - 273.15
        label = "Suhu (°C)"
        cmap = "coolwarm"
    elif "ugrd10m" in parameter:
        u = ds["ugrd10m"][forecast_hour, :, :]
        v = ds["vgrd10m"][forecast_hour, :, :]
        speed = (u**2 + v**2)**0.5 * 1.94384
        var = speed
        label = "Kecepatan Angin (knot)"
        cmap = plt.cm.get_cmap("RdYlGn_r", 10)
        is_vector = True
    elif "prmsl" in parameter:
        var = ds["prmslmsl"][forecast_hour, :, :] / 100
        label = "Tekanan Permukaan Laut (hPa)"
        cmap = "cool"
        is_contour = True
    else:
        st.warning("Parameter tidak dikenali.")
        st.stop()

    # Area DKI Jakarta
    var = var.sel(lat=slice(-6.4, -5.9), lon=slice(106.6, 107.05))
    if is_vector:
        u = u.sel(lat=slice(-6.4, -5.9), lon=slice(106.6, 107.05))
        v = v.sel(lat=slice(-6.4, -5.9), lon=slice(106.6, 107.05))

    # Plot
    fig = plt.figure(figsize=(9, 7))
    ax = plt.axes(projection=ccrs.PlateCarree())
    ax.set_extent([106.6, 107.05, -6.4, -5.9], crs=ccrs.PlateCarree())

    valid_time = ds.time[forecast_hour].values
    valid_dt = pd.to_datetime(str(valid_time))
    valid_str = valid_dt.strftime("%HUTC %a %d %b %Y")
    tstr = f"GFS t+{forecast_hour:03d}"

    # Gunakan fig.suptitle satu baris
    fig.suptitle(f"{label} | Valid {valid_str} | {tstr}", fontsize=12, fontweight="bold", y=0.95)

    if is_contour:
        cs = ax.contour(var.lon, var.lat, var.values, levels=15, colors='black', linewidths=0.8, transform=ccrs.PlateCarree())
        ax.clabel(cs, fmt="%d", colors='black', fontsize=8)
    else:
        im = ax.pcolormesh(var.lon, var.lat, var.values,
                           cmap=cmap, vmin=0, vmax=50,
                           transform=ccrs.PlateCarree())
        cbar = plt.colorbar(im, ax=ax, orientation='vertical', pad=0.02)
        cbar.set_label(label)
        if is_vector:
            ax.quiver(var.lon[::1], var.lat[::1],
                      u.values[::1, ::1], v.values[::1, ::1],
                      transform=ccrs.PlateCarree(), scale=500, width=0.002, color='black')

    # Tambahkan fitur peta
    ax.coastlines(resolution='10m', linewidth=0.8)
    ax.add_feature(cfeature.BORDERS, linestyle=':')
    ax.add_feature(cfeature.LAND, facecolor='lightgray')

    # Titik-titik DKI Jakarta
    lokasi_jakarta = {
        "Jakarta Pusat": (106.8272, -6.1806),
        "Jakarta Barat": (106.7564, -6.1681),
        "Jakarta Timur": (106.8855, -6.2251),
        "Jakarta Utara": (106.8451, -6.1214),
        "Jakarta Selatan": (106.8140, -6.2666),
        "Bandara Soetta": (106.655, -6.125),
    }

    for nama, (lon, lat) in lokasi_jakarta.items():
        ax.plot(lon, lat, marker='o', color='red', markersize=5, transform=ccrs.PlateCarree())
        ax.text(lon + 0.015, lat + 0.015, nama, fontsize=8, fontweight='bold', color='black',
                transform=ccrs.PlateCarree(),
                bbox=dict(facecolor='white', edgecolor='black', boxstyle='round,pad=0.2'))

    st.pyplot(fig)
