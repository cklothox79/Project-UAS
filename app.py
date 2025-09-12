# app.py - Cuaca Perjalanan (dengan Sidebar + simplified TAF generator)
import streamlit as st
import requests
import pandas as pd
from datetime import date, datetime, timezone
from streamlit_folium import st_folium
import folium
import plotly.graph_objects as go
import math

st.set_page_config(page_title="Cuaca Perjalanan", layout="wide")

# ----- Header -----
st.markdown("<h1 style='font-size:36px;'>🌤️ Cuaca Perjalanan</h1>", unsafe_allow_html=True)
st.markdown("<p style='font-size:18px; color:gray;'><em>Editor: Ferri Kusuma (Stamet_Juanda/NIP.197912222000031001)</em></p>", unsafe_allow_html=True)
st.markdown("<p style='font-size:17px;'>Lihat prakiraan suhu, hujan, awan, kelembapan, dan angin setiap jam — disertai dengan generator TAF sederhana (edukatif/informal).</p>", unsafe_allow_html=True)

# ----- Sidebar (input) -----
st.sidebar.header("Input Lokasi & Tanggal")
kota = st.sidebar.text_input("📝 Nama kota (opsional):")
tanggal = st.sidebar.date_input("📅 Tanggal perjalanan:", value=date.today(), min_value=date.today())

st.sidebar.markdown("---")
st.sidebar.header("Opsi Tambahan")
use_taf = st.sidebar.checkbox("🔁 Generate simplified TAF (EDUCATIONAL)", value=False)
if use_taf:
    st.sidebar.caption("Hasil hanya ilustrasi — **bukan** TAF resmi untuk operasi penerbangan.")
st.sidebar.markdown("---")
st.sidebar.caption("Aplikasi: prakicu.streamlit.app")

# ----- Fungsi koordinat -----
@st.cache_data(show_spinner=False)
def get_coordinates(nama_kota):
    try:
        url = f"https://nominatim.openstreetmap.org/search?q={nama_kota}&format=json&limit=1"
        headers = {"User-Agent": "cuaca-perjalanan-app"}
        r = requests.get(url, headers=headers, timeout=10)
        r.raise_for_status()
        hasil = r.json()
        if hasil:
            return float(hasil[0]["lat"]), float(hasil[0]["lon"])
        else:
            st.warning("⚠️ Kota tidak ditemukan. Coba nama kota yang lebih lengkap.")
            return None, None
    except:
        fallback_kota = {
            "mojokerto": (-7.4722, 112.4333),
            "surabaya": (-7.2575, 112.7521),
            "sidoarjo": (-7.45, 112.7167),
            "malang": (-7.9839, 112.6214),
            "jakarta": (-6.2, 106.8),
            "bandung": (-6.9147, 107.6098),
            "semarang": (-6.9667, 110.4167),
        }
        nama = nama_kota.strip().lower()
        if nama in fallback_kota:
            st.info("🔁 Menggunakan koordinat lokal karena koneksi API gagal.")
            return fallback_kota[nama]
        else:
            st.error("❌ Gagal mengambil koordinat dari internet dan tidak ditemukan dalam data lokal.")
            return None, None

# ----- Peta (kanan besar) -----
st.markdown("<h3 style='font-size:20px;'>🗺️ Klik lokasi di peta atau masukkan nama kota</h3>", unsafe_allow_html=True)
default_location = [-2.5, 117.0]
m = folium.Map(location=default_location, zoom_start=5)

lat = lon = None
if kota:
    lat, lon = get_coordinates(kota)
    if lat is None or lon is None:
        st.stop()
    folium.Marker([lat, lon], tooltip=f"📍 {kota.title()}").add_to(m)
    m.location = [lat, lon]
    m.zoom_start = 9

m.add_child(folium.LatLngPopup())
map_data = st_folium(m, height=420, use_container_width=True)

if map_data and map_data.get("last_clicked"):
    lat = map_data["last_clicked"]["lat"]
    lon = map_data["last_clicked"]["lng"]
    st.success(f"📍 Lokasi dari peta: {lat:.4f}, {lon:.4f}")

