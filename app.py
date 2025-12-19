# Versi 2.77 (Final Clean)
# Status: Stabil & Lengkap
# Update: Menghapus nama author di footer sidebar. Fitur lain tetap sama (v2.76).

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

# --- KONFIGURASI HALAMAN ---
st.set_page_config(
    page_title="Delivery Tracker", 
    page_icon="📦", 
    layout="wide", 
    initial_sidebar_state="collapsed" 
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
except:
    GATEKEEPER_PASSWORD = "blibli"
    if not 'supabase' in locals():
        st.error("Secrets belum lengkap.")
        st.stop()

supabase: Client = create_client(url, key)

# --- FUNGSI BANTUAN ---
def get_status_color(status):
    s = str(status).lower()
    if "selesai" in s or "diterima" in s: return "success"
    elif "dikirim" in s or "jalan" in s or "pengiriman" in s: return "info"
    else: return "warning"

# --- FUNGSI CETAK PDF (Thermal 80mm) ---
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

    # HEADER (Absolute Center)
    pdf.set_font("Arial", 'B', 16)
    pdf.set_x(0)
    pdf.cell(80, 8, "SURAT JALAN", 0, 1, 'C')
    pdf.set_x(margin)
    draw_line()
    
    # INFO
    pdf.set_font("Arial", '', 10)
    pdf.cell(20, 5, "No Order", 0, 0)
    pdf.set_font("Arial", 'B', 11)
    pdf.cell(52, 5, f": {safe_text(data['order_id'])}", 0, 1)
    
    pdf.set_font("Arial", '', 10)
    pdf.cell(20, 5, "Tanggal", 0, 0)
    pdf.cell(52, 5, f": {print_timestamp.strftime('%d/%m/%Y %H:%M')}", 0, 1)
    draw_line()
    
    # PENERIMA
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
    
    # SALES (Label: SALES, Kontak: HP)
    pdf.set_font("Arial", 'B', 11)
    pdf.cell(w_full, 6, "SALES:", 0, 1)
    pdf.set_font("Arial", '', 10)
    pdf.cell(15, 5, "Nama", 0, 0)
    pdf.cell(57, 5, f": {safe_text(data['sales_name'])} ({safe_text(data['branch'])})", 0, 1)
    pdf.cell(15, 5, "HP", 0, 0)
    pdf.cell(57, 5, f": {safe_text(data.get('sales_phone', '-'))}", 0, 1)
    draw_line()
    
    # BARANG
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
        pdf.cell(47, 5, f": YA (Vendor)", 0, 1)
        pdf.cell(25, 5, "Biaya", 0, 0)
        pdf.cell(47, 5, f": Rp {safe_text(data.get('installation_fee', '-'))}", 0, 1)
    draw_line()
    
    # TTD (Sales & Penerima)
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
    
    # QR CODE
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
    
    in_id = s.get("in_id", "").strip()
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
    
    # Waktu WIB (+7)
    TIME_OFFSET = timedelta(hours=7) 
    current_time_wib = datetime.utcnow() + TIME_OFFSET 

    if not (in_id and in_sales and in_nama and in_barang):
        st.session_state['sales_error'] = "⚠️ Data wajib belum lengkap (ID, Sales, Customer, Barang)."
        return

    if in_tipe == "Tukar Tambah" and not in_old_item:
        st.session_state['sales_error'] = "⚠️ Anda memilih Tukar Tambah. Harap isi Detail Barang Lama!"
        return

    try:
        payload = {
            "order_id": in_id, "customer_name": in_nama, "customer_phone": in_hp,
            "delivery_address": in_alamat, "product_name": in_barang, "delivery_type": in_tipe,
            "sales_name": in_sales, "sales_phone": in_sales_hp, "branch": branch,
            "status": "Menunggu Konfirmasi", 
            "last_updated": current_time_wib.isoformat(),
            "installation_opt": in_inst, "installation_fee": in_fee,
            "old_product_name": in_old_item
        }
        supabase.table("shipments").insert(payload).execute()
        
        pdf_bytes = create_thermal_pdf(payload, current_time_wib)
        st.session_state['sales_pdf_data'] = base64.b64encode(pdf_bytes).decode('latin-1')
        st.session_state['sales_success'] = True
        st.session_state['sales_last_id'] = in_id
        
        # Reset Data Input
        for k in ["in_id", "in_sales", "in_sales_hp", "in_nama", "in_hp", "in_alamat", "in_barang", "in_biaya_inst", "in_barang_lama"]:
            st.session_state[k] = ""
        st.session_state["in_tipe"] = "Reguler"
        st.session_state["in_instalasi"] = "Tidak"
        
    except Exception as e:
        err_msg = str(e)
        if "duplicate key" in err_msg:
            st.session_state['sales_error'] = f"⛔ Order ID **{in_id}** sudah ada."
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
        "status": new_stat, "courier": new_kurir, "resi": new_resi,
        "last_updated": final_dt, "customer_name": corr_nama, "product_name": corr_barang
    }
    
    try:
        supabase.table("shipments").update(upd).eq("order_id", oid).execute()
        st.success("✅ Data Berhasil Diupdate!") # NOTIFIKASI SUKSES PERSISTEN
        st.toast("Data Terupdate!", icon="✅")
        st.session_state["upd_sel"] = None
    except Exception as e:
        st.toast(f"Error: {e}", icon="❌")

