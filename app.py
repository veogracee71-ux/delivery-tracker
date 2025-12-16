# Versi 1.2
# Update: Menambahkan proteksi password "admin123" pada menu Admin
# Fitur: Sales Tracker & Admin Input (Secured)

import streamlit as st
from supabase import create_client, Client

# --- KONFIGURASI DARI SECRETS ---
try:
    # Mengambil URL dan KEY dari Secrets Streamlit
    # Pastikan di Dashboard Streamlit Cloud > Settings > Secrets sudah diisi dengan benar
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
except FileNotFoundError:
    st.error("File secrets.toml tidak ditemukan. Jika di Streamlit Cloud, atur di 'App Settings > Secrets'.")
    st.stop()
except KeyError:
    st.error("Secrets 'SUPABASE_URL' atau 'SUPABASE_KEY' belum diatur dengan benar.")
    st.stop()

# Inisialisasi Client Supabase
if not url or "https" not in url:
    st.error("Format SUPABASE_URL salah. Harus dimulai dengan 'https://'")
    st.stop()

supabase: Client = create_client(url, key)

# --- MENU NAVIGASI ---
st.set_page_config(page_title="Blibli Tracker", page_icon="📦")
menu = st.sidebar.radio("Menu Aplikasi", ["🔍 Cek Resi (Sales)", "📝 Input Data (Admin)"])

# ==========================================
# HALAMAN 1: SALES (Pencarian)
# ==========================================
if menu == "🔍 Cek Resi (Sales)":
    st.title("📦 Cek Status Pengiriman")
    st.markdown("Masukkan **Order ID** yang tertera di formulir delivery.")

    # Input Pencarian
    query_id = st.text_input("Ketik Order ID:", placeholder="Contoh: 12187564832")

    if st.button("Lacak Paket"):
        if query_id:
            try:
                # Cari data di database
                response = supabase.table("shipments").select("*").eq("order_id", query_id.strip()).execute()
                
                if response.data:
                    data = response.data[0]
                    
                    # Tampilan Kartu Hasil
                    st.success(f"Status: {data['status'].upper()}")
                    
                    with st.container():
                        st.markdown(f"""
                        **Informasi Order:**
                        * **Nama Customer:** {data['customer_name']}
                        * **Barang:** {data['product_name']}
                        
                        **Detail Pengiriman:**
                        * **Ekspedisi/Kurir:** {data['courier'] if data['courier'] else '-'}
                        * **No Resi / Plat No:** {data['resi'] if data['resi'] else '-'}
                        * **Terakhir Update:** {data['created_at'][:10]}
                        """)
                else:
                    st.warning("❌ Order ID tidak ditemukan. Pastikan Admin sudah menginput data.")
            except Exception as e:
                st.error(f"Error koneksi: {e}")

# ==========================================
# HALAMAN 2: ADMIN (Input & Update)
# ==========================================
elif menu == "📝 Input Data (Admin)":
    st.title("🔐 Akses Admin")
    
    # --- FITUR KEAMANAN: PASSWORD ---
    password = st.text_input("Masukkan Password Admin:", type="password")
    
    if password == "admin123":
        st.success("Login Berhasil! Silakan kelola data di bawah.")
        st.divider()
        
        # --- KONTEN ADMIN (Hanya muncul jika password benar) ---
        tab1, tab2 = st.tabs(["Input Order Baru", "Update Status Pengiriman"])
        
        # --- TAB 1: Input Baru (Dari Foto WA) ---
        with tab1:
            st.caption("Masukan data sesuai Foto Formulir Sales")
            with st.form("form_input"):
                c1, c2 = st.columns(2)
                input_id = c1.text_input("Order ID (Wajib)", placeholder="12187...")
                input_nama = c2.text_input("Nama Customer", placeholder="Iis Lita")
                input_barang = st.text_input("Nama Barang (Singkat)", placeholder="Contoh: Kulkas 2 Pintu")
                
                btn_simpan = st.form_submit_button("Simpan Order Baru")
                
                if btn_simpan:
                    if input_id and input_nama and input_barang:
                        try:
                            data = {
                                "order_id": input_id,
                                "customer_name": input_nama,
                                "product_name": input_barang,
                                "status": "Diproses Gudang"
                            }
                            supabase.table("shipments").insert(data).execute()
                            st.toast("✅ Data berhasil disimpan!", icon="🎉")
                        except Exception as e:
                            st.error(f"Gagal simpan (ID mungkin duplikat): {e}")
                    else:
                        st.warning("Mohon lengkapi ID, Nama, dan Barang.")

        # --- TAB 2: Update Status (Saat Barang Jalan) ---
        with tab2:
            st.write("Cari order yang mau diupdate statusnya:")
            search_update = st.text_input("Cari Order ID:", key="search_admin")
            
            if search_update:
                res = supabase.table("shipments").select("*").eq("order_id", search_update).execute()
                if res.data:
                    curr_data = res.data[0]
                    st.info(f"Mengedit: {curr_data['customer_name']} - {curr_data['product_name']}")
                    
                    with st.form("form_update"):
                        new_status = st.selectbox("Update Status", 
                                                ["Diproses Gudang", "Menunggu Kurir", "Dalam Pengiriman", "Selesai/Diterima"],
                                                index=0)
                        new_courier = st.text_input("Nama Kurir / Supir", value=curr_data['courier'] if curr_data['courier'] else "")
                        new_resi = st.text_input("No Resi / Info Lain", value=curr_data['resi'] if curr_data['resi'] else "")
                        
                        if st.form_submit_button("Update Data Pengiriman"):
                            update_payload = {
                                "status": new_status,
                                "courier": new_courier,
                                "resi": new_resi
                            }
                            supabase.table("shipments").update(update_payload).eq("order_id", search_update).execute()
                            st.success("✅ Status berhasil diperbarui!")
                else:
                    st.caption("Data tidak ditemukan.")

        # Tabel Data (Monitoring)
        st.divider()
        st.caption("10 Data Terakhir Masuk")
        data_log = supabase.table("shipments").select("order_id, customer_name, status").order("created_at", desc=True).limit(10).execute()
        if data_log.data:
            st.dataframe(data_log.data)
            
    elif password:
        st.error("Password salah! Akses ditolak.")
    else:
        st.info("Halaman ini terkunci. Masukkan password untuk melanjutkan.")