# ----- Ambil cuaca (Open-Meteo) -----
def get_hourly_weather(lat, lon, tanggal):
    tgl = tanggal.strftime("%Y-%m-%d")
    url = (
        f"https://api.open-meteo.com/v1/forecast?"
        f"latitude={lat}&longitude={lon}"
        f"&hourly=temperature_2m,precipitation,cloudcover,weathercode,"
        f"relativehumidity_2m,windspeed_10m,winddirection_10m"
        f"&timezone=UTC&start_date={tgl}&end_date={tgl}"
    )
    r = requests.get(url, timeout=15)
    return r.json() if r.status_code == 200 else None

# ----- Mapping sederhana WMO weathercode -> METAR group -----
def wmo_to_metar_group(code):
    # Simplified mapping for common WMO codes (based on Open-Meteo/WMO tables)
    if code in (0,): return {"wx":"", "desc":"Clear"}
    if code in (1,2,3): return {"wx":"", "desc":"Clouds"}
    if code in (45,48): return {"wx":"FG", "desc":"Fog"}
    if code in (51,53,55,56,57): return {"wx":"DZ", "desc":"Drizzle"}
    if code in (61,63,65,66,67): return {"wx":"RA", "desc":"Rain"}
    if code in (71,73,75,77): return {"wx":"SN", "desc":"Snow/Grains"}
    if code in (80,81,82): return {"wx":"SHRA", "desc":"Showers"}
    if code in (95,96,99): return {"wx":"TS", "desc":"Thunderstorm"}
    return {"wx":"", "desc":"Unknown"}

def cloudcover_to_group(cc):
    if cc < 10: return "SKC"
    if cc < 30: return "SCT"
    if cc < 70: return "BKN"
    return "OVC"

def precip_to_visibility(p_mm):
    # very rough: no precip -> 9999, light -> 8000, moderate->3000, heavy->1000
    if p_mm <= 0.0: return "9999"
    if p_mm < 1.0: return "8000"
    if p_mm < 5.0: return "3000"
    return "1000"

def ms_to_kt(ms):
    return ms * 1.94384

