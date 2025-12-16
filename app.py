# Versi 2.19
# Update: Mengubah tahun copyright di footer menjadi 2025.

import streamlit as st
import streamlit.components.v1 as components 
from supabase import create_client, Client
from urllib.parse import quote
import time
from datetime import datetime, date 

# --- KONFIGURASI HALAMAN (SIDEBAR COLLAPSED) ---
st.set_page_config(
    page_title="Delivery Tracker", 
    page_icon="📦", 
    layout="wide", 
    initial_sidebar_state="collapsed" 
)

# --- LOAD KONFIGURASI DARI SECRETS ---
try:
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    ADMIN_PASSWORD = st.secrets["passwords"]["admin"]
    SALES_CREDENTIALS = st.secrets["passwords"]["sales"]
    SPV_CREDENTIALS = st.secrets["passwords"]["spv"]
except FileNotFoundError:
    st.error("File secrets.toml tidak ditemukan. Harap atur di Dashboard Streamlit.")
    st.stop()
except KeyError as e:
    st.error(f"Konfigurasi Secrets belum lengkap. Key yang hilang: {e}. Harap cek format secrets.toml Anda.")
    st.stop()

if not url or "https" not in url:
    st.error("Format SUPABASE_URL salah.")
    st.stop()

supabase: Client = create_client(url, key)

# --- FUNGSI BANTUAN ---
def get_status_color(status):
    s = status.lower()
    if "selesai" in s or "diterima" in s:
        return "success"
    elif "dikirim" in s or "jalan" in s or "pengiriman" in s:
        return "info"
    else:
        return "warning"

def clear_input_form():
    for key in ["in_id", "in_sales", "in_nama", "in_hp", "in_alamat", "in_barang"]:
        if key in st.session_state:
            st.session_state[key] = ""
    if "in_tipe" in st.session_state:
        st.session_state["in_tipe"] = "Reguler"

# --- CUSTOM CSS ---
st.markdown("""
<style>
    div.stButton > button {
        background-color: #0095DA !important;
        color: white !important;
        border: 1px solid #0095DA !important;
        font-weight: bold !important;
    }
    div.stButton > button:hover {
        background-color: #007AB8 !important;
        border-color: #007AB8 !important;
        color: white !important;
    }
    div.stForm > div.stFormSubmitButton > button {
        background-color: #0095DA !important;
        color: white !important;
        border: none !important;
    }
</style>
""", unsafe_allow_html=True)

# --- SIDEBAR LOGIC ---
if 'user_role' not in st.session_state:
    st.session_state['user_role'] = "Guest" 
if 'user_branch' not in st.session_state:
    st.session_state['user_branch'] = ""

if st.session_state['user_role'] == "Guest":
    menu_options = ["🔐 Login Staff", "🔍 Cek Resi (Public)"]
elif st.session_state['user_role'] == "Sales":
    menu_options = ["📝 Input Delivery Order", "📊 Dashboard Monitoring", "🔍 Cek Resi (Public)"]
elif st.session_state['user_role'] == "SPV":
    menu_options = ["📝 Input Delivery Order", "⚙️ Update Status (SPV)", "📊 Dashboard Monitoring", "🔍 Cek Resi (Public)"]
elif st.session_state['user_role'] == "Admin":
    menu_options = ["📊 Dashboard Monitoring", "⚙️ Update Status (Admin)", "🗑️ Hapus Data (Admin)", "🔍 Cek Resi (Public)"]

menu = st.sidebar.radio("Menu Aplikasi", menu_options)

# --- FOOTER & INFO USER DI SIDEBAR ---
with st.sidebar:
    st.divider()
    
    if st.session_state['user_role'] != "Guest":
        st.info(f"👤 {st.session_state['user_role']} - {st.session_state['user_branch']}")
        if st.button("Logout / Keluar"):
            st.session_state['user_role'] = "Guest"
            st.session_state['user_branch'] = ""
            st.rerun()
    
    # --- FOOTER PROFESIONAL (UPDATED YEAR) ---
    st.markdown("---")
    st.caption("© 2025 **Delivery Tracker System**")
    st.caption("🚀 **Versi 2.19 (Beta)**")
    st.caption("Dibuat untuk mempermudah operasional & monitoring pengiriman.")
    st.caption("_Internal Use Only | Developed by Agung Sudrajat_")

