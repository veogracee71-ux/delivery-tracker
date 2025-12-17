# Versi 3.0 (Modern UI/UX Edition) - FIXED
# Status: Production Ready
# Update: Complete UI/UX overhaul dengan navigasi modern

import streamlit as st
import streamlit.components.v1 as components 
from supabase import create_client, Client
from urllib.parse import quote
import time
from datetime import datetime, date, timedelta
from fpdf import FPDF
import base64
import qrcode
import tempfile
import os
import pandas as pd
import io 

# Optional: Plotly untuk charts (install dengan: pip install plotly)
try:
    import plotly.express as px
    import plotly.graph_objects as go
    PLOTLY_AVAILABLE = True
except ImportError:
    PLOTLY_AVAILABLE = False

# --- KONFIGURASI HALAMAN ---
st.set_page_config(
    page_title="📦 Delivery Tracker Pro", 
    page_icon="📦", 
    layout="wide", 
    initial_sidebar_state="expanded"
)

# --- LINK APLIKASI ---
APP_BASE_URL = "https://delivery-tracker.streamlit.app" 

# --- LOAD SECRETS ---
try:
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    ADMIN_PASSWORD = st.secrets["passwords"]["admin"]
    SALES_CREDENTIALS = st.secrets["passwords"]["sales"]
    SPV_CREDENTIALS = st.secrets["passwords"]["spv"]
    GATEKEEPER_PASSWORD = st.secrets["passwords"].get("gatekeeper", "blibli")
    supabase: Client = create_client(url, key)
except Exception as e:
    GATEKEEPER_PASSWORD = "blibli"
    ADMIN_PASSWORD = "admin123"
    SALES_CREDENTIALS = {"Jakarta": "jkt123", "Bandung": "bdg123"}
    SPV_CREDENTIALS = {"Jakarta": "spvjkt", "Bandung": "spvbdg"}
    supabase = None

# =============================================
# 🎨 CUSTOM CSS - MODERN UI DESIGN SYSTEM
# =============================================
st.markdown("""
<style>
    /* ===== ROOT VARIABLES ===== */
    :root {
        --primary: #0095DA;
        --primary-dark: #007AB8;
        --primary-light: #E3F2FD;
        --success: #10B981;
        --warning: #F59E0B;
        --danger: #EF4444;
        --info: #3B82F6;
        --dark: #1F2937;
        --light: #F9FAFB;
        --gray: #6B7280;
        --border-radius: 12px;
        --shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
        --shadow-lg: 0 10px 15px -3px rgba(0, 0, 0, 0.1);
    }
    
    /* ===== GLOBAL STYLES ===== */
    .main .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
        max-width: 1400px;
    }
    
    /* ===== HEADER BRANDING ===== */
    .brand-header {
        background: linear-gradient(135deg, var(--primary) 0%, var(--primary-dark) 100%);
        padding: 1.5rem 2rem;
        border-radius: var(--border-radius);
        margin-bottom: 2rem;
        box-shadow: var(--shadow-lg);
    }
    
    .brand-header h1 {
        color: white !important;
        margin: 0;
        font-size: 1.8rem;
        font-weight: 700;
    }
    
    .brand-header p {
        color: rgba(255,255,255,0.85);
        margin: 0.5rem 0 0 0;
        font-size: 0.95rem;
    }
    
    /* ===== STAT CARDS ===== */
    .stat-card {
        background: white;
        padding: 1.5rem;
        border-radius: var(--border-radius);
        box-shadow: var(--shadow);
        border-left: 4px solid var(--primary);
        transition: transform 0.3s ease, box-shadow 0.3s ease;
    }
    
    .stat-card:hover {
        transform: translateY(-5px);
        box-shadow: var(--shadow-lg);
    }
    
    .stat-card.warning { border-left-color: var(--warning); }
    .stat-card.success { border-left-color: var(--success); }
    .stat-card.info { border-left-color: var(--info); }
    .stat-card.danger { border-left-color: var(--danger); }
    
    .stat-number {
        font-size: 2.5rem;
        font-weight: 700;
        color: var(--dark);
        line-height: 1;
    }
    
    .stat-label {
        color: var(--gray);
        font-size: 0.9rem;
        margin-top: 0.5rem;
        font-weight: 500;
    }
    
    /* ===== STATUS BADGES ===== */
    .status-badge {
        display: inline-flex;
        align-items: center;
        gap: 0.4rem;
        padding: 0.4rem 0.8rem;
        border-radius: 50px;
        font-size: 0.8rem;
        font-weight: 600;
    }
    
    .status-pending { background: #FEF3C7; color: #92400E; }
    .status-shipping { background: #DBEAFE; color: #1E40AF; }
    .status-done { background: #D1FAE5; color: #065F46; }
    .status-new { background: #FEE2E2; color: #991B1B; animation: pulse 2s infinite; }
    
    @keyframes pulse {
        0%, 100% { opacity: 1; }
        50% { opacity: 0.7; }
    }
    
    /* ===== CARDS & CONTAINERS ===== */
    .modern-card {
        background: white;
        border-radius: var(--border-radius);
        padding: 1.5rem;
        box-shadow: var(--shadow);
        margin-bottom: 1rem;
    }
    
    /* ===== FORM STYLING ===== */
    .stTextInput > div > div > input,
    .stTextArea > div > div > textarea,
    .stSelectbox > div > div > div {
        border-radius: 8px !important;
        border: 2px solid #E5E7EB !important;
    }
    
    .stTextInput > div > div > input:focus,
    .stTextArea > div > div > textarea:focus {
        border-color: var(--primary) !important;
        box-shadow: 0 0 0 3px rgba(0, 149, 218, 0.1) !important;
    }
    
    /* ===== BUTTONS ===== */
    .stButton > button {
        background: linear-gradient(135deg, var(--primary) 0%, var(--primary-dark) 100%) !important;
        color: white !important;
        border: none !important;
        border-radius: 8px !important;
        padding: 0.6rem 1.5rem !important;
        font-weight: 600 !important;
        box-shadow: 0 4px 12px rgba(0, 149, 218, 0.3) !important;
    }
    
    .stButton > button:hover {
        transform: translateY(-2px) !important;
        box-shadow: 0 6px 16px rgba(0, 149, 218, 0.4) !important;
    }
    
    div.stFormSubmitButton > button {
        background: linear-gradient(135deg, var(--primary) 0%, var(--primary-dark) 100%) !important;
        width: 100%;
    }
    
    /* ===== SIDEBAR STYLING ===== */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #1F2937 0%, #111827 100%);
    }
    
    [data-testid="stSidebar"] .stRadio > label,
    [data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p {
        color: rgba(255,255,255,0.8) !important;
    }
    
    .sidebar-logo {
        text-align: center;
        padding: 1.5rem 1rem;
        border-bottom: 1px solid rgba(255,255,255,0.1);
        margin-bottom: 1rem;
    }
    
    .sidebar-logo h2 {
        color: white;
        font-size: 1.3rem;
        margin: 0.5rem 0 0 0;
    }
    
    /* ===== ALERT BOXES ===== */
    .alert-box {
        padding: 1rem 1.25rem;
        border-radius: 8px;
        margin-bottom: 1rem;
        display: flex;
        align-items: flex-start;
        gap: 0.75rem;
    }
    
    .alert-warning { background: #FEF3C7; border: 1px solid #F59E0B; color: #92400E; }
    .alert-success { background: #D1FAE5; border: 1px solid #10B981; color: #065F46; }
    .alert-danger { background: #FEE2E2; border: 1px solid #EF4444; color: #991B1B; }
    .alert-info { background: #DBEAFE; border: 1px solid #3B82F6; color: #1E40AF; }
    
    /* ===== PROGRESS TRACKER ===== */
    .progress-tracker {
        display: flex;
        justify-content: space-between;
        margin: 2rem 0;
        position: relative;
    }
    
    .progress-tracker::before {
        content: '';
        position: absolute;
        top: 20px;
        left: 0;
        right: 0;
        height: 4px;
        background: #E5E7EB;
        z-index: 1;
    }
    
    .progress-step {
        display: flex;
        flex-direction: column;
        align-items: center;
        position: relative;
        z-index: 2;
    }
    
    .progress-step-icon {
        width: 40px;
        height: 40px;
        border-radius: 50%;
        background: #E5E7EB;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 1.2rem;
        margin-bottom: 0.5rem;
    }
    
    .progress-step.active .progress-step-icon { background: var(--primary); color: white; }
    .progress-step.completed .progress-step-icon { background: var(--success); color: white; }
    
    .progress-step-label {
        font-size: 0.75rem;
        color: var(--gray);
        text-align: center;
        max-width: 80px;
    }
    
    /* ===== EMPTY STATE ===== */
    .empty-state {
        text-align: center;
        padding: 3rem;
        color: var(--gray);
    }
    
    .empty-state-icon {
        font-size: 4rem;
        margin-bottom: 1rem;
        opacity: 0.5;
    }
    
    /* ===== ANIMATIONS ===== */
    @keyframes fadeIn {
        from { opacity: 0; transform: translateY(10px); }
        to { opacity: 1; transform: translateY(0); }
    }
    
    .animate-fade-in { animation: fadeIn 0.5s ease forwards; }
    
    /* ===== RESPONSIVE ===== */
    @media (max-width: 768px) {
        .stat-card { padding: 1rem; }
        .stat-number { font-size: 1.8rem; }
        .brand-header h1 { font-size: 1.4rem; }
    }
</style>
""", unsafe_allow_html=True)

