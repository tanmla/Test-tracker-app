import streamlit as st
from streamlit_js_eval import get_geolocation
import pandas as pd
import time
from datetime import datetime

st.set_page_config(page_title="Auto Route Tracker", page_icon="🚴‍♂️")

st.title("🚴‍♂️ Automatic Route Tracker")
st.write("Aplikasi ini akan merekam posisi Anda secara otomatis setiap 10 detik.")

# 1. Inisialisasi Session State (Database sementara di memori)
if 'tracking_active' not in st.session_state:
    st.session_state.tracking_active = False
if 'route_history' not in st.session_state:
    st.session_state.route_history = []

# 2. Tombol Kontrol
col1, col2 = st.columns(2)
with col1:
    if st.button("▶️ Mulai Tracking"):
        st.session_state.tracking_active = True
        st.session_state.route_history = [] # Reset rute baru
        st.rerun()

with col2:
    if st.button("⏹️ Berhenti"):
        st.session_state.tracking_active = False
        st.rerun()

# 3. Area Tampilan Peta & Statistik (Akan diperbarui terus)
placeholder_stats = st.empty()
placeholder_map = st.empty()

# 4. Logika Pengambilan Lokasi Otomatis
if st.session_state.tracking_active:
    # Ambil lokasi dari browser
    loc = get_geolocation()
    
    if loc:
        curr_lat = loc['coords']['latitude']
        curr_lon = loc['coords']['longitude']
        timestamp = datetime.now().strftime("%H:%M:%S")

        # Simpan ke riwayat jika koordinat baru berbeda dari sebelumnya
        current_coord = {'lat': curr_lat, 'lon': curr_lon, 'time': timestamp}
        
        # Hindari duplikasi data yang sama persis
        if not st.session_state.route_history or \
           (st.session_state.route_history[-1]['lat'] != curr_lat):
            st.session_state.route_history.append(current_coord)

        # Ubah riwayat ke DataFrame untuk tampilan
        df_route = pd.DataFrame(st.session_state.route_history)

        # Update Statistik di layar
        with placeholder_stats.container():
            st.write(f"📍 Titik Tercatat: **{len(df_route)}**")
            st.write(f"🕒 Terakhir diperbarui: **{timestamp}**")

        # Update Peta di layar
        with placeholder_map:
            st.map(df_route[['lat', 'lon']])

        # Jeda waktu sebelum pengulangan (Refresh otomatis)
        time.sleep(10) # Ambil data setiap 10 detik
        st.rerun()
    else:
        st.warning("Mencari sinyal GPS... Pastikan izin lokasi diberikan.")

# 5. Opsi Simpan Data setelah Berhenti
if not st.session_state.tracking_active and len(st.session_state.route_history) > 0:
    st.success("Tracking Selesai!")
    df_final = pd.DataFrame(st.session_state.route_history)
    
    # Download Button
    csv = df_final.to_csv(index=False).encode('utf-8')
    st.download_button("💾 Simpan Rute ke CSV", data=csv, file_name='rute_saya.csv')
    
    st.subheader("Data Lengkap Rute:")
    st.dataframe(df_final)