# ----- Generate simplified TAF ----- (educational)
def generate_taf_simplified(lat, lon, tanggal, ident="XXXX"):
    data = get_hourly_weather(lat, lon, tanggal)
    if not data or "hourly" not in data:
        return None, "No data"

    d = data["hourly"]
    waktu = d["time"]  # in UTC (ISO)
    temps = d["temperature_2m"]
    prec = d["precipitation"]
    cc = d["cloudcover"]
    wcode = d["weathercode"]
    rh = d["relativehumidity_2m"]
    wsp = d["windspeed_10m"]
    wdir = d["winddirection_10m"]

    # Build DataFrame
    df = pd.DataFrame({
        "time_utc": pd.to_datetime(waktu),
        "temp": temps,
        "precip": prec,
        "cloudcover": cc,
        "wcode": wcode,
        "rh": rh,
        "wsp": wsp,
        "wdir": wdir
    })

    # Headline validity: use full selected date 00/24 UTC
    valid_from = datetime.combine(tanggal, datetime.min.time()).strftime("%d%H%MZ")
    valid_to = (datetime.combine(tanggal, datetime.min.time()) + pd.Timedelta(days=1)).strftime("%d%H%MZ")
    issue_time = datetime.utcnow().strftime("%d%H%MZ")

    # Determine initial/main conditions (first 3 hours median)
    first3 = df.iloc[:3]
    mean_wsp = first3["wsp"].mean()
    mean_wdir = first3["wdir"].mean()
    wind_kt = int(round(ms_to_kt(mean_wsp)))
    dir_deg = int(round(mean_wdir / 10.0) * 10) if not math.isnan(mean_wdir) else 0
    wind_str = f"{dir_deg:03d}{wind_kt:02d}KT"

    # Visibility from precip of first hour
    vis = precip_to_visibility(first3.iloc[0]["precip"])
    # Cloud group from mean cloudcover
    cloud_group = cloudcover_to_group(first3["cloudcover"].mean())
    # Weather group from most severe wcode in first 3 hours
    most_wcode = int(df["wcode"].max())
    wxgrp = wmo_to_metar_group(most_wcode)["wx"]

    # Build main forecast line
    main_elements = [wind_str, vis]
    if wxgrp: main_elements.append(wxgrp)
    if cloud_group and cloud_group != "SKC":
        main_elements.append(cloud_group + "020")  # crude base height

    main_line = " ".join(main_elements)

    # Detect change groups: scan hourly and find contiguous blocks where
    # "major state" changes (we use a simplified rule: change if wxgrp changes
    # or cloudgroup changes or wind changes > 6 kt)
    groups = []
    prev_state = None
    current_block = {"start": None, "end": None, "state": None, "hours": []}

    def state_of_row(row):
        s_wx = wmo_to_metar_group(int(row["wcode"]))["wx"]
        s_cc = cloudcover_to_group(row["cloudcover"])
        s_wind = int(round(ms_to_kt(row["wsp"])))
        return (s_wx, s_cc, s_wind)

    for idx, row in df.iterrows():
        stt = state_of_row(row)
        hour = row["time_utc"]
        if prev_state is None:
            current_block["start"] = hour
            current_block["end"] = hour
            current_block["state"] = stt
            current_block["hours"].append(hour)
            prev_state = stt
        else:
            # define "significant change" if wx or cloud differs OR wind diff > 6 kt
            wind_diff = abs(stt[2] - prev_state[2])
            if (stt[0] != prev_state[0]) or (stt[1] != prev_state[1]) or (wind_diff > 6):
                # close current block, start new
                groups.append(current_block.copy())
                current_block = {"start": hour, "end": hour, "state": stt, "hours":[hour]}
                prev_state = stt
            else:
                current_block["end"] = hour
                current_block["hours"].append(hour)

    # append last block
    if current_block["start"] is not None:
        groups.append(current_block)

    # Convert groups to FM/BECMG/TEMPO heuristics
    taf_changes = []
    for g in groups:
        start_h = g["start"]
        end_h = g["end"]
        length_h = (end_h - start_h) / pd.Timedelta(hours=1) + 1
        # If block length >= 3 hours and starts after hour 0 -> FM
        hhmm = start_h.strftime("%H%M")
        s_wx, s_cc, s_wind = g["state"]
        wkt = f"{int(round(s_wind)):02d}"
        wdir = int(round(g["state"][2] / 10.0) * 10) if g["state"][2] > 0 else 0
        windtxt = f"{wdir:03d}{int(round(s_wind)):02d}KT"
        vistxt = precip_to_visibility(df[df["time_utc"]==start_h].iloc[0]["precip"])
        cltxt = s_cc + "020" if s_cc != "SKC" else ""
        wxtxt = s_wx
        change_line = " ".join([p for p in [windtxt, vistxt, wxtxt, cltxt] if p])
        if length_h >= 3 and start_h.hour != 0:
            taf_changes.append(("FM" + hhmm, change_line))
        else:
            # short -> TEMPO window roughly start to end
            start_str = start_h.strftime("%H%M")
            end_str = end_h.strftime("%H%M")
            taf_changes.append((f"TEMPO {start_str}/{end_str}", change_line))

    # Build encoded simplified TAF
    taf_id = ident
    taf_header = f"TAF {taf_id} {issue_time} {valid_from}/{valid_to}"
    taf_body = main_line
    for tag, txt in taf_changes:
        taf_body += " " + tag + " " + txt

    taf_encoded = taf_header + " " + taf_body + " ="

    # Decoded plain language (simple)
    decoded_lines = [
        f"Issued: {issue_time} UTC",
        f"Valid: {valid_from} -> {valid_to} UTC",
        f"Main: {main_line}"
    ]
    for tag, txt in taf_changes:
        decoded_lines.append(f"{tag}: {txt}")

    taf_decoded = "\n".join(decoded_lines)
    return taf_encoded, taf_decoded