# ==========================================
# HALAMAN 1: LOGIN PAGE (KHUSUS GUEST)
# ==========================================
if menu == "🔐 Login Staff":
    st.title("🔐 Login Sistem Delivery Tracker")
    st.info("ℹ️ Klik tanda panah (>) di pojok kiri atas untuk membuka menu lainnya.")
    st.markdown("Silakan login sesuai peran Anda untuk mengakses Dashboard Operasional.")
    
    col_login1, col_login2, col_login3 = st.columns([1, 2, 1])
    
    with col_login2:
        with st.container(border=True):
            login_type = st.radio("Pilih Tipe Akun:", ["Sales Cabang", "SPV Cabang", "Admin Pusat"], horizontal=True)
            st.divider()
            
            if login_type == "Sales Cabang":
                cabang_list = list(SALES_CREDENTIALS.keys())
                selected_cabang = st.selectbox("Pilih Cabang Anda:", cabang_list)
                pw = st.text_input("Password Sales:", type="password")
                if st.button("Masuk sebagai Sales", use_container_width=True):
                    if pw == SALES_CREDENTIALS.get(selected_cabang):
                        st.session_state['user_role'] = "Sales"
                        st.session_state['user_branch'] = selected_cabang
                        st.toast("Login Berhasil!", icon="👋")
                        time.sleep(0.5)
                        st.rerun()
                    else:
                        st.error("Password Salah!")

            elif login_type == "SPV Cabang":
                cabang_list = list(SPV_CREDENTIALS.keys())
                selected_cabang = st.selectbox("Pilih Cabang Anda:", cabang_list, key="spv_login_sel")
                pw = st.text_input("Password SPV:", type="password")
                if st.button("Masuk sebagai SPV", use_container_width=True):
                    if pw == SPV_CREDENTIALS.get(selected_cabang):
                        st.session_state['user_role'] = "SPV"
                        st.session_state['user_branch'] = selected_cabang
                        st.toast("Login Berhasil!", icon="👔")
                        time.sleep(0.5)
                        st.rerun()
                    else:
                        st.error("Password Salah!")

            else: # Admin Pusat
                pw_admin = st.text_input("Password Admin Pusat:", type="password")
                if st.button("Masuk Admin", use_container_width=True):
                    if pw_admin == ADMIN_PASSWORD:
                        st.session_state['user_role'] = "Admin"
                        st.session_state['user_branch'] = "Pusat"
                        st.toast("Login Admin Berhasil!", icon="🔐")
                        time.sleep(0.5)
                        st.rerun()
                    else:
                        st.error("Password Salah!")

# ==========================================
# HALAMAN 2: DASHBOARD (PROTECTED)
# ==========================================
elif menu == "📊 Dashboard Monitoring":
    st.title("📊 Monitoring Operasional")
    
    try:
        response = supabase.table("shipments").select("*").execute()
        all_data = response.data

        if all_data:
            if st.session_state['user_role'] in ["Sales", "SPV"]:
                selected_branch = st.session_state['user_branch']
                st.info(f"📍 Menampilkan Data Cabang: **{selected_branch}**")
            else:
                unique_branches = sorted(list(set([d['branch'] for d in all_data if d.get('branch')])))
                unique_branches.insert(0, "Semua Cabang")
                selected_branch = st.selectbox("📍 Filter Cabang (Admin Mode):", unique_branches)
            
            if selected_branch != "Semua Cabang":
                filtered_data = [d for d in all_data if d.get('branch') == selected_branch]
            else:
                filtered_data = all_data

            processed_orders = []
            shipping_orders = []
            completed_orders = []

            for item in filtered_data:
                s = item['status'].lower()
                if "selesai" in s or "diterima" in s:
                    completed_orders.append(item)
                elif "dikirim" in s or "jalan" in s or "pengiriman" in s:
                    shipping_orders.append(item)
                else:
                    processed_orders.append(item)

            c1, c2, c3 = st.columns(3)
            c1.metric("📦 Diproses Gudang", f"{len(processed_orders)}")
            c2.metric("🚚 Sedang Jalan", f"{len(shipping_orders)}")
            c3.metric("✅ Selesai", f"{len(completed_orders)}")
            
            st.divider()
            
            with st.expander(f"📦 Sedang Diproses Gudang - {len(processed_orders)}", expanded=False):
                if processed_orders:
                    clean_wh = []
                    for x in processed_orders:
                        tgl_update = (x.get('last_updated') or x['created_at'])[:16].replace("T", " ")
                        clean_wh.append({
                            "ID": x['order_id'], "Customer": x['customer_name'], 
                            "Barang": x['product_name'], "Status": x['status'], "Update": tgl_update
                        })
                    st.dataframe(clean_wh, use_container_width=True)
                else:
                    st.success("Tidak ada barang antre.")

            with st.expander(f"🚚 Sedang Dalam Pengiriman - {len(shipping_orders)}", expanded=False):
                if shipping_orders:
                    clean_ship = []
                    for x in shipping_orders:
                        tgl_update = (x.get('last_updated') or x['created_at'])[:16].replace("T", " ")
                        clean_ship.append({
                            "ID": x['order_id'], "Customer": x['customer_name'], 
                            "Barang": x['product_name'], "Status": x['status'], "Kurir": x['courier'], "Update": tgl_update
                        })
                    st.dataframe(clean_ship, use_container_width=True)
                else:
                    st.info("Tidak ada barang jalan.")

            with st.expander(f"✅ Riwayat Selesai - {len(completed_orders)}", expanded=False):
                if completed_orders:
                    clean_done = []
                    for x in completed_orders:
                        tgl_update = (x.get('last_updated') or x['created_at'])[:16].replace("T", " ")
                        clean_done.append({
                            "ID": x['order_id'], "Customer": x['customer_name'], 
                            "Barang": x['product_name'], "Status": x['status'], "Waktu Selesai": tgl_update
                        })
                    st.dataframe(clean_done, use_container_width=True)
                else:
                    st.info("Belum ada history selesai.")
        else:
            st.info("Data kosong.")
    except Exception as e:
        st.error(f"Error: {e}")