# --- CUSTOM CSS ---
st.markdown("""
<style>
    div.stButton > button { background-color: #0095DA !important; color: white !important; border: 1px solid #0095DA !important; font-weight: bold !important; }
    div.stButton > button:hover { background-color: #007AB8 !important; border-color: #007AB8 !important; color: white !important; }
    button[kind="primary"] { background-color: #0095DA !important; color: white !important; border: none !important; }
    [data-testid="stLinkButton"] > a { background-color: #0095DA !important; color: white !important; border: 1px solid #0095DA !important; font-weight: bold !important; }
    div.stFormSubmitButton > button { background-color: #0095DA !important; color: white !important; border: none !important; }
    [data-testid="stFormSubmitButton"] > button { background-color: #0095DA !important; color: white !important; border: none !important; } 
</style>
""", unsafe_allow_html=True)

# --- SIDEBAR LOGIC ---
if 'user_role' not in st.session_state: st.session_state['user_role'] = "Guest" 
if 'user_branch' not in st.session_state: st.session_state['user_branch'] = ""

if st.session_state['user_role'] == "Guest":
    menu_options = ["🔍 Cek Resi (Public)", "🔐 Login Staff"] 
elif st.session_state['user_role'] == "Sales":
    menu_options = ["📊 Dashboard Monitoring", "📝 Input Delivery Order", "🔍 Cek Resi (Public)"]
elif st.session_state['user_role'] == "SPV":
    # SPV: Tidak ada Input (Optimized Role)
    menu_options = ["📊 Dashboard Monitoring", "⚙️ Update Status (SPV)", "🗄️ Manajemen Data", "🔍 Cek Resi (Public)"]
elif st.session_state['user_role'] == "Admin":
    # Admin: Tidak ada Input (Optimized Role)
    menu_options = ["📊 Dashboard Monitoring", "⚙️ Update Status (Admin)", "🗄️ Manajemen Data", "🔍 Cek Resi (Public)"]

menu = st.sidebar.radio("Menu Aplikasi", menu_options)

# --- FOOTER (NO AUTHOR) ---
with st.sidebar:
    st.divider()
    if st.session_state['user_role'] != "Guest":
        st.info(f"👤 {st.session_state['user_role']} - {st.session_state['user_branch']}")
        if st.button("Logout / Keluar"):
            st.session_state['user_role'] = "Guest"
            st.rerun()
    st.markdown("---")
    st.caption("© 2025 **Delivery Tracker System**")
    st.caption("🚀 **Versi 2.77 (Final)**")
    st.caption("_Internal Use Only_")

