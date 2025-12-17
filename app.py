# Versi 2.32
# Update:
# 1. LAYOUT STRUK JUMBO: Semua font diperbesar (Min 10pt) agar tegas dan jelas.
# 2. Menghapus teks kecil/slogan/catatan kaki yang tidak perlu.
# 3. Fokus pada keterbacaan (Readability) di kertas thermal.

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

# --- FUNGSI CETAK PDF (UPDATE 2.32 - FONT BESAR & TEGAS) ---
def create_thermal_pdf(data):
    # Setup PDF: Lebar 80mm, Tinggi Auto (diset panjang biar aman)
    pdf = FPDF(orientation='P', unit='mm', format=(80, 250))
    pdf.add_page()
    
    # Margin 4mm
    margin = 4
    pdf.set_margins(margin, margin, margin)
    
    # Lebar area cetak efektif
    w_full = 72
    
    def draw_line():
        pdf.ln(2)
        y = pdf.get_y()
        pdf.line(margin, y, margin + w_full, y)
        pdf.ln(2)

    # 1. HEADER (Sangat Jelas)
    pdf.set_font("Arial", 'B', 16) # Font Besar
    pdf.cell(w_full, 8, "BLIBLI ELEKTRONIK", 0, 1, 'C')
    
    pdf.set_font("Arial", 'B', 14)
    pdf.cell(w_full, 8, "SURAT JALAN", 1, 1, 'C')
    draw_line()
    
    # 2. INFO TRANSAKSI (Tegas)
    pdf.set_font("Arial", '', 10)
    pdf.cell(20, 5, "No Order", 0, 0)
    pdf.set_font("Arial", 'B', 11) # Order ID Besar
    pdf.cell(52, 5, f": {data['order_id']}", 0, 1)
    
    pdf.set_font("Arial", '', 10)
    pdf.cell(20, 5, "Tanggal", 0, 0)
    pdf.cell(52, 5, f": {datetime.now().strftime('%d/%m/%y %H:%M')}", 0, 1)
    
    draw_line()
    
    # 3. PENERIMA (Fokus Alamat)
    pdf.set_font("Arial", 'B', 11)
    pdf.cell(w_full, 6, "PENERIMA:", 0, 1)
    
    pdf.set_font("Arial", 'B', 12) # Nama Customer Besar
    pdf.multi_cell(w_full, 6, f"{data['customer_name']}")
    
    pdf.set_font("Arial", '', 11)
    pdf.cell(w_full, 6, f"HP: {data['customer_phone']}", 0, 1)
    
    pdf.ln(1)
    pdf.set_font("Arial", '', 11) # Alamat Jelas
    pdf.multi_cell(w_full, 5, f"{data['delivery_address']}")
    
    draw_line()
    
    # 4. PENGIRIM
    pdf.set_font("Arial", 'B', 11)
    pdf.cell(w_full, 6, "PENGIRIM (SALES):", 0, 1)
    pdf.set_font("Arial", '', 10)
    pdf.cell(15, 5, "Nama", 0, 0)
    pdf.cell(57, 5, f": {data['sales_name']} ({data['branch']})", 0, 1)
    pdf.cell(15, 5, "WA", 0, 0)
    pdf.cell(57, 5, f": {data.get('sales_phone', '-')}", 0, 1)
    
    draw_line()
    
    # 5. BARANG (Paling Penting)
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(w_full, 8, "BARANG:", 0, 1)
    
    pdf.set_font("Arial", 'B', 11)
    pdf.multi_cell(w_full, 6, f"• {data['product_name']}")
    
    pdf.ln(2)
    pdf.set_font("Arial", '', 10)
    pdf.cell(25, 5, "Tipe Kirim", 0, 0)
    pdf.cell(47, 5, f": {data['delivery_type']}", 0, 1)
    
    if data.get('installation_opt') == "Ya - Vendor":
        pdf.cell(25, 5, "Instalasi", 0, 0)
        pdf.cell(47, 5, f": YA (Vendor)", 0, 1)
        pdf.cell(25, 5, "Biaya", 0, 0)
        pdf.cell(47, 5, f": Rp {data.get('installation_fee', '-')}", 0, 1)
    
    draw_line()
    
    # 6. TANDA TANGAN (Luas)
    pdf.ln(5)
    y_start = pdf.get_y()
    col_w = 36
    
    pdf.set_font("Arial", '', 10)
    pdf.set_xy(margin, y_start)
    pdf.cell(col_w, 5, "Pengirim,", 0, 0, 'C')
    pdf.set_xy(margin + col_w, y_start)
    pdf.cell(col_w, 5, "Penerima,", 0, 1, 'C')
    
    pdf.ln(20) # Ruang TTD Besar (2cm)
    
    y_end = pdf.get_y()
    pdf.set_font("Arial", 'B', 10)
    pdf.set_xy(margin, y_end)
    pdf.cell(col_w, 5, f"({data['sales_name']})", 0, 0, 'C')
    pdf.set_xy(margin + col_w, y_end)
    pdf.cell(col_w, 5, "(....................)", 0, 1, 'C')
    
    pdf.ln(8)
    
    # 7. QR CODE (Besar)
    qr_data = f"ID:{data['order_id']}|{data['customer_name']}|{data['status']}"
    qr = qrcode.make(qr_data)
    with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as tmp:
        qr.save(tmp.name)
        tmp_path = tmp.name
    
    # QR ditengah dan agak besar (30mm)
    qr_x = margin + (w_full - 30) / 2
    pdf.image(tmp_path, x=qr_x, w=30) 
    os.unlink(tmp_path)
    
    pdf.ln(2)
    pdf.set_font("Arial", 'B', 10)
    pdf.cell(w_full, 5, "SCAN UNTUK CEK STATUS", 0, 1, 'C')
    
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
    in_inst = s.get("in_instalasi", "Tidak")
    in_fee = s.get("in_biaya_inst", "")
    branch = s.get("user_branch", "")

    if not (in_id and in_sales and in_nama and in_barang):
        st.session_state['sales_error'] = "⚠️ Mohon lengkapi data wajib (ID, Nama Sales, Nama Customer, Nama Barang)."
        return

    try:
        payload = {
            "order_id": in_id, "customer_name": in_nama, "customer_phone": in_hp,
            "delivery_address": in_alamat, "product_name": in_barang, "delivery_type": in_tipe,
            "sales_name": in_sales, "sales_phone": in_sales_hp, "branch": branch,
            "status": "Menunggu Konfirmasi", "last_updated": datetime.now().isoformat(),
            "installation_opt": in_inst, "installation_fee": in_fee
        }
        supabase.table("shipments").insert(payload).execute()
        
        pdf_bytes = create_thermal_pdf(payload)
        b64_pdf = base64.b64encode(pdf_bytes).decode('latin-1')
        
        st.session_state['sales_success'] = True
        st.session_state['sales_pdf_data'] = b64_pdf
        st.session_state['sales_last_id'] = in_id
        
        keys_to_clear = ["in_id", "in_sales", "in_sales_hp", "in_nama", "in_hp", "in_alamat", "in_barang", "in_biaya_inst"]
        for k in keys_to_clear:
            st.session_state[k] = ""
        st.session_state["in_tipe"] = "Reguler"
        st.session_state["in_instalasi"] = "Tidak"
        
    except Exception as e:
        err_msg = str(e)
        if "duplicate key" in err_msg or "23505" in err_msg:
            st.session_state['sales_error'] = f"⛔ Gagal! Order ID **{in_id}** sudah terdaftar. Cek nomor nota Anda."
        else:
            st.session_state['sales_error'] = f"Error Sistem: {err_msg}"