# ==========================================
# HALAMAN 3: INPUT ORDER (SALES & SPV)
# ==========================================
elif menu == "📝 Input Delivery Order":
    st.title("📝 Input Delivery Order")
    
    cabang_aktif = st.session_state['user_branch']
    st.info(f"Input Data untuk Cabang: **{cabang_aktif}**")
    
    with st.form("sales_input_form", clear_on_submit=False):
        st.subheader("Data Pelanggan & Barang")
        
        c1, c2 = st.columns(2)
        in_id = c1.text_input("Order ID (Wajib)", placeholder="Contoh: 12187...", key="in_id")
        in_sales = c2.text_input("Nama Sales", placeholder="Nama Anda", key="in_sales")
        
        c3, c4 = st.columns(2)
        in_nama = c3.text_input("Nama Customer", placeholder="Nama Pelanggan", key="in_nama")
        in_hp = c4.text_input("No HP Customer", placeholder="0812...", key="in_hp")
        
        in_alamat = st.text_area("Alamat Pengiriman", placeholder="Alamat lengkap...", key="in_alamat")
        
        c5, c6 = st.columns(2)
        in_barang = c5.text_input("Nama Barang", placeholder="Kulkas, TV, dll", key="in_barang")
        in_tipe = c6.selectbox("Tipe Pengiriman", ["Reguler", "Tukar Tambah", "Express"], key="in_tipe")
        
        submitted = st.form_submit_button("Kirim ke Gudang", type="primary")
        
        if submitted:
            if in_id and in_nama and in_barang and in_sales:
                try:
                    payload = {
                        "order_id": in_id,
                        "customer_name": in_nama,
                        "customer_phone": in_hp,
                        "delivery_address": in_alamat,
                        "product_name": in_barang,
                        "delivery_type": in_tipe,
                        "sales_name": in_sales,
                        "branch": cabang_aktif, 
                        "status": "Menunggu Konfirmasi",
                        "last_updated": datetime.now().isoformat()
                    }
                    supabase.table("shipments").insert(payload).execute()
                    
                    st.toast(f"Sukses! Order {in_id} berhasil dikirim.", icon="✅")
                    clear_input_form()
                    time.sleep(1)
                    st.rerun()
                except Exception as e:
                    error_msg = str(e)
                    if "duplicate key" in error_msg or "23505" in error_msg:
                        st.error(f"⚠️ Gagal! Order ID **{in_id}** sudah terdaftar di sistem. Mohon cek kembali nomornya.")
                    else:
                        st.error(f"Terjadi kesalahan sistem: {e}")
            else:
                st.toast("Gagal! Mohon lengkapi data wajib.", icon="❌")

# ==========================================
# HALAMAN 4: CEK RESI (PUBLIC)
# ==========================================
elif menu == "🔍 Cek Resi (Public)":
    st.title("🔍 Cek Status Pengiriman")
    query = st.text_input("Masukkan Order ID / Nama Customer:")

    if st.button("Lacak") or query:
        if query:
            try:
                if query.isdigit() and len(query) > 5:
                    res = supabase.table("shipments").select("*").eq("order_id", query.strip()).execute()
                else:
                    res = supabase.table("shipments").select("*").ilike("customer_name", f"%{query}%").execute()
                
                if res.data:
                    for d in res.data:
                        color = get_status_color(d['status'])
                        if color == "success": st.success(f"Status: {d['status'].upper()}", icon="✅")
                        elif color == "info": st.info(f"Status: {d['status'].upper()}", icon="🚚")
                        else: st.warning(f"Status: {d['status'].upper()}", icon="⏳")
                        
                        tgl_update = d.get('last_updated') or d['created_at']
                        try:
                            dt_obj = datetime.fromisoformat(tgl_update.replace('Z', '+00:00'))
                            tgl_str = dt_obj.strftime("%d %b %Y, %H:%M WIB")
                        except:
                            tgl_str = tgl_update[:16].replace("T", " ")

                        st.markdown(f"""
                        ### {d['product_name']}
                        **Rincian Pengiriman:**
                        * 🏢 Cabang: **{d.get('branch', '-')}**
                        * 👤 Customer: **{d['customer_name']}**
                        * 🔢 Order ID: `{d['order_id']}`
                        * 🚚 Kurir: {d['courier'] or '-'}
                        * 🔖 Resi: {d['resi'] or '-'}
                        * 🕒 **Update Terakhir:** {tgl_str}
                        """)
                        
                        st.caption("Salin pesan update:")
                        msg = f"Halo Kak {d['customer_name']}, pesanan {d['product_name']} statusnya: *{d['status']}*.\nUpdate: {tgl_str}.\nTerima kasih!"
                        st.code(msg, language=None)
                        st.divider()
                else:
                    st.warning("Data tidak ditemukan.")
            except Exception as e:
                st.error(f"Error: {e}")