# ==========================================
# HALAMAN 1: CEK RESI (LANDING PAGE)
# ==========================================
if menu == "🔍 Cek Resi (Public)":
    st.title("🔍 Lacak Pengiriman")
    st.markdown("Masukkan Nomor Order ID atau Nama Anda untuk melacak status barang.")
    
    default_oid = st.query_params.get("oid", "")
    q = st.text_input("Order ID / Nama Customer:", value=default_oid)
    auto_click = True if default_oid else False

    if st.button("Lacak Paket") or q or auto_click:
        if q:
            try:
                res = supabase.table("shipments").select("*").or_(f"order_id.eq.{q},customer_name.ilike.%{q}%").execute()
                if res.data:
                    for d in res.data:
                        col = get_status_color(d['status'])
                        if col=="success": st.success(f"Status: {d['status']}", icon="✅")
                        elif col=="info": st.info(f"Status: {d['status']}", icon="🚚")
                        else: st.warning(f"Status: {d['status']}", icon="⏳")
                        
                        tgl = d.get('last_updated') or d['created_at']
                        install_info = ""
                        if d.get('installation_opt') == "Ya - Vendor":
                            install_info = f"* 🔧 **Instalasi:** Ya (Vendor) - Biaya: {d.get('installation_fee')}"
                        
                        old_item_info = ""
                        if d.get('delivery_type') == "Tukar Tambah" and d.get('old_product_name'):
                            old_item_info = f"* 🔄 **Tukar Tambah:** {d.get('old_product_name')}"

                        st.markdown(f"""
                        ### {d['product_name']}
                        * 🏢 Cabang: **{d.get('branch', '-')}**
                        * 👤 Customer: **{d['customer_name']}**
                        * 🔢 Order ID: `{d['order_id']}`
                        * 🚚 Kurir: {d['courier'] or '-'}
                        * 🔖 Resi: {d['resi'] or '-'}
                        {old_item_info}
                        {install_info}
                        * 🕒 **Update:** {tgl[:16].replace('T',' ')}
                        """)
                        st.divider()
                        
                        if d['resi'] and ("jalan" in str(d['status']).lower() or "kirim" in str(d['status']).lower()):
                             with st.expander("🌍 Lacak di Website PT. BES"):
                                components.iframe("https://www.bes-paket.com/track-package", height=500, scrolling=True)

                else: st.warning("Data tidak ditemukan.")
            except: st.error("Terjadi kesalahan koneksi.")

# ==========================================
# HALAMAN 2: LOGIN
# ==========================================
elif menu == "🔐 Login Staff":
    st.title("🔐 Login Staff & Admin")
    
    if not st.session_state.get("gate_unlocked"):
        c_pin1, c_pin2, c_pin3 = st.columns([1,2,1])
        with c_pin2:
            st.info("🔒 Masukkan Kode Akses Internal")
            gate_pin = st.text_input("Kode Akses:", type="password", key="gate_pin")
            if st.button("Buka Akses"):
                if gate_pin == GATEKEEPER_PASSWORD:
                    st.session_state["gate_unlocked"] = True
                    st.toast("Akses Diterima.", icon="🔓")
                    time.sleep(0.5)
                    st.rerun()
                else:
                    st.error("Kode Akses Salah.")
        st.stop()
    
    st.success("Akses Terbuka. Silakan Login.")
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        with st.container(border=True):
            tp = st.radio("Pilih Tipe Akun:", ["Sales Cabang", "SPV Cabang", "Admin Pusat"], horizontal=True)
            st.divider()
            if tp == "Sales Cabang":
                cb = st.selectbox("Cabang:", list(SALES_CREDENTIALS.keys()))
                pw = st.text_input("Password Sales:", type="password")
                if st.button("Masuk Sales", use_container_width=True):
                    if pw == SALES_CREDENTIALS.get(cb): st.session_state.update({'user_role': "Sales", 'user_branch': cb}); st.rerun()
                    else: st.error("Salah!")
            elif tp == "SPV Cabang":
                cb = st.selectbox("Cabang:", list(SPV_CREDENTIALS.keys()))
                pw = st.text_input("Password SPV:", type="password")
                if st.button("Masuk SPV", use_container_width=True):
                    if pw == SPV_CREDENTIALS.get(cb): st.session_state.update({'user_role': "SPV", 'user_branch': cb}); st.rerun()
                    else: st.error("Salah!")
            else:
                pw = st.text_input("Password Admin:", type="password")
                if st.button("Masuk Admin", use_container_width=True):
                    if pw == ADMIN_PASSWORD: st.session_state.update({'user_role': "Admin", 'user_branch': "Pusat"}); st.rerun()
                    else: st.error("Salah!")

