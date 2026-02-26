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

import streamlit as st
from PIL import Image
import io
import pandas as pd
from datetime import datetime

# --- FUNGSI KOMPRESI FOTO ---
def compress_image(uploaded_file, quality=60):
    # 1. Buka foto dari input kamera
    img = Image.open(uploaded_file)
    
    # 2. Ubah ukuran (Resize) jika terlalu besar (max lebar 800px)
    if img.width > 800:
        new_height = int(800 * img.height / img.width)
        img = img.resize((800, new_height), Image.LANCZOS)
    
    # 3. Ubah ke mode RGB (untuk memastikan bisa simpan ke JPEG)
    if img.mode in ("RGBA", "P"):
        img = img.convert("RGB")
        
    # 4. Simpan ke memory buffer dengan kompresi
    buffer = io.BytesIO()
    img.save(buffer, format="JPEG", quality=quality, optimize=True)
    return buffer.getvalue()

# --- TAMPILAN DASHBOARD ---
st.divider()
st.subheader("📸 Dokumentasi Rute (Terkompresi)")

# Inisialisasi galeri di memori (session state)
if 'photo_gallery' not in st.session_state:
    st.session_state.photo_gallery = []

# Input Kamera
img_file = st.camera_input("Ambil Foto Perjalanan")

if img_file:
    # Proses Kompresi
    with st.spinner('Sedang mengompres foto...'):
        compressed_data = compress_image(img_file, quality=50) # Kualitas 50%
        size_kb = len(compressed_data) / 1024

    # Ambil data lokasi terakhir dari tracking (jika ada)
    if 'route_history' in st.session_state and st.session_state.route_history:
        last_loc = st.session_state.route_history[-1]
        lat, lon = last_loc['lat'], last_loc['lon']
        km = st.session_state.get('total_km', 0.0)
    else:
        lat, lon, km = 0.0, 0.0, 0.0

    # Data Foto untuk Galeri
    timestamp = datetime.now().strftime("%H:%M:%S")
    foto_item = {
        "bin": compressed_data,
        "lat": lat,
        "lon": lon,
        "km": km,
        "waktu": timestamp,
        "size": size_kb
    }

    # Simpan ke galeri (cegah duplikasi saat rerun)
    if not st.session_state.photo_gallery or st.session_state.photo_gallery[-1]['waktu'] != timestamp:
        st.session_state.photo_gallery.append(foto_item)
        st.toast(f"Foto tersimpan! Ukuran: {size_kb:.1f} KB", icon="✅")

# --- TAMPILAN GALERI ---
if st.session_state.photo_gallery:
    st.write(f"### 🖼️ Galeri Foto ({len(st.session_state.photo_gallery)} Foto)")
    
    # Tampilkan dalam grid 2 kolom
    cols = st.columns(2)
    for i, item in enumerate(st.session_state.photo_gallery):
        with cols[i % 2]:
            st.image(item['bin'], use_container_width=True)
            st.caption(f"📍 KM {item['km']:.2f} | 🕒 {item['waktu']} | ⚖️ {item['size']:.1f} KB")
            
            # Tombol download untuk tiap foto
            st.download_button(
                label=f"💾 Simpan Foto {i+1}",
                data=item['bin'],
                file_name=f"foto_km_{item['km']:.2f}.jpg",
                mime="image/jpeg",
                key=f"dl_{i}"
            )

    if st.button("🗑️ Kosongkan Galeri"):
        st.session_state.photo_gallery = []
        st.rerun()
