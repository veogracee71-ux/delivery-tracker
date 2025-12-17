# Versi 2.26
# Update:
# 1. GENERATE QR CODE di dalam Struk PDF.
# 2. Redesign Layout PDF agar mirip "Surat Jalan" profesional (Sesuai Foto).
# 3. Fitur input Sales & Dashboard tetap sama.

import streamlit as st
import streamlit.components.v1 as components 
from supabase import create_client, Client
from urllib.parse import quote
import time
from datetime import datetime
from fpdf import FPDF
import base64
import qrcode
import tempfile
import os

# --- KONFIGURASI HALAMAN ---
st.set_page_config(
    page_title="Delivery Tracker", 
    page_icon="📦", 
    layout="wide", 
    initial_sidebar_state="collapsed" 
)

# --- KONFIGURASI URL APLIKASI (GANTI DENGAN LINK STREAMLIT ANDA) ---
# Agar saat QR discan, customer langsung diarahkan ke aplikasi ini.
APP_BASE_URL = "https://delivery-tracker-app.streamlit.app" # Ganti link ini nanti

# --- LOAD SECRETS ---
try:
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    ADMIN_PASSWORD = st.secrets["passwords"]["admin"]
    SALES_CREDENTIALS = st.secrets["passwords"]["sales"]
    SPV_CREDENTIALS = st.secrets["passwords"]["spv"]
except:
    st.error("Secrets belum lengkap.")
    st.stop()

supabase: Client = create_client(url, key)

# --- FUNGSI BANTUAN ---
def get_status_color(status):
    s = status.lower()
    if "selesai" in s or "diterima" in s: return "success"
    elif "dikirim" in s or "jalan" in s: return "info"
    else: return "warning"

def clear_input_form():
    keys = ["in_id", "in_sales", "in_sales_hp", "in_nama", "in_hp", "in_alamat", "in_barang", "in_biaya_inst"]
    for k in keys:
        if k in st.session_state: st.session_state[k] = ""
    if "in_tipe" in st.session_state: st.session_state["in_tipe"] = "Reguler"
    if "in_instalasi" in st.session_state: st.session_state["in_instalasi"] = "Tidak"

