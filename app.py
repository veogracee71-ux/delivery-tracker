# Versi 2.3
# Update: Mengubah default dropdown Dashboard (Gudang & Jalan) menjadi tertutup agar tampilan lebih rapi.

import streamlit as st
from supabase import create_client, Client
from urllib.parse import quote
import time

# --- KONFIGURASI CABANG & PASSWORD ---
BRANCH_CREDENTIALS = {
    "Kopo Bandung": "kopo123",
    "Banjaran Bandung": "banjaran123",
    "Moh. Toha Bandung": "toha123",
    "Ujung Berung Bandung": "uber123",
    "Margacinta Bandung": "marga123",
    "Kalimalang Bekasi": "bekasi123",
    "Pusat": "admin123" # Password Admin
}

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

# --- SETUP HALAMAN ---
st.set_page_config(page_title="Delivery Tracker", page_icon="📦", layout="wide") 

# --- SIDEBAR LOGIC ---
if 'user_role' not in st.session_state:
    st.session_state['user_role'] = "Guest"
if 'user_branch' not in st.session_state:
    st.session_state['user_branch'] = ""

menu_options = ["📊 Dashboard Monitoring", "🔍 Cek Resi (Public)"]

if st.session_state['user_role'] == "Sales":
    menu_options.insert(0, "📝 Input Delivery Order")
elif st.session_state['user_role'] == "Admin":
    menu_options.append("⚙️ Update Status (Admin)")
    menu_options.append("🗑️ Hapus Data (Admin)")

menu = st.sidebar.radio("Menu Aplikasi", menu_options)

# --- LOGIN AREA ---
with st.sidebar:
    st.divider()
    if st.session_state['user_role'] == "Guest":
        with st.expander("🔐 Login Staff / Sales"):
            login_type = st.selectbox("Login Sebagai:", ["Sales Cabang", "Admin Pusat"])
            
            if login_type == "Sales Cabang":
                cabang_list = [k for k in BRANCH_CREDENTIALS.keys() if k != "Pusat"]
                selected_cabang = st.selectbox("Pilih Cabang:", cabang_list)
                pw = st.text_input("Password Cabang:", type="password")
                
                if st.button("Masuk"):
                    if pw == BRANCH_CREDENTIALS.get(selected_cabang):
                        st.session_state['user_role'] = "Sales"
                        st.session_state['user_branch'] = selected_cabang
                        st.success(f"Login Berhasil: {selected_cabang}")
                        time.sleep(1)
                        st.rerun()
                    else:
                        st.error("Password Salah!")
            else:
                pw_admin = st.text_input("Password Admin:", type="password")
                if st.button("Masuk Admin"):
                    if pw_admin == BRANCH_CREDENTIALS["Pusat"]:
                        st.session_state['user_role'] = "Admin"
                        st.session_state['user_branch'] = "Pusat"
                        st.success("Login Admin Berhasil")
                        time.sleep(1)
                        st.rerun()
                    else:
                        st.error("Password Salah!")
    else:
        st.info(f"Halo, {st.session_state['user_role']} ({st.session_state['user_branch']})")
        if st.button("Logout"):
            st.session_state['user_role'] = "Guest"
            st.session_state['user_branch'] = ""
            st.rerun()

# ==========================================
# HALAMAN 1: DASHBOARD (Monitoring Global)
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
            
            if st.session_state['user_role'] == "Sales" and st.session_state['user_branch'] in unique_branches:
                default_index = unique_branches.index(st.session_state['user_branch'])

            selected_branch = st.selectbox("📍 Filter Cabang:", unique_branches, index=default_index)
            
            if selected_branch != "Semua Cabang":
                filtered_data = [d for d in all_data if d.get('branch') == selected_branch]
            else:
                filtered_data = all_data

            # --- LOGIKA PEMISAHAN DATA BARU ---
            processed_orders = []  # Gudang (Proses)
            shipping_orders = []   # Jalan (Dikirim)
            completed_orders = []  # Selesai

            for item in filtered_data:
                s = item['status'].lower()
                if "selesai" in s or "diterima" in s:
                    completed_orders.append(item)
                elif "dikirim" in s or "jalan" in s or "pengiriman" in s:
                    shipping_orders.append(item)
                else:
                    # Sisanya masuk ke Proses Gudang (Menunggu Konfirmasi, Packing, dll)
                    processed_orders.append(item)

            # Statistik (Angka Besar)
            c1, c2, c3 = st.columns(3)
            c1.metric("📦 Diproses Gudang", f"{len(processed_orders)}")
            c2.metric("🚚 Sedang Jalan", f"{len(shipping_orders)}")
            c3.metric("✅ Selesai", f"{len(completed_orders)}")
            
            st.divider()
            
            # 1. TABEL DIPROSES GUDANG (Default: Tertutup/False)
            with st.expander(f"📦 Sedang Diproses Gudang - {len(processed_orders)}", expanded=False):
                if processed_orders:
                    data_wh = []
                    for x in processed_orders:
                        data_wh.append({
                            "ID": x['order_id'],
                            "Sales": x.get('sales_name', '-'),
                            "Customer": x['customer_name'],
                            "Barang": x['product_name'],
                            "Status": x['status'],
                            "Tgl": x['created_at'][:10]
                        })
                    st.dataframe(data_wh, use_container_width=True)
                else:
                    st.success("Tidak ada barang antre di gudang.")

            # 2. TABEL SEDANG JALAN (Default: Tertutup/False)
            with st.expander(f"🚚 Sedang Dalam Pengiriman - {len(shipping_orders)}", expanded=False):
                if shipping_orders:
                    data_ship = []
                    for x in shipping_orders:
                        data_ship.append({
                            "ID": x['order_id'],
                            "Sales": x.get('sales_name', '-'),
                            "Customer": x['customer_name'],
                            "Barang": x['product_name'],
                            "Status": x['status'],
                            "Kurir": x['courier'] or '-',
                            "Tgl": x['created_at'][:10]
                        })
                    st.dataframe(data_ship, use_container_width=True)
                else:
                    st.info("Tidak ada barang yang sedang di jalan.")

            # 3. TABEL SELESAI (Default: Tertutup/False)
            with st.expander(f"✅ Riwayat Selesai - {len(completed_orders)}", expanded=False):
                if completed_orders:
                    data_done = []
                    for x in completed_orders:
                        data_done.append({
                            "ID": x['order_id'],
                            "Sales": x.get('sales_name', '-'),
                            "Customer": x['customer_name'],
                            "Barang": x['product_name'],
                            "Tgl": x['created_at'][:10]
                        })
                    st.dataframe(data_done, use_container_width=True)
                else:
                    st.info("Belum ada history selesai.")

        else:
            st.info("Data kosong.")
    except Exception as e:
        st.error(f"Error: {e}")

