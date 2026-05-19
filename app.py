import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime

st.set_page_config(
    page_title="PT. Remenia Satori Tepas - AI Logistics Dashboard",
    page_icon="🚚",
    layout="wide"
)

# ====================== CUSTOM CSS (Simple & Clean) ======================
st.markdown("""
<style>
    .main-header {
        font-size: 2.4rem;
        color: #0A2540;
        text-align: center;
        font-weight: bold;
        margin-bottom: 10px;
    }
    .sub-header {
        font-size: 1.6rem;
        color: #0A2540;
        font-weight: 600;
        margin-top: 20px;
        margin-bottom: 15px;
    }
    .metric-card {
        background: linear-gradient(135deg, #1E88E5, #0A2540);
        color: white;
        padding: 20px;
        border-radius: 12px;
        text-align: center;
    }
    .problem-row {
        background-color: #ffebee;
    }
    .stButton > button {
        background: linear-gradient(135deg, #1E88E5, #0A2540);
        color: white;
        font-weight: bold;
        border-radius: 8px;
        height: 50px;
    }
</style>
""", unsafe_allow_html=True)

# ====================== LOAD DATA ======================
@st.cache_data
def load_data():
    try:
        # Load data
        orders = pd.read_csv('data/orders.csv')
        delivery = pd.read_csv('data/delivery_performance.csv')
        routes = pd.read_csv('data/route_distance_id.csv')
        feedback = pd.read_csv('data/customer_feedback.csv')
        costs = pd.read_csv('data/cost_breakdown.csv')

        # Merge semua data
        df = pd.merge(orders, delivery, on='Order_ID', how='left')
        df = pd.merge(df, routes, on='Order_ID', how='left')
        df = pd.merge(df, costs, on='Order_ID', how='left')
        
        # Merge feedback
        fb = feedback.groupby('Order_ID').agg({
            'Rating': 'mean',
            'Issue_Category': 'first',
            'Feedback_Text': 'first'
        }).reset_index()
        df = pd.merge(df, fb, on='Order_ID', how='left')

        # === PERBAIKAN UTAMA: Hitung Total_Cost ===
        cost_columns = ['Fuel_Cost', 'Labor_Cost', 'Vehicle_Maintenance', 
                       'Insurance', 'Packaging_Cost', 'Technology_Platform_Fee', 
                       'Other_Overhead']
        
        # Hanya pakai kolom yang benar-benar ada
        available_costs = [col for col in cost_columns if col in df.columns]
        df['Total_Cost'] = df[available_costs].sum(axis=1)

        # Hitung Delay
        df['Delivery_Delay_Days'] = df['Actual_Delivery_Days'] - df['Promised_Delivery_Days']
        
        st.success(f"✅ Data berhasil dimuat! Total Order: {len(df)}")
        return df
        
    except FileNotFoundError as e:
        st.error(f"❌ File tidak ditemukan: {e}")
        st.info("""
        Pastikan folder **data/** berisi file berikut:
        - orders.csv
        - delivery_perfomance.csv
        - route_distance_id.csv
        - customer_feedback.csv
        - cost_breakdown.csv
        """)
        return None
    except Exception as e:
        st.error(f"Error loading data: {e}")
        return None

