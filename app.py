# Versi 2.70 (Professional Minimalist)
# Status: Stabil & Bersih
# Update: Mengembalikan Navigasi Sidebar, Mengurangi Noise Emoji, 
#         dan Mempertahankan Layout Form 2 Kolom yang Rapi.

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
    initial_sidebar_state="expanded" 
)

# --- LOAD SECRETS ---
try:
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    ADMIN_PASSWORD = st.secrets["passwords"]["admin"]
    SALES_CREDENTIALS = st.secrets["passwords"]["sales"]
    SPV_CREDENTIALS = st.secrets["passwords"]["spv"]
    GATEKEEPER_PASSWORD = st.secrets["passwords"].get("gatekeeper", "blibli")
except:
    st.error("Secrets belum lengkap. Pastikan SUPABASE_URL, SUPABASE_KEY, dan passwords tersedia.")
    st.stop()

supabase: Client = create_client(url, key)
APP_BASE_URL = "https://delivery-tracker.streamlit.app" 

# --- CUSTOM CSS (PREMIUM CLEAN LOOK) ---
st.markdown("""
<style>
    /* Font Selection */
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;600;700&display=swap');
    html, body, [class*="css"] { font-family: 'Plus Jakarta Sans', sans-serif; }

    /* Main Button Styling */
    div.stButton > button { 
        background-color: #0095DA !important; 
        color: white !important; 
        border-radius: 8px !important;
        font-weight: 600 !important;
        border: none !important;
        padding: 0.5rem 1rem !important;
    }
    div.stButton > button:hover { background-color: #007AB8 !important; }

    /* Form Submit Button */
    div.stFormSubmitButton > button { 
        background-color: #0095DA !important; 
        width: 100% !important;
        border-radius: 8px !important;
    }

    /* Input Styling */
    .stTextInput>div>div>input, .stTextArea>div>div>textarea {
        border-radius: 8px !important;
    }

    /* Sidebar Styling */
    [data-testid="stSidebar"] { background-color: #F8FAFC; border-right: 1px solid #E2E8F0; }
</style>
""", unsafe_allow_html=True)

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

    # HEADER
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
    
    # BARANG
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(w_full, 8, "BARANG:", 0, 1)
    pdf.set_font("Arial", 'B', 11)
    pdf.multi_cell(w_full, 6, f"- {safe_text(data['product_name'])}")
    draw_line()
    
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
    
    # Capture inputs from session state
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
    
    # WIB Time
    TIME_OFFSET = timedelta(hours=7) 
    current_time_wib = datetime.utcnow() + TIME_OFFSET 

    if not (in_id and in_sales and in_nama and in_barang):
        st.session_state['sales_error'] = "Harap isi data wajib (ID, Sales, Customer, Barang)."
        return

    try:
        payload = {
            "order_id": in_id, "customer_name": in_nama, "customer_phone": in_hp,
            "delivery_address": in_alamat, "product_name": in_barang, "delivery_type": in_tipe,
            "sales_name": in_sales, "sales_phone": in_sales_hp, "branch": branch,
            "status": "Menunggu Konfirmasi", "last_updated": current_time_wib.isoformat(),
            "installation_opt": in_inst, "installation_fee": in_fee, "old_product_name": in_old_item
        }
        supabase.table("shipments").insert(payload).execute()
        
        # PDF Generation
        pdf_bytes = create_thermal_pdf(payload, current_time_wib)
        st.session_state['sales_pdf_data'] = base64.b64encode(pdf_bytes).decode('latin-1')
        st.session_state['sales_success'] = True
        st.session_state['sales_last_id'] = in_id
        
        # Reset inputs
        for k in ["in_id", "in_sales", "in_sales_hp", "in_nama", "in_hp", "in_alamat", "in_barang", "in_barang_lama", "in_biaya_inst"]:
            if k in st.session_state: st.session_state[k] = ""
            
    except Exception as e:
        st.session_state['sales_error'] = f"Gagal menyimpan: {str(e)}"

# --- CALLBACK ADMIN UPDATE ---
def process_admin_update(oid):
    upd = {
        "status": st.session_state.get(f"stat_{oid}"),
        "courier": st.session_state.get(f"kur_{oid}"),
        "resi": st.session_state.get(f"res_{oid}"),
        "last_updated": datetime.combine(st.session_state.get(f"date_{oid}"), st.session_state.get(f"time_{oid}")).isoformat(),
        "customer_name": st.session_state.get(f"cnama_{oid}"),
        "product_name": st.session_state.get(f"cbar_{oid}")
    }
    try:
        supabase.table("shipments").update(upd).eq("order_id", oid).execute()
        st.toast("Data Berhasil Diupdate!", icon="✅")
        st.session_state["upd_sel"] = None
    except Exception as e:
        st.error(f"Gagal Update: {e}")

# --- SIDEBAR LOGIC ---
if 'user_role' not in st.session_state: st.session_state['user_role'] = "Guest"
if 'user_branch' not in st.session_state: st.session_state['user_branch'] = ""

with st.sidebar:
    st.image("https://upload.wikimedia.org/wikipedia/commons/9/9e/Blibli.com_Logo.svg", width=120)
    st.markdown("### Delivery Tracker")
    
    if st.session_state['user_role'] == "Guest":
        menu_options = ["🔍 Lacak Paket", "🔐 Login Staff"]
    elif st.session_state['user_role'] == "Sales":
        menu_options = ["📊 Dashboard", "📝 Input Order", "🔍 Lacak Paket"]
    elif st.session_state['user_role'] == "SPV":
        menu_options = ["📊 Dashboard", "📝 Input Order", "⚙️ Update Status", "🗄️ Manajemen Data", "🔍 Lacak Paket"]
    elif st.session_state['user_role'] == "Admin":
        menu_options = ["📊 Dashboard", "⚙️ Update Status", "🗄️ Manajemen Data", "🔍 Lacak Paket"]
    
    menu = st.radio("Navigasi", menu_options)
    st.divider()
    
    if st.session_state['user_role'] != "Guest":
        st.info(f"User: {st.session_state['user_role']}\nCabang: {st.session_state['user_branch']}")
        if st.button("Log Out"):
            st.session_state['user_role'] = "Guest"
            st.rerun()

# ==========================================
# HALAMAN: LACAK PAKET
# ==========================================
if menu == "🔍 Lacak Paket":
    st.title("Lacak Pengiriman")
    q = st.text_input("Order ID atau Nama Customer:", value=st.query_params.get("oid", ""))
    if st.button("Cari Pesanan") or q:
        if q:
            try:
                res = supabase.table("shipments").select("*").or_(f"order_id.eq.{q},customer_name.ilike.%{q}%").execute()
                if res.data:
                    for d in res.data:
                        tgl = d.get('last_updated') or d['created_at']
                        st.success(f"Status: {d['status']}")
                        st.markdown(f"""
                        **Detail Pesanan:**
                        * Barang: {d['product_name']}
                        * Kurir: {d['courier'] or '-'}
                        * Update Terakhir: {tgl[:16].replace('T',' ')}
                        """)
                        st.divider()
                else: st.warning("Data tidak ditemukan.")
            except: st.error("Masalah koneksi.")

# ==========================================
# HALAMAN: LOGIN STAFF
# ==========================================
elif menu == "🔐 Login Staff":
    if not st.session_state.get('gate_unlocked'):
        st.title("Akses Terbatas")
        gp = st.text_input("Masukkan Kode Akses Internal:", type="password")
        if st.button("Buka Akses"):
            if gp == GATEKEEPER_PASSWORD: st.session_state['gate_unlocked'] = True; st.rerun()
            else: st.error("Kode Salah.")
        st.stop()
    
    st.title("Login Staff")
    col1, col2 = st.columns([1,1])
    with col1:
        tp = st.selectbox("Pilih Tipe Akun", ["Sales", "SPV", "Admin"])
        if tp != "Admin":
            cb = st.selectbox("Pilih Cabang", list(SALES_CREDENTIALS.keys()))
        pw = st.text_input("Password", type="password")
        if st.button("Masuk"):
            if tp == "Admin" and pw == ADMIN_PASSWORD:
                st.session_state.update({'user_role': "Admin", 'user_branch': "Pusat"}); st.rerun()
            elif tp == "Sales" and pw == SALES_CREDENTIALS.get(cb):
                st.session_state.update({'user_role': "Sales", 'user_branch': cb}); st.rerun()
            elif tp == "SPV" and pw == SPV_CREDENTIALS.get(cb):
                st.session_state.update({'user_role': "SPV", 'user_branch': cb}); st.rerun()
            else: st.error("Password Salah!")