# ==========================================
# HALAMAN 2: INPUT ORDER (KHUSUS SALES)
# ==========================================
elif menu == "📝 Input Delivery Order":
    st.title("📝 Input Delivery Order")
    
    cabang_aktif = st.session_state['user_branch']
    st.info(f"Login sebagai: **{cabang_aktif}**")
    
    with st.form("sales_input_form"):
        st.subheader("Data Pelanggan & Barang")
        
        c1, c2 = st.columns(2)
        in_id = c1.text_input("Order ID (Wajib)", placeholder="Contoh: 12187...")
        in_sales = c2.text_input("Nama Sales", placeholder="Nama Anda")
        
        c3, c4 = st.columns(2)
        in_nama = c3.text_input("Nama Customer", placeholder="Nama Pelanggan")
        in_hp = c4.text_input("No HP Customer", placeholder="0812...")
        
        in_alamat = st.text_area("Alamat Pengiriman", placeholder="Alamat lengkap...")
        
        c5, c6 = st.columns(2)
        in_barang = c5.text_input("Nama Barang", placeholder="Kulkas, TV, dll")
        in_tipe = c6.selectbox("Tipe Pengiriman", ["Reguler", "Tukar Tambah", "Express"])
        
        submitted = st.form_submit_button("Kirim ke Gudang 🚀", type="primary")
        
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
                    st.success(f"Order {in_id} Berhasil Dikirim ke Gudang!")
                    time.sleep(2)
                    st.rerun()
                except Exception as e:
                    st.error(f"Gagal kirim data (ID mungkin kembar): {e}")
            else:
                st.warning("Mohon lengkapi: Order ID, Nama Customer, Nama Barang, dan Nama Sales.")

# ==========================================
# HALAMAN 3: CEK RESI (PUBLIC/SALES)
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
                        
                        st.markdown(f"""
                        **{d['product_name']}** ({d.get('delivery_type', 'Reguler')})
                        
                        * 👤 **Customer:** {d['customer_name']} ({d.get('customer_phone', '-')})
                        * 🏠 **Alamat:** {d.get('delivery_address', '-')}
                        * 👨‍💼 **Sales:** {d.get('sales_name', '-')} ({d.get('branch', '-')})
                        * 🚚 **Info Kurir:** {d['courier'] or '-'} | Resi: {d['resi'] or '-'}
                        """)
                        
                        st.caption("Salin pesan update:")
                        msg = f"Halo Kak {d['customer_name']}, pesanan {d['product_name']} statusnya: *{d['status']}*.\nKurir: {d['courier'] or '-'}.\nTerima kasih!"
                        st.code(msg, language=None)
                        st.divider()
                else:
                    st.warning("Data tidak ditemukan.")
            except Exception as e:
                st.error(f"Error: {e}")

# ==========================================
# HALAMAN 4: UPDATE STATUS (KHUSUS ADMIN)
# ==========================================
elif menu == "⚙️ Update Status (Admin)":
    st.title("⚙️ Validasi & Update Order")
    
    recent = supabase.table("shipments").select("*").order("created_at", desc=True).limit(50).execute()
    
    if recent.data:
        opts = {f"[{d['status']}] {d['order_id']} - {d['customer_name']}": d for d in recent.data}
        sel = st.selectbox("Pilih Order:", list(opts.keys()), index=None, placeholder="Pilih order untuk diproses...")
        
        if sel:
            curr = opts[sel]
            st.info(f"Edit Order: **{curr['product_name']}** | Cabang: {curr.get('branch')} | Sales: {curr.get('sales_name')}")
            
            with st.form("admin_update"):
                c1, c2 = st.columns(2)
                stat_list = ["Menunggu Konfirmasi", "Diproses Gudang", "Menunggu Kurir", "Dalam Pengiriman", "Selesai/Diterima"]
                
                try: idx = stat_list.index(curr['status'])
                except: idx = 0
                
                new_stat = c1.selectbox("Update Status", stat_list, index=idx)
                new_kurir = c2.text_input("Kurir / Supir", value=curr['courier'] or "")
                new_resi = st.text_input("Nomor Resi / Plat Nomor", value=curr['resi'] or "")
                
                if st.form_submit_button("Simpan Update"):
                    upd = {"status": new_stat, "courier": new_kurir, "resi": new_resi}
                    supabase.table("shipments").update(upd).eq("order_id", curr['order_id']).execute()
                    st.success("✅ Terupdate!")
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
            st.success("Terhapus.")