# ====================== MAIN APP ======================
def main():
    st.markdown('<h1 class="main-header">🚚 PT. Remenia Satori Tepas</h1>', unsafe_allow_html=True)
    st.markdown('<p style="text-align:center; font-size:1.2rem;">AI Dashboard Monitoring & Optimalisasi Logistik Pengiriman</p>', unsafe_allow_html=True)

    data = load_data()
    if data is None:
        st.stop()

    # Sidebar Filter
    st.sidebar.header("🔍 Filter Pengiriman")
    date_range = st.sidebar.date_input(
        "Tanggal Order",
        value=(data['Order_Date'].min(), data['Order_Date'].max()),
        min_value=data['Order_Date'].min(),
        max_value=data['Order_Date'].max()
    )

    status_filter = st.sidebar.multiselect(
        "Status Pengiriman",
        options=['All', 'Severely-Delayed', 'Slightly-Delayed', 'On-Time'],
        default=['All']
    )

    # Filter data
    filtered = data.copy()
    if 'All' not in status_filter:
        filtered = filtered[filtered['Delivery_Status'].isin(status_filter)]

    # KPI
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Order", len(filtered))
    with col2:
        problematic = len(filtered[filtered['Delivery_Delay_Days'] > 0])
        st.metric("Pengiriman Bermasalah", problematic, f"{problematic/len(filtered)*100:.1f}%")
    with col3:
        avg_rating = filtered['Rating'].mean()
        st.metric("Rata-rata Rating", f"{avg_rating:.2f}/5")
    with col4:
        on_time = len(filtered[filtered['Delivery_Delay_Days'] <= 0]) / len(filtered) * 100
        st.metric("On-Time Rate", f"{on_time:.1f}%")

    st.markdown("---")

    # ================== TABEL PENGIRIMAN BERMASALAH ==================
    st.markdown('<div class="sub-header">⚠️ Daftar Pengiriman Bermasalah</div>', unsafe_allow_html=True)

    # Definisikan pengiriman bermasalah
    problem_df = filtered[filtered['Delivery_Delay_Days'] > 0].copy()
    problem_df = problem_df.sort_values('Delivery_Delay_Days', ascending=False)

    # Tampilkan kolom penting
    display_cols = [
        'Order_ID', 'Order_Date', 'Origin', 'Destination', 'Route',
        'Promised_Delivery_Days', 'Actual_Delivery_Days', 'Delivery_Delay_Days',
        'Delivery_Status', 'Rating', 'Issue_Category', 'Total_Cost'
    ]

    if not problem_df.empty:
        st.dataframe(
            problem_df[display_cols],
            use_container_width=True,
            hide_index=True
        )
    else:
        st.success("🎉 Tidak ada pengiriman bermasalah saat ini!")

    st.markdown("---")

    # ================== AI OPTIMIZATION ==================
    st.markdown('<div class="sub-header">🤖 AI Optimalisasi Pengiriman</div>', unsafe_allow_html=True)

    st.write("Pilih 1 atau lebih order di bawah ini untuk mendapatkan rekomendasi AI:")

    # Pilih order
    selected_orders = st.multiselect(
        "Pilih Order ID yang ingin dioptimasi",
        options=problem_df['Order_ID'].tolist() if not problem_df.empty else [],
        max_selections=5
    )

    if st.button("🚀 Jalankan AI Optimalisasi", type="primary"):
        if not selected_orders:
            st.warning("Silakan pilih minimal 1 order")
        else:
            with st.spinner("AI sedang menganalisis..."):
                for order_id in selected_orders:
                    row = filtered[filtered['Order_ID'] == order_id].iloc[0]
                    
                    st.subheader(f"Rekomendasi AI - {order_id}")
                    col_a, col_b = st.columns([3,2])
                    
                    with col_a:
                        st.write(f"**Rute:** {row['Route']}")
                        st.write(f"**Delay Saat Ini:** {row['Delivery_Delay_Days']:.1f} hari")
                        st.write(f"**Masalah:** {row['Issue_Category']} | Rating: {row['Rating']}/5")
                    
                    with col_b:
                        st.success("**Rekomendasi Optimalisasi**")
                    
                    # Rekomendasi sederhana berdasarkan kondisi
                    if row['Delivery_Delay_Days'] > 5:
                        st.info("→ **Ganti Carrier** ke yang lebih cepat (rekomendasi: ReliableExpress)")
                        st.info("→ **Gunakan rute alternatif** via darat + ferry")
                    elif row['Weather_Impact'] in ['Heavy_Rain', 'Storm', 'Flood']:
                        st.info("→ **Tunda pengiriman** atau gunakan kendaraan tertutup")
                    else:
                        st.info("→ **Optimasi jadwal** + pengecekan muatan ulang")
                    
                    st.info(f"**Estimasi Penghematan:** Rp {int(row['Total_Cost'] * 0.15):,}")
                    st.markdown("---")

    # Overview Chart
    st.markdown('<div class="sub-header">📊 Ringkasan Pengiriman</div>', unsafe_allow_html=True)
    col1, col2 = st.columns(2)
    
    with col1:
        fig = px.pie(filtered, names='Delivery_Status', title='Status Pengiriman')
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        fig2 = px.histogram(filtered, x='Delivery_Delay_Days', nbins=20, title='Distribusi Keterlambatan (hari)')
        st.plotly_chart(fig2, use_container_width=True)

if __name__ == "__main__":
    main()