# ==========================================
# HALAMAN 3: DASHBOARD
# ==========================================
elif menu == "📊 Dashboard Monitoring":
    st.title("📊 Monitoring Operasional")
    try:
        res = supabase.table("shipments").select("*").execute()
        raw = res.data if res.data else []
        if st.session_state['user_role'] in ["Sales", "SPV"]:
            branch = st.session_state['user_branch']
            filtered = [d for d in raw if d.get('branch') == branch]
        else:
            br_list = sorted(list(set([d['branch'] for d in raw if d.get('branch')])))
            br_list.insert(0, "Semua Cabang")
            sel_br = st.selectbox("Filter Cabang:", br_list)
            filtered = raw if sel_br == "Semua Cabang" else [d for d in raw if d.get('branch') == sel_br]

        if not filtered:
            st.info("📍 Belum ada data pengiriman.")
        else:
            # Notifikasi Badge
            p_conf = [x for x in filtered if str(x.get('status','')).strip() == "Menunggu Konfirmasi"]
            if p_conf and st.session_state['user_role'] in ["SPV", "Admin"]:
                 st.error(f"🔔 PERHATIAN: Ada {len(p_conf)} Order Baru Menunggu Konfirmasi!", icon="🔥")

            df = pd.DataFrame(filtered)
            for col in ['last_updated', 'created_at']:
                if col in df.columns: df[col] = pd.to_datetime(df[col], errors='coerce').dt.floor('S').dt.strftime('%d/%m/%Y %H:%M').fillna('-')

            c1, c2, c3 = st.columns(3)
            # Robust filtering
            pending = df[~df['status'].str.lower().str.contains('selesai|diterima|dikirim|jalan|pengiriman', na=False)]
            shipping = df[df['status'].str.lower().str.contains('dikirim|jalan|pengiriman', na=False)]
            done = df[df['status'].str.lower().str.contains('selesai|diterima', na=False)]
            
            c1.metric("📦 Diproses", len(pending))
            c2.metric("🚚 Sedang Jalan", len(shipping))
            c3.metric("✅ Selesai", len(done))
            st.divider()

            disp = ['order_id', 'customer_name', 'product_name', 'status', 'last_updated', 'delivery_type']
            if st.session_state['user_role'] == "Admin": disp.insert(3, 'branch')
            final_cols = [c for c in disp if c in df.columns]

            with st.expander(f"📦 Diproses Gudang ({len(pending)})", expanded=False): st.dataframe(pending[final_cols], use_container_width=True, hide_index=True)
            with st.expander(f"🚚 Sedang Jalan ({len(shipping)})", expanded=False): st.dataframe(shipping[final_cols], use_container_width=True, hide_index=True)
            with st.expander(f"✅ Selesai ({len(done)})", expanded=False): st.dataframe(done[final_cols], use_container_width=True, hide_index=True)
    except Exception as e: st.error(str(e))

