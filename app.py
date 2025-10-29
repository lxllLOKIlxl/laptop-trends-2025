import streamlit as st
import pandas as pd
import plotly.express as px
from src.data_processing import load_data, filter_data, compute_brand_share, compute_trends

st.set_page_config(page_title="Laptop Trends 2025", layout="centered")

st.title("💻 Laptop Trends 2025")
st.markdown("Інтерактивний аналіз моделей ноутбуків: ціни, автономність, OLED, AI-процесори")

# --- Завантаження даних ---
DATA_PATH = "data/sample_laptops.csv"
df = load_data(DATA_PATH)

if df.empty:
    st.error("❌ Дані не завантажені або CSV-файл порожній.")
    st.stop()

# --- Бокова панель: фільтри ---
with st.sidebar:
    st.header("🔍 Фільтри")
    brands = st.multiselect("Бренд", options=sorted(df['brand'].unique()), default=sorted(df['brand'].unique())[:5])
    price_min, price_max = st.slider("Ціна (USD)", int(df['price_usd'].min()), int(df['price_usd'].max()), (int(df['price_usd'].min()), int(df['price_usd'].max())))
    screen_min, screen_max = st.slider("Діагональ екрану (in)", float(df['screen_size_in'].min()), float(df['screen_size_in'].max()), (float(df['screen_size_in'].min()), float(df['screen_size_in'].max())))
    ai_cpu = st.selectbox("AI CPU", options=["Усі", "Із AI", "Без AI"])

# --- Фільтрація ---
filtered = filter_data(df, brands=brands, price_range=(price_min, price_max), screen_range=(screen_min, screen_max), ai_cpu=ai_cpu)

# --- Метрики ---
st.markdown("### 📊 Загальні метрики")
col1, col2, col3 = st.columns(3)
col1.metric("Моделей (відфільтровано)", len(filtered))
col2.metric("Середня ціна (USD)", f"{filtered['price_usd'].mean():.0f}")
col3.metric("Середня автономність (Wh)", f"{filtered['battery_wh'].mean():.0f}")

# --- Вкладки ---
tab1, tab2, tab3 = st.tabs(["📋 Таблиця", "🥧 Частка брендів", "📈 Тренди"])

with tab1:
    st.dataframe(filtered.sort_values(by='price_usd').reset_index(drop=True), use_container_width=True)

with tab2:
    brand_share = compute_brand_share(filtered)
    fig1 = px.pie(brand_share, names='brand', values='count', title='Розподіл за брендами', template='plotly_dark')
    st.plotly_chart(fig1, use_container_width=True)

with tab3:
    trend_df = compute_trends(df)
    if trend_df.empty:
        st.warning("Немає даних для побудови трендів.")
    else:
        fig2 = px.line(
            trend_df,
            x='year',
            y='value',
            color='metric',
            markers=True,
            line_shape='spline',
            template='plotly_dark',
            title='Тренди: ціна, автономність, OLED'
        )
        fig2.update_layout(
            legend_title_text='Характеристика',
            xaxis_title='Рік',
            yaxis_title='Значення',
            margin=dict(l=40, r=40, t=60, b=40)
        )
        st.plotly_chart(fig2, use_container_width=True)

# --- Експорт CSV ---
st.markdown("### 📤 Експорт результатів")
st.download_button(
    "⬇️ Завантажити відфільтровані дані у CSV",
    data=filtered.to_csv(index=False).encode('utf-8'),
    file_name="filtered_laptops.csv",
    mime="text/csv"
)
