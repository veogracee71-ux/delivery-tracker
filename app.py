# Versi 1.3
# Update:
# 1. Fitur Search by Name (Pencarian nama customer)
# 2. Fitur Hapus Data (Tab baru di Admin)
# 3. Visualisasi Warna Status (Kuning/Biru/Hijau)
# 4. Tombol Share to WA

import streamlit as st
from supabase import create_client, Client
from urllib.parse import quote # Untuk encode pesan WA

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
    """Menentukan warna notifikasi berdasarkan status"""
    s = status.lower()
    if "selesai" in s or "diterima" in s:
        return "success" # Hijau
    elif "dikirim" in s or "jalan" in s or "pengiriman" in s:
        return "info"    # Biru
    else:
        return "warning" # Kuning (Default/Proses)

# --- MENU NAVIGASI ---
st.set_page_config(page_title="Blibli Tracker", page_icon="📦")
menu = st.sidebar.radio("Menu Aplikasi", ["🔍 Cek Resi (Sales)", "📝 Input Data (Admin)"])

# ==========================================
# HALAMAN 1: SALES (Pencarian Cerdas)
# ==========================================
if menu == "🔍 Cek Resi (Sales)":
    st.title("📦 Cek Status Pengiriman")
    st.markdown("Cari berdasarkan **Order ID** atau **Nama Customer**.")

    # Input Pencarian
    query = st.text_input("Ketik disini:", placeholder="Contoh: 12187... atau 'Iis Lita'")

    if st.button("Lacak Paket") or query:
        if query:
            try:
                # LOGIKA PENCARIAN CERDAS
                # Jika input angka semua & panjang, asumsi Order ID
                if query.isdigit() and len(query) > 5:
                    response = supabase.table("shipments").select("*").eq("order_id", query.strip()).execute()
                else:
                    # Jika ada huruf, cari Nama Customer (ilike = case insensitive search)
                    # %query% artinya mencari teks yang mengandung kata tersebut
                    response = supabase.table("shipments").select("*").ilike("customer_name", f"%{query}%").execute()
                
                if response.data:
                    # Loop hasil (karena cari nama bisa muncul lebih dari 1 orang)
                    for data in response.data:
                        color_type = get_status_color(data['status'])
                        
                        # Tampilan Kartu Visual
                        if color_type == "success":
                            container = st.success
                        elif color_type == "info":
                            container = st.info
                        else:
                            container = st.warning
                            
                        with container(f"Status: {data['status'].upper()}"):
                            c1, c2 = st.columns([3, 1])
                            with c1:
                                st.markdown(f"""
                                **{data['product_name']}**
                                * 👤 Customer: **{data['customer_name']}**
                                * 🔢 Order ID: `{data['order_id']}`
                                * 🚚 Kurir: {data['courier'] if data['courier'] else '-'}
                                * 🔖 Resi/Info: {data['resi'] if data['resi'] else '-'}
                                * 📅 Update: {data['created_at'][:10]}
                                """)
                            
                            # Tombol Share WA
                            with c2:
                                message = f"Halo Kak {data['customer_name']}, update untuk pesanan *{data['product_name']}*.\n\nStatus saat ini: *{data['status']}*.\nEkspedisi: {data['courier'] or '-'}.\n\nTerima kasih! - Blibli Elektronik"
                                wa_link = f"https://wa.me/?text={quote(message)}"
                                st.link_button("📲 Chat Customer", wa_link)
                            
                else:
                    st.warning("❌ Data tidak ditemukan. Coba cek ejaan nama atau nomor ID.")
            except Exception as e:
                st.error(f"Error koneksi: {e}")

# ==========================================
# HALAMAN 2: ADMIN (Input, Update, Hapus)
# ==========================================
elif menu == "📝 Input Data (Admin)":
    st.title("🔐 Akses Admin")
    password = st.text_input("Masukkan Password Admin:", type="password")
    
    if password == "admin123":
        st.success("Login Berhasil!")
        st.divider()
        
        # Tab Menu Admin
        tab1, tab2, tab3 = st.tabs(["Input Order", "Update Status", "Hapus Data"])
        
        # --- TAB 1: Input Baru ---
        with tab1:
            st.caption("Input data baru dari formulir sales")
            with st.form("form_input"):
                c1, c2 = st.columns(2)
                input_id = c1.text_input("Order ID (Wajib)", placeholder="12187...")
                input_nama = c2.text_input("Nama Customer", placeholder="Iis Lita")
                input_barang = st.text_input("Nama Barang", placeholder="Contoh: Kulkas 2 Pintu")
                
                if st.form_submit_button("Simpan Order Baru"):
                    if input_id and input_nama and input_barang:
                        try:
                            data = {
                                "order_id": input_id,
                                "customer_name": input_nama,
                                "product_name": input_barang,
                                "status": "Diproses Gudang"
                            }
                            supabase.table("shipments").insert(data).execute()
                            st.toast("✅ Data tersimpan!", icon="🎉")
                        except Exception as e:
                            st.error(f"Gagal simpan: {e}")
                    else:
                        st.warning("Lengkapi data dulu.")

        # --- TAB 2: Update Status ---
        with tab2:
            st.write("Update status pengiriman")
            search_update = st.text_input("Cari Order ID untuk Update:", key="search_admin_upd")
            
            if search_update:
                res = supabase.table("shipments").select("*").eq("order_id", search_update).execute()
                if res.data:
                    curr = res.data[0]
                    st.info(f"Mengedit: {curr['customer_name']} - {curr['product_name']}")
                    
                    with st.form("form_update"):
                        new_status = st.selectbox("Pilih Status", 
                                                ["Diproses Gudang", "Menunggu Kurir", "Dalam Pengiriman", "Selesai/Diterima"],
                                                index=0)
                        new_courier = st.text_input("Nama Kurir / Supir", value=curr['courier'] or "")
                        new_resi = st.text_input("No Resi / Info Lain", value=curr['resi'] or "")
                        
                        if st.form_submit_button("Update Data"):
                            upd_data = {"status": new_status, "courier": new_courier, "resi": new_resi}
                            supabase.table("shipments").update(upd_data).eq("order_id", search_update).execute()
                            st.success("✅ Status diperbarui!")
                else:
                    st.caption("Data tidak ditemukan.")

        # --- TAB 3: Hapus Data (FITUR BARU) ---
        with tab3:
            st.error("⚠️ Hati-hati! Data yang dihapus tidak bisa kembali.")
            del_id = st.text_input("Masukkan Order ID yang mau DIHAPUS:", key="del_search")
            
            if del_id:
                # Cek dulu datanya ada gak
                res_del = supabase.table("shipments").select("*").eq("order_id", del_id).execute()
                if res_del.data:
                    d = res_del.data[0]
                    st.warning(f"Apakah Anda yakin ingin menghapus data **{d['customer_name']}** ({d['product_name']})?")
                    
                    # Tombol konfirmasi hapus
                    if st.button("🗑️ YA, HAPUS PERMANEN", type="primary"):
                        supabase.table("shipments").delete().eq("order_id", del_id).execute()
                        st.success(f"Data Order ID {del_id} berhasil dihapus.")
                else:
                    st.caption("Data tidak ditemukan.")

        # Tabel Monitoring 10 Terakhir
        st.divider()
        st.caption("Monitoring 10 Data Terakhir")
        data_log = supabase.table("shipments").select("order_id, customer_name, status").order("created_at", desc=True).limit(10).execute()
        if data_log.data:
            st.dataframe(data_log.data)
            
    elif password:
        st.error("Password salah!")