# --- FUNGSI CETAK STRUK PDF DENGAN QR CODE ---
def create_thermal_pdf(data):
    pdf = FPDF(orientation='P', unit='mm', format=(80, 180)) # Panjang dinamis estimasi
    pdf.add_page()
    pdf.set_margins(4, 4, 4)
    
    # 1. HEADER (Tebal & Besar)
    pdf.set_font("Arial", 'B', 14)
    pdf.cell(72, 6, "BLIBLI ELECTRONIC", 0, 1, 'C')
    
    pdf.set_font("Arial", '', 8)
    pdf.cell(72, 4, "Solusi Elektronik Terpercaya Anda", 0, 1, 'C')
    pdf.ln(2)
    
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(72, 6, "SURAT JALAN", 1, 1, 'C') # Kotak Judul
    pdf.ln(2)
    
    # 2. INFO TRANSAKSI
    pdf.set_font("Courier", '', 9)
    pdf.cell(20, 4, "No Order", 0, 0)
    pdf.set_font("Courier", 'B', 9)
    pdf.cell(52, 4, f": {data['order_id']}", 0, 1)
    
    pdf.set_font("Courier", '', 9)
    pdf.cell(20, 4, "Tanggal", 0, 0)
    pdf.cell(52, 4, f": {datetime.now().strftime('%d-%m-%Y %H:%M')}", 0, 1)
    
    pdf.cell(72, 2, "-"*42, 0, 1, 'C')
    
    # 3. PENGIRIM & PENERIMA (Layout Kiri-Kanan atau Atas-Bawah)
    pdf.set_font("Arial", 'B', 9)
    pdf.cell(72, 5, "PENERIMA (CUSTOMER):", 0, 1)
    pdf.set_font("Arial", '', 9)
    pdf.multi_cell(72, 4, f"{data['customer_name']}\n{data['customer_phone']}\n{data['delivery_address']}")
    pdf.ln(2)
    
    pdf.set_font("Arial", 'B', 9)
    pdf.cell(72, 5, "PENGIRIM (SALES/TOKO):", 0, 1)
    pdf.set_font("Arial", '', 9)
    pdf.cell(20, 4, "Nama", 0, 0)
    pdf.cell(52, 4, f": {data['sales_name']} ({data['branch']})", 0, 1)
    pdf.cell(20, 4, "Kontak", 0, 0)
    pdf.cell(52, 4, f": {data.get('sales_phone', '-')}", 0, 1)
    
    pdf.cell(72, 2, "-"*42, 0, 1, 'C')
    
    # 4. DETAIL BARANG (Penting)
    pdf.set_font("Arial", 'B', 10)
    pdf.cell(72, 6, "DETAIL BARANG:", 0, 1)
    
    pdf.set_font("Courier", 'B', 9)
    pdf.multi_cell(72, 4, f"> {data['product_name']}")
    
    pdf.set_font("Courier", '', 8)
    pdf.cell(25, 4, "Tipe Kirim", 0, 0)
    pdf.cell(47, 4, f": {data['delivery_type']}", 0, 1)
    
    if data.get('installation_opt') == "Ya - Vendor":
        pdf.cell(25, 4, "Instalasi", 0, 0)
        pdf.cell(47, 4, f": YA (Vendor)", 0, 1)
        pdf.cell(25, 4, "Biaya Trans", 0, 0)
        pdf.cell(47, 4, f": Rp {data.get('installation_fee', '-')}", 0, 1)
        
    pdf.ln(2)
    pdf.set_font("Arial", 'I', 7)
    pdf.multi_cell(72, 3, "Catatan: Barang telah diperiksa fisik & kelengkapannya sebelum dikirim.", 0, 'C')
    
    pdf.cell(72, 2, "-"*42, 0, 1, 'C')
    
    # 5. TANDA TANGAN (Layout Tabel)
    pdf.ln(3)
    y_pos = pdf.get_y()
    
    pdf.set_font("Arial", '', 8)
    pdf.set_xy(4, y_pos)
    pdf.cell(34, 4, "Hormat Kami,", 0, 0, 'C')
    pdf.set_xy(42, y_pos)
    pdf.cell(34, 4, "Penerima,", 0, 1, 'C')
    
    pdf.ln(12) # Ruang TTD
    
    y_line = pdf.get_y()
    pdf.set_xy(4, y_line)
    pdf.cell(34, 4, f"({data['sales_name']})", 0, 0, 'C') # Nama Sales
    pdf.set_xy(42, y_line)
    pdf.cell(34, 4, "(....................)", 0, 1, 'C')
    
    pdf.ln(4)
    
    # 6. QR CODE (GENERATOR)
    # Buat QR Code sementara
    qr_data = f"ORDER ID: {data['order_id']}\nCUSTOMER: {data['customer_name']}\nSTATUS: {data['status']}"
    qr = qrcode.make(qr_data)
    
    # Simpan ke temp file
    with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as tmp:
        qr.save(tmp.name)
        tmp_path = tmp.name
        
    # Masukkan QR ke PDF (Tengah Bawah)
    pdf.image(tmp_path, x=25, w=30)
    os.unlink(tmp_path) # Hapus file temp
    
    pdf.set_font("Courier", '', 7)
    pdf.cell(72, 4, "Scan untuk Cek Resi Digital", 0, 1, 'C')
    
    return pdf.output(dest='S').encode('latin-1')

# --- CUSTOM CSS ---
st.markdown("""
<style>
    div.stButton > button { background-color: #0095DA !important; color: white !important; border: 1px solid #0095DA !important; font-weight: bold !important; }
    div.stButton > button:hover { background-color: #007AB8 !important; border-color: #007AB8 !important; color: white !important; }
    div.stForm > div.stFormSubmitButton > button { background-color: #0095DA !important; color: white !important; border: none !important; }
    [data-testid="stLinkButton"] > a { background-color: #0095DA !important; color: white !important; border: 1px solid #0095DA !important; font-weight: bold !important; }
</style>
""", unsafe_allow_html=True)

