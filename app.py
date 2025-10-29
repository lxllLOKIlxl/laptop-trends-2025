import math
import logging
import streamlit as st
import pandas as pd
import plotly.express as px
from src.data_processing import load_data, filter_data, compute_brand_share, compute_trends

logger = logging.getLogger(__name__)
st.set_page_config(page_title="Інтерактивний вебдодаток для аналізу трендів ноутбуків 2025 року", layout="wide", initial_sidebar_state="expanded")

# СSS для стильних карток і загального вигляду
CARD_CSS = """
<style>
:root{
  --page-bg: #f5f7fb;
  --container-bg: #ffffff;
  --card-border: #9fd7ff;   /* підсилена блакитна рамка */
  --card-shadow: 0 8px 30px rgba(18,36,63,0.08);
  --accent: #0b6bff;
  --price-color: #d8232a;
  --muted: #6b7280;
}
body {
  background: var(--page-bg);
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial;
  color: #111827;
}

/* Центруємо основний блок і даємо відступи */
.block-container {
  max-width: 1200px !important;
  margin-left: auto !important;
  margin-right: auto !important;
  padding-top: 18px !important;
  padding-bottom: 40px !important;
}

/* Заголовок */
.app-title { display:flex; align-items:center; gap:16px; margin-bottom:14px; }
.app-title h1 { margin:0; font-size:28px; font-weight:700; }
.small-muted { color:var(--muted); font-size:13px; }

/* Карта (card) */
.card {
  border-radius:10px;
  background: var(--container-bg);
  border: 2px solid var(--card-border); /* товща, чіткіша рамка */
  box-shadow: var(--card-shadow);
  padding:12px;
  overflow:hidden;
  display:flex;
  flex-direction:column;
  height:100%;
}

/* Квадратне превʼю: гарантія квадрату та обрізка без розтягування */
.card .thumb {
  width:100%;
  aspect-ratio: 1 / 1;    /* квадрат */
  object-fit: cover;      /* обрізає, не розтягує */
  border-radius:6px;
  display:block;
  margin-bottom:10px;
  background:#f7f9fb;
}

/* Текстові стилі картки */
.card .title { font-weight:700; font-size:14px; margin-bottom:6px; color:#111827; }
.card .meta { font-size:12px; color:var(--muted); margin-bottom:8px; }
.card .price { color: var(--price-color); font-weight:800; font-size:16px; margin-top:auto; }
.card .card-footer { display:flex; align-items:center; justify-content:space-between; gap:8px; margin-top:10px; }
.small-note { font-size:11px; color:var(--muted); }

/* Кнопки/контейнери внизу сторінки */
.controls-row { display:flex; gap:8px; align-items:center; }

/* Невеликі відступи колонок у Streamlit */
.stColumns > div {
  padding-left:6px;
  padding-right:6px;
}

/* Знижуємо яскравість placeholder'ів щоб не кидались в очі */
img.thumb[alt="No image"] { filter: none; }

</style>
"""

def sanitize_text_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Позбуваємось сирих 'http' у текстових стовпцях щоб уникнути автолінкування в браузері.
       Пропускаємо колонку 'thumbnail' — її ми нормалізували у load_data.
    """
    df = df.copy()
    for col in df.select_dtypes(include=['object', 'string']).columns:
        if col == 'thumbnail':
            continue
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

st.markdown(CARD_CSS, unsafe_allow_html=True)

# Заголовок (в рамках .block-container)
st.markdown("""
<div class="block-container">
  <div class="app-title">
    <div>
      <h1>💻 Інтерактивний вебдодаток для аналізу трендів ноутбуків 2025 року</h1>
      <div class="small-muted">Інтерактивний аналіз моделей: ціни, автономність, OLED, AI‑процесори</div>
    </div>
  </div>
