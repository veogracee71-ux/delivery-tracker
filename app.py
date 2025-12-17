# Versi 2.67 (Layout Terpisah & Terorganisir)
# Status: Stabil & Profesional
# Update: Mengembalikan layout formulir yang dipisah menjadi 3 bagian utama:
#         1. Informasi Sales, 2. Data Pelanggan, 3. Detail Barang & Layanan.

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
    st.error("Secrets belum lengkap. Silakan periksa pengaturan di Streamlit Cloud.")
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
    
    # SALES
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
    
    # WIB Time Offset (+7)
    TIME_OFFSET = timedelta(hours=7) 
    current_time_wib = datetime.utcnow() + TIME_OFFSET 

    if not (in_id and in_sales and in_nama and in_barang):
        st.session_state['sales_error'] = "⚠️ Data wajib belum lengkap (ID, Sales, Customer, Barang)."
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
        
        pdf_bytes = create_thermal_pdf(payload, current_time_wib)
        st.session_state['sales_pdf_data'] = base64.b64encode(pdf_bytes).decode('latin-1')
        st.session_state['sales_success'] = True
        st.session_state['sales_last_id'] = in_id
        
        # Reset Data Input
        for k in ["in_id", "in_sales", "in_sales_hp", "in_nama", "in_hp", "in_alamat", "in_barang", "in_biaya_inst", "in_barang_lama"]:
            if k in st.session_state: st.session_state[k] = ""
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
    menu_options = ["📊 Dashboard Monitoring", "📝 Input Delivery Order", "⚙️ Update Status", "🗄️ Manajemen Data", "🔍 Cek Resi (Public)"]
elif st.session_state['user_role'] == "Admin":
    menu_options = ["📊 Dashboard Monitoring", "⚙️ Update Status", "🗄️ Manajemen Data", "🔍 Cek Resi (Public)"]

menu = st.sidebar.radio("Menu Aplikasi", menu_options)

with st.sidebar:
    st.divider()
    if st.session_state['user_role'] != "Guest":
        st.info(f"👤 {st.session_state['user_role']} - {st.session_state['user_branch']}")
        if st.button("Logout / Keluar"):
            st.session_state['user_role'] = "Guest"
            st.rerun()
    st.markdown("---")
    st.caption("© 2025 **Delivery Tracker System**")
    st.caption("🚀 **Versi 2.67 (Organized Layout)**")

# ==========================================
# HALAMAN 1: CEK RESI (LANDING PAGE)
# ==========================================
if menu == "🔍 Cek Resi (Public)":
    st.title("🔍 Lacak Pengiriman")
    default_oid = st.query_params.get("oid", "")
    q = st.text_input("Order ID / Nama Customer:", value=default_oid)
    if st.button("Lacak Paket") or q:
        if q:
            try:
                res = supabase.table("shipments").select("*").or_(f"order_id.eq.{q},customer_name.ilike.%{q}%").execute()
                if res.data:
                    for d in res.data:
                        tgl = d.get('last_updated') or d['created_at']
                        st.info(f"Status: {d['status']}")
                        st.markdown(f"### {d['product_name']}\n* Cabang: **{d.get('branch', '-')}**\n* Customer: **{d['customer_name']}**\n* Update: {tgl[:16].replace('T',' ')}")
                        st.divider()
                else: st.warning("Data tidak ditemukan.")
            except: st.error("Masalah koneksi database.")

# ==========================================
# HALAMAN 2: LOGIN STAFF
# ==========================================
elif menu == "🔐 Login Staff":
    st.title("🔐 Login Staff & Admin")
    if not st.session_state.get("gate_unlocked"):
        gp = st.text_input("Masukkan Kode Akses Internal:", type="password")
        if st.button("Buka Akses"):
            if gp == GATEKEEPER_PASSWORD: st.session_state["gate_unlocked"] = True; st.rerun()
            else: st.error("Kode Salah.")
        st.stop()
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        with st.container(border=True):
            tp = st.radio("Tipe Akun:", ["Sales Cabang", "SPV Cabang", "Admin Pusat"], horizontal=True)
            if tp == "Sales Cabang":
                cb = st.selectbox("Cabang:", list(SALES_CREDENTIALS.keys()))
                pw = st.text_input("Password Sales:", type="password")
                if st.button("Masuk Sales", use_container_width=True):
                    if pw == SALES_CREDENTIALS.get(cb): st.session_state.update({'user_role': "Sales", 'user_branch': cb}); st.rerun()
                    else: st.error("Password Salah!")
            elif tp == "SPV Cabang":
                cb = st.selectbox("Cabang:", list(SPV_CREDENTIALS.keys()))
                pw = st.text_input("Password SPV:", type="password")
                if st.button("Masuk SPV", use_container_width=True):
                    if pw == SPV_CREDENTIALS.get(cb): st.session_state.update({'user_role': "SPV", 'user_branch': cb}); st.rerun()
                    else: st.error("Password Salah!")
            else:
                pw = st.text_input("Password Admin:", type="password")
                if st.button("Masuk Admin", use_container_width=True):
                    if pw == ADMIN_PASSWORD: st.session_state.update({'user_role': "Admin", 'user_branch': "Pusat"}); st.rerun()
                    else: st.error("Password Salah!")

