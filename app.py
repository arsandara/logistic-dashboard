import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders

st.set_page_config(
    page_title="PT. Remenia Satori Tepas - AI Logistics Dashboard",
    page_icon="🚚",
    layout="wide"
)

# ====================== EMAIL FUNCTION ======================
from dotenv import load_dotenv
import os

load_dotenv()

def send_email(subject, body, attachment_df=None, filename="problem_orders.csv"):
    sender_email = os.getenv ("EMAIL") 
    sender_password = os.getenv ("APP_PASSWORD")
    
    receiver_emails = ["pinkanveronica23@gmail.com", "arsandaraz@gmail.com"]
    
    msg = MIMEMultipart()
    msg['From'] = sender_email
    msg['To'] = ", ".join(receiver_emails)
    msg['Subject'] = subject
    msg.attach(MIMEText(body, 'plain'))

    if attachment_df is not None:
        csv = attachment_df.to_csv(index=False)
        part = MIMEBase('application', 'octet-stream')
        part.set_payload(csv.encode())
        encoders.encode_base64(part)
        part.add_header('Content-Disposition', f'attachment; filename={filename}')
        msg.attach(part)

    try:
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(sender_email, sender_password)
        server.sendmail(sender_email, receiver_emails, msg.as_string())
        server.quit()
        return True, "✅ Email berhasil dikirim ke Tim Operasional"
    except Exception as e:
        return False, f"❌ Gagal mengirim email: {str(e)}"

# ====================== LOAD DATA ======================
@st.cache_data
def load_data():
    orders = pd.read_csv('data/orders.csv')
    routes = pd.read_csv('data/route_distance_id.csv')
    costs = pd.read_csv('data/cost_breakdown.csv')
    warehouse = pd.read_csv('data/warehouse_inventory.csv')

    cost_cols = ['Fuel_Cost','Labor_Cost','Vehicle_Maintenance','Insurance',
                 'Packaging_Cost','Technology_Platform_Fee','Other_Overhead']
    costs[cost_cols] = costs[cost_cols] * 1000

    df = pd.merge(orders, routes, on='Order_ID', how='left')
    df = pd.merge(df, costs, on='Order_ID', how='left')

    df['Total_Cost'] = df[cost_cols].sum(axis=1)

    df['Promised_Delivery_Days'] = 5
    df['Actual_Delivery_Days'] = (df['Distance_KM'].fillna(0) / 350 + 
                                  df['Traffic_Delay_Minutes'].fillna(0) / 1440 * 10).round(1)
    df['Delivery_Delay_Days'] = (df['Actual_Delivery_Days'] - df['Promised_Delivery_Days']).round(1)
    df['Delivery_Status'] = df['Delivery_Delay_Days'].apply(lambda x: 'Delayed' if x > 0 else 'On Time')

    return df, warehouse

df, warehouse = load_data()

# ====================== MAIN APP ======================
st.markdown('<h1 style="text-align:center;">🚚 PT. Remenia Satori Tepas</h1>', unsafe_allow_html=True)
st.markdown('<p style="text-align:center; font-size:1.3rem;">AI-Powered Logistics Dashboard</p>', unsafe_allow_html=True)

tab1, tab2 = st.tabs(["📦 Pengiriman & Rute", "📊 Stok Gudang"])

