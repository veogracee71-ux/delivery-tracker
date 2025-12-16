# Versi 1.7
# Update: Mengganti tombol WA otomatis menjadi Template Pesan (Copy-Paste) agar lebih fleksibel

import streamlit as st
from supabase import create_client, Client
from urllib.parse import quote

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
st.set_page_config(page_title="Delivery Tracker", page_icon="📦", layout="wide") 
menu = st.sidebar.radio("Menu Aplikasi", ["📊 Dashboard Monitoring", "🔍 Cek Resi (Sales)", "📝 Input Data (Admin)"])

# ==========================================
# HALAMAN 1: DASHBOARD (Monitoring Global)
# ==========================================
if menu == "📊 Dashboard Monitoring":
    st.title("📊 Monitoring Operasional")
    st.markdown("Rekapitulasi status pengiriman barang secara real-time.")

    try:
        response = supabase.table("shipments").select("*").execute()
        all_data = response.data

        if all_data:
            total_gudang = 0
            total_jalan = 0
            total_selesai = 0
            active_orders = []

            for item in all_data:
                s = item['status'].lower()
                if "selesai" in s or "diterima" in s:
                    total_selesai += 1
                elif "dikirim" in s or "jalan" in s or "pengiriman" in s:
                    total_jalan += 1
                    active_orders.append(item)
                else:
                    total_gudang += 1
                    active_orders.append(item)

            c1, c2, c3 = st.columns(3)
            c1.metric("📦 Diproses Gudang", f"{total_gudang} Order")
            c2.metric("🚚 Sedang Jalan", f"{total_jalan} Order")
            c3.metric("✅ Selesai Diterima", f"{total_selesai} Order")
            
            st.divider()
            st.subheader("📋 Daftar Barang Belum Sampai")
            st.caption("Menampilkan order 'Diproses' atau 'Sedang Jalan'.")

            if active_orders:
                clean_data = []
                for x in active_orders:
                    clean_data.append({
                        "Order ID": x['order_id'],
                        "Customer": x['customer_name'],
                        "Barang": x['product_name'],
                        "Status": x['status'],
                        "Kurir": x['courier'] if x['courier'] else "-",
                        "Tanggal Input": x['created_at'][:10]
                    })
                st.dataframe(clean_data, use_container_width=True)
            else:
                st.success("Tidak ada barang pending.")
        else:
            st.info("Belum ada data pengiriman.")

    except Exception as e:
        st.error(f"Gagal memuat dashboard: {e}")

# ==========================================
# HALAMAN 2: SALES (Pencarian Cerdas)
# ==========================================
elif menu == "🔍 Cek Resi (Sales)":
    st.title("📦 Cek Status Pengiriman")
    st.markdown("Cari berdasarkan **Order ID** atau **Nama Customer**.")

    query = st.text_input("Ketik disini:", placeholder="Contoh: 12187... atau 'Iis Lita'")

    if st.button("Lacak Paket") or query:
        if query:
            try:
                if query.isdigit() and len(query) > 5:
                    response = supabase.table("shipments").select("*").eq("order_id", query.strip()).execute()
                else:
                    response = supabase.table("shipments").select("*").ilike("customer_name", f"%{query}%").execute()
                
                if response.data:
                    for data in response.data:
                        color_type = get_status_color(data['status'])
                        
                        if color_type == "success": container = st.success
                        elif color_type == "info": container = st.info
                        else: container = st.warning
                        
                        with container():
                            st.markdown(f"### Status: {data['status'].upper()}")
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
                            
                            # Update: Mengganti Tombol Link dengan Copy-Paste Area
                            with c2:
                                st.caption("📋 Template Pesan (Salin):")
                                message = f"Halo Kak {data['customer_name']}, update pesanan *{data['product_name']}*.\nStatus: *{data['status']}*.\nEkspedisi: {data['courier'] or '-'}.\nTerima kasih! - Tim Pengiriman"
                                # st.code otomatis membuat tombol 'copy' di pojok kanan atasnya
                                st.code(message, language=None)
                else:
                    st.warning("❌ Data tidak ditemukan.")
            except Exception as e:
                st.error(f"Error koneksi: {e}")

# ==========================================
# HALAMAN 3: ADMIN (Input, Update, Hapus)
# ==========================================
elif menu == "📝 Input Data (Admin)":
    st.title("🔐 Akses Admin")
    password = st.text_input("Masukkan Password Admin:", type="password")
    
    if password == "admin123":
        st.success("Login Berhasil!")
        st.divider()
        
        tab1, tab2, tab3 = st.tabs(["Input Order", "Update Status", "Hapus Data"])
        
        with tab1:
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

        with tab2:
            search_update = st.text_input("Cari Order ID untuk Update:", key="search_admin_upd")
            if search_update:
                res = supabase.table("shipments").select("*").eq("order_id", search_update).execute()
                if res.data:
                    curr = res.data[0]
                    st.info(f"Mengedit: {curr['customer_name']} - {curr['product_name']}")
                    with st.form("form_update"):
                        new_status = st.selectbox("Pilih Status", ["Diproses Gudang", "Menunggu Kurir", "Dalam Pengiriman", "Selesai/Diterima"], index=0)
                        new_courier = st.text_input("Nama Kurir / Supir", value=curr['courier'] or "")
                        new_resi = st.text_input("No Resi / Info Lain", value=curr['resi'] or "")
                        
                        if st.form_submit_button("Update Data"):
                            upd_data = {"status": new_status, "courier": new_courier, "resi": new_resi}
                            supabase.table("shipments").update(upd_data).eq("order_id", search_update).execute()
                            st.success("✅ Status diperbarui!")
                else:
                    st.caption("Data tidak ditemukan.")

        with tab3:
            st.error("⚠️ Hati-hati! Data yang dihapus tidak bisa kembali.")
            del_id = st.text_input("Masukkan Order ID yang mau DIHAPUS:", key="del_search")
            if del_id:
                res_del = supabase.table("shipments").select("*").eq("order_id", del_id).execute()
                if res_del.data:
                    d = res_del.data[0]
                    st.warning(f"Hapus data **{d['customer_name']}** ({d['product_name']})?")
                    if st.button("🗑️ YA, HAPUS PERMANEN", type="primary"):
                        supabase.table("shipments").delete().eq("order_id", del_id).execute()
                        st.success("Data berhasil dihapus.")
                else:
                    st.caption("Data tidak ditemukan.")
    elif password:
        st.error("Password salah!")