# ----- Main: Tampilkan cuaca, grafik, windrose, tabel, TAF -----
if lat and lon and tanggal:
    data = get_hourly_weather(lat, lon, tanggal)
    if data and "hourly" in data:
        d = data["hourly"]
        waktu = d["time"]
        jam_labels = [w[-5:] for w in waktu]
        suhu = d["temperature_2m"]
        hujan = d["precipitation"]
        awan = d["cloudcover"]
        kode = d["weathercode"]
        rh = d["relativehumidity_2m"]
        angin_speed = d["windspeed_10m"]
        angin_dir = d["winddirection_10m"]

        df = pd.DataFrame({
            "Waktu": waktu,
            "Suhu (°C)": suhu,
            "Hujan (mm)": hujan,
            "Awan (%)": awan,
            "RH (%)": rh,
            "Kecepatan Angin (m/s)": angin_speed,
            "Arah Angin (°)": angin_dir,
            "Kode Cuaca": kode
        })

        # Cuaca ekstrem detection
        ekstrem = [w.replace("T", " ") for i, w in enumerate(waktu) if kode[i] >= 80]
        st.markdown("<h3 style='font-size:20px;'>⚠️ Peringatan Cuaca Ekstrem</h3>", unsafe_allow_html=True)
        if ekstrem:
            daftar = "\n".join(f"• {e}" for e in ekstrem)
            st.warning(f"Cuaca ekstrem diperkirakan pada:\n\n{daftar}")
        else:
            st.success("✅ Tidak ada cuaca ekstrem yang terdeteksi.")

        # Grafik suhu & lainnya
        st.markdown("<h3 style='font-size:20px;'>📈 Grafik Cuaca per Jam</h3>", unsafe_allow_html=True)
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=jam_labels, y=suhu, name="Suhu (°C)"))
        fig.add_trace(go.Bar(x=jam_labels, y=hujan, name="Hujan (mm)", yaxis="y2", opacity=0.7))
        fig.add_trace(go.Bar(x=jam_labels, y=awan, name="Awan (%)", yaxis="y2", opacity=0.4))
        fig.add_trace(go.Scatter(x=jam_labels, y=rh, name="RH (%)", yaxis="y2", line=dict(dash="dot")))

        fig.update_layout(
            xaxis=dict(title="Jam (UTC)"),
            yaxis=dict(title="Suhu (°C)"),
            yaxis2=dict(title="RH / Hujan / Awan", overlaying="y", side="right"),
            height=480
        )
        st.plotly_chart(fig, use_container_width=True)

        # Windrose (polar bar)
        st.markdown("<h3 style='font-size:20px;'>🧭 Arah & Kecepatan Angin</h3>", unsafe_allow_html=True)
        warna = ['#1f77b4'] * len(angin_speed)
        fig_angin = go.Figure()
        fig_angin.add_trace(go.Barpolar(
            r=angin_speed,
            theta=angin_dir,
            name="Angin per jam",
            marker_color=warna,
            opacity=0.85
        ))
        fig_angin.update_layout(polar=dict(angularaxis=dict(direction="clockwise", rotation=90)), height=520)
        st.plotly_chart(fig_angin, use_container_width=True)

        # Tabel & unduh
        st.markdown("<h3 style='font-size:20px;'>📊 Tabel Data Cuaca</h3>", unsafe_allow_html=True)
        st.dataframe(df, use_container_width=True)
        csv = df.to_csv(index=False).encode("utf-8")
        st.download_button("📥 Unduh Data (CSV)", data=csv, file_name="cuaca_per_jam.csv", mime="text/csv")

        # TAF generator (opsional)
        if use_taf:
            st.markdown("<h3 style='font-size:20px;'>📝 Simplified TAF (EDUCATIONAL)</h3>", unsafe_allow_html=True)
            taf_enc, taf_dec = generate_taf_simplified(lat, lon, tanggal, ident="XXXX")
            if taf_enc:
                st.code(taf_enc)
                with st.expander("Decoded (plain language)"):
                    st.text(taf_dec)
            else:
                st.error("Gagal membuat TAF sederhana.")

    else:
        st.error("❌ Data cuaca tidak tersedia.")