# =============================================
# 🔧 HELPER FUNCTIONS
# =============================================

def get_status_color(status):
    s = str(status).lower()
    if "selesai" in s or "diterima" in s: 
        return "success"
    elif "dikirim" in s or "jalan" in s or "pengiriman" in s: 
        return "info"
    elif "konfirmasi" in s:
        return "danger"
    return "warning"

def get_status_badge(status):
    s = str(status).lower()
    if "selesai" in s or "diterima" in s:
        return f'<span class="status-badge status-done">✅ {status}</span>'
    elif "dikirim" in s or "jalan" in s or "pengiriman" in s:
        return f'<span class="status-badge status-shipping">🚚 {status}</span>'
    elif "konfirmasi" in s:
        return f'<span class="status-badge status-new">🔔 {status}</span>'
    return f'<span class="status-badge status-pending">⏳ {status}</span>'

def render_stat_card(icon, number, label, color="primary"):
    return f"""
    <div class="stat-card {color}">
        <div style="display: flex; justify-content: space-between; align-items: center;">
            <div>
                <div class="stat-number">{number}</div>
                <div class="stat-label">{label}</div>
            </div>
            <div style="font-size: 2rem; opacity: 0.8;">{icon}</div>
        </div>
    </div>
    """

def render_header(title, subtitle=""):
    st.markdown(f"""
    <div class="brand-header">
        <h1>📦 {title}</h1>
        <p>{subtitle}</p>
    </div>
    """, unsafe_allow_html=True)

def render_progress_tracker(current_status):
    steps = [
        ("📝", "Order Dibuat"),
        ("✅", "Dikonfirmasi"),
        ("📦", "Diproses"),
        ("🚚", "Dikirim"),
        ("🏠", "Diterima")
    ]
    
    status_map = {
        "Menunggu Konfirmasi": 0,
        "Diproses Gudang": 2,
        "Menunggu Kurir": 2,
        "Dalam Pengiriman": 3,
        "Selesai/Diterima": 4
    }
    
    current_step = status_map.get(current_status, 0)
    
    html = '<div class="progress-tracker">'
    for i, (icon, label) in enumerate(steps):
        if i < current_step:
            status_class = "completed"
        elif i == current_step:
            status_class = "active"
        else:
            status_class = ""
        
        html += f"""
        <div class="progress-step {status_class}">
            <div class="progress-step-icon">{icon}</div>
            <div class="progress-step-label">{label}</div>
        </div>
        """
    html += '</div>'
    return html