# ========================= TAB 1: PENGIRIMAN =========================
with tab1:
    st.markdown('<div class="tab-header">📋 Data Pengiriman & Rute</div>', unsafe_allow_html=True)
    st.dataframe(
        df[['Order_ID', 'Order_Date', 'Origin', 'Destination', 'Route', 'Distance_KM', 
            'Delivery_Delay_Days', 'Delivery_Status', 'Weather_Impact', 'Total_Cost']]
        .sort_values('Delivery_Delay_Days', ascending=False),
        use_container_width=True, 
        hide_index=True
    )

    st.markdown("---")
    st.markdown('<div class="tab-header">🤖 AI Analysis - Pengiriman Bermasalah</div>', unsafe_allow_html=True)

    problem_df = df[df['Delivery_Delay_Days'] > 0].copy()
    
    if not problem_df.empty:
        problem_df['Problem_Cluster'] = 'Lainnya'
        problem_df.loc[problem_df['Delivery_Delay_Days'] > 5, 'Problem_Cluster'] = 'Severe Delay'
        problem_df.loc[problem_df['Weather_Impact'].isin(['Heavy_Rain','Storm','Flood']), 'Problem_Cluster'] = 'Cuaca Buruk'
        problem_df.loc[problem_df['Total_Cost'] > problem_df['Total_Cost'].quantile(0.85), 'Problem_Cluster'] = 'Biaya Tinggi'

        st.dataframe(
            problem_df[['Order_ID', 'Order_Date', 'Origin', 'Destination', 'Route', 
                       'Distance_KM', 'Delivery_Delay_Days', 'Total_Cost', 
                       'Weather_Impact', 'Problem_Cluster']]
            .sort_values('Delivery_Delay_Days', ascending=False),
            use_container_width=True, 
            hide_index=True
        )

        # ================== GRAFIK ANALISIS TAB 1 ==================
        st.markdown("### 📊 Grafik Analisis Pengiriman")
        col1, col2 = st.columns(2)
        with col1:
            fig1 = px.bar(problem_df['Problem_Cluster'].value_counts().reset_index(), 
                         x='Problem_Cluster', y='count', color='Problem_Cluster',
                         title="Jumlah Masalah per Kategori")
            st.plotly_chart(fig1, use_container_width=True)
        with col2:
            fig2 = px.pie(df, names='Weather_Impact', title="Dampak Cuaca terhadap Pengiriman")
            st.plotly_chart(fig2, use_container_width=True)

        # ================== REKOMENDASI LEBIH DETAIL ==================
        st.markdown("### 🤖 Rekomendasi AI Detail per Cluster")
        for cluster in problem_df['Problem_Cluster'].unique():
            cluster_data = problem_df[problem_df['Problem_Cluster'] == cluster]
            with st.expander(f"🔍 {cluster} — {len(cluster_data)} Order", expanded=True):
                st.write(f"**Rata-rata Delay:** {cluster_data['Delivery_Delay_Days'].mean():.2f} hari")
                st.write(f"**Total Biaya:** Rp {cluster_data['Total_Cost'].sum():,}")

                st.subheader("✅ Rekomendasi & Langkah Selanjutnya:")
                if cluster == "Severe Delay":
                    st.error("• Segera ganti carrier ke yang lebih reliable\n• Gunakan rute alternatif yang lebih pendek\n• Hubungi customer untuk update ETA baru + tawarkan kompensasi\n• Evaluasi kontrak carrier jangka panjang")
                elif cluster == "Cuaca Buruk":
                    st.warning("• Tunda pengiriman sampai cuaca membaik\n• Gunakan armada tertutup / container\n• Update status ke customer secara real-time\n• Siapkan stok cadangan di gudang terdekat")
                elif cluster == "Biaya Tinggi":
                    st.info("• Evaluasi rute dan cari alternatif lebih murah\n• Negosiasi tarif dengan vendor & tol\n• Lakukan konsolidasi order\n• Pertimbangkan penggunaan transportasi multimoda")
                else:
                    st.info("• Lakukan root cause analysis mendalam\n• Optimasi jadwal pengiriman\n• Monitoring rutin cuaca & lalu lintas\n• Review SOP pengiriman")

        # ================== TOMBOL KIRIM EMAIL TAB 1 ==================
        st.markdown("---")
        if st.button("📤 Send Delivery Report to Operational Team", type="primary", use_container_width=True):
            with st.spinner("Mengirim email..."):
                body = f"""PT. Remenia Satori Tepas - AI Delivery Report
Tanggal: {datetime.now().strftime('%Y-%m-%d %H:%M')}

Total Order Bermasalah: {len(problem_df)}
Detail terlampir dalam file CSV.

AI Logistics System"""
                
                success, msg = send_email(
                    subject=f"AI Problem Report - {len(problem_df)} Orders",
                    body=body,
                    attachment_df=problem_df,
                    filename="problem_orders.csv"
                )
                if success:
                    st.success(msg)
                else:
                    st.error(msg)

    else:
        st.success("✅ Saat ini tidak ada pengiriman yang delay.")

