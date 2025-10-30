import streamlit as st
import pandas as pd
import plotly.express as px
import logging
import math
from src.data_processing import load_data, filter_data, compute_brand_share, compute_trends

logger = logging.getLogger(__name__)
st.set_page_config(page_title="Laptop Trends 2025", layout="wide")

# Inject CSS прямо в код
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;800&display=swap');
:root {
  --neon: #00e6ff;
  --neon-2: #7c5cff;
  --bg: #f4f7fb;
  --panel: #ffffff;
  --muted: #6b7280;
  --card-shadow: 0 6px 30px rgba(15,23,42,0.06);
}
html, body, [data-testid="stAppViewContainer"] > .main {
  background: var(--bg);
  font-family: 'Inter', sans-serif;
  color: #0f172a;
}
.card {
  border-radius:12px;
  background: var(--panel);
  border: 1.5px solid rgba(0,230,255,0.12);
  box-shadow: var(--card-shadow);
  padding:12px;
  display:flex;
  flex-direction:column;
  transition: transform .18s ease, box-shadow .18s ease;
}
.card:hover {
  transform: translateY(-6px);
  box-shadow: 0 12px 40px rgba(124,92,255,0.12);
}
.thumb {
  width:100%;
  height:200px;
  object-fit:cover;
  border-radius:8px;
  margin-bottom:12px;
}
.title {
  font-weight:700;
  font-size:15px;
  margin-bottom:6px;
}
.meta {
  font-size:12px;
  color:var(--muted);
  margin-bottom:8px;
}
.price {
  color: #ff3b30;
  font-weight:800;
  font-size:16px;
  margin-top:auto;
}
.action {
  display:inline-block;
  padding:8px 12px;
  border-radius:10px;
  font-weight:700;
  font-size:13px;
  color: #fff;
  background: linear-gradient(90deg, var(--neon), var(--neon-2));
  text-decoration:none;
  box-shadow: 0 8px 20px rgba(124,92,255,0.12);
}
</style>
""", unsafe_allow_html=True)

# Header
st.markdown("## 💻 Laptop Trends 2025")
st.markdown("Інтерактивний аналіз моделей: ціни, автономність, OLED, AI‑процесори")

# Load data
DATA_PATH = "data/sample_laptops.csv"
df = load_data(DATA_PATH)
if df.empty:
    st.error("❌ Дані не завантажені або CSV-файл порожній.")
    st.stop()

# Sidebar filters
with st.sidebar:
    st.header("🔍 Фільтри")
    brands = st.multiselect("Бренд", sorted(df['brand'].unique()), default=sorted(df['brand'].unique())[:5])
    price_min, price_max = st.slider("Ціна (USD)", int(df['price_usd'].min()), int(df['price_usd'].max()), (int(df['price_usd'].min()), int(df['price_usd'].max())))
    screen_min, screen_max = st.slider("Діагональ екрану (in)", float(df['screen_size_in'].min()), float(df['screen_size_in'].max()), (float(df['screen_size_in'].min()), float(df['screen_size_in'].max())))
    ai_cpu = st.selectbox("AI CPU", ["Усі", "Із AI", "Без AI"])
    max_show = st.number_input("Кількість моделей на сторінці", min_value=3, max_value=60, value=12)

# Filter
filtered = filter_data(df, brands, (price_min, price_max), (screen_min, screen_max), ai_cpu)

# Metrics
st.markdown("### 📊 Загальні метрики")
c1, c2, c3 = st.columns(3)
c1.metric("Моделей (відфільтровано)", len(filtered))
c2.metric("Середня ціна (USD)", f"{filtered['price_usd'].mean():.0f}" if len(filtered) else "—")
c3.metric("Середня автономність (Wh)", f"{filtered['battery_wh'].mean():.0f}" if len(filtered) else "—")

# Tabs
tab1, tab2, tab3 = st.tabs(["🖼️ Каталог", "🥧 Частка брендів", "📈 Тренди"])

with tab1:
    display_df = filtered.sort_values(by='price_usd').reset_index(drop=True)
    total = len(display_df)
    page_size = int(max_show)
    total_pages = max(1, math.ceil(total / page_size))
    if 'page' not in st.session_state:
        st.session_state.page = 1

    # Pager
    pc1, pc2, pc3, pc4 = st.columns([1,3,1,3])
    with pc1:
        if st.button("⬅️ Prev") and st.session_state.page > 1:
            st.session_state.page -= 1
    with pc2:
        st.markdown(f"**Сторінка {st.session_state.page} / {total_pages}**")
    with pc3:
        if st.button("Next ➡️") and st.session_state.page < total_pages:
            st.session_state.page += 1
    with pc4:
        jump = st.number_input("Перейти на стор.", min_value=1, max_value=total_pages, value=st.session_state.page, step=1, key="jump_page")
        if jump != st.session_state.page:
            st.session_state.page = int(jump)

    # Cards
    start_idx = (st.session_state.page - 1) * page_size
    end_idx = start_idx + page_size
    page_df = display_df.iloc[start_idx:end_idx]
    cols = st.columns(4)
    for i, row in enumerate(page_df.itertuples()):
        with cols[i % 4]:
            st.markdown(f"""
            <div class="card">
                <img src="{row.thumbnail.replace('[:]//', '://')}" class="thumb" />
                <div class="title">{row.brand} {row.model}</div>
                <div class="meta">{row.screen_size_in}″ • {row.display_type} • {row.cpu}</div>
                <div class="price">${row.price_usd:.0f}</div>
            </div>
            """, unsafe_allow_html=True)

            show = st.toggle(f"🔍 Детальніше", key=f"toggle_{i}")
            if show:
                st.markdown(f"""
                <div style="border:1.5px solid #00e6ff; border-radius:10px; padding:12px; margin-top:8px; background: #ffffffcc;">
                    <b>💰 Ціна:</b> ${row.price_usd:.0f}<br>
                    <b>📺 Екран:</b> {row.screen_size_in}″ {row.display_type}, {getattr(row, 'refresh_rate', '—')}Hz<br>
                    <b>🧠 Процесор:</b> {row.cpu}<br>
                    <b>🔋 Батарея:</b> {row.battery_wh} Wh<br>
                    <b>🧮 RAM:</b> {row.ram_gb} GB, SSD: {row.storage_gb} GB<br>
                    <b>📅 Рік:</b> {row.release_year}<br>
                    <b>🔗 <a href="{row.url}" target="_blank">Сторінка товару</a></b>
                </div>
                """, unsafe_allow_html=True)

with tab2:
    brand_share = compute_brand_share(filtered)
    fig1 = px.pie(brand_share, names='brand', values='count', title='Розподіл за брендами', template='plotly_white')
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
            template='plotly_white',
            title='Тренди: ціна, автономність, OLED'
        )
        fig2.update_layout(
            legend_title_text='Характеристика',
            xaxis_title='Рік',
            yaxis
            # Export
st.markdown("### 📤 Експорт результатів")
st.download_button(
    label="⬇️ Завантажити CSV",
    data=filtered.to_csv(index=False).encode('utf-8'),
    file_name="filtered_laptops.csv",
    mime="text/csv"
)