# ==========================================
# HALAMAN 4: INPUT ORDER (HANYA SALES - DENGAN PEMISAH)
# ==========================================
elif menu == "📝 Input Delivery Order":
    if st.session_state['user_role'] != "Sales": st.error("Akses Ditolak."); st.stop()
    st.title("📝 Input Delivery Order")
    branch = st.session_state['user_branch']
    st.info(f"Cabang: **{branch}**")
    
    if st.session_state.get('sales_success'):
        st.success(f"✅ Order {st.session_state.get('sales_last_id')} Berhasil Disimpan!")
        b64 = st.session_state.get('sales_pdf_data')
        st.markdown(f'<a href="data:application/pdf;base64,{b64}" download="SJ_{st.session_state.get("sales_last_id")}.pdf" style="text-decoration:none;"><button style="background-color:#0095DA;color:white;border:none;padding:12px;border-radius:8px;cursor:pointer;width:100%;">DOWNLOAD SURAT JALAN (PDF 80mm)</button></a>', unsafe_allow_html=True)
        st.divider()
        if st.button("Selesai / Buat Baru"): st.session_state['sales_success'] = False; st.rerun()
    else:
        if st.session_state.get('sales_error'): st.error(st.session_state['sales_error'])
        with st.container(border=True):
            st.subheader("1. Data Sales & Order")
            st.text_input("Order ID (Wajib)", key="in_id")
            c1, c2 = st.columns(2)
            c1.text_input("Nama Sales", key="in_sales")
            c2.text_input("No WA Sales", key="in_sales_hp")
            st.divider()

            st.subheader("2. Data Pelanggan")
            c3, c4 = st.columns(2)
            c3.text_input("Nama Customer", key="in_nama")
            c4.text_input("No HP Customer", key="in_hp")
            st.text_area("Alamat Pengiriman", key="in_alamat")
            st.divider()

            st.subheader("3. Detail Barang & Layanan")
            c5, c6 = st.columns(2)
            c5.text_input("Nama Barang", key="in_barang")
            tp = st.selectbox("Tipe Pengiriman", ["Reguler", "Tukar Tambah", "Express"], key="in_tipe")
            if tp == "Tukar Tambah":
                st.info("🔄 Mode Tukar Tambah Aktif")
                st.text_input("Detail Barang Lama (Wajib)", key="in_barang_lama", placeholder="Merk, Tipe, Kondisi...")
            
            c7, c8 = st.columns(2)
            sel_inst = st.selectbox("Opsi Instalasi?", ["Tidak", "Ya - Vendor"], key="in_instalasi")
            if sel_inst == "Ya - Vendor":
                st.info("🔧 Mode Instalasi Vendor Aktif")
                st.text_input("Biaya Transport (Rp)", key="in_biaya_inst")
            
            st.divider()
            st.button("Kirim ke Gudang", type="primary", on_click=process_sales_submit)