# ==========================================
# HALAMAN 3: DASHBOARD
# ==========================================
elif menu == "📊 Dashboard Monitoring":
    st.title("📊 Monitoring Operasional")
    try:
        res = supabase.table("shipments").select("*").execute()
        if res.data:
            if st.session_state['user_role'] in ["Sales", "SPV"]:
                filtered = [d for d in res.data if d.get('branch') == st.session_state['user_branch']]
            else:
                br_list = sorted(list(set([d['branch'] for d in res.data if d.get('branch')])))
                br_list.insert(0, "Semua Cabang")
                sel_br = st.selectbox("Filter Cabang:", br_list)
                filtered = res.data if sel_br == "Semua Cabang" else [d for d in res.data if d.get('branch') == sel_br]

            if not filtered:
                st.info("Belum ada data pengiriman di cabang ini.")
            else:
                p_conf = [x for x in filtered if x['status'].strip() == "Menunggu Konfirmasi"]
                if p_conf and st.session_state['user_role'] in ["SPV", "Admin"]:
                     st.error(f"🔔 PERHATIAN: Ada {len(p_conf)} Order Baru Menunggu Konfirmasi!", icon="🔥")

                df = pd.DataFrame(filtered)
                for col in ['last_updated', 'created_at']:
                    if col in df.columns: df[col] = pd.to_datetime(df[col], errors='coerce').dt.floor('S').dt.strftime('%d/%m/%Y %H:%M')
                
                disp_cols = ['order_id', 'customer_name', 'product_name', 'status', 'last_updated']
                if st.session_state['user_role'] == "Admin": disp_cols.insert(3, 'branch')
                
                c1, c2, c3 = st.columns(3)
                pending = df[~df['status'].str.contains('Selesai|Diterima|Dikirim|Jalan', case=False, na=False)]
                shipping = df[df['status'].str.contains('Dikirim|Jalan', case=False, na=False)]
                done = df[df['status'].str.contains('Selesai|Diterima', case=False, na=False)]
                
                c1.metric("📦 Diproses", len(pending))
                c2.metric("🚚 Sedang Jalan", len(shipping))
                c3.metric("✅ Selesai", len(done))
                
                with st.expander("Detail Rekapitulasi Data"):
                    st.dataframe(df[disp_cols], use_container_width=True, hide_index=True)
        else: st.info("Database masih kosong.")
    except Exception as e: st.error(f"Gagal memuat Dashboard: {e}")

# ==========================================
# HALAMAN 4: INPUT ORDER (LAYOUT TERPISAH)
# ==========================================
elif menu == "📝 Input Delivery Order":
    st.title("📝 Input Delivery Order")
    if st.session_state.get('sales_success'):
        st.success(f"✅ Order {st.session_state.get('sales_last_id')} Berhasil Disimpan!")
        b64 = st.session_state.get('sales_pdf_data')
        st.markdown(f'<a href="data:application/pdf;base64,{b64}" download="SJ_{st.session_state.get("sales_last_id")}.pdf" style="text-decoration:none;"><button style="background-color:#0095DA;color:white;border:none;padding:12px;border-radius:8px;cursor:pointer;width:100%;font-weight:bold;">DOWNLOAD SURAT JALAN (PDF 80mm)</button></a>', unsafe_allow_html=True)
        st.divider()
        if st.button("Buat Baru"): st.session_state['sales_success'] = False; st.rerun()
    else:
        if st.session_state.get('sales_error'): st.error(st.session_state['sales_error'])
        
        with st.container(border=True):
            # --- BAGIAN 1: INFO SALES & ORDER ---
            st.subheader("1. Informasi Sales & Order")
            c1, c2 = st.columns(2)
            with c1:
                st.text_input("Nomor Order / Invoice (Wajib)", key="in_id")
                st.text_input("Nama Sales Penginput", key="in_sales")
            with c2:
                st.text_input("No. WhatsApp Sales", key="in_sales_hp")
                st.info(f"📍 Cabang Asal: **{st.session_state['user_branch']}**")
            
            st.divider()
            
            # --- BAGIAN 2: DATA PELANGGAN ---
            st.subheader("2. Data Pelanggan & Alamat")
            c3, c4 = st.columns(2)
            with c3:
                st.text_input("Nama Lengkap Customer", key="in_nama")
                st.text_input("No. HP Customer", key="in_hp")
            with c4:
                st.text_area("Alamat Pengiriman Lengkap", key="in_alamat", height=100)
            
            st.divider()
            
            # --- BAGIAN 3: DETAIL BARANG ---
            st.subheader("3. Detail Barang & Layanan")
            c5, c6 = st.columns(2)
            with c5:
                st.text_input("Nama Produk", key="in_barang")
                sel_tipe = st.selectbox("Tipe Pengiriman", ["Reguler", "Tukar Tambah", "Express"], key="in_tipe")
                if sel_tipe == "Tukar Tambah":
                    st.warning("🔄 Mode Tukar Tambah Aktif")
                    st.text_input("Detail Barang Bekas (Wajib)", placeholder="Merk, Kondisi, dll...", key="in_barang_lama")
            
            with c6:
                sel_inst = st.selectbox("Opsi Instalasi?", ["Tidak", "Ya - Vendor"], key="in_instalasi")
                if sel_inst == "Ya - Vendor":
                    st.info("🔧 Instalasi Vendor Dipilih")
                    st.text_input("Biaya Transport / Instalasi (Rp)", key="in_biaya_inst")
            
            st.divider()
            st.button("Kirim ke Gudang", type="primary", on_click=process_sales_submit)

