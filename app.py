import math
import logging
import streamlit as st
import pandas as pd
import plotly.express as px
from src.data_processing import load_data, filter_data, compute_brand_share, compute_trends

logger = logging.getLogger(__name__)
st.set_page_config(page_title="Laptop Trends 2025", layout="wide", initial_sidebar_state="expanded")

# СSS: сучасний інтерфейс, неонові обводки, шрифт, shimmer заголовка, стильні кнопки
CARD_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;800&display=swap');

:root{
  --bg: #f4f7fb;
  --panel: #ffffff;
  --muted: #6b7280;
  --neon: #00e6ff;
  --neon-2: #7c5cff;
  --accent: linear-gradient(90deg, #00e6ff 0%, #7c5cff 100%);
  --card-border: rgba(0,230,255,0.12);
  --card-shadow: 0 6px 30px rgba(15,23,42,0.06);
  --glass: rgba(255,255,255,0.8);
}

html, body, [data-testid="stAppViewContainer"] > .main {
  background: var(--bg) !important;
  font-family: 'Inter', system-ui, -apple-system, "Segoe UI", Roboto, "Helvetica Neue", Arial !important;
  color: #0f172a;
}

/* Центруємо основний контейнер схоже на магазин */
.block-container {
  max-width: 1200px !important;
  margin-left: auto !important;
  margin-right: auto !important;
  padding-top: 18px !important;
  padding-bottom: 40px !important;
}

/* Shimmer заголовка */
.app-title {
  display:flex;
  align-items:center;
  gap:16px;
  margin-bottom:14px;
}
.app-title h1 {
  margin:0;
  font-size:30px;
  font-weight:800;
  letter-spacing:-0.4px;
  background: linear-gradient(90deg, #111827 0%, #111827 30%, #00e6ff 60%, #7c5cff 100%);
  -webkit-background-clip: text;
  background-clip: text;
  color: transparent;
  position: relative;
  overflow: hidden;
}
/* subtle shimmer animation */
@keyframes shimmer {
  0% { background-position: -400px 0; }
  100% { background-position: 400px 0; }
}
.app-title h1.shimmer {
  background-image: linear-gradient(
    to right,
    rgba(255,255,255,0) 0%,
    rgba(255,255,255,0.08) 40%,
    rgba(255,255,255,0) 80%
  ), linear-gradient(90deg, #00e6ff, #7c5cff);
  background-size: 800px 100%;
  animation: shimmer 3s linear infinite;
  -webkit-background-clip: text;
  background-clip: text;
  color: transparent;
}

/* Card */
.card {
  border-radius:12px;
  background: var(--panel);
  border: 1.5px solid var(--card-border);
  box-shadow: var(--card-shadow);
  padding:12px;
  overflow:hidden;
  display:flex;
  flex-direction:column;
  height:100%;
  transition: transform .18s ease, box-shadow .18s ease, border-color .18s ease;
  position: relative;
}
/* neon glow on hover */
.card:hover {
  transform: translateY(-6px);
  border-color: rgba(124,92,255,0.7);
  box-shadow: 0 12px 40px rgba(124,92,255,0.12), 0 6px 18px rgba(0,230,255,0.06);
}
/* subtle neon outline pseudo-element */
.card::after {
  content: "";
  position: absolute;
  left: -1.5px; right: -1.5px; top: -1.5px; bottom: -1.5px;
  border-radius: 14px;
  pointer-events: none;
  background: linear-gradient(90deg, rgba(0,230,255,0.06), rgba(124,92,255,0.04));
  z-index: 0;
}

/* Image / thumb: fixed aspect and center crop */
.card .thumb {
  width:100%;
  aspect-ratio: 1 / 1;
  height: 260px;
  object-fit: cover;
  object-position: center center;
  display:block;
  margin-bottom:12px;
  border-radius:8px;
  background:#f7f9fb;
  z-index: 1;
  border: 6px solid rgba(255,255,255,0.6);
  box-shadow: inset 0 1px 0 rgba(255,255,255,0.6);
}

/* Title, meta, price */
.card .title { font-weight:700; font-size:15px; margin-bottom:6px; color:#0f172a; z-index:1; }
.card .meta { font-size:12px; color:var(--muted); margin-bottom:8px; z-index:1; }
.card .price { color: #ff3b30; font-weight:800; font-size:16px; margin-top:auto; z-index:1; }

/* modern button (also try to style Streamlit buttons) */
.card .action {
  display:inline-block;
  padding:8px 12px;
  border-radius:10px;
  font-weight:700;
  font-size:13px;
  color: #fff;
  background: linear-gradient(90deg, #00e6ff, #7c5cff);
  text-decoration:none;
  transition: transform .12s ease, box-shadow .12s ease;
  box-shadow: 0 8px 20px rgba(124,92,255,0.12);
}
.card .action:hover { transform: translateY(-3px); box-shadow: 0 18px 40px rgba(124,92,255,0.18); }

/* adjust Streamlit native buttons */
.stButton>button, .stDownloadButton>button {
  font-family: 'Inter', system-ui, -apple-system, "Segoe UI", Roboto, "Helvetica Neue", Arial !important;
  border-radius:10px !important;
  padding:8px 12px !important;
  font-weight:700 !important;
  color:#fff !important;
  background: linear-gradient(90deg, #00e6ff, #7c5cff) !important;
  border: none !important;
  box-shadow: 0 8px 20px rgba(124,92,255,0.12) !important;
  transition: transform .12s ease !important;
}
.stButton>button:hover, .stDownloadButton>button:hover { transform: translateY(-3px) !important; }

/* small notes and layout tweaks */
.small-note { font-size:11px; color:var(--muted); z-index:1; }
.stColumns > div { padding-left:8px; padding-right:8px; }
.empty-state { text-align:center; padding:40px 0; color:var(--muted); }
.sidebar .small-muted { color: var(--muted); }
</style>
"""

def sanitize_text_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Екранізуємо 'http' в текстових колонках, щоб уникнути автолінкування."""
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

# Inject CSS
st.markdown(CARD_CSS, unsafe_allow_html=True)

# Header with shimmer
st.markdown("""
<div class="block-container">
  <div class="app-title">
    <h1 class="shimmer">💻 Laptop Trends 2025</h1>
  </div>
  <div class="small-muted">Інтерактивний аналіз моделей: ціни, автономність, OLED, AI‑процесори</div>
</div>
""", unsafe_allow_html=True)

# Data
DATA_PATH = "data/sample_laptops.csv"
df = load_data(DATA_PATH)
if df.empty:
    st.error("❌ Дані не завантажені або CSV-файл порожній.")
    st.stop()

# Sidebar filters
with st.sidebar:
    st.header("🔍 Фільтри")
    try:
        brands = st.multiselect("Бренд", options=sorted(df['brand'].unique()), default=sorted(df['brand'].unique())[:5])
    except Exception:
        brands = st.multiselect("Бренд", options=[], default=[])
    price_min, price_max = st.slider("Ціна (USD)", int(df['price_usd'].min()), int(df['price_usd'].max()), (int(df['price_usd'].min()), int(df['price_usd'].max())))
    screen_min, screen_max = st.slider("Діагональ екрану (in)", float(df['screen_size_in'].min()), float(df['screen_size_in'].max()), (float(df['screen_size_in'].min()), float(df['screen_size_in'].max())))
    ai_cpu = st.selectbox("AI CPU", options=["Усі", "Із AI", "Без AI"])
    max_show = st.number_input("Кількість моделей на сторінці", min_value=3, max_value=60, value=12)
    st.markdown("---")
    st.markdown("Шаблінський Студент 2 курсу")  # твій підпис

# Filter
try:
    filtered = filter_data(df, brands=brands, price_range=(price_min, price_max), screen_range=(screen_min, screen_max), ai_cpu=ai_cpu)
except Exception:
    logger.exception("Filter error")
    st.error("Помилка під час фільтрації даних. Перевірте структуру CSV.")
    st.stop()

# Metrics
st.markdown('<div class="block-container">', unsafe_allow_html=True)
st.markdown("### 📊 Загальні метрики")
c1, c2, c3 = st.columns(3)
c1.metric("Моделей (відфільтровано)", len(filtered))
c2.metric("Середня ціна (USD)", f"{filtered['price_usd'].mean():.0f}" if len(filtered) else "—")
c3.metric("Середня автономність (Wh)", f"{filtered['battery_wh'].mean():.0f}" if len(filtered) else "—")

# Tabs
tab1, tab2, tab3 = st.tabs(["🖼️ Каталог", "🥧 Частка брендів", "📈 Тренди"])

with tab1:
    try:
        display_df = filtered.sort_values(by='price_usd').reset_index(drop=True)
        if 'url' in display_df.columns:
            display_df = display_df.drop(columns=['url'])
        display_df = sanitize_text_columns(display_df)

        total = len(display_df)
        page_size = int(max_show)
        total_pages = max(1, math.ceil(total / page_size))

        if 'page' not in st.session_state:
            st.session_state.page = 1

        # simple pager
        pc1, pc2, pc3, pc4 = st.columns([1,3,1,3])
        with pc1:
            if st.button("⬅️ Prev"):
                if st.session_state.page > 1:
                    st.session_state.page -= 1
        with pc2:
            st.markdown(f"**Сторінка {st.session_state.page} / {total_pages}**")
        with pc3:
            if st.button("Next ➡️"):
                if st.session_state.page < total_pages:
                    st.session_state.page += 1
        with pc4:
            jump = st.number_input("Перейти на стор.", min_value=1, max_value=total_pages, value=st.session_state.page, step=1, key="jump_page")
            if jump != st.session_state.page:
                st.session_state.page = int(jump)

        start = (st.session_state.page - 1) * page_size
        end = start + page_size
        rows = display_df.iloc[start:end]

        if rows.empty:
            st.markdown('<div class="empty-state">Немає моделей для відображення.</div>', unsafe_allow_html=True)
        else:
            cols_per_row = 4
            for i in range(0, len(rows), cols_per_row):
                cols = st.columns(cols_per_row, gap="large")
                for j, (_, row) in enumerate(rows.iloc[i:i+cols_per_row].iterrows()):
                    col = cols[j]
                    thumb = row.get('thumbnail', '')
                    if thumb and isinstance(thumb, str) and thumb.strip():
                        thumb_url = thumb.replace('[:]//', '://')
                    else:
                        thumb_url = "https://via.placeholder.com/600x600?text=No+image"

                    # inline img to force styles and fallback
                    img_html = f'''
                    <img class="thumb" src="{thumb_url}" alt="{row.get('brand','')} {row.get('model','')}"
                         style="display:block; width:100%; height:260px; object-fit:cover; object-position:center center; border-radius:8px;"
                         onerror="this.onerror=null;this.src='https://via.placeholder.com/600x600?text=No+image';">
                    '''

                    brand = row.get('brand', '')
                    model = row.get('model', '')
                    price = row.get('price_usd', '—')
                    screen = row.get('screen_size_in', '—')
                    display_type = row.get('display_type', '—')
                    battery = row.get('battery_wh', '—')
                    code = row.get('code', '') or row.get('sku', '') or ''

                    # card HTML
                    card_html = f'''
                    <div class="card" role="article">
                      {img_html}
                      <div class="title">{brand} {model}</div>
                      <div class="meta">{screen}" • {display_type} • {battery} Wh</div>
                      <div class="small-note">Код: {code}</div>
                      <div style="display:flex;justify-content:space-between;align-items:center;margin-top:10px;">
                        <div class="price">${price}</div>
                        <a class="action" href="#" onclick="window.alert('Переглянути: {brand} {model}');return false;">Переглянути</a>
                      </div>
                    </div>
                    '''
                    col.markdown(card_html, unsafe_allow_html=True)

                    # Keep Streamlit "Детальніше" for real action (server-side)
                    if col.button("Детальніше", key=f"det_{start+i+j}"):
                        st.info(f"Деталі: {brand} {model} — Ціна: ${price}; Екран: {screen}\" • {display_type}; Батарея: {battery}Wh")
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

st.markdown('</div>', unsafe_allow_html=True)

# Export CSV
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