# ==========================================
# HALAMAN 5: UPDATE STATUS (SPV & ADMIN)
# ==========================================
elif menu == "⚙️ Update Status (Admin)" or menu == "⚙️ Update Status (SPV)":
    st.title("⚙️ Validasi Order")
    
    if "admin_success_msg" in st.session_state:
        st.success(st.session_state["admin_success_msg"])
        del st.session_state["admin_success_msg"]

    q = supabase.table("shipments").select("*").order("created_at", desc=True).limit(50)
    if st.session_state['user_role'] == "SPV": q = q.eq("branch", st.session_state['user_branch'])
    res = q.execute()
    
    if res.data:
        opts = {f"[{d['status']}] {d['order_id']} - {d['customer_name']}": d for d in res.data}
        sel = st.selectbox("Pilih Order:", list(opts.keys()), index=None, key="upd_sel")
        
        if sel:
            curr = opts[sel]; oid = curr['order_id']
            # RESTORED: Tracking BES (Scrollable)
            with st.expander("🌍 Tracking Website PT. BES"): 
                st.caption("Cek resi langsung:")
                components.iframe("https://www.bes-paket.com/track-package", height=500, scrolling=True)
            
            with st.form("upd_form"):
                sts = ["Menunggu Konfirmasi", "Diproses Gudang", "Menunggu Kurir", "Dalam Pengiriman", "Selesai/Diterima"]
                st.selectbox("Status", sts, index=sts.index(curr['status']) if curr['status'] in sts else 0, key=f"stat_{oid}")
                st.text_input("Kurir", value=curr['courier'] or "", key=f"kur_{oid}")
                st.text_input("Resi", value=curr['resi'] or "", key=f"res_{oid}")
                st.divider()
                
                # FIX TIMEZONE: Defaultnya sekarang WIB (UTC+7)
                utc_now = datetime.utcnow()
                wib_now = utc_now + timedelta(hours=7)
                
                st.write("**Waktu Fakta Lapangan:**")
                st.date_input("Tanggal", value=wib_now.date(), key=f"date_{oid}")
                st.time_input("Jam (WIB)", value=wib_now.time(), key=f"time_{oid}")
                st.divider()
                st.caption("Koreksi Data:")
                st.text_input("Nama Customer", value=curr['customer_name'], key=f"cnama_{oid}")
                st.text_input("Nama Barang", value=curr['product_name'], key=f"cbar_{oid}")
                st.form_submit_button("Simpan Perubahan", on_click=process_admin_update, args=(oid,))
    else: st.info("📍 Belum ada order baru.")

# ==========================================
# HALAMAN 6: MANAJEMEN DATA (RESTORED TABS)
# ==========================================
elif menu == "🗄️ Manajemen Data":
    st.title("🗄️ Manajemen Data")
    res = supabase.table("shipments").select("*").execute()
    all_d = [d for d in res.data if d.get('branch') == st.session_state['user_branch']] if st.session_state['user_role'] == "SPV" else res.data
    if all_d:
        df = pd.DataFrame(all_d)
        # RESTORED: Nama Tab Lengkap & Jelas
        tab1, tab2, tab3 = st.tabs(["📥 Download Excel", "🗑️ Hapus Order", "🔥 Reset Database"])
        
        with tab1:
            st.subheader("Laporan Bulanan")
            for c in ['created_at', 'last_updated']: 
                if c in df.columns: df[c] = pd.to_datetime(df[c], errors='coerce').dt.strftime('%d/%m/%Y %H:%M')
            out = io.BytesIO()
            with pd.ExcelWriter(out, engine='xlsxwriter') as wr:
                df.to_excel(wr, index=False, sheet_name='Laporan')
                wb = wr.book; ws = wr.sheets['Laporan']
                fmt = wb.add_format({'bold':True,'fg_color':'#0095DA','font_color':'#FFFFFF','border':1})
                for i, v in enumerate(df.columns.values): ws.write(0, i, v, fmt); ws.set_column(i, i, 20)
            st.download_button("Download Laporan (.xlsx)", out.getvalue(), "Laporan_Delivery.xlsx")
        
        with tab2:
            st.subheader("Hapus Satuan")
            del_o = {f"{d['order_id']} - {d['customer_name']}": d['order_id'] for d in all_d}
            s = st.selectbox("Pilih ID:", list(del_o.keys()), index=None)
            if s and st.button("Hapus Permanen"): 
                supabase.table("shipments").delete().eq("order_id", del_o[s]).execute(); st.rerun()
        
        with tab3:
            st.subheader("Reset Total")
            if st.session_state['user_role'] == "Admin":
                if st.text_input("Ketik 'HAPUS SEMUA':") == "HAPUS SEMUA":
                    if st.button("🔴 RESET DATABASE"): supabase.table("shipments").delete().neq("id",0).execute(); st.rerun()
            else: st.warning("Akses Khusus Admin Pusat.")
    else: st.info("Data Kosong.")