# --- SIDEBAR & MENU ---
if 'user_role' not in st.session_state: st.session_state['user_role'] = "Guest" 
if 'user_branch' not in st.session_state: st.session_state['user_branch'] = ""

if st.session_state['user_role'] == "Guest": menu_options = ["🔐 Login Staff", "🔍 Cek Resi (Public)"]
elif st.session_state['user_role'] == "Sales": menu_options = ["📝 Input Delivery Order", "📊 Dashboard Monitoring", "🔍 Cek Resi (Public)"]
elif st.session_state['user_role'] == "SPV": menu_options = ["📝 Input Delivery Order", "⚙️ Update Status (SPV)", "📊 Dashboard Monitoring", "🔍 Cek Resi (Public)"]
elif st.session_state['user_role'] == "Admin": menu_options = ["📊 Dashboard Monitoring", "⚙️ Update Status (Admin)", "🗑️ Hapus Data (Admin)", "🔍 Cek Resi (Public)"]

menu = st.sidebar.radio("Menu Aplikasi", menu_options)

# --- FOOTER ---
with st.sidebar:
    st.divider()
    if st.session_state['user_role'] != "Guest":
        st.info(f"👤 {st.session_state['user_role']} - {st.session_state['user_branch']}")
        if st.button("Logout / Keluar"):
            st.session_state['user_role'] = "Guest"
            st.rerun()
    st.markdown("---")
    st.caption("© 2025 **Delivery Tracker System**")
    st.caption("🚀 **Versi 2.26 (Beta)**")
    st.caption("_Internal Use Only | Developed by Agung Sudrajat_")

# ==========================================
# HALAMAN 1: LOGIN
# ==========================================
if menu == "🔐 Login Staff":
    st.title("🔐 Login Sistem")
    st.info("ℹ️ Klik tanda panah (>>) di pojok kiri atas untuk menu.")
    col1, col2, col3 = st.columns([1,2,1])
    with col2:
        with st.container(border=True):
            login_type = st.radio("Tipe Akun:", ["Sales Cabang", "SPV Cabang", "Admin Pusat"])
            st.divider()
            if login_type == "Sales Cabang":
                cabang = st.selectbox("Pilih Cabang:", list(SALES_CREDENTIALS.keys()))
                pw = st.text_input("Password:", type="password")
                if st.button("Masuk", use_container_width=True):
                    if pw == SALES_CREDENTIALS.get(cabang):
                        st.session_state.update({'user_role': "Sales", 'user_branch': cabang})
                        st.rerun()
                    else: st.error("Password Salah!")
            elif login_type == "SPV Cabang":
                cabang = st.selectbox("Pilih Cabang:", list(SPV_CREDENTIALS.keys()))
                pw = st.text_input("Password:", type="password")
                if st.button("Masuk", use_container_width=True):
                    if pw == SPV_CREDENTIALS.get(cabang):
                        st.session_state.update({'user_role': "SPV", 'user_branch': cabang})
                        st.rerun()
                    else: st.error("Password Salah!")
            else:
                pw = st.text_input("Password:", type="password")
                if st.button("Masuk", use_container_width=True):
                    if pw == ADMIN_PASSWORD:
                        st.session_state.update({'user_role': "Admin", 'user_branch': "Pusat"})
                        st.rerun()
                    else: st.error("Password Salah!")