# --- CUSTOM CSS ---
st.markdown("""
<style>
    div.stButton > button { background-color: #0095DA !important; color: white !important; border: 1px solid #0095DA !important; font-weight: bold !important; }
    div.stButton > button:hover { background-color: #007AB8 !important; border-color: #007AB8 !important; color: white !important; }
    div.stForm > div.stFormSubmitButton > button { background-color: #0095DA !important; color: white !important; border: none !important; }
    [data-testid="stFormSubmitButton"] > button { background-color: #0095DA !important; color: white !important; border: none !important; } 
    [data-testid="stLinkButton"] > a { background-color: #0095DA !important; color: white !important; border: 1px solid #0095DA !important; font-weight: bold !important; }
</style>
""", unsafe_allow_html=True)

# --- SIDEBAR LOGIC ---
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
    st.caption("🚀 **Versi 2.32 (Beta)**")
    st.caption("_Internal Use Only | Developed by Agung Sudrajat_")

# ==========================================
# HALAMAN 1: LOGIN
# ==========================================
if menu == "🔐 Login Staff":
    st.title("🔐 Login Sistem Delivery Tracker")
    st.info("ℹ️ Klik tanda panah (>>) di pojok kiri atas untuk membuka menu lainnya.")
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        with st.container(border=True):
            login_type = st.radio("Pilih Tipe Akun:", ["Sales Cabang", "SPV Cabang", "Admin Pusat"], horizontal=True)
            st.divider()
            if login_type == "Sales Cabang":
                cabang = st.selectbox("Pilih Cabang:", list(SALES_CREDENTIALS.keys()))
                pw = st.text_input("Password Sales:", type="password")
                if st.button("Masuk sebagai Sales", use_container_width=True):
                    if pw == SALES_CREDENTIALS.get(cabang):
                        st.session_state.update({'user_role': "Sales", 'user_branch': cabang})
                        st.rerun()
                    else: st.error("Password Salah!")
            elif login_type == "SPV Cabang":
                cabang = st.selectbox("Pilih Cabang:", list(SPV_CREDENTIALS.keys()))
                pw = st.text_input("Password SPV:", type="password")
                if st.button("Masuk sebagai SPV", use_container_width=True):
                    if pw == SPV_CREDENTIALS.get(cabang):
                        st.session_state.update({'user_role': "SPV", 'user_branch': cabang})
                        st.rerun()
                    else: st.error("Password Salah!")
            else:
                pw = st.text_input("Password Admin:", type="password")
                if st.button("Masuk Admin", use_container_width=True):
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

            with st.expander(f"📦 Diproses Gudang ({len(pending)})", expanded=False): st.dataframe(pending, use_container_width=True)
            with st.expander(f"🚚 Sedang Jalan ({len(shipping)})", expanded=False): st.dataframe(shipping, use_container_width=True)
            with st.expander(f"✅ Selesai ({len(done)})", expanded=False): st.dataframe(done, use_container_width=True)
        else: st.info("Data kosong.")
    except Exception as e: st.error(str(e))

# ==========================================
# HALAMAN 3: INPUT ORDER
# ==========================================
elif menu == "📝 Input Delivery Order":
    st.title("📝 Input Delivery Order")
    branch = st.session_state['user_branch']
    st.info(f"Cabang: **{branch}**")
    
    if st.session_state.get('sales_success'):
        st.success(f"✅ Order {st.session_state.get('sales_last_id')} Berhasil Dikirim!")
        st.toast("Data terkirim!", icon="🚀")
        b64 = st.session_state.get('sales_pdf_data')
        st.markdown(f'<a href="data:application/pdf;base64,{b64}" download="SJ_{st.session_state.get("sales_last_id")}.pdf" style="text-decoration:none;"><button style="background-color:#0095DA;color:white;border:none;padding:10px;border-radius:5px;cursor:pointer;width:100%;">🖨️ DOWNLOAD SURAT JALAN (PDF 80mm)</button></a>', unsafe_allow_html=True)
        st.caption("*Silakan download sebelum input data baru.*")
        st.divider()
    
    if st.session_state.get('sales_error'):
        st.error(st.session_state['sales_error'])

    with st.form("sales_form", clear_on_submit=False):
        c1, c2 = st.columns(2)
        st.text_input("Order ID (Wajib)", key="in_id")
        
        c2a, c2b = c2.columns(2)
        st.text_input("Nama Sales", key="in_sales")
        st.text_input("No WA Sales", key="in_sales_hp")
        
        c3, c4 = st.columns(2)
        st.text_input("Nama Customer", key="in_nama")
        st.text_input("No HP Customer", key="in_hp")
        st.text_area("Alamat Pengiriman", key="in_alamat")
        
        st.markdown("**Detail Barang**")
        c5, c6 = st.columns(2)
        st.text_input("Nama Barang", key="in_barang")
        st.selectbox("Tipe Pengiriman", ["Reguler", "Tukar Tambah", "Express"], key="in_tipe")
        
        c7, c8 = st.columns(2)
        st.selectbox("Instalasi?", ["Tidak", "Ya - Vendor"], key="in_instalasi")
        st.text_input("Biaya Trans (Rp)", key="in_biaya_inst")
        
        st.form_submit_button("Kirim ke Gudang", type="primary", on_click=process_sales_submit)

# ==========================================
# HALAMAN 4: CEK RESI
# ==========================================
elif menu == "🔍 Cek Resi (Public)":
    st.title("🔍 Cek Resi")
    
    default_oid = ""
    try:
        qp = st.query_params
        if "oid" in qp: default_oid = qp["oid"]
    except: pass

    q = st.text_input("Order ID / Nama Customer:", value=default_oid)
    auto_click = True if default_oid else False

    if st.button("Lacak") or q or auto_click:
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

                        st.markdown(f"""
                        ### {d['product_name']}
                        * 🏢 Cabang: **{d.get('branch', '-')}**
                        * 👤 Customer: **{d['customer_name']}**
                        * 🔢 Order ID: `{d['order_id']}`
                        * 🚚 Kurir: {d['courier'] or '-'}
                        * 🔖 Resi: {d['resi'] or '-'}
                        {install_info}
                        * 🕒 **Update:** {tgl[:16].replace('T',' ')}
                        """)
                        msg = f"Halo Kak {d['customer_name']}, pesanan {d['product_name']} statusnya: *{d['status']}*."
                        st.code(msg, language=None)
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
                
                st.divider()
                st.write("**Waktu Status Terakhir (Fakta Lapangan):**")
                d_date = c1.date_input("Tanggal", value="today")
                d_time = c2.time_input("Jam", value="now")
                final_dt = datetime.combine(d_date, d_time).isoformat()

                if st.form_submit_button("Simpan"):
                    upd = {"status": n_st, "courier": n_kur, "resi": n_resi, "last_updated": final_dt}
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
