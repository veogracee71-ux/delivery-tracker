# Versi 3.0 (Modern Prototype)
# Status: Prototype / Design Upgrade
# Update: Transformasi UI total. Navigasi atas, pembersihan emoji, dan layout kartu premium.

import streamlit as st
import streamlit.components.v1 as components 
from supabase import create_client, Client
from streamlit_option_menu import option_menu # Library Navigasi Baru
import streamlit_antd_components as sac # Library Komponen Modern
import time
from datetime import datetime, date, timedelta
from fpdf import FPDF
import base64
import qrcode
import tempfile
import os
import pandas as pd
import io 

# --- KONFIGURASI HALAMAN ---
st.set_page_config(
    page_title="Delivery Tracker Pro", 
    page_icon="📦", 
    layout="wide", 
    initial_sidebar_state="collapsed" 
)

# --- LOAD SECRETS & SUPABASE ---
try:
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    ADMIN_PASSWORD = st.secrets["passwords"]["admin"]
    SALES_CREDENTIALS = st.secrets["passwords"]["sales"]
    SPV_CREDENTIALS = st.secrets["passwords"]["spv"]
    GATEKEEPER_PASSWORD = st.secrets["passwords"].get("gatekeeper", "blibli")
except:
    st.error("Konfigurasi Secrets tidak ditemukan.")
    st.stop()

supabase: Client = create_client(url, key)
APP_BASE_URL = "https://delivery-tracker.streamlit.app"

# --- CUSTOM CSS (MODERN UI) ---
st.markdown("""
<style>
    /* Import Font Premium */
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;600;700&family=Inter:wght@400;600&display=swap');

    html, body, [class*="css"] {
        font-family: 'Plus Jakarta Sans', sans-serif;
    }

    /* Background Aplikasi */
    .stApp {
        background-color: #F8FAFC;
    }

    /* Desain Kartu (Shadow & Rounded) */
    div[data-testid="stVerticalBlock"] > div.element-container:has(div.card-ui) {
        background: white;
        padding: 2rem;
        border-radius: 20px;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
        margin-bottom: 1.5rem;
    }

    /* Tombol Biru Blibli Pro */
    div.stButton > button {
        background-color: #0095DA !important;
        color: white !important;
        border-radius: 12px !important;
        padding: 0.6rem 2rem !important;
        font-weight: 600 !important;
        border: none !important;
        transition: all 0.3s ease;
    }
    div.stButton > button:hover {
        background-color: #007AB8 !important;
        transform: translateY(-2px);
        box-shadow: 0 10px 15px -3px rgba(0, 149, 218, 0.3);
    }

    /* Sidebar Hider */
    [data-testid="collapsedControl"] { display: none; }
    section[data-testid="stSidebar"] { display: none; }

    /* Hide Streamlit Header */
    header {visibility: hidden;}
    .main .block-container {padding-top: 1rem;}
</style>
""", unsafe_allow_html=True)

# --- FUNGSI BANTUAN ---
def get_status_color(status):
    s = str(status).lower()
    if "selesai" in s: return "#10B981" # Green
    if "dikirim" in s or "jalan" in s: return "#3B82F6" # Blue
    return "#F59E0B" # Orange

# --- SESSION STATE INITIALIZATION ---
if 'user_role' not in st.session_state: st.session_state['user_role'] = "Guest"
if 'user_branch' not in st.session_state: st.session_state['user_branch'] = ""
if 'gate_unlocked' not in st.session_state: st.session_state['gate_unlocked'] = False

# ==========================================
# MODERN NAVIGATION (TOP NAVBAR)
# ==========================================
role = st.session_state['user_role']

if role == "Guest":
    menu_items = ["Lacak Paket", "Login Staff"]
    icons = ["search", "person-lock"]
elif role == "Sales":
    menu_items = ["Dashboard", "Input Order", "Lacak Paket", "Keluar"]
    icons = ["grid", "plus-circle", "search", "box-arrow-right"]
elif role == "SPV":
    menu_items = ["Dashboard", "Input Order", "Update Status", "Laporan", "Lacak Paket", "Keluar"]
    icons = ["grid", "plus-circle", "check2-circle", "file-earmark-bar-graph", "search", "box-arrow-right"]
