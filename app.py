import streamlit as st
import pandas as pd
import plotly.express as px
import logging
import math
from src.data_processing import load_data, filter_data, compute_brand_share, compute_trends

logger = logging.getLogger(__name__)
st.set_page_config(page_title="Laptop Trends 2025", layout="wide")

# Inject CSS прямо в код — підсилені неонові рамки та стилі
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;800&display=swap');
:root {
  --neon-1: #00e6ff;
  --neon-2: #7c5cff;
  --neon-3: #00ff9c;
  --bg: #f4f7fb;
  --panel: #ffffff;
  --muted: #6b7280;
  --card-shadow: 0 6px 40px rgba(15,23,42,0.08);
}
/* Base */
html, body, [data-testid="stAppViewContainer"] > .main {
  background: var(--bg);
  font-family: 'Inter', sans-serif;
  color: #0f172a;
}

/* Cards */
.card {
  border-radius:14px;
  background: var(--panel);
  border: 1.5px solid rgba(0,230,255,0.18);
  box-shadow: var(--card-shadow);
  padding:14px;
  display:flex;
  flex-direction:column;
  transition: transform .16s ease, box-shadow .16s ease, border-color .16s ease;
  position: relative;
  z-index: 0;
}

/* stronger neon glow */
.card::before {
  content: "";
  position: absolute;
  inset: -2px;
  border-radius: 16px;
  background: linear-gradient(90deg, rgba(0,230,255,0.07), rgba(124,92,255,0.06));
  z-index: -2;
  filter: blur(8px);
  opacity: 0.9;
}

.card:hover {
  transform: translateY(-8px);
  border-color: rgba(0,230,255,0.95);
  box-shadow: 0 18px 50px rgba(124,92,255,0.18), 0 8px 30px rgba(0,230,255,0.12);
}

/* bright neon outline on hover using ::after */
.card:hover::after {
  content: "";
  position: absolute;
  left: -4px; right: -4px; top: -4px; bottom: -4px;
  border-radius: 18px;
  background: linear-gradient(90deg, rgba(0,230,255,0.18), rgba(124,92,255,0.18));
  filter: blur(10px);
  z-index: -3;
  pointer-events: none;
}

/* Thumbnail */
.thumb {
  width:100%;
  height:220px;
  object-fit:cover;
  object-position:center center;
  border-radius:10px;
  margin-bottom:12px;
  display:block;
  background:#f7f9fb;
  border: 6px solid rgba(255,255,255,0.6);
  box-shadow: inset 0 1px 0 rgba(255,255,255,0.6);
}

/* Text */
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

/* Buttons */
.action {
  display:inline-block;
  padding:8px 12px;
  border-radius:10px;
  font-weight:700;
  font-size:13px;
  color: #fff;
  background: linear-gradient(90deg, var(--neon-1), var(--neon-2));
  text-decoration:none;
  box-shadow: 0 10px 28px rgba(124,92,255,0.12);
}

/* Sidebar footer / note */
.sidebar-note {
  margin-top: 18px;
  padding-top: 12px;
  border-top: 1px dashed rgba(0,0,0,0.06);
  color: var(--muted);
  font-size:13px;
  line-height:1.35;
  white-space: pre-line;
}

/* small layout tweaks */
.stColumns > div { padding-left:8px; padding-right:8px; }
.empty-state { text-align:center; padding:40px 0; color:var(--muted); }
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

    # Add the requested signature/note at the end of filters
    st.markdown("---")
    st.markdown('<div class="sidebar-note">Шаблінський 2 курс ІПЗ\nверсія програми 0.01</div>', unsafe_allow_html=True)

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

    # render rows (4 columns)
    for i in range(0, len(page_df), 4):
        cols = st.columns(4, gap="large")
        for j, (_, row) in enumerate(page_df.iloc[i:i+4].iterrows()):
            col = cols[j]
            # thumbnail safe source
            thumb = str(row.get('thumbnail', '') or "").strip()
            if thumb:
                thumb_src = thumb.replace('[:]//', '://')
            else:
                thumb_src = "https://via.placeholder.com/600x600?text=No+image"

            brand = row.get('brand', '')
            model = row.get('model', '')
            price = row.get('price_usd', '—')
            screen = row.get('screen_size_in', '—')
            display_type = row.get('display_type', '—')
            cpu = row.get('cpu', '—')
            code = row.get('code', '') or row.get('sku', '') or ''

            img_html = f'''
            <img src="{thumb_src}" class="thumb" alt="{brand} {model}" loading="lazy"
                 onerror="this.onerror=null;this.src='https://via.placeholder.com/600x600?text=No+image';" />
            '''
            # Removed inactive "Переглянути" action from card_html
            card_html = f'''
            <div class="card" role="article">
              {img_html}
              <div class="title">{brand} {model}</div>
              <div class="meta">{screen}" • {display_type} • {cpu}</div>
              <div class="small-note">Код: {code}</div>
              <div style="display:flex;justify-content:space-between;align-items:center;margin-top:10px;">
                <div class="price">${price}</div>
              </div>
            </div>
            '''
            col.markdown(card_html, unsafe_allow_html=True)

            # server-side details toggle
            key = f"toggle_{start_idx + i + j}"
            show = col.checkbox("🔍 Детальніше", key=key)
            if show:
                product_url = row.get('url', '') or ""
                if isinstance(product_url, str) and product_url.strip():
                    url_html = f'<b>🔗 <a href="{product_url}" target="_blank" rel="noopener noreferrer">Сторінка товару</a></b>'
                else:
                    url_html = '<b>🔗 Немає посилання</b>'

                col.markdown(f"""
                <div style="border:1.5px solid #00e6ff; border-radius:10px; padding:12px; margin-top:8px; background: #ffffffcc;">
                    <b>💰 Ціна:</b> ${price:.0f}<br>
                    <b>📺 Екран:</b> {screen}" {display_type}<br>
                    <b>🧠 Процесор:</b> {cpu}<br>
                    <b>🔋 Батарея:</b> {row.get('battery_wh','—')} Wh<br>
                    <b>🧮 RAM:</b> {row.get('ram_gb','—')} GB, SSD: {row.get('storage_gb','—')} GB<br>
                    <b>📅 Рік:</b> {row.get('release_year','—')}<br>
                    {url_html}
                </div>
                """, unsafe_allow_html=True)

with tab2:
    brand_share = compute_brand_share(filtered)
    fig1 = px.pie(brand_share, names='brand', values='count', title='Розподіл за брендами', template='plotly_white')
    st.plotly_chart(fig1, use_container_width=True)

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
            st.plotly_chart(fig2, use_container_width=True)
    except Exception:
        logger.exception("Error in trends")
        st.error("Не вдалося побудувати тренди. Подробиці в логах.")

# Export
st.markdown("### 📤 Експорт результатів")
st.download_button(
    label="⬇️ Завантажити CSV",
    data=filtered.to_csv(index=False).encode('utf-8'),
    file_name="filtered_laptops.csv",
    mime="text/csv"
)
