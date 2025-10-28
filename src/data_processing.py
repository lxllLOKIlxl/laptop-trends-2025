import pandas as pd
import numpy as np

def load_data(path: str) -> pd.DataFrame:
    df = pd.read_csv(path)
    df['brand'] = df['brand'].str.strip().str.title()
    df['price_usd'] = pd.to_numeric(df['price_usd'], errors='coerce').fillna(df['price_usd'].median())
    df['screen_size_in'] = pd.to_numeric(df['screen_size_in'], errors='coerce').fillna(13.3)
    df['battery_wh'] = pd.to_numeric(df.get('battery_wh', pd.Series(np.nan)), errors='coerce').fillna(df['battery_wh'].median() if 'battery_wh' in df else 50)
    df['release_year'] = pd.to_numeric(df.get('release_year', pd.Series(np.nan)), errors='coerce').fillna(2025).astype(int)
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
    s = df['brand'].value_counts().reset_index()
    s.columns = ['brand', 'count']
    return s

def compute_trends(df: pd.DataFrame) -> pd.DataFrame:
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