# --- FUNGSI CETAK PDF ---
def create_thermal_pdf(data, print_timestamp):
    def safe_text(text):
        if not text: return "-"
        return str(text).encode('latin-1', 'replace').decode('latin-1')

    pdf = FPDF(orientation='P', unit='mm', format=(80, 250))
    pdf.add_page()
    margin = 4
    pdf.set_margins(margin, margin, margin)
    w_full = 72
    
    def draw_line():
        pdf.ln(2)
        y = pdf.get_y()
        pdf.line(margin, y, margin + w_full, y)
        pdf.ln(2)

    pdf.set_font("Arial", 'B', 16)
    pdf.set_x(0)
    pdf.cell(80, 8, "SURAT JALAN", 0, 1, 'C')
    pdf.set_x(margin)
    draw_line()
    
    pdf.set_font("Arial", '', 10)
    pdf.cell(20, 5, "No Order", 0, 0)
    pdf.set_font("Arial", 'B', 11)
    pdf.cell(52, 5, f": {safe_text(data['order_id'])}", 0, 1)
    
    pdf.set_font("Arial", '', 10)
    pdf.cell(20, 5, "Tanggal", 0, 0)
    pdf.cell(52, 5, f": {print_timestamp.strftime('%d/%m/%Y %H:%M')}", 0, 1)
    draw_line()
    
    pdf.set_font("Arial", 'B', 11)
    pdf.cell(w_full, 6, "PENERIMA:", 0, 1)
    pdf.set_font("Arial", 'B', 12)
    pdf.multi_cell(w_full, 6, safe_text(data['customer_name']))
    pdf.set_font("Arial", '', 11)
    pdf.cell(w_full, 6, f"HP: {safe_text(data['customer_phone'])}", 0, 1)
    pdf.ln(1)
    pdf.set_font("Arial", '', 11)
    pdf.multi_cell(w_full, 5, safe_text(data['delivery_address']))
    draw_line()
    
    pdf.set_font("Arial", 'B', 11)
    pdf.cell(w_full, 6, "SALES:", 0, 1)
    pdf.set_font("Arial", '', 10)
    pdf.cell(15, 5, "Nama", 0, 0)
    pdf.cell(57, 5, f": {safe_text(data['sales_name'])} ({safe_text(data['branch'])})", 0, 1)
    pdf.cell(15, 5, "HP", 0, 0)
    pdf.cell(57, 5, f": {safe_text(data.get('sales_phone', '-'))}", 0, 1)
    draw_line()
    
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(w_full, 8, "BARANG:", 0, 1)
    pdf.set_font("Arial", 'B', 11)
    pdf.multi_cell(w_full, 6, f"- {safe_text(data['product_name'])}")
    pdf.ln(2)
    pdf.set_font("Arial", '', 10)
    pdf.cell(25, 5, "Tipe Kirim", 0, 0)
    pdf.cell(47, 5, f": {safe_text(data['delivery_type'])}", 0, 1)
    
    if data['delivery_type'] == "Tukar Tambah" and data.get('old_product_name'):
        pdf.set_font("Arial", 'I', 9)
        pdf.cell(25, 5, "Brg Lama", 0, 0)
        pdf.multi_cell(47, 5, f": {safe_text(data.get('old_product_name'))}")
        pdf.set_font("Arial", '', 10)

    if data.get('installation_opt') == "Ya - Vendor":
        pdf.cell(25, 5, "Instalasi", 0, 0)
        pdf.cell(47, 5, ": YA (Vendor)", 0, 1)
        pdf.cell(25, 5, "Biaya", 0, 0)
        pdf.cell(47, 5, f": Rp {safe_text(data.get('installation_fee', '-'))}", 0, 1)
    draw_line()
    
    pdf.ln(5)
    y_start = pdf.get_y()
    col_w = 36
    pdf.set_font("Arial", '', 10)
    pdf.set_xy(margin, y_start)
    pdf.cell(col_w, 5, "Sales,", 0, 0, 'C')
    pdf.set_xy(margin + col_w, y_start)
    pdf.cell(col_w, 5, "Penerima,", 0, 1, 'C')
    pdf.ln(20)
    y_end = pdf.get_y()
    pdf.set_font("Arial", 'B', 10)
    pdf.set_xy(margin, y_end)
    pdf.cell(col_w, 5, f"({safe_text(data['sales_name'])})", 0, 0, 'C')
    pdf.set_xy(margin + col_w, y_end)
    pdf.cell(col_w, 5, f"({safe_text(data['customer_name'])})", 0, 1, 'C')
    pdf.ln(8)
    
    qr_url = f"{APP_BASE_URL}/?oid={data['order_id']}"
    qr = qrcode.make(qr_url)
    with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as tmp:
        qr.save(tmp.name)
        tmp_path = tmp.name
    
    qr_x = margin + (w_full - 30) / 2
    pdf.image(tmp_path, x=qr_x, w=30) 
    os.unlink(tmp_path)
    
    pdf.ln(2)
    pdf.set_x(0)
    pdf.set_font("Arial", 'B', 10)
    pdf.cell(80, 5, "SCAN UNTUK TRACKING", 0, 1, 'C')
    
    return pdf.output(dest='S').encode('latin-1')

# --- CALLBACK SALES SUBMIT ---
def process_sales_submit():
    st.session_state['sales_success'] = False
    st.session_state['sales_error'] = None
    s = st.session_state
    
    in_id = s.get("in_id", "")
    in_sales = s.get("in_sales", "")
    in_sales_hp = s.get("in_sales_hp", "")
    in_nama = s.get("in_nama", "")
    in_hp = s.get("in_hp", "")
    in_alamat = s.get("in_alamat", "")
    in_barang = s.get("in_barang", "")
    in_tipe = s.get("in_tipe", "Reguler")
    branch = s.get("user_branch", "")
    
    in_old_item = s.get("in_barang_lama", "") if in_tipe == "Tukar Tambah" else ""
    in_inst = s.get("in_instalasi", "Tidak")
    in_fee = s.get("in_biaya_inst", "") if in_inst == "Ya - Vendor" else ""
    
    TIME_OFFSET = timedelta(hours=7) 
    current_time_wib = datetime.utcnow() + TIME_OFFSET 

    if not (in_id and in_sales and in_nama and in_barang):
        st.session_state['sales_error'] = "Data wajib belum lengkap (ID, Sales, Customer, Barang)."
        return

    if in_tipe == "Tukar Tambah" and not in_old_item:
        st.session_state['sales_error'] = "Anda memilih Tukar Tambah. Harap isi Detail Barang Lama!"
        return

    try:
        payload = {
            "order_id": in_id, 
            "customer_name": in_nama, 
            "customer_phone": in_hp,
            "delivery_address": in_alamat, 
            "product_name": in_barang, 
            "delivery_type": in_tipe,
            "sales_name": in_sales, 
            "sales_phone": in_sales_hp, 
            "branch": branch,
            "status": "Menunggu Konfirmasi", 
            "last_updated": current_time_wib.isoformat(),
            "installation_opt": in_inst, 
            "installation_fee": in_fee,
            "old_product_name": in_old_item
        }
        supabase.table("shipments").insert(payload).execute()
        
        pdf_bytes = create_thermal_pdf(payload, current_time_wib)
        b64_pdf = base64.b64encode(pdf_bytes).decode('latin-1')
        
        st.session_state['sales_success'] = True
        st.session_state['sales_pdf_data'] = b64_pdf
        st.session_state['sales_last_id'] = in_id
        
        for k in ["in_id", "in_sales", "in_sales_hp", "in_nama", "in_hp", "in_alamat", "in_barang", "in_biaya_inst", "in_barang_lama"]:
            st.session_state[k] = ""
        st.session_state["in_tipe"] = "Reguler"
        st.session_state["in_instalasi"] = "Tidak"
        
    except Exception as e:
        err_msg = str(e)
        if "duplicate key" in err_msg:
            st.session_state['sales_error'] = f"Order ID {in_id} sudah ada."
        else:
            st.session_state['sales_error'] = f"Error: {err_msg}"

