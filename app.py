# Versi 2.7
# Update:
# 1. Menu Update Status otomatis menutup form (Reset Pilihan) setelah simpan.
# 2. Memastikan Form Input Order sales benar-benar bersih setelah kirim.

import streamlit as st
import streamlit.components.v1 as components 
from supabase import create_client, Client
from urllib.parse import quote
import time

# --- KONFIGURASI PASSWORD (SALES, SPV, ADMIN) ---
SALES_CREDENTIALS = {
    "Kopo Bandung": "kopo123",
    "Banjaran Bandung": "banjaran123",
    "Moh. Toha Bandung": "toha123",
    "Ujung Berung Bandung": "uber123",
    "Margacinta Bandung": "marga123",
    "Kalimalang Bekasi": "bekasi123"
}

SPV_CREDENTIALS = {
    "Kopo Bandung": "spvkopo",
    "Banjaran Bandung": "spvbanjaran",
    "Moh. Toha Bandung": "spvtoha",
    "Ujung Berung Bandung": "spvuber",
    "Margacinta Bandung": "spvmarga",
    "Kalimalang Bekasi": "spvbekasi"
}

ADMIN_PASSWORD = "admin123" 

# --- KONFIGURASI DARI SECRETS ---
try:
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
except FileNotFoundError:
    st.error("File secrets.toml tidak ditemukan.")
    st.stop()
except KeyError:
    st.error("Secrets belum diatur dengan benar.")
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
    """Membersihkan session state formulir input sales"""
    # Kita set semua key input menjadi string kosong
    for key in ["in_id", "in_sales", "in_nama", "in_hp", "in_alamat", "in_barang"]:
        if key in st.session_state:
            st.session_state[key] = ""

# --- SETUP HALAMAN ---
st.set_page_config(page_title="Delivery Tracker", page_icon="📦", layout="wide") 

# --- CUSTOM CSS: TOMBOL BIRU BLIBLI ---
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

menu_options = ["📊 Dashboard Monitoring", "🔍 Cek Resi (Public)"]

if st.session_state['user_role'] == "Sales":
    menu_options.insert(0, "📝 Input Delivery Order")

elif st.session_state['user_role'] == "SPV":
    menu_options.insert(0, "📝 Input Delivery Order")
    menu_options.append("⚙️ Update Status (SPV)")

elif st.session_state['user_role'] == "Admin":
    menu_options.append("⚙️ Update Status (Admin)")
    menu_options.append("🗑️ Hapus Data (Admin)")

menu = st.sidebar.radio("Menu Aplikasi", menu_options)

# --- LOGIN AREA ---
with st.sidebar:
    st.divider()
    if st.session_state['user_role'] == "Guest":
        with st.expander("🔐 Login Sistem"):
            login_type = st.selectbox("Tipe Login:", ["Sales Cabang", "SPV Cabang", "Admin Pusat"])
            
            if login_type == "Sales Cabang":
                cabang_list = list(SALES_CREDENTIALS.keys())
                selected_cabang = st.selectbox("Pilih Cabang:", cabang_list)
                pw = st.text_input("Password Sales:", type="password")
                if st.button("Masuk Sales"):
                    if pw == SALES_CREDENTIALS.get(selected_cabang):
                        st.session_state['user_role'] = "Sales"
                        st.session_state['user_branch'] = selected_cabang
                        st.toast(f"Selamat Datang Sales {selected_cabang}!", icon="👋")
                        time.sleep(1)
                        st.rerun()
                    else:
                        st.error("Password Salah!")

            elif login_type == "SPV Cabang":
                cabang_list = list(SPV_CREDENTIALS.keys())
                selected_cabang = st.selectbox("Pilih Cabang:", cabang_list, key="spv_select")
                pw = st.text_input("Password SPV:", type="password")
                if st.button("Masuk SPV"):
                    if pw == SPV_CREDENTIALS.get(selected_cabang):
                        st.session_state['user_role'] = "SPV"
                        st.session_state['user_branch'] = selected_cabang
                        st.toast(f"Selamat Datang SPV {selected_cabang}!", icon="👔")
                        time.sleep(1)
                        st.rerun()
                    else:
                        st.error("Password Salah!")

            else: # Admin Pusat
                pw_admin = st.text_input("Password Admin:", type="password")
                if st.button("Masuk Admin"):
                    if pw_admin == ADMIN_PASSWORD:
                        st.session_state['user_role'] = "Admin"
                        st.session_state['user_branch'] = "Pusat"
                        st.toast("Login Admin Berhasil!", icon="🔐")
                        time.sleep(1)
                        st.rerun()
                    else:
                        st.error("Password Salah!")
    else:
        st.info(f"Login: {st.session_state['user_role']} ({st.session_state['user_branch']})")
        if st.button("Logout"):
            st.session_state['user_role'] = "Guest"
            st.session_state['user_branch'] = ""
            st.rerun()

