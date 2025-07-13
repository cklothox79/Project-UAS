# ... (bagian import dan konfigurasi tidak berubah)

# Wilayah Kalimantan diperluas
lat_min, lat_max = -5, 5
lon_min, lon_max = 108, 120
var = var.sel(lat=slice(lat_min, lat_max), lon=slice(lon_min, lon_max))

if is_vector:
    u = u.sel(lat=slice(lat_min, lat_max), lon=slice(lon_min, lon_max))
    v = v.sel(lat=slice(lat_min, lat_max), lon=slice(lon_min, lon_max))

# Plot
fig = plt.figure(figsize=(10, 7))
ax = plt.axes(projection=ccrs.PlateCarree())
ax.set_extent([lon_min, lon_max, lat_min, lat_max], crs=ccrs.PlateCarree())

valid_time = ds.time[forecast_hour].values
valid_dt = pd.to_datetime(str(valid_time))
valid_str = valid_dt.strftime("%HUTC %a %d %b %Y")
tstr = f"t+{forecast_hour:03d}"

ax.set_title(f"{label} • Valid: {valid_str} • GFS {tstr}",
             fontsize=11, fontweight="bold", loc="center", pad=15)

if is_contour:
    cs = ax.contour(var.lon, var.lat, var.values, levels=15, colors='black', linewidths=0.8, transform=ccrs.PlateCarree())
    ax.clabel(cs, fmt="%d", colors='black', fontsize=8)
else:
    im = ax.pcolormesh(var.lon, var.lat, var.values,
                       cmap=cmap, vmin=vmin, vmax=vmax,
                       transform=ccrs.PlateCarree())
    cbar = plt.colorbar(im, ax=ax, orientation='vertical', pad=0.02)
    cbar.set_label(label)
    if is_vector:
        ax.quiver(var.lon[::1], var.lat[::1],
                  u.values[::1, ::1], v.values[::1, ::1],
                  transform=ccrs.PlateCarree(), scale=500, width=0.002, color='black')

ax.coastlines(resolution='10m', linewidth=0.8)
ax.add_feature(cfeature.BORDERS, linestyle=':')
ax.add_feature(cfeature.LAND, facecolor='lightgray')

# Titik Buntok
lon_buntok, lat_buntok = 114.845, -1.735
ax.plot(lon_buntok, lat_buntok, marker='o', color='red', markersize=6, transform=ccrs.PlateCarree())
ax.text(lon_buntok + 0.2, lat_buntok + 0.1, "Buntok", fontsize=9, fontweight='bold', color='black',
        transform=ccrs.PlateCarree(), bbox=dict(facecolor='white', edgecolor='black', boxstyle='round,pad=0.2'))

# Titik Tambahan (misalnya lokasi observasi)
lon_obs, lat_obs = 114.907933, -1.682540
ax.plot(lon_obs, lat_obs, marker='^', color='blue', markersize=6, transform=ccrs.PlateCarree())
ax.text(lon_obs + 0.2, lat_obs - 0.2, "Obs Point", fontsize=9, fontweight='bold', color='blue',
        transform=ccrs.PlateCarree(), bbox=dict(facecolor='white', edgecolor='blue', boxstyle='round,pad=0.2'))

# Tampilkan ke Streamlit
st.pyplot(fig)

# Download tombol
buf = io.BytesIO()
fig.savefig(buf, format="png", bbox_inches="tight")
st.download_button("📥 Download Gambar", buf.getvalue(), file_name="gfs_kalimantan.png", mime="image/png")