# ========================= TAB 2: STOK GUDANG =========================
with tab2:
    st.markdown('<div class="tab-header">📦 Stok Gudang & AI Recommendation</div>', unsafe_allow_html=True)
    
    st.subheader("1. Semua Data Stok Gudang")
    st.dataframe(warehouse, use_container_width=True, hide_index=True)

    warehouse['Stock_Ratio'] = warehouse['Current_Stock_Units'] / warehouse['Reorder_Level']
    warehouse['Stock_Status'] = pd.cut(warehouse['Stock_Ratio'], 
                                       bins=[0, 0.7, 1.0, 1.5, 999], 
                                       labels=['Kritis', 'Rendah', 'Normal', 'Berlebih'])

    st.markdown("---")
    st.subheader("2. Klasifikasi Status Stok & Rekomendasi AI")

    col1, col2 = st.columns(2)
    col3, col4 = st.columns(2)

    with col1:
        berlebih = warehouse[warehouse['Stock_Status'] == 'Berlebih']
        st.success(f"**Berlebih** ({len(berlebih)} item)")
        if not berlebih.empty:
            st.dataframe(berlebih[['Warehouse_ID','Location','Product_Category','Current_Stock_Units','Reorder_Level']], hide_index=True)

    with col2:
        normal = warehouse[warehouse['Stock_Status'] == 'Normal']
        st.info(f"**Normal** ({len(normal)} item)")
        if not normal.empty:
            st.dataframe(normal[['Warehouse_ID','Location','Product_Category','Current_Stock_Units','Reorder_Level']], hide_index=True)

    with col3:
        kritis = warehouse[warehouse['Stock_Status'] == 'Kritis']
        st.error(f"**Kritis** ({len(kritis)} item)")
        if not kritis.empty:
            st.dataframe(kritis[['Warehouse_ID','Location','Product_Category','Current_Stock_Units','Reorder_Level']], hide_index=True)

    with col4:
        rendah = warehouse[warehouse['Stock_Status'] == 'Rendah']
        st.warning(f"**Rendah** ({len(rendah)} item)")
        if not rendah.empty:
            st.dataframe(rendah[['Warehouse_ID','Location','Product_Category','Current_Stock_Units','Reorder_Level']], hide_index=True)

    # ================== GRAFIK ANALISIS TAB 2 ==================
    st.markdown("### 📊 Grafik Analisis Stok Gudang")
    col_g1, col_g2 = st.columns(2)
    with col_g1:
        fig3 = px.bar(warehouse['Stock_Status'].value_counts().reset_index(), 
                      x='Stock_Status', y='count', color='Stock_Status',
                      title="Distribusi Status Stok")
        st.plotly_chart(fig3, use_container_width=True)
    with col_g2:
        fig4 = px.bar(warehouse.groupby('Location')['Current_Stock_Units'].sum().reset_index(),
                      x='Location', y='Current_Stock_Units', color='Location',
                      title="Total Stok per Lokasi Gudang")
        st.plotly_chart(fig4, use_container_width=True)

    # ================== REKOMENDASI DETAIL TAB 2 ==================
    st.markdown("### 🤖 Rekomendasi AI Stok Gudang")
    if len(kritis) > 0 or len(rendah) > 0:
        st.error("**Tindakan Mendesak:**")
        st.write("• Segera lakukan restock untuk item Kritis dan Rendah")
        st.write("• Percepat proses Purchase Order ke supplier")
        st.write("• Cek supplier alternatif untuk pengiriman lebih cepat")
    
    if len(berlebih) > 0:
        st.success("**Tindakan untuk Stok Berlebih:**")
        st.write("• Kurangi frekuensi restock barang tersebut")
        st.write("• Lakukan promosi / diskon untuk mempercepat penjualan")
        st.write("• Pertimbangkan transfer stok antar gudang")

    # ================== TOMBOL KIRIM EMAIL TAB 2 ==================
    st.markdown("---")
    if st.button("📤 Send Stock Report to Operational Team", type="primary", use_container_width=True):
        with st.spinner("Mengirim email..."):
            body = f"""PT. Remenia Satori Tepas - AI Stock Report
Tanggal: {datetime.now().strftime('%Y-%m-%d %H:%M')}

Ringkasan Stok:
- Kritis : {len(kritis)} item
- Rendah  : {len(rendah)} item  
- Normal  : {len(normal)} item
- Berlebih: {len(berlebih)} item

Detail lengkap stok gudang terlampir.

AI Logistics System"""

            success, msg = send_email(
                subject=f"AI Stock Report - {datetime.now().strftime('%Y-%m-%d')}",
                body=body,
                attachment_df=warehouse,
                filename="stock_report.csv"
            )
            if success:
                st.success("✅ Laporan Stok berhasil dikirim ke Tim Operasional")
            else:
                st.error(msg)

st.caption(f"Update Terakhir: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | PT. Remenia Satori Tepas")