# ==========================================
# HALAMAN: DASHBOARD
# ==========================================
elif menu == "📊 Dashboard":
    st.title(f"Monitoring: {st.session_state['user_branch']}")
    try:
        res = supabase.table("shipments").select("*").execute()
        if res.data:
            filtered = [d for d in res.data if d.get('branch') == st.session_state['user_branch']] if st.session_state['user_role'] != "Admin" else res.data
            
            p_conf = [x for x in filtered if str(x.get('status','')).strip() == "Menunggu Konfirmasi"]
            if p_conf and st.session_state['user_role'] in ["SPV", "Admin"]:
                 st.error(f"Notifikasi: Ada {len(p_conf)} Order Baru Menunggu Konfirmasi!")

            df = pd.DataFrame(filtered)
            if not df.empty:
                for col in ['last_updated', 'created_at']:
                    if col in df.columns: df[col] = pd.to_datetime(df[col], errors='coerce').dt.strftime('%d/%m/%Y %H:%M')
                
                disp = ['order_id', 'customer_name', 'product_name', 'status', 'last_updated']
                if st.session_state['user_role'] == "Admin": disp.insert(3, 'branch')
                
                c1, c2, c3 = st.columns(3)
                pending = df[~df['status'].str.contains('Selesai|Dikirim|Jalan|Diterima', case=False, na=False)]
                shipping = df[df['status'].str.contains('Dikirim|Jalan', case=False, na=False)]
                done = df[df['status'].str.contains('Selesai|Diterima', case=False, na=False)]
                
                c1.metric("📦 Diproses", len(pending))
                c2.metric("🚚 Di Jalan", len(shipping))
                c3.metric("✅ Selesai", len(done))
                
                with st.expander("Detail Data"):
                    st.dataframe(df[disp], use_container_width=True, hide_index=True)
        else: st.info("Belum ada data.")
    except Exception as e: st.error(f"Gagal memuat: {e}")

# ==========================================
# HALAMAN: INPUT ORDER (CLEAN 2 COLUMNS)
# ==========================================
elif menu == "📝 Input Order":
    st.title("Input Delivery Order")
    if st.session_state.get('sales_success'):
        st.success(f"Order Berhasil Disimpan! (ID: {st.session_state.get('sales_last_id')})")
        b64 = st.session_state.get('sales_pdf_data')
        st.markdown(f'<a href="data:application/pdf;base64,{b64}" download="SJ_{st.session_state.get("sales_last_id")}.pdf" style="text-decoration:none;"><button style="background-color:#0095DA;color:white;border:none;padding:12px;border-radius:8px;cursor:pointer;width:100%;font-weight:600;">DOWNLOAD SURAT JALAN</button></a>', unsafe_allow_html=True)
        if st.button("Buat Order Baru"): st.session_state['sales_success'] = False; st.rerun()
    else:
        if st.session_state.get('sales_error'): st.error(st.session_state['sales_error'])
        with st.container(border=True):
            st.subheader("Data Pengiriman")
            c1, c2 = st.columns(2)
            with c1:
                st.text_input("Nomor Order (ID)", key="in_id")
                st.text_input("Nama Customer", key="in_nama")
                st.text_input("No HP Customer", key="in_hp")
                st.text_input("Nama Sales", key="in_sales")
            with c2:
                st.text_area("Alamat Pengiriman", key="in_alamat", height=100)
                st.text_input("No WA Sales", key="in_sales_hp")
            
            st.divider()
            st.subheader("Detail Produk")
            c3, c4 = st.columns(2)
            with c3:
                st.text_input("Nama Barang", key="in_barang")
                tp = st.selectbox("Tipe Pengiriman", ["Reguler", "Tukar Tambah", "Express"], key="in_tipe")
                if tp == "Tukar Tambah": st.text_input("Detail Barang Lama (Wajib)", key="in_barang_lama")
            with c4:
                inst = st.selectbox("Instalasi Vendor?", ["Tidak", "Ya - Vendor"], key="in_instalasi")
                if inst == "Ya - Vendor": st.text_input("Biaya Transport (Rp)", key="in_biaya_inst")
            
            st.divider()
            st.button("Simpan & Kirim ke Gudang", on_click=process_sales_submit)