# ==========================================
# HALAMAN 2: DASHBOARD
# ==========================================
elif menu == "📊 Dashboard Monitoring":
    st.title("📊 Monitoring Operasional")
    try:
        res = supabase.table("shipments").select("*").execute()
        if res.data:
            if st.session_state['user_role'] in ["Sales", "SPV"]:
                branch = st.session_state['user_branch']
                st.info(f"📍 Data Cabang: **{branch}**")
                filtered = [d for d in res.data if d.get('branch') == branch]
            else:
                br_list = sorted(list(set([d['branch'] for d in res.data if d.get('branch')])))
                br_list.insert(0, "Semua Cabang")
                sel_br = st.selectbox("Filter Cabang:", br_list)
                filtered = res.data if sel_br == "Semua Cabang" else [d for d in res.data if d.get('branch') == sel_br]

            pending = [x for x in filtered if "selesai" not in x['status'].lower() and "dikirim" not in x['status'].lower() and "jalan" not in x['status'].lower()]
            shipping = [x for x in filtered if "dikirim" in x['status'].lower() or "jalan" in x['status'].lower()]
            done = [x for x in filtered if "selesai" in x['status'].lower() or "diterima" in x['status'].lower()]

            c1, c2, c3 = st.columns(3)
            c1.metric("📦 Diproses", f"{len(pending)}")
            c2.metric("🚚 Sedang Jalan", f"{len(shipping)}")
            c3.metric("✅ Selesai", f"{len(done)}")
            st.divider()

            with st.expander(f"📦 Diproses Gudang ({len(pending)})"):
                st.dataframe(pending, use_container_width=True)
            with st.expander(f"🚚 Sedang Jalan ({len(shipping)})"):
                st.dataframe(shipping, use_container_width=True)
            with st.expander(f"✅ Selesai ({len(done)})"):
                st.dataframe(done, use_container_width=True)
        else: st.info("Data kosong.")
    except Exception as e: st.error(str(e))

# ==========================================
# HALAMAN 3: INPUT ORDER
# ==========================================
elif menu == "📝 Input Delivery Order":
    st.title("📝 Input Delivery Order")
    branch = st.session_state['user_branch']
    st.info(f"Cabang: **{branch}**")
    
    with st.form("sales_form", clear_on_submit=False):
        c1, c2 = st.columns(2)
        in_id = c1.text_input("Order ID (Wajib)", key="in_id")
        
        c2a, c2b = c2.columns(2)
        in_sales = c2a.text_input("Nama Sales", key="in_sales")
        in_sales_hp = c2b.text_input("No WA Sales", key="in_sales_hp")
        
        c3, c4 = st.columns(2)
        in_nama = c3.text_input("Nama Customer", key="in_nama")
        in_hp = c4.text_input("No HP Customer", key="in_hp")
        in_alamat = st.text_area("Alamat Pengiriman", key="in_alamat")
        
        st.markdown("**Detail Barang**")
        c5, c6 = st.columns(2)
        in_barang = c5.text_input("Nama Barang", key="in_barang")
        in_tipe = c6.selectbox("Tipe Pengiriman", ["Reguler", "Tukar Tambah", "Express"], key="in_tipe")
        
        c7, c8 = st.columns(2)
        in_inst = c7.selectbox("Instalasi?", ["Tidak", "Ya - Vendor"], key="in_instalasi")
        in_fee = c8.text_input("Biaya Trans (Rp)", key="in_biaya_inst")
        
        if st.form_submit_button("Kirim ke Gudang"):
            if in_id and in_nama and in_barang:
                try:
                    payload = {
                        "order_id": in_id, "customer_name": in_nama, "customer_phone": in_hp,
                        "delivery_address": in_alamat, "product_name": in_barang, "delivery_type": in_tipe,
                        "sales_name": in_sales, "sales_phone": in_sales_hp, "branch": branch,
                        "status": "Menunggu Konfirmasi", "last_updated": datetime.now().isoformat(),
                        "installation_opt": in_inst, "installation_fee": in_fee
                    }
                    supabase.table("shipments").insert(payload).execute()
                    
                    # Generate PDF
                    pdf_bytes = create_thermal_pdf(payload)
                    b64_pdf = base64.b64encode(pdf_bytes).decode('latin-1')
                    
                    st.toast("Sukses! Data terkirim.", icon="✅")
                    st.success("✅ Order Berhasil Dibuat!")
                    st.markdown(f'<a href="data:application/pdf;base64,{b64_pdf}" download="SJ_{in_id}.pdf" style="text-decoration:none;"><button style="background-color:#0095DA;color:white;border:none;padding:10px;border-radius:5px;cursor:pointer;width:100%;">🖨️ CETAK SURAT JALAN (PDF 80mm)</button></a>', unsafe_allow_html=True)
                    
                    clear_input_form()
                except Exception as e: st.error(f"Error: {e}")
            else: st.toast("Lengkapi data wajib!", icon="❌")

