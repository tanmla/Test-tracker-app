import streamlit as st
from streamlit_js_eval import get_geolocation
from geopy.distance import geodesic
import pandas as pd
import time
from datetime import datetime

# 1. Konfigurasi Halaman
st.set_page_config(page_title="Pro Route Tracker", page_icon="🏃‍♂️", layout="wide")

st.title("🏃‍♂️ Pro Automatic Route Tracker")
st.write("Aplikasi ini merekam koordinat, menghitung jarak, dan menggambar rute Anda.")

# 2. Inisialisasi Session State (Database Memori)
if 'tracking_active' not in st.session_state:
    st.session_state.tracking_active = False
if 'route_history' not in st.session_state:
    st.session_state.route_history = []
if 'total_km' not in st.session_state:
    st.session_state.total_km = 0.0

# 3. Sidebar Kontrol
with st.sidebar:
    st.header("Kontrol Tracker")
    if not st.session_state.tracking_active:
        if st.button("▶️ MULAI REKAM", use_container_width=True):
            st.session_state.tracking_active = True
            st.session_state.route_history = []
            st.session_state.total_km = 0.0
            st.rerun()
    else:
        if st.button("⏹️ BERHENTI", use_container_width=True):
            st.session_state.tracking_active = False
            st.rerun()
    
    if st.button("🗑️ Reset Data", use_container_width=True):
        st.session_state.clear()
        st.rerun()

# 4. Area Tampilan Utama (Metrik)
col1, col2, col3 = st.columns(3)
placeholder_dist = col1.empty()
placeholder_pts = col2.empty()
placeholder_time = col3.empty()
placeholder_map = st.empty()

# 5. Logika Tracking Otomatis
if st.session_state.tracking_active:
    # Ambil lokasi dari browser (Wajib HTTPS jika di internet)
    loc = get_geolocation()
    
    if loc:
        curr_lat = loc['coords']['latitude']
        curr_lon = loc['coords']['longitude']
        now = datetime.now().strftime("%H:%M:%S")

        # Logika Perhitungan Jarak (Jika sudah ada titik sebelumnya)
        if len(st.session_state.route_history) > 0:
            last_pt = (st.session_state.route_history[-1]['lat'], st.session_state.route_history[-1]['lon'])
            curr_pt = (curr_lat, curr_lon)
            
            # Hitung jarak dari titik terakhir ke titik sekarang
            step_dist = geodesic(last_pt, curr_pt).kilometers
            
            # Filter GPS "Melompat" (Akurasi rendah biasanya melompat jauh tiba-tiba)
            if step_dist < 0.5: # Hanya tambah jika jarak masuk akal dalam 10 detik
                st.session_state.total_km += step_dist

        # Simpan ke Riwayat
        st.session_state.route_history.append({
            'lat': curr_lat, 
            'lon': curr_lon, 
            'waktu': now
        })

        # Update Tampilan Metrik
        placeholder_dist.metric("Total Jarak", f"{st.session_state.total_km:.3f} KM")
        placeholder_pts.metric("Titik Tercatat", len(st.session_state.route_history))
        placeholder_time.metric("Update Terakhir", now)

        # Update Peta
        df_route = pd.DataFrame(st.session_state.route_history)
        placeholder_map.map(df_route[['lat', 'lon']])

        # Jeda 10 detik sebelum refresh otomatis
        time.sleep(10)
        st.rerun()
    else:
        st.warning("📡 Mencari sinyal GPS... Pastikan izin lokasi aktif.")

# 6. Fitur Setelah Berhenti (Ekspor Data)
if not st.session_state.tracking_active and len(st.session_state.route_history) > 0:
    st.divider()
    st.success(f"Selesai! Total jarak yang Anda tempuh: {st.session_state.total_km:.3f} KM")
    
    df_final = pd.DataFrame(st.session_state.route_history)
    
    # Tombol Download CSV
    csv = df_final.to_csv(index=False).encode('utf-8')
    st.download_button(
        label="📥 Download Data Rute (CSV)",
        data=csv,
        file_name=f"rute_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
        mime='text/csv',
    )
    
    st.subheader("Riwayat Koordinat")
    st.dataframe(df_final, use_container_width=True)