# ==========================================
# HALAMAN 1: DASHBOARD
# ==========================================
if menu == "📊 Dashboard Monitoring":
    st.title("📊 Monitoring Operasional")
    
    default_index = 0
    try:
        response = supabase.table("shipments").select("*").execute()
        all_data = response.data

        if all_data:
            unique_branches = sorted(list(set([d['branch'] for d in all_data if d.get('branch')])))
            unique_branches.insert(0, "Semua Cabang")
            
            # Auto-filter jika Sales/SPV login
            if st.session_state['user_role'] in ["Sales", "SPV"] and st.session_state['user_branch'] in unique_branches:
                default_index = unique_branches.index(st.session_state['user_branch'])

            selected_branch = st.selectbox("📍 Filter Cabang:", unique_branches, index=default_index)
            
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
            
            # Tabel Default Tertutup (expanded=False)
            with st.expander(f"📦 Sedang Diproses Gudang - {len(processed_orders)}", expanded=False):
                if processed_orders:
                    st.dataframe(processed_orders, use_container_width=True, column_config={
                        "created_at": "Tanggal", "order_id": "ID", "customer_name": "Customer", 
                        "product_name": "Barang", "sales_name": "Sales", "status": "Status"
                    })
                else:
                    st.success("Tidak ada barang antre.")

            with st.expander(f"🚚 Sedang Dalam Pengiriman - {len(shipping_orders)}", expanded=False):
                if shipping_orders:
                    st.dataframe(shipping_orders, use_container_width=True, column_config={
                        "created_at": "Tanggal", "order_id": "ID", "customer_name": "Customer", 
                        "product_name": "Barang", "courier": "Kurir", "status": "Status"
                    })
                else:
                    st.info("Tidak ada barang jalan.")

            with st.expander(f"✅ Riwayat Selesai - {len(completed_orders)}", expanded=False):
                if completed_orders:
                    st.dataframe(completed_orders, use_container_width=True, column_config={
                        "created_at": "Tanggal", "order_id": "ID", "customer_name": "Customer", 
                        "product_name": "Barang", "sales_name": "Sales"
                    })
                else:
                    st.info("Belum ada history selesai.")
        else:
            st.info("Data kosong.")
    except Exception as e:
        st.error(f"Error: {e}")

# ==========================================
# HALAMAN 2: INPUT ORDER (SALES & SPV)
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
        in_tipe = c6.selectbox("Tipe Pengiriman", ["Reguler", "Tukar Tambah", "Express"])
        
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
                        "status": "Menunggu Konfirmasi" 
                    }
                    supabase.table("shipments").insert(payload).execute()
                    
                    st.toast(f"Sukses! Order {in_id} berhasil dikirim.", icon="✅")
                    clear_input_form() # Bersihkan Form
                    time.sleep(1)
                    st.rerun()
                except Exception as e:
                    st.error(f"Gagal kirim data (ID mungkin kembar): {e}")
            else:
                st.toast("Gagal! Mohon lengkapi data wajib.", icon="❌")

# ==========================================
# HALAMAN 3: CEK RESI (PUBLIC)
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
                        # 1. Banner Status
                        color = get_status_color(d['status'])
                        if color == "success": st.success(f"Status: {d['status'].upper()}", icon="✅")
                        elif color == "info": st.info(f"Status: {d['status'].upper()}", icon="🚚")
                        else: st.warning(f"Status: {d['status'].upper()}", icon="⏳")
                        
                        # 2. Detail Data (Text Only)
                        st.markdown(f"""
                        ### {d['product_name']}
                        **Rincian Pengiriman:**
                        * 🏢 Cabang: **{d.get('branch', '-')}**
                        * 👤 Customer: **{d['customer_name']}**
                        * 🔢 Order ID: `{d['order_id']}`
                        * 🚚 Kurir: {d['courier'] or '-'}
                        * 🔖 Resi: {d['resi'] or '-'}
                        * 📅 Tgl: {d['created_at'][:10]}
                        """)
                        
                        # 3. Template Pesan (Full Width)
                        st.caption("Salin pesan update:")
                        msg = f"Halo Kak {d['customer_name']}, pesanan {d['product_name']} statusnya: *{d['status']}*.\nKurir: {d['courier'] or '-'}.\nTerima kasih!"
                        st.code(msg, language=None)
                        st.divider()
                else:
                    st.warning("Data tidak ditemukan.")
            except Exception as e:
                st.error(f"Error: {e}")

# ==========================================
# HALAMAN 4: UPDATE STATUS (SPV & ADMIN)
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
        
        # KEY DITAMBAHKAN DISINI agar bisa di-reset
        sel = st.selectbox(
            "Pilih Order:", 
            list(opts.keys()), 
            index=None, 
            placeholder="Pilih order untuk diproses...",
            key="update_order_selector" # Kunci unik
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
                st.caption("Koreksi Data (Jika Diperlukan)")
                corr_nama = st.text_input("Nama Customer", value=curr['customer_name'])
                corr_barang = st.text_input("Nama Barang", value=curr['product_name'])
                
                if st.form_submit_button("Simpan Perubahan"):
                    upd = {
                        "status": new_stat, "courier": new_kurir, "resi": new_resi,
                        "customer_name": corr_nama, "product_name": corr_barang
                    }
                    supabase.table("shipments").update(upd).eq("order_id", curr['order_id']).execute()
                    
                    st.toast("Data Terupdate!", icon="✅")
                    
                    # RESET PILIHAN AGAR FORM MENUTUP
                    st.session_state["update_order_selector"] = None
                    
                    time.sleep(1)
                    st.rerun()

# ==========================================
# HALAMAN 5: HAPUS DATA (KHUSUS ADMIN)
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