# --- CALLBACK ADMIN UPDATE ---
def process_admin_update(oid):
    new_stat = st.session_state.get(f"stat_{oid}")
    new_kurir = st.session_state.get(f"kur_{oid}")
    new_resi = st.session_state.get(f"res_{oid}")
    d_date = st.session_state.get(f"date_{oid}")
    d_time = st.session_state.get(f"time_{oid}")
    corr_nama = st.session_state.get(f"cnama_{oid}")
    corr_barang = st.session_state.get(f"cbar_{oid}")
    
    final_dt = datetime.combine(d_date, d_time).isoformat()
    
    upd = {
        "status": new_stat, 
        "courier": new_kurir, 
        "resi": new_resi,
        "last_updated": final_dt, 
        "customer_name": corr_nama, 
        "product_name": corr_barang
    }
    
    try:
        supabase.table("shipments").update(upd).eq("order_id", oid).execute()
        st.toast("✅ Data berhasil diupdate!", icon="✅")
        st.session_state["upd_sel"] = None
    except Exception as e:
        st.toast(f"❌ Error: {e}", icon="❌")

# =============================================
# 🎛️ SESSION STATE INITIALIZATION
# =============================================
if 'user_role' not in st.session_state: 
    st.session_state['user_role'] = "Guest" 
if 'user_branch' not in st.session_state: 
    st.session_state['user_branch'] = ""
if 'current_page' not in st.session_state:
    st.session_state['current_page'] = "tracking"