elif role == "Admin":
    menu_items = ["Dashboard", "Update Status", "Laporan", "Lacak Paket", "Keluar"]
    icons = ["grid", "check2-circle", "database", "search", "box-arrow-right"]

# Container Navbar
with st.container():
    selected_menu = option_menu(
        menu_title=None,
        options=menu_items,
        icons=icons,
        menu_icon="cast",
        default_index=0,
        orientation="horizontal",
        styles={
            "container": {"padding": "0!important", "background-color": "#ffffff", "border-radius": "0px", "box-shadow": "0 1px 2px 0 rgba(0,0,0,0.05)"},
            "icon": {"color": "#64748B", "font-size": "18px"}, 
            "nav-link": {"font-size": "15px", "text-align": "center", "margin":"0px", "--hover-color": "#F1F5F9", "color": "#475569"},
            "nav-link-selected": {"background-color": "#0095DA", "color": "white"},
        }
    )

st.markdown("<br>", unsafe_allow_html=True)

# Handle Logout
if selected_menu == "Keluar":
    st.session_state['user_role'] = "Guest"
    st.session_state['user_branch'] = ""
    st.rerun()

# ==========================================
# PAGE: LACAK PAKET (CEK RESI)
# ==========================================
if selected_menu == "Lacak Paket":
    st.markdown("<h2 style='text-align: center; color: #1E293B;'>Pelacakan Pengiriman</h2>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; color: #64748B;'>Masukkan Order ID untuk melihat posisi barang secara real-time</p>", unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1,2,1])
    with col2:
        oid = st.text_input("", placeholder="Contoh: INV-12345", label_visibility="collapsed")
        search_btn = st.button("Cari Pesanan", use_container_width=True)
        
        if search_btn and oid:
            try:
                res = supabase.table("shipments").select("*").eq("order_id", oid).execute()
                if res.data:
                    d = res.data[0]
                    st.markdown(f"""
                    <div style='background: white; padding: 25px; border-radius: 20px; box-shadow: 0 10px 15px -3px rgba(0,0,0,0.1); border-top: 5px solid #0095DA;'>
                        <h4 style='margin-bottom: 0;'>{d['product_name']}</h4>
                        <p style='color: #64748B; font-size: 14px;'>Order ID: {d['order_id']}</p>
                        <hr style='opacity: 0.1;'>
                        <div style='display: flex; justify-content: space-between; align-items: center;'>
                            <span style='color: #475569; font-weight: 600;'>Status:</span>
                            <span style='background: {get_status_color(d['status'])}20; color: {get_status_color(d['status'])}; padding: 5px 15px; border-radius: 20px; font-weight: bold; font-size: 14px;'>{d['status'].upper()}</span>
                        </div>
                        <p style='margin-top: 15px; font-size: 14px; color: #64748B;'>Penerima: <b>{d['customer_name']}</b></p>
                        <p style='font-size: 14px; color: #64748B;'>Kurir: {d['courier'] or '-'}</p>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    # Visual Step Indicator (Modern)
                    current_status = d['status']
                    steps = ["Menunggu Konfirmasi", "Diproses Gudang", "Dalam Pengiriman", "Selesai/Diterima"]
                    try: current_idx = steps.index(current_status)
                    except: current_idx = 0
                    
                    st.markdown("<br>", unsafe_allow_html=True)
                    sac.steps(
                        items=[sac.StepsItem(title=s) for s in steps],
                        index=current_idx,
                        color='#0095DA'
                    )
                else:
                    st.warning("Pesanan tidak ditemukan.")
            except: st.error("Koneksi bermasalah.")

# ==========================================
# PAGE: DASHBOARD (MODERN CARDS)
# ==========================================
elif selected_menu == "Dashboard":
    st.markdown(f"### Dashboard Operasional: {st.session_state['user_branch']}")
    
    try:
        res = supabase.table("shipments").select("*").execute()
        if res.data:
            # Filtering
            if role in ["Sales", "SPV"]:
                filtered = [d for d in res.data if d.get('branch') == st.session_state['user_branch']]
            else: filtered = res.data

            # Metrik dalam Kartu
            c1, c2, c3 = st.columns(3)
            with c1:
                st.markdown(f"""<div style='background: white; padding: 20px; border-radius: 15px; text-align: center; border-left: 5px solid #F59E0B;'>
                    <p style='margin:0; color:#64748B;'>Gudang</p>
                    <h2 style='margin:0; color:#1E293B;'>{len([x for x in filtered if "selesai" not in x['status'].lower() and "kirim" not in x['status'].lower()])}</h2>
                </div>""", unsafe_allow_html=True)
            with c2:
                st.markdown(f"""<div style='background: white; padding: 20px; border-radius: 15px; text-align: center; border-left: 5px solid #3B82F6;'>
                    <p style='margin:0; color:#64748B;'>Di Jalan</p>
                    <h2 style='margin:0; color:#1E293B;'>{len([x for x in filtered if "kirim" in x['status'].lower() or "jalan" in x['status'].lower()])}</h2>
                </div>""", unsafe_allow_html=True)
            with c3:
                st.markdown(f"""<div style='background: white; padding: 20px; border-radius: 15px; text-align: center; border-left: 5px solid #10B981;'>
                    <p style='margin:0; color:#64748B;'>Selesai</p>
                    <h2 style='margin:0; color:#1E293B;'>{len([x for x in filtered if "selesai" in x['status'].lower()])}</h2>
                </div>""", unsafe_allow_html=True)
            
            st.markdown("<br>", unsafe_allow_html=True)
            
            # Tabel Data Clean
            df = pd.DataFrame(filtered)
            if not df.empty:
                df['Waktu'] = pd.to_datetime(df['last_updated']).dt.strftime('%d %b, %H:%M')
                st.dataframe(df[['order_id', 'customer_name', 'product_name', 'status', 'Waktu']], use_container_width=True, hide_index=True)
        else:
            st.info("Belum ada data.")
    except: st.error("Gagal memuat data.")

# ==========================================
# PAGE: LOGIN STAFF (MODERN GATE)
# ==========================================
elif selected_menu == "Login Staff":
    if not st.session_state['gate_unlocked']:
        st.markdown("<div style='text-align:center;'>", unsafe_allow_html=True)
        st.markdown("## 🔒 Akses Terbatas")
        st.markdown("Masukkan Kode Akses Perusahaan")
        col1, col2, col3 = st.columns([1,1.5,1])
        with col2:
            pin = st.text_input("Kode Akses", type="password", label_visibility="collapsed")
            if st.button("Buka Pintu"):
                if pin == GATEKEEPER_PASSWORD:
                    st.session_state['gate_unlocked'] = True; st.rerun()
                else: st.error("Kode Salah")
        st.stop()
    
    st.markdown("### Pilih Akun Anda")
    col1, col2, col3 = st.columns([1,2,1])
    with col2:
        with st.container(border=True):
            tp = sac.segmented(items=[sac.SegmentedItem(label='Sales'), sac.SegmentedItem(label='SPV'), sac.SegmentedItem(label='Admin')], color='#0095DA', align='center')
            
            if tp in ['Sales', 'SPV']:
                cb = st.selectbox("Cabang", list(SALES_CREDENTIALS.keys()))
                pw = st.text_input("Password", type="password")
                if st.button("Masuk"):
                    creds = SALES_CREDENTIALS if tp == 'Sales' else SPV_CREDENTIALS
                    if pw == creds.get(cb):
                        st.session_state.update({'user_role': tp, 'user_branch': cb})
                        st.rerun()
                    else: st.error("Password Salah")
            else:
                pw = st.text_input("Admin Password", type="password")
                if st.button("Masuk Admin"):
                    if pw == ADMIN_PASSWORD:
                        st.session_state.update({'user_role': "Admin", 'user_branch': "Pusat"})
                        st.rerun()
                    else: st.error("Password Salah")

# --- PLACEHOLDER UNTUK MENU LAIN ---
else:
    st.info(f"Halaman {selected_menu} sedang dikonfigurasi ulang untuk tampilan V3.0.")