</div>
""", unsafe_allow_html=True)

# Завантаження даних
DATA_PATH = "data/sample_laptops.csv"
df = load_data(DATA_PATH)

if df.empty:
    st.error("❌ Дані не завантажені або CSV-файл порожній. Перевірте data/sample_laptops.csv")
    st.stop()

with st.sidebar:
    st.header("🔍 Фільтри")
    st.write("Фільтруйте та шукайте швидко")
    available_brands = sorted(df['brand'].dropna().unique()) if 'brand' in df.columns else []
    brands = st.multiselect("Бренд", options=available_brands, default=available_brands[:5] if available_brands else [])
    price_min, price_max = st.slider("Ціна (USD)", int(df['price_usd'].min()), int(df['price_usd'].max()), (int(df['price_usd'].min()), int(df['price_usd'].max())))
    screen_min, screen_max = st.slider("Діагональ екрану (in)", float(df['screen_size_in'].min()), float(df['screen_size_in'].max()), (float(df['screen_size_in'].min()), float(df['screen_size_in'].max())))
    ai_cpu = st.selectbox("AI CPU", options=["Усі", "Із AI", "Без AI"])
    max_show = st.number_input("Карток на сторінці", min_value=3, max_value=60, value=12)
    st.markdown("---")
    # Замінив рядок про версію інтерфейсу на потрібний підпис
    st.markdown("Шаблінський Студент 2 курсу")

# Пошук загальний (brand + model)
search_q = st.text_input("🔎 Пошук (бренд або модель)", value="")

try:
    filtered = filter_data(df, brands=brands, price_range=(price_min, price_max), screen_range=(screen_min, screen_max), ai_cpu=ai_cpu)
except Exception:
    logger.exception("Filter error")
    st.error("Помилка під час фільтрації даних. Перевірте структуру CSV.")
    st.stop()

# Швидкий пошук по brand/model
if search_q and isinstance(search_q, str) and search_q.strip():
    q = search_q.strip().lower()
    mask = filtered.apply(lambda row: q in f"{row.get('brand','')} {row.get('model','')}".lower(), axis=1)
    filtered = filtered[mask]

# Метрики (обгорнуті в контейнер — без додаткового 'raw' <div>)
st.markdown('<div class="block-container">', unsafe_allow_html=True)
st.markdown("### 📊 Загальні метрики")
col1, col2, col3 = st.columns(3)
col1.metric("Моделей (відфільтровано)", len(filtered))
col2.metric("Середня ціна (USD)", f"{filtered['price_usd'].mean():.0f}" if len(filtered) else "—")
col3.metric("Середня автономність (Wh)", f"{filtered['battery_wh'].mean():.0f}" if len(filtered) else "—")

# Вкладки
tab1, tab2, tab3 = st.tabs(["🖼️ Каталог", "🥧 Частка брендів", "📈 Тренди"])

with tab1:
    try:
        display_df = filtered.sort_values(by='price_usd').reset_index(drop=True)
        # Приберемо службові колонки з відображення
        for c in ['url', 'image_urls_raw', 'image_list']:
            if c in display_df.columns:
                display_df = display_df.drop(columns=[c])
        display_df = sanitize_text_columns(display_df)

        total_items = len(display_df)
        page_size = int(max_show)
        total_pages = max(1, math.ceil(total_items / page_size))

        # Ініціалізація стану сторінки
        if 'page' not in st.session_state:
            st.session_state.page = 1
        # Контрол панель пагінації
        pager_cols = st.columns([1,2,1,2])
        with pager_cols[0]:
            if st.button("⬅️ Prev"):
                if st.session_state.page > 1:
                    st.session_state.page -= 1
        with pager_cols[1]:
            st.markdown(f"**Сторінка {st.session_state.page} / {total_pages}**")
        with pager_cols[2]:
            if st.button("Next ➡️"):
                if st.session_state.page < total_pages:
                    st.session_state.page += 1
        with pager_cols[3]:
            jump = st.number_input("Перейти на стор.", min_value=1, max_value=total_pages, value=st.session_state.page, step=1, key="jump_page")
            if jump != st.session_state.page:
                st.session_state.page = int(jump)

        start_idx = (st.session_state.page - 1) * page_size
        end_idx = start_idx + page_size
        rows = display_df.iloc[start_idx:end_idx]

        if rows.empty:
            st.markdown('<div class="empty-state">Немає моделей для відображення.</div>', unsafe_allow_html=True)
        else:
            cols_per_row = 4  # більше колонок — менші квадрати
            # Рендер карток
            for i in range(0, len(rows), cols_per_row):
                cols = st.columns(cols_per_row, gap="large")
                for j, (_, row) in enumerate(rows.iloc[i:i+cols_per_row].iterrows()):
                    col = cols[j]
                    thumb = row.get('thumbnail', '')
                    # Якщо thumbnail не валідний — використовуємо квадратний плейсхолдер
                    if thumb and isinstance(thumb, str) and thumb.strip():
                        thumb_url = thumb.replace('[:]//', '://')
                    else:
                        thumb_url = "https://via.placeholder.com/300x300?text=No+image"

                    # Побудова HTML-картки з використанням класу .thumb (стилі в CARD_CSS)
                    brand = row.get('brand', '')
                    model = row.get('model', '')
                    price = row.get('price_usd', '—')
                    screen = row.get('screen_size_in', '—')
                    display_type = row.get('display_type', '—')
                    battery = row.get('battery_wh', '—')
                    code = row.get('code', '') or row.get('sku', '') or ''
                    img_html = f'''
                    <img class="thumb" src="{thumb_url}" alt="{brand} {model}"
                         onerror="this.onerror=null;this.src='https://via.placeholder.com/300x300?text=No+image';">
                    '''
                    # УНИКНУЛИ кнопку "Купити" — виводимо лише інформацію і мету
                    card_html = f'''
                    <div class="card">
                      {img_html}
                      <div class="title">{brand} {model}</div>
                      <div class="meta">{screen}" • {display_type} • {battery} Wh</div>
                      <div class="small-note">Код: {code}</div>
                      <div class="card-footer">
                        <div class="price">${price}</div>
                        <div></div>
                      </div>
                    </div>
                    '''
                    col.markdown(card_html, unsafe_allow_html=True)
                    # Кнопка "Детальніше" під карткою залишилась як Streamlit контрол
                    if col.button("Детальніше", key=f"det_{start_idx+i+j}"):
                        st.info(f'Деталі: {brand} {model} — Ціна: ${price}; Екран: {screen}" • Тип: {display_type}; Батарея: {battery}Wh')
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

# Експорт CSV
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
