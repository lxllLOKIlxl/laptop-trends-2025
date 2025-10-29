import streamlit as st
import pandas as pd
import plotly.express as px
from src.data_processing import load_data, filter_data, compute_brand_share, compute_trends
import logging

st.set_page_config(page_title="Laptop Trends 2025", layout="centered")
logger = logging.getLogger(__name__)

def sanitize_text_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Позбуваємось сирих 'http' у всіх текстових стовпцях, щоб уникнути автолінкування в браузері."""
    df = df.copy()
    for col in df.select_dtypes(include=['object', 'string']).columns:
        try:
            df[col] = df[col].astype(str).str.replace(r'https?://', lambda m: m.group(0).replace('://', '[:]//'), regex=True)
        except Exception:
            df[col] = df[col].astype(str).apply(lambda s: s.replace('://', '[:]//'))
        df[col] = df[col].apply(lambda s: s if len(s) <= 300 else s[:300] + '...')
    return df

def safe_plotly_chart(fig):
    try:
        st.plotly_chart(fig, use_container_width=True)
    except Exception:
        logger.exception("Plotly render error")
        st.error("Виникла помилка під час побудови графіка. Деталі в логах.")

# Заголовок
st.title("💻 Laptop Trends 2025")
st.markdown("Інтерактивний аналіз моделей ноутбуків: ціни, автономність, OLED, AI‑процесори")

# --- Завантаження даних ---
DATA_PATH = "data/sample_laptops.csv"
df = load_data(DATA_PATH)

if df.empty:
    st.error("❌ Дані не завантажені або CSV-файл порожній.")
    st.stop()

# --- Бокова панель: фільтри ---
with st.sidebar:
    st.header("🔍 Фільтри")
    try:
        brands = st.multiselect("Бренд", options=sorted(df['brand'].unique()), default=sorted(df['brand'].unique())[:5])
    except Exception:
        brands = st.multiselect("Бренд", options=[], default=[])
    price_min, price_max = st.slider("Ціна (USD)", int(df['price_usd'].min()), int(df['price_usd'].max()), (int(df['price_usd'].min()), int(df['price_usd'].max())))
    screen_min, screen_max = st.slider("Діагональ екрану (in)", float(df['screen_size_in'].min()), float(df['screen_size_in'].max()), (float(df['screen_size_in'].min()), float(df['screen_size_in'].max())))
    ai_cpu = st.selectbox("AI CPU", options=["Усі", "Із AI", "Без AI"])
    # Кількість карток для відображення
    max_show = st.number_input("Кількість моделей на сторінці", min_value=3, max_value=60, value=9)

# --- Фільтрація ---
try:
    filtered = filter_data(df, brands=brands, price_range=(price_min, price_max), screen_range=(screen_min, screen_max), ai_cpu=ai_cpu)
except Exception:
    logger.exception("Filter error")
    st.error("Помилка під час фільтрації даних. Перевірте структуру CSV.")
    st.stop()

# --- Метрики ---
st.markdown("### 📊 Загальні метрики")
col1, col2, col3 = st.columns(3)
col1.metric("Моделей (відфільтровано)", len(filtered))
col2.metric("Середня ціна (USD)", f"{filtered['price_usd'].mean():.0f}" if len(filtered) else "—")
col3.metric("Середня автономність (Wh)", f"{filtered['battery_wh'].mean():.0f}" if len(filtered) else "—")

# --- Вкладки ---
tab1, tab2, tab3 = st.tabs(["🖼️ Каталог", "🥧 Частка брендів", "📈 Тренди"])

with tab1:
    try:
        display_df = filtered.sort_values(by='price_usd').reset_index(drop=True)
        if 'url' in display_df.columns:
            display_df = display_df.drop(columns=['url'])
        display_df = sanitize_text_columns(display_df)

        # Показати як сітку карток
        rows = display_df.head(int(max_show))
        cols_per_row = 3
        for i in range(0, len(rows), cols_per_row):
            cols = st.columns(cols_per_row)
            for j, (_, row) in enumerate(rows.iloc[i:i+cols_per_row].iterrows()):
                col = cols[j]
                thumb = row.get('thumbnail', '')
                if thumb:
                    # якщо thumbnail містить '[:]', відновимо '://'
                    col.image(thumb.replace('[:]//', '://'), use_container_width=True)
                else:
                    col.image("https://via.placeholder.com/300x200?text=No+image", use_container_width=True)
                col.markdown(f"**{row.get('brand','')} {row.get('model','')}**")
                col.write(f"Ціна: ${row.get('price_usd','—')}")
                col.write(f"Екран: {row.get('screen_size_in','—')}\"  •  {row.get('display_type','—')}")
                if col.button("Детальніше", key=f"det_{i}_{j}"):
                    st.info(f"Деталі: {row.get('brand','')} {row.get('model','')}")
    except Exception:
        logger.exception("Error rendering catalog")
        st.error("Не вдалося відобразити каталог. Подробиці в логах.")

with tab2:
    try:
        brand_share = compute_brand_share(filtered)
        fig1 = px.pie(brand_share, names='brand', values='count', title='Розподіл за брендами', template='plotly_white')
        safe_plotly_chart(fig1)
    except Exception:
        logger.exception("Error in brand pie")
        st.error("Не вдалося побудувати діаграму часток брендів.")

with tab3:
    try:
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
                template='plotly_white',
                title='Тренди: ціна, автономність, OLED'
            )
            fig2.update_layout(
                legend_title_text='Характеристика',
                xaxis_title='Рік',
                yaxis_title='Значення',
                margin=dict(l=20, r=20, t=40, b=20),
                font=dict(size=14)
            )
            safe_plotly_chart(fig2)
    except Exception:
        logger.exception("Error in trends")
        st.error("Не вдалося побудувати тренди. Подробиці в логах.")

# --- Експорт CSV ---
st.markdown("### 📤 Експорт результатів")
try:
    st.download_button(
        "⬇️ Завантажити відфільтровані дані у CSV",
        data=filtered.to_csv(index=False).encode('utf-8'),
        file_name="filtered_laptops.csv",
        mime="text/csv"
    )
except Exception:
    logger.exception("Download error")
    st.error("Експорт CSV тимчасово недоступний.")