# ==========================================
# HALAMAN 4: CEK RESI
# ==========================================
elif menu == "🔍 Cek Resi (Public)":
    st.title("🔍 Cek Resi")
    q = st.text_input("Order ID / Nama:")
    if st.button("Lacak") or q:
        if q:
            try:
                res = supabase.table("shipments").select("*").or_(f"order_id.eq.{q},customer_name.ilike.%{q}%").execute()
                if res.data:
                    for d in res.data:
                        col = get_status_color(d['status'])
                        if col=="success": st.success(f"Status: {d['status']}", icon="✅")
                        elif col=="info": st.info(f"Status: {d['status']}", icon="🚚")
                        else: st.warning(f"Status: {d['status']}", icon="⏳")
                        st.write(f"**{d['product_name']}**\nCabang: {d['branch']} | Resi: {d.get('resi','-')}")
                        st.caption("Update: " + str(d.get('last_updated', d['created_at']))[:16])
                        st.divider()
                else: st.warning("Tidak ditemukan.")
            except: st.error("Error koneksi.")

# ==========================================
# HALAMAN 5: UPDATE STATUS
# ==========================================
elif menu == "⚙️ Update Status (Admin)" or menu == "⚙️ Update Status (SPV)":
    st.title("⚙️ Validasi Order")
    q = supabase.table("shipments").select("*").order("created_at", desc=True).limit(50)
    if st.session_state['user_role'] == "SPV": q = q.eq("branch", st.session_state['user_branch'])
    res = q.execute()
    
    if res.data:
        opts = {f"[{d['status']}] {d['order_id']} - {d['customer_name']}": d for d in res.data}
        sel = st.selectbox("Pilih Order:", list(opts.keys()), index=None, key="upd_sel")
        
        if sel:
            curr = opts[sel]
            with st.expander("Tracking PT. BES"):
                st.link_button("Buka Web BES", "https://www.bes-paket.com/track-package")
                components.iframe("https://www.bes-paket.com/track-package", height=400)
            
            with st.form("upd_form"):
                c1, c2 = st.columns(2)
                sts = ["Menunggu Konfirmasi", "Diproses Gudang", "Menunggu Kurir", "Dalam Pengiriman", "Selesai/Diterima"]
                try: idx = sts.index(curr['status']) 
                except: idx=0
                n_st = c1.selectbox("Status", sts, index=idx)
                n_kur = c2.text_input("Kurir", value=curr['courier'] or "")
                n_resi = st.text_input("Resi", value=curr['resi'] or "")
                
                if st.form_submit_button("Simpan"):
                    upd = {"status": n_st, "courier": n_kur, "resi": n_resi, "last_updated": datetime.now().isoformat()}
                    supabase.table("shipments").update(upd).eq("order_id", curr['order_id']).execute()
                    st.toast("Updated!", icon="✅")
                    st.session_state["upd_sel"] = None
                    time.sleep(1)
                    st.rerun()

# ==========================================
# HALAMAN 6: HAPUS
# ==========================================
elif menu == "🗑️ Hapus Data (Admin)":
    st.title("Hapus Data")
    did = st.text_input("Order ID:")
    if st.button("Hapus Permanen", type="primary"):
        supabase.table("shipments").delete().eq("order_id", did).execute()
        st.toast("Dihapus.", icon="🗑️")