# ==========================================
# HALAMAN: UPDATE STATUS
# ==========================================
elif menu == "⚙️ Update Status":
    st.title("Validasi & Update Status")
    q = supabase.table("shipments").select("*").order("created_at", desc=True).limit(50)
    if st.session_state['user_role'] == "SPV": q = q.eq("branch", st.session_state['user_branch'])
    res = q.execute()
    if res.data:
        opts = {f"[{d['status']}] {d['order_id']} - {d['customer_name']}": d for d in res.data}
        sel = st.selectbox("Pilih Order untuk Diupdate:", list(opts.keys()), index=None, key="upd_sel")
        if sel:
            curr = opts[sel]; oid = curr['order_id']
            with st.form("upd_form"):
                st.subheader(f"Update: {oid}")
                c1, c2 = st.columns(2)
                with c1:
                    sts = ["Menunggu Konfirmasi", "Diproses Gudang", "Menunggu Kurir", "Dalam Pengiriman", "Selesai/Diterima"]
                    st.selectbox("Status Baru", sts, index=sts.index(curr['status']) if curr['status'] in sts else 0, key=f"stat_{oid}")
                    st.text_input("Nama Kurir", value=curr['courier'] or "", key=f"kur_{oid}")
                    st.text_input("No Resi / Plat No", value=curr['resi'] or "", key=f"res_{oid}")
                with c2:
                    st.date_input("Tanggal Kejadian", value=date.today(), key=f"date_{oid}")
                    st.time_input("Jam Kejadian (WIB)", value=datetime.now().time(), key=f"time_{oid}")
                st.divider()
                st.caption("Koreksi Data:")
                cx, cy = st.columns(2)
                with cx: st.text_input("Koreksi Nama Customer", value=curr['customer_name'], key=f"cnama_{oid}")
                with cy: st.text_input("Koreksi Nama Barang", value=curr['product_name'], key=f"cbar_{oid}")
                st.form_submit_button("Simpan Perubahan", on_click=process_admin_update, args=(oid,))
    else: st.info("Belum ada data untuk divalidasi.")

# ==========================================
# HALAMAN: MANAJEMEN DATA
# ==========================================
elif menu == "🗄️ Manajemen Data":
    st.title("Manajemen Data")
    res = supabase.table("shipments").select("*").execute()
    all_d = [d for d in res.data if d.get('branch') == st.session_state['user_branch']] if st.session_state['user_role'] == "SPV" else res.data
    if all_d:
        df = pd.DataFrame(all_d)
        tab1, tab2, tab3 = st.tabs(["Download Excel", "Hapus Order", "Reset Database"])
        with tab1:
            for c in ['created_at', 'last_updated']: 
                if c in df.columns: df[c] = pd.to_datetime(df[c], errors='coerce').dt.strftime('%d/%m/%Y %H:%M')
            out = io.BytesIO()
            with pd.ExcelWriter(out, engine='xlsxwriter') as wr:
                df.to_excel(wr, index=False, sheet_name='Laporan')
            st.download_button("Download Laporan (.xlsx)", out.getvalue(), "Laporan_Delivery.xlsx")
        with tab2:
            del_o = {f"{d['order_id']} - {d['customer_name']}": d['order_id'] for d in all_d}
            s = st.selectbox("Pilih Order yang akan dihapus:", list(del_o.keys()), index=None)
            if s and st.button("Hapus Permanen"): 
                supabase.table("shipments").delete().eq("order_id", del_o[s]).execute(); st.rerun()
        with tab3:
            if st.session_state['user_role'] == "Admin":
                if st.text_input("Ketik 'HAPUS SEMUA' untuk konfirmasi:") == "HAPUS SEMUA":
                    if st.button("KOSONGKAN DATABASE"): supabase.table("shipments").delete().neq("id",0).execute(); st.rerun()
            else: st.warning("Akses Khusus Admin Pusat.")
    else: st.info("Data Kosong.")
