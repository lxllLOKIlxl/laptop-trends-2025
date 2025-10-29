import pandas as pd
import numpy as np
import logging
import re
from typing import List

logger = logging.getLogger(__name__)

# Якщо у репо є папка images/ з картинками — RAW_BASE формує прямі raw URL для імен файлів
RAW_BASE = "https://raw.githubusercontent.com/lxllLOKIlxl/laptop-trends-2025/main/images/"

def _split_image_list(val: str) -> List[str]:
    """Розбиває рядок image_urls (розділювач ;) на список, очищає пробіли."""
    if not isinstance(val, str) or val.strip() == "":
        return []
    parts = [p.strip() for p in val.split(';') if p.strip()]
    return parts

def _to_raw_github_url(url: str) -> str:
    """Якщо це github.com/.../blob/... → перетворити на raw.githubusercontent.com/...,
       якщо це ім'я файлу — приписати RAW_BASE, якщо це вже валідний http(s) — повернути як є.
       Повертає '' якщо не валідне.
    """
    if not isinstance(url, str) or url.strip() == "":
        return ""
    url = url.strip()
    # Якщо вже raw
    if url.startswith("https://raw.githubusercontent.com/"):
        return url
    # blob → raw (припускаємо гілку main)
    m = re.match(r'^https?://github\.com/([^/]+/[^/]+)/(?:blob|raw)/(.+)$', url)
    if m:
        repo_part = m.group(1)
        path = m.group(2)
        return f"https://raw.githubusercontent.com/{repo_part}/main/{path}"
    # якщо повний http(s) інший — повертаємо як є
    if url.startswith("http://") or url.startswith("https://"):
        return url
    # якщо це просто ім'я файлу (наприклад envy15.png) — припишемо до RAW_BASE
    if re.match(r'^[\w\-\./]+\.(png|jpg|jpeg|gif)$', url, flags=re.IGNORECASE):
        filename = url
        return RAW_BASE + filename
    return ""

def load_data(path: str) -> pd.DataFrame:
    """Завантаження CSV без звернення до Streamlit у модулі — повертаємо порожній DataFrame при помилці."""
    try:
        df = pd.read_csv(path)
    except Exception:
        logger.exception("Error reading CSV")
        return pd.DataFrame()

    # Нормалізація та приведення типів
    try:
        df['brand'] = df.get('brand', pd.Series(dtype='object')).astype(str).str.strip().str.title()
    except Exception:
        df['brand'] = df.get('brand', pd.Series(dtype='object')).astype(str)

    df['price_usd'] = pd.to_numeric(df.get('price_usd', pd.Series(np.nan)), errors='coerce')
    if df['price_usd'].isna().all():
        return pd.DataFrame()
    df['price_usd'] = df['price_usd'].fillna(df['price_usd'].median())

    df['screen_size_in'] = pd.to_numeric(df.get('screen_size_in', pd.Series(np.nan)), errors='coerce').fillna(13.3)

    if 'battery_wh' in df.columns:
        df['battery_wh'] = pd.to_numeric(df['battery_wh'], errors='coerce').fillna(df['battery_wh'].median())
    else:
        df['battery_wh'] = 50.0

    df['release_year'] = pd.to_numeric(df.get('release_year', pd.Series(np.nan)), errors='coerce').fillna(2025).astype(int)

    # Підтримка колонок image_url або image_urls (з розділенням ;)
    df['image_urls_raw'] = df.get('image_url', df.get('image_urls', '')).fillna('').astype(str)
    df['image_list'] = df['image_urls_raw'].apply(_split_image_list)
    # Перша картинка як thumbnail або порожній рядок
    df['thumbnail'] = df['image_list'].apply(lambda lst: lst[0] if lst else '')

    # Нормалізація thumbnail → повний raw URL або ''
    df['thumbnail'] = df['thumbnail'].apply(lambda v: _to_raw_github_url(v))

    # Якщо thumbnail порожній, але є окремі стовпці з ім'ям файлу, підхопимо їх
    for alt_col in ['image_path', 'image']:
        if alt_col in df.columns:
            df['thumbnail'] = df.apply(lambda row: _to_raw_github_url(row.get('thumbnail')) or _to_raw_github_url(str(row.get(alt_col,''))), axis=1)

    # Булеві ознаки
    df['cpu'] = df.get('cpu', pd.Series(dtype='object')).astype(str)
    df['display_type'] = df.get('display_type', pd.Series(dtype='object')).astype(str)
    df['is_ai_cpu'] = df['cpu'].str.contains('Ultra|AI|Ryzen AI', case=False, na=False)
    df['is_oled'] = df['display_type'].str.contains('OLED', case=False, na=False)

    return df

def filter_data(df: pd.DataFrame, brands=None, price_range=None, screen_range=None, ai_cpu="Усі") -> pd.DataFrame:
    q = df.copy()
    if brands:
        q = q[q['brand'].isin(brands)]
    if price_range:
        q = q[(q['price_usd'] >= price_range[0]) & (q['price_usd'] <= price_range[1])]
    if screen_range:
        q = q[(q['screen_size_in'] >= screen_range[0]) & (q['screen_size_in'] <= screen_range[1])]
    if ai_cpu == "Із AI":
        q = q[q['is_ai_cpu']]
    elif ai_cpu == "Без AI":
        q = q[~q['is_ai_cpu']]
    return q

def compute_brand_share(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return pd.DataFrame(columns=['brand','count'])
    s = df['brand'].value_counts().reset_index()
    s.columns = ['brand', 'count']
    return s

def compute_trends(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return pd.DataFrame(columns=['year','metric','value'])
    price_trend = df.groupby('release_year')['price_usd'].mean().reset_index()
    price_trend['metric'] = 'Середня ціна'
    price_trend.rename(columns={'release_year': 'year', 'price_usd': 'value'}, inplace=True)

    battery_trend = df.groupby('release_year')['battery_wh'].mean().reset_index()
    battery_trend['metric'] = 'Середня автономність'
    battery_trend.rename(columns={'release_year': 'year', 'battery_wh': 'value'}, inplace=True)

    oled_trend = df.groupby('release_year')['is_oled'].mean().reset_index()
    oled_trend['metric'] = 'Частка OLED'
    oled_trend.rename(columns={'release_year': 'year', 'is_oled': 'value'}, inplace=True)

    long = pd.concat([price_trend, battery_trend, oled_trend], ignore_index=True)
    return long
