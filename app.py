import streamlit as st
import pandas as pd
import plotly.express as px
from src.data_processing import load_data, filter_data, compute_brand_share, compute_trends

st.set_page_config(page_title="Laptop Trends 2025", layout="wide")

st.title("Інтерактивний аналіз трендів ноутбуків — 2025")

# --- Завантаження даних ---
DATA_PATH = "data/sample_laptops.csv"
df = load_data(DATA_PATH)

# --- Бокова панель: фільтри ---
st.sidebar.header("Фільтри")
brands = st.sidebar.multiselect("Бренд", options=sorted(df['brand'].unique()), default=sorted(df['brand'].unique())[:5])
price_min, price_max = st.sidebar.slider("Ціна (USD)", int(df['price_usd'].min()), int(df['price_usd'].max()), (int(df['price_usd'].min()), int(df['price_usd'].max())))
screen_min, screen_max = st.sidebar.slider("Діагональ екрану (in)", float(df['screen_size_in'].min()), float(df['screen_size_in'].max()), (float(df['screen_size_in'].min()), float(df['screen_size_in'].max())))
ai_cpu = st.sidebar.selectbox("AI CPU", options=["Усі","Із AI", "Без AI"])

# --- Фільтрація ---
filtered = filter_data(df, brands=brands, price_range=(price_min, price_max), screen_range=(screen_min, screen_max), ai_cpu=ai_cpu)

# --- Верхня панель: статистики ---
col1, col2, col3 = st.columns(3)
col1.metric("Моделей (відфільтровано)", len(filtered))
col2.metric("Середня ціна (USD)", f"{filtered['price_usd'].mean():.0f}")
col3.metric("Середня автономність (Wh)", f"{filtered['battery_wh'].mean():.0f}")

# --- Таблиця результатів ---
st.subheader("Список моделей")
st.dataframe(filtered.sort_values(by='price_usd').reset_index(drop=True))

# --- Графік: частка брендів ---
st.subheader("Частка брендів (відфільтровано)")
brand_share = compute_brand_share(filtered)
fig1 = px.pie(brand_share, names='brand', values='count', title='Розподіл за брендами')
st.plotly_chart(fig1, use_container_width=True)

# --- Графік: тренди за роками ---
st.subheader("Тренди характеристик за роками")
trend_df = compute_trends(df)
fig2 = px.line(trend_df, x='year', y='avg_price', color='metric', markers=True,
               title='Тренди: середня ціна / середня автономність / частка OLED')
st.plotly_chart(fig2, use_container_width=True)

# --- Експорт CSV ---
st.download_button("Експорт відфільтрованих результатів у CSV", data=filtered.to_csv(index=False).encode('utf-8'), file_name="filtered_laptops.csv", mime="text/csv")