# ==========================================
# HALAMAN 5: UPDATE STATUS (SPV & ADMIN)
# ==========================================
elif menu == "⚙️ Update Status (Admin)" or menu == "⚙️ Update Status (SPV)":
    st.title("⚙️ Validasi & Update Order")
    
    query_db = supabase.table("shipments").select("*").order("created_at", desc=True).limit(50)
    
    if st.session_state['user_role'] == "SPV":
        query_db = query_db.eq("branch", st.session_state['user_branch'])
        st.info(f"Mode SPV: Hanya menampilkan data cabang **{st.session_state['user_branch']}**")
    
    recent = query_db.execute()
    
    if recent.data:
        opts = {f"[{d['status']}] {d['order_id']} - {d['customer_name']}": d for d in recent.data}
        
        sel = st.selectbox(
            "Pilih Order:", 
            list(opts.keys()), 
            index=None, 
            placeholder="Pilih order untuk diproses...",
            key="update_order_selector" 
        )
        
        if sel:
            curr = opts[sel]
            st.info(f"Edit: **{curr['product_name']}** | Sales: {curr.get('sales_name')}")
            
            with st.expander("🌍 Buka Tracking PT. BES (Cek Resi)"):
                st.caption("Salin nomor resi yang sudah Anda input, lalu tempel di website di bawah ini.")
                st.link_button("Buka Website PT. BES di Tab Baru ↗️", "https://www.bes-paket.com/track-package")
                components.iframe("https://www.bes-paket.com/track-package", height=600, scrolling=True)

            with st.form("admin_update"):
                c1, c2 = st.columns(2)
                stat_list = ["Menunggu Konfirmasi", "Diproses Gudang", "Menunggu Kurir", "Dalam Pengiriman", "Selesai/Diterima"]
                
                try: idx = stat_list.index(curr['status'])
                except: idx = 0
                
                new_stat = c1.selectbox("Update Status", stat_list, index=idx)
                new_kurir = c2.text_input("Kurir / Supir", value=curr['courier'] or "")
                new_resi = st.text_input("Nomor Resi / Plat Nomor", value=curr['resi'] or "")
                
                st.divider()
                st.write("**Waktu Status Terakhir (Sesuai Fakta di Lapangan/Web BES):**")
                col_tgl, col_jam = st.columns(2)
                update_date = col_tgl.date_input("Tanggal Kejadian", value="today")
                update_time = col_jam.time_input("Jam Kejadian", value="now")
                
                final_datetime = datetime.combine(update_date, update_time).isoformat()

                st.divider()
                st.caption("Koreksi Data (Jika Diperlukan)")
                corr_nama = st.text_input("Nama Customer", value=curr['customer_name'])
                corr_barang = st.text_input("Nama Barang", value=curr['product_name'])
                
                if st.form_submit_button("Simpan Perubahan"):
                    upd = {
                        "status": new_stat, 
                        "courier": new_kurir, 
                        "resi": new_resi,
                        "customer_name": corr_nama, 
                        "product_name": corr_barang,
                        "last_updated": final_datetime
                    }
                    supabase.table("shipments").update(upd).eq("order_id", curr['order_id']).execute()
                    
                    st.toast("Data Terupdate!", icon="✅")
                    st.session_state["update_order_selector"] = None
                    time.sleep(1)
                    st.rerun()

# ==========================================
# HALAMAN 6: HAPUS DATA (KHUSUS ADMIN)
# ==========================================
elif menu == "🗑️ Hapus Data (Admin)":
    st.title("🗑️ Hapus Data")
    st.error("Area Berbahaya. Data hilang permanen.")
    
    del_id = st.text_input("Masukkan Order ID yang mau dihapus:")
    if st.button("Hapus Permanen", type="primary"):
        if del_id:
            supabase.table("shipments").delete().eq("order_id", del_id).execute()
            st.toast("Data berhasil dihapus.", icon="🗑️")
            time.sleep(1)
            st.rerun()