# ==========================================
# HALAMAN 5: UPDATE STATUS (LAYOUT TERPISAH)
# ==========================================
elif menu == "⚙️ Update Status":
    st.title("⚙️ Validasi Order")
    q = supabase.table("shipments").select("*").order("created_at", desc=True).limit(50)
    if st.session_state['user_role'] == "SPV": q = q.eq("branch", st.session_state['user_branch'])
    res = q.execute()
    
    if res.data:
        opts = {f"[{d['status']}] {d['order_id']} - {d['customer_name']}": d for d in res.data}
        sel = st.selectbox("Pilih Order untuk Diproses:", list(opts.keys()), index=None, key="upd_sel")
        
        if sel:
            curr = opts[sel]; oid = curr['order_id']
            with st.form("upd_form"):
                st.subheader(f"Update Order: {oid}")
                c1, c2 = st.columns(2)
                with c1:
                    sts = ["Menunggu Konfirmasi", "Diproses Gudang", "Menunggu Kurir", "Dalam Pengiriman", "Selesai/Diterima"]
                    try: idx = sts.index(curr['status']) 
                    except: idx=0
                    st.selectbox("Status Baru", sts, index=idx, key=f"stat_{oid}")
                    st.text_input("Nama Kurir / Plat No", value=curr['courier'] or "", key=f"kur_{oid}")
                    st.text_input("Nomor Resi", value=curr['resi'] or "", key=f"res_{oid}")
                
                with c2:
                    st.write("**Waktu Kejadian (Fakta Lapangan):**")
                    st.date_input("Tanggal", value=date.today(), key=f"date_{oid}")
                    st.time_input("Jam (WIB)", value=datetime.now().time(), key=f"time_{oid}")
                
                st.divider()
                st.caption("Koreksi Kesalahan Input:")
                cx, cy = st.columns(2)
                with cx: st.text_input("Koreksi Nama Customer", value=curr['customer_name'], key=f"cnama_{oid}")
                with cy: st.text_input("Koreksi Nama Barang", value=curr['product_name'], key=f"cbar_{oid}")
                
                st.form_submit_button("Simpan Perubahan", on_click=process_admin_update, args=(oid,))
    else:
        st.info("📍 Belum ada order yang masuk untuk divalidasi di cabang ini.")

# ==========================================
# HALAMAN 6: MANAJEMEN DATA
# ==========================================
elif menu == "🗄️ Manajemen Data":
    st.title("🗄️ Manajemen Data")
    res = supabase.table("shipments").select("*").execute()
    all_d = [d for d in res.data if d.get('branch') == st.session_state['user_branch']] if st.session_state['user_role'] == "SPV" else res.data
    if all_d:
        df = pd.DataFrame(all_d)
        tab1, tab2, tab3 = st.tabs(["📥 Download Excel", "🗑️ Hapus Order", "🔥 Reset"])
        with tab1:
            for c in ['created_at', 'last_updated']: 
                if c in df.columns: df[c] = pd.to_datetime(df[c], errors='coerce').dt.strftime('%d/%m/%Y %H:%M')
            output = io.BytesIO()
            with pd.ExcelWriter(output, engine='xlsxwriter') as wr:
                df.to_excel(wr, index=False, sheet_name='Laporan')
                workbook = wr.book; worksheet = wr.sheets['Laporan']
                fmt = workbook.add_format({'bold': True, 'fg_color': '#0095DA', 'font_color': '#FFFFFF', 'border': 1})
                for i, v in enumerate(df.columns.values): worksheet.write(0, i, v, fmt); worksheet.set_column(i, i, 20)
            st.download_button("Download Laporan (.xlsx)", output.getvalue(), "Laporan_Delivery.xlsx")
        with tab2:
            del_o = {f"{d['order_id']} - {d['customer_name']}": d['order_id'] for d in all_d}
            s = st.selectbox("Pilih ID untuk Dihapus:", list(del_o.keys()), index=None)
            if s and st.button("Hapus Permanen"): 
                supabase.table("shipments").delete().eq("order_id", del_o[s]).execute(); st.rerun()
        with tab3:
            if st.session_state['user_role'] == "Admin":
                if st.text_input("Konfirmasi (Ketik 'HAPUS SEMUA'):") == "HAPUS SEMUA":
                    if st.button("🔴 KOSONGKAN DATABASE"): supabase.table("shipments").delete().neq("id",0).execute(); st.rerun()
            else: st.warning("Akses Terbatas: Hanya Admin Pusat.")
    else: st.info("Data Kosong.")