# =============================================
# 📱 SIDEBAR - MODERN NAVIGATION
# =============================================
with st.sidebar:
    # Logo & Branding
    st.markdown("""
    <div class="sidebar-logo">
        <div style="font-size: 3rem;">📦</div>
        <h2>Delivery Tracker</h2>
        <p style="font-size: 0.8rem; opacity: 0.7;">v3.0 Modern Edition</p>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # User Info Card
    if st.session_state['user_role'] != "Guest":
        user_role = st.session_state['user_role']
        user_branch = st.session_state['user_branch']
        role_colors = {"Admin": "#EF4444", "SPV": "#F59E0B", "Sales": "#10B981"}
        role_color = role_colors.get(user_role, "#6B7280")
        role_initial = user_role,[object Object], if user_role else "U"
        
        st.markdown(f"""
        <div style="background: rgba(255,255,255,0.1); padding: 1rem; border-radius: 8px; margin-bottom: 1rem;">
            <div style="display: flex; align-items: center; gap: 0.75rem;">
                <div style="width: 40px; height: 40px; border-radius: 50%; background: {role_color}; 
                            display: flex; align-items: center; justify-content: center; color: white; font-weight: bold;">
                    {role_initial}
                </div>
                <div>
                    <div style="color: white; font-weight: 600;">{user_role}</div>
                    <div style="color: rgba(255,255,255,0.6); font-size: 0.8rem;">{user_branch}</div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    # Navigation Menu
    st.markdown('<p style="color: rgba(255,255,255,0.5); font-size: 0.75rem; text-transform: uppercase; letter-spacing: 1px; margin-bottom: 0.5rem;">Menu Utama</p>', unsafe_allow_html=True)
    
    # Define menu based on role
    user_role = st.session_state['user_role']
    if user_role == "Guest":
        menu_items = [
            ("🔍", "Lacak Paket", "tracking"),
            ("🔐", "Login Staff", "login")
        ]
    elif user_role == "Sales":
        menu_items = [
            ("📊", "Dashboard", "dashboard"),
            ("📝", "Input Order", "input"),
            ("🔍", "Lacak Paket", "tracking")
        ]
    elif user_role == "SPV":
        menu_items = [
            ("📊", "Dashboard", "dashboard"),
            ("📝", "Input Order", "input"),
            ("⚙️", "Update Status", "update"),
            ("🗄️", "Manajemen Data", "data"),
            ("🔍", "Lacak Paket", "tracking")
        ]
    elif user_role == "Admin":
        menu_items = [
            ("📊", "Dashboard", "dashboard"),
            ("⚙️", "Update Status", "update"),
            ("🗄️", "Manajemen Data", "data"),
            ("🔍", "Lacak Paket", "tracking")
        ]
    else:
        menu_items = [("🔍", "Lacak Paket", "tracking")]
    
    for icon, label, page_key in menu_items:
        if st.button(f"{icon}  {label}", key=f"nav_{page_key}", use_container_width=True):
            st.session_state['current_page'] = page_key
            st.rerun()
    
    st.markdown("---")
    
    # Logout Button
    if st.session_state['user_role'] != "Guest":
        if st.button("🚪 Logout", use_container_width=True):
            st.session_state['user_role'] = "Guest"
            st.session_state['user_branch'] = ""
            st.session_state['current_page'] = "tracking"
            st.rerun()
    
    # Footer
    st.markdown("---")
    st.markdown("""
    <div style="text-align: center; padding: 1rem 0;">
        <p style="color: rgba(255,255,255,0.4); font-size: 0.7rem; margin: 0;">
            © 2025 Delivery Tracker<br>
            Developed by Agung Sudrajat
        </p>
    </div>
    """, unsafe_allow_html=True)

# =============================================
# 📄 MAIN CONTENT AREA
# =============================================

current_page = st.session_state.get('current_page', 'tracking')

# ==========================================
# PAGE: TRACKING (PUBLIC)
# ==========================================
if current_page == "tracking":
    render_header("Lacak Pengiriman", "Masukkan Order ID atau nama Anda untuk melacak status paket")
    
    # Check for URL parameter
    default_oid = ""
    try:
        qp = st.query_params
        if "oid" in qp: 
            default_oid = qp["oid"]
    except: 
        pass
    
    # Search Section
    col1, col2 = st.columns([4, 1])
    with col1:
        q = st.text_input("🔍 Order ID / Nama Customer", value=default_oid, placeholder="Masukkan Order ID atau nama...", label_visibility="collapsed")
    with col2:
        search_clicked = st.button("Lacak", use_container_width=True)
    
    auto_search = True if default_oid else False
    
    if search_clicked or (q and auto_search):
        if q and supabase:
            with st.spinner("Mencari data..."):
                try:
                    res = supabase.table("shipments").select("*").or_(f"order_id.eq.{q},customer_name.ilike.%{q}%").execute()
                    
                    if res.data:
                        for d in res.data:
                            st.markdown('<div class="modern-card animate-fade-in">', unsafe_allow_html=True)
                            
                            # Header with status
                            col_a, col_b = st.columns([3, 1])
                            with col_a:
                                st.markdown(f"### 📦 {d['product_name']}")
                                st.markdown(f"`Order: {d['order_id']}`")
                            with col_b:
                                st.markdown(get_status_badge(d['status']), unsafe_allow_html=True)
                            
                            # Progress Tracker
                            st.markdown(render_progress_tracker(d['status']), unsafe_allow_html=True)
                            
                            # Details
                            st.markdown("---")
                            c1, c2, c3 = st.columns(3)
                            with c1:
                                st.markdown("**👤 Customer**")
                                st.write(d['customer_name'])
                            with c2:
                                st.markdown("**🏢 Cabang**")
                                st.write(d.get('branch', '-'))
                            with c3:
                                st.markdown("**📅 Update Terakhir**")
                                tgl = d.get('last_updated') or d['created_at']
                                st.write(tgl[:16].replace('T', ' '))
                            
                            if d.get('courier') or d.get('resi'):
                                st.markdown("---")
                                c4, c5 = st.columns(2)
                                with c4:
                                    st.markdown("**🚚 Kurir**")
                                    st.write(d.get('courier', '-'))
                                with c5:
                                    st.markdown("**📋 No. Resi**")
                                    st.code(d.get('resi', '-'))
                            
                            st.markdown('</div>', unsafe_allow_html=True)
                    else:
                        st.markdown("""
                        <div class="empty-state">
                            <div class="empty-state-icon">🔍</div>
                            <h3>Data Tidak Ditemukan</h3>
                            <p>Pastikan Order ID atau nama yang Anda masukkan sudah benar</p>
                        </div>
                        """, unsafe_allow_html=True)
                        
                except Exception as e:
                    st.error(f"Terjadi kesalahan: {e}")
        elif not supabase:
            st.warning("⚠️ Database tidak terhubung (Demo Mode)")

# ==========================================
# PAGE: LOGIN
# ==========================================
elif current_page == "login":
    render_header("Login Staff", "Masuk ke sistem untuk mengelola pengiriman")
    
    # Gatekeeper
    if not st.session_state.get("gate_unlocked"):
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            st.markdown('<div class="modern-card">', unsafe_allow_html=True)
            st.markdown("### 🔐 Akses Internal")
            st.markdown("Masukkan kode akses untuk melanjutkan")
            gate_pin = st.text_input("Kode Akses", type="password", placeholder="••••••••")
            if st.button("Buka Akses", use_container_width=True):
                if gate_pin == GATEKEEPER_PASSWORD:
                    st.session_state["gate_unlocked"] = True
                    st.rerun()
                else:
                    st.error("❌ Kode akses salah!")
            st.markdown('</div>', unsafe_allow_html=True)
        st.stop()
    
    # Login Form
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown('<div class="modern-card">', unsafe_allow_html=True)
        
        login_type = st.radio(
            "Pilih Tipe Akun", 
            ["👤 Sales", "👔 SPV", "⚡ Admin"],
            horizontal=True
        )
        
        st.markdown("---")
        
        if "Sales" in login_type:
            cabang = st.selectbox("🏢 Pilih Cabang", list(SALES_CREDENTIALS.keys()))
            pw = st.text_input("🔑 Password", type="password", placeholder="Masukkan password...")
            
            if st.button("Masuk", use_container_width=True):
                if pw == SALES_CREDENTIALS.get(cabang):
                    st.session_state['user_role'] = "Sales"
                    st.session_state['user_branch'] = cabang
                    st.session_state['current_page'] = 'dashboard'
                    st.rerun()
                else:
                    st.error("❌ Password salah!")
                    
        elif "SPV" in login_type:
            cabang = st.selectbox("🏢 Pilih Cabang", list(SPV_CREDENTIALS.keys()))
            pw = st.text_input("🔑 Password", type="password", placeholder="Masukkan password...")
            
            if st.button("Masuk", use_container_width=True):
                if pw == SPV_CREDENTIALS.get(cabang):
                    st.session_state['user_role'] = "SPV"
                    st.session_state['user_branch'] = cabang
                    st.session_state['current_page'] = 'dashboard'
                    st.rerun()
                else:
                    st.error("❌ Password salah!")
                    
        else:  # Admin
            pw = st.text_input("🔑 Password Admin", type="password", placeholder="Masukkan password...")
            
            if st.button("Masuk", use_container_width=True):
                if pw == ADMIN_PASSWORD:
                    st.session_state['user_role'] = "Admin"
                    st.session_state['user_branch'] = "Pusat"
                    st.session_state['current_page'] = 'dashboard'
                    st.rerun()
                else:
                    st.error("❌ Password salah!")
        
        st.markdown('</div>', unsafe_allow_html=True)

# ==========================================
# PAGE: DASHBOARD
# ==========================================
elif current_page == "dashboard":
    user_role = st.session_state['user_role']
    user_branch = st.session_state['user_branch']
    render_header("Dashboard Monitoring", f"Cabang: {user_branch} | Role: {user_role}")
    
    if not supabase:
        st.warning("⚠️ Database tidak terhubung (Demo Mode)")
        st.stop()
    
    try:
        res = supabase.table("shipments").select("*").execute()
        raw_data = res.data if res.data else []
        
        # Filter by branch
        if user_role in ["Sales", "SPV"]:
            filtered = [d for d in raw_data if d.get('branch') == user_branch]
        else:
            # Admin filter
            br_list = sorted(list(set([d['branch'] for d in raw_data if d.get('branch')])))
            br_list.insert(0, "Semua Cabang")
            sel_br = st.selectbox("🏢 Filter Cabang", br_list)
            filtered = raw_data if sel_br == "Semua Cabang" else [d for d in raw_data if d.get('branch') == sel_br]
        
        if not filtered:
            st.markdown("""
            <div class="empty-state">
                <div class="empty-state-icon">📭</div>
                <h3>Belum Ada Data</h3>
                <p>Belum ada pengiriman untuk cabang ini</p>
            </div>
            """, unsafe_allow_html=True)
        else:
            # Categorize data
            pending = [x for x in filtered if "selesai" not in str(x.get('status','')).lower() 
                      and "dikirim" not in str(x.get('status','')).lower() 
                      and "jalan" not in str(x.get('status','')).lower()]
            shipping = [x for x in filtered if "dikirim" in str(x.get('status','')).lower() 
                       or "jalan" in str(x.get('status','')).lower()]
            done = [x for x in filtered if "selesai" in str(x.get('status','')).lower() 
                   or "diterima" in str(x.get('status','')).lower()]
            
            # Alert for pending confirmation
            p_conf = [x for x in filtered if str(x.get('status','')).strip() == "Menunggu Konfirmasi"]
            if p_conf and user_role in ["SPV", "Admin"]:
                conf_count = len(p_conf)
                st.markdown(f"""
                <div class="alert-box alert-danger">
                    <span style="font-size: 1.5rem;">🔔</span>
                    <div>
                        <strong>Perhatian!</strong><br>
                        Ada {conf_count} order baru menunggu konfirmasi
                    </div>
                </div>
                """, unsafe_allow_html=True)
            
            # Stats Cards
            c1, c2, c3, c4 = st.columns(4)
            with c1:
                st.markdown(render_stat_card("📦", len(pending), "Diproses", "warning"), unsafe_allow_html=True)
            with c2:
                st.markdown(render_stat_card("🚚", len(shipping), "Dalam Perjalanan", "info"), unsafe_allow_html=True)
            with c3:
                st.markdown(render_stat_card("✅", len(done), "Selesai", "success"), unsafe_allow_html=True)
            with c4:
                st.markdown(render_stat_card("📊", len(filtered), "Total Order", ""), unsafe_allow_html=True)
            
            st.markdown("<br>", unsafe_allow_html=True)
            
            # Charts Section (if Plotly available)
            if PLOTLY_AVAILABLE:
                col_chart1, col_chart2 = st.columns(2)
                
                with col_chart1:
                    st.markdown('<div class="modern-card">', unsafe_allow_html=True)
                    st.markdown("#### 📈 Distribusi Status")
                    
                    status_counts = {"Diproses": len(pending), "Dikirim": len(shipping), "Selesai": len(done)}
                    fig_pie = px.pie(
                        values=list(status_counts.values()),
                        names=list(status_counts.keys()),
                        color_discrete_sequence=['#F59E0B', '#3B82F6', '#10B981'],
                        hole=0.4
                    )
                    fig_pie.update_layout(
                        margin=dict(t=20, b=20, l=20, r=20),
                        height=250,
                        showlegend=True,
                        legend=dict(orientation="h", yanchor="bottom", y=-0.2)
                    )
                    st.plotly_chart(fig_pie, use_container_width=True)
                    st.markdown('</div>', unsafe_allow_html=True)
                
                with col_chart2:
                    st.markdown('<div class="modern-card">', unsafe_allow_html=True)
                    st.markdown("#### 📊 Order per Tipe Pengiriman")
                    
                    df_temp = pd.DataFrame(filtered)
                    if 'delivery_type' in df_temp.columns and not df_temp.empty:
                        type_counts = df_temp['delivery_type'].value_counts()
                        fig_bar = px.bar(
                            x=type_counts.index,
                            y=type_counts.values,
                            color_discrete_sequence=['#0095DA']
                        )
                        fig_bar.update_layout(
                            margin=dict(t=20, b=20, l=20, r=20),
                            height=250,
                            xaxis_title="",
                            yaxis_title="Jumlah"
                        )
                        st.plotly_chart(fig_bar, use_container_width=True)
                    st.markdown('</div>', unsafe_allow_html=True)
            
            # Data Tables
            st.markdown("<br>", unsafe_allow_html=True)
            
            df_all = pd.DataFrame(filtered)
            
            if not df_all.empty and 'order_id' in df_all.columns:
                for col in ['last_updated', 'created_at']:
                    if col in df_all.columns:
                        df_all[col] = pd.to_datetime(df_all[col], errors='coerce').dt.floor('S').dt.strftime('%d/%m/%Y %H:%M')
                        df_all[col] = df_all[col].fillna('-')
                
                disp_cols = ['order_id', 'customer_name', 'product_name', 'status', 'last_updated', 'delivery_type']
                if user_role == "Admin":
                    disp_cols.insert(3, 'branch')
                
                final_cols = [c for c in disp_cols if c in df_all.columns]
                
                # Tabs for different status
                tab1, tab2, tab3 = st.tabs([
                    f"📦 Diproses ({len(pending)})", 
                    f"🚚 Dalam Perjalanan ({len(shipping)})", 
                    f"✅ Selesai ({len(done)})"
                ])
                
                with tab1:
                    if pending:
                        p_ids = [d.get('order_id') for d in pending]
                        st.dataframe(
                            df_all[df_all['order_id'].isin(p_ids)][final_cols],
                            use_container_width=True,
                            hide_index=True
                        )
                    else:
                        st.info("Tidak ada order yang sedang diproses")
                
                with tab2:
                    if shipping:
                        s_ids = [d.get('order_id') for d in shipping]
                        st.dataframe(
                            df_all[df_all['order_id'].isin(s_ids)][final_cols],
                            use_container_width=True,
                            hide_index=True
                        )
                    else:
                        st.info("Tidak ada order dalam perjalanan")
                
                with tab3:
                    if done:
                        d_ids = [d.get('order_id') for d in done]
                        st.dataframe(
                            df_all[df_all['order_id'].isin(d_ids)][final_cols],
                            use_container_width=True,
                            hide_index=True
                        )
                    else:
                        st.info("Belum ada order selesai")
                        
    except Exception as e:
        st.error(f"Terjadi kesalahan: {e}")

# ==========================================
# PAGE: INPUT ORDER
# ==========================================
elif current_page == "input":
    user_branch = st.session_state['user_branch']
    render_header("Input Delivery Order", f"Cabang: {user_branch}")
    
    if not supabase:
        st.warning("⚠️ Database tidak terhubung (Demo Mode)")
        st.stop()
    
    # Success State
    if st.session_state.get('sales_success'):
        last_id = st.session_state.get('sales_last_id', '')
        st.markdown(f"""
        <div class="alert-box alert-success">
            <span style="font-size: 2rem;">✅</span>
            <div>
                <strong>Order Berhasil Dibuat!</strong><br>
                Order ID: {last_id}
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        b64 = st.session_state.get('sales_pdf_data', '')
        if b64:
            st.markdown(f"""
            <a href="data:application/pdf;base64,{b64}" download="SJ_{last_id}.pdf" 
               style="display: inline-block; background: linear-gradient(135deg, #10B981 0%, #059669 100%); 
                      color: white; padding: 1rem 2rem; border-radius: 8px; text-decoration: none; 
                      font-weight: 600; margin: 1rem 0;">
                📄 Download Surat Jalan (PDF)
            </a>
            """, unsafe_allow_html=True)
        
        if st.button("➕ Buat Order Baru"):
            st.session_state['sales_success'] = False
            st.rerun()
        st.stop()
    
    # Error State
    if st.session_state.get('sales_error'):
        error_msg = st.session_state['sales_error']
        st.markdown(f"""
        <div class="alert-box alert-danger">
            <span style="font-size: 1.5rem;">⚠️</span>
            <div>{error_msg}</div>
        </div>
        """, unsafe_allow_html=True)
    
    # Form
    st.markdown('<div class="modern-card">', unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### 📋 Informasi Order")
        st.text_input("Order ID *", key="in_id", placeholder="Contoh: ORD-001")
        
        st.markdown("#### 👤 Data Sales")
        st.text_input("Nama Sales *", key="in_sales", placeholder="Nama lengkap sales")
        st.text_input("No. WA Sales", key="in_sales_hp", placeholder="08xxxxxxxxxx")
    
    with col2:
        st.markdown("#### 🏠 Data Customer")
        st.text_input("Nama Customer *", key="in_nama", placeholder="Nama penerima")
        st.text_input("No. HP Customer", key="in_hp", placeholder="08xxxxxxxxxx")
    
    st.text_area("📍 Alamat Pengiriman", key="in_alamat", placeholder="Alamat lengkap pengiriman...", height=100)
    
    st.markdown("---")
    st.markdown("#### 📦 Detail Barang")
    
    col3, col4 = st.columns(2)
    with col3:
        st.text_input("Nama Barang *", key="in_barang", placeholder="Nama produk")
    with col4:
        sel_tipe = st.selectbox("Tipe Pengiriman", ["Reguler", "Tukar Tambah", "Express"], key="in_tipe")
    
    if sel_tipe == "Tukar Tambah":
        st.text_input("📦 Detail Barang Lama (Wajib untuk Tukar Tambah)", key="in_barang_lama", 
                     placeholder="Deskripsi barang yang ditukar")
    
    col5, col6 = st.columns(2)
    with col5:
        sel_inst = st.selectbox("🔧 Instalasi?", ["Tidak", "Ya - Vendor"], key="in_instalasi")
    with col6:
        if sel_inst == "Ya - Vendor":
            st.text_input("💰 Biaya Transport (Rp)", key="in_biaya_inst", placeholder="Contoh: 50000")
    
    st.markdown("<br>", unsafe_allow_html=True)
    st.button("🚀 Kirim ke Gudang", type="primary", on_click=process_sales_submit, use_container_width=True)
    
    st.markdown('</div>', unsafe_allow_html=True)

# ==========================================
# PAGE: UPDATE STATUS
# ==========================================
elif current_page == "update":
    user_role = st.session_state['user_role']
    user_branch = st.session_state['user_branch']
    render_header("Update Status Order", f"Validasi dan update status pengiriman")
    
    if not supabase:
        st.warning("⚠️ Database tidak terhubung (Demo Mode)")
        st.stop()
    
    try:
        q = supabase.table("shipments").select("*").order("created_at", desc=True).limit(50)
        if user_role == "SPV":
            q = q.eq("branch", user_branch)
        res = q.execute()
        
        if res.data:
            opts = {}
            for d in res.data:
                key = f"[{d['status']}] {d['order_id']} - {d['customer_name']}"
                opts[key] = d
            
            sel = st.selectbox("📦 Pilih Order untuk Update:", list(opts.keys()), index=None, key="upd_sel")
            
            if sel:
                curr = opts[sel]
                oid = curr['order_id']
                
                # Show current status
                st.markdown(f"""
                <div class="alert-box alert-info">
                    <span style="font-size: 1.5rem;">📋</span>
                    <div>
                        <strong>Order: {oid}</strong><br>
                        Customer: {curr['customer_name']} | Barang: {curr['product_name']}
                    </div>
                </div>
                """, unsafe_allow_html=True)
                
                # Tracking iframe
                with st.expander("🔍 Tracking BES"):
                    components.iframe("https://www.bes-paket.com/track-package", height=400)
                
                # Update form
                st.markdown('<div class="modern-card">', unsafe_allow_html=True)
                st.markdown("#### ✏️ Update Data")
                
                with st.form("upd_form"):
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        sts = ["Menunggu Konfirmasi", "Diproses Gudang", "Menunggu Kurir", "Dalam Pengiriman", "Selesai/Diterima"]
                        curr_idx = sts.index(curr['status']) if curr['status'] in sts else 0
                        st.selectbox("📊 Status", sts, index=curr_idx, key=f"stat_{oid}")
                        st.text_input("🚚 Kurir", value=curr.get('courier') or "", key=f"kur_{oid}")
                        st.text_input("📋 No. Resi", value=curr.get('resi') or "", key=f"res_{oid}")
                    
                    with col2:
                        st.text_input("👤 Koreksi Nama", value=curr['customer_name'], key=f"cnama_{oid}")
                        st.text_input("📦 Koreksi Barang", value=curr['product_name'], key=f"cbar_{oid}")
                    
                    st.markdown("---")
                    st.markdown("**📅 Waktu Update**")
                    col3, col4 = st.columns(2)
                    with col3:
                        st.date_input("Tanggal", value=date.today(), key=f"date_{oid}")
                    with col4:
                        st.time_input("Jam", value=datetime.now().time(), key=f"time_{oid}")
                    
                    st.form_submit_button("💾 Simpan Perubahan", on_click=process_admin_update, args=(oid,))
                
                st.markdown('</div>', unsafe_allow_html=True)
        else:
            st.info("📭 Tidak ada data order")
            
    except Exception as e:
        st.error(f"Terjadi kesalahan: {e}")

# ==========================================
# PAGE: DATA MANAGEMENT
# ==========================================
elif current_page == "data":
    user_role = st.session_state['user_role']
    user_branch = st.session_state['user_branch']
    render_header("Manajemen Data", "Download, hapus, dan kelola data pengiriman")
    
    if not supabase:
        st.warning("⚠️ Database tidak terhubung (Demo Mode)")
        st.stop()
    
    try:
        res = supabase.table("shipments").select("*").execute()
        all_data = res.data if res.data else []
        
        if user_role == "SPV":
            all_data = [d for d in all_data if d.get('branch') == user_branch]
        
        if all_data:
            df = pd.DataFrame(all_data)
            
            # Tabs
            tab1, tab2, tab3 = st.tabs(["📥 Download Excel", "🗑️ Hapus Order", "🔥 Reset Database"])
            
            with tab1:
                st.markdown('<div class="modern-card">', unsafe_allow_html=True)
                st.markdown("#### 📊 Export Data ke Excel")
                st.markdown(f"Total data: **{len(all_data)}** order")
                
                # Format dates
                df_export = df.copy()
                for col in ['created_at', 'last_updated']:
                    if col in df_export.columns:
                        df_export[col] = pd.to_datetime(df_export[col], errors='coerce').dt.strftime('%d/%m/%Y %H:%M')
                
                output = io.BytesIO()
                with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                    df_export.to_excel(writer, index=False, sheet_name='Laporan')
                    wb = writer.book
                    ws = writer.sheets['Laporan']
                    fmt = wb.add_format({'bold': True, 'fg_color': '#0095DA', 'font_color': '#FFFFFF', 'border': 1})
                    for i, v in enumerate(df_export.columns.values):
                        ws.write(0, i, v, fmt)
                        ws.set_column(i, i, 20)
                
                st.download_button(
                    "📥 Download File Excel",
                    output.getvalue(),
                    file_name=
# ... (Sambungan dari kode sebelumnya di bagian elif current_page == "data":)

elif current_page == "data":
    user_role = st.session_state['user_role']
    user_branch = st.session_state['user_branch']
    render_header("Manajemen Data", "Download, hapus, dan kelola data pengiriman")
    
    if not supabase:
        st.warning("⚠️ Database tidak terhubung (Demo Mode)")
        st.stop()
    
    try:
        res = supabase.table("shipments").select("*").execute()
        all_data = res.data if res.data else []
        
        # Filter data jika user adalah SPV
        if user_role == "SPV":
            all_data = [d for d in all_data if d.get('branch') == user_branch]
        
        if all_data:
            df = pd.DataFrame(all_data)
            
            # Tabs Menu
            tab1, tab2, tab3 = st.tabs(["📥 Download Excel", "🗑️ Hapus Order", "🔥 Reset Database"])
            
            # --- TAB 1: DOWNLOAD EXCEL ---
            with tab1:
                st.markdown('<div class="modern-card">', unsafe_allow_html=True)
                st.markdown("#### 📊 Export Data ke Excel")
                st.markdown(f"Total data: **{len(all_data)}** order")
                
                # Format tanggal agar rapi di Excel
                df_export = df.copy()
                for col in ['created_at', 'last_updated']:
                    if col in df_export.columns:
                        df_export[col] = pd.to_datetime(df_export[col], errors='coerce').dt.strftime('%d/%m/%Y %H:%M')
                
                # Proses pembuatan file Excel di memori
                output = io.BytesIO()
                with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                    df_export.to_excel(writer, index=False, sheet_name='Laporan')
                    wb = writer.book
                    ws = writer.sheets['Laporan']
                    # Styling Header Excel
                    fmt = wb.add_format({'bold': True, 'fg_color': '#0095DA', 'font_color': '#FFFFFF', 'border': 1})
                    for i, v in enumerate(df_export.columns.values):
                        ws.write(0, i, v, fmt)
                        ws.set_column(i, i, 20)
                
                st.download_button(
                    label="📥 Download File Excel",
                    data=output.getvalue(),
                    file_name=f"Laporan_Delivery_{date.today()}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    use_container_width=True
                )
                st.markdown('</div>', unsafe_allow_html=True)

            # --- TAB 2: HAPUS ORDER ---
            with tab2:
                st.markdown('<div class="modern-card">', unsafe_allow_html=True)
                st.markdown("#### 🗑️ Hapus Order Satuan")
                st.warning("Data yang dihapus tidak dapat dikembalikan.")
                
                del_opts = {f"{d['order_id']} - {d['customer_name']}": d['order_id'] for d in all_data}
                d_sel = st.selectbox("Pilih Order untuk Dihapus:", list(del_opts.keys()), index=None)
                
                if d_sel:
                    st.markdown(f"Anda akan menghapus order ID: **{del_opts[d_sel]}**")
                    if st.button("🗑️ Hapus Permanen", type="primary"): 
                        try:
                            supabase.table("shipments").delete().eq("order_id", del_opts[d_sel]).execute()
                            st.toast("Data berhasil dihapus!", icon="✅")
                            time.sleep(1)
                            st.rerun()
                        except Exception as e:
                            st.error(f"Gagal menghapus: {e}")
                st.markdown('</div>', unsafe_allow_html=True)

            # --- TAB 3: RESET DATABASE (ADMIN ONLY) ---
            with tab3:
                st.markdown('<div class="modern-card">', unsafe_allow_html=True)
                st.markdown("#### 🔥 Reset Database")
                
                if user_role == "Admin":
                    st.markdown("""
                    <div class="alert-box alert-danger">
                        <span style="font-size: 1.5rem;">⚠️</span>
                        <div>
                            <strong>BAHAYA!</strong><br>
                            Tindakan ini akan menghapus <strong>SEMUA DATA</strong> pengiriman di database.
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    confirm_text = st.text_input("Ketik 'HAPUS SEMUA' untuk konfirmasi:", placeholder="Ketik disini...")
                    
                    if confirm_text == "HAPUS SEMUA":
                        if st.button("🔥 YA, RESET DATABASE SEKARANG", type="primary"): 
                            try:
                                supabase.table("shipments").delete().neq("id", 0).execute()
                                st.success("Database berhasil di-reset bersih!")
                                time.sleep(2)
                                st.rerun()
                            except Exception as e:
                                st.error(f"Error: {e}")
                else:
                    st.warning("⛔ Akses Ditolak. Menu ini khusus Admin Pusat.")
                st.markdown('</div>', unsafe_allow_html=True)
                
        else:
            st.info("📭 Data Kosong. Belum ada pengiriman yang tercatat.")
            
    except Exception as e:
        st.error(f"Terjadi kesalahan saat memuat data: {e}")

# End of File
