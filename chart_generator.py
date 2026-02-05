# ============================================================
# chart_generator.py — Grafik Üretim Engine
# ============================================================
# Bu modül:
# 1) Her hisse için çok katmanlı teknik analiz grafiği üretir
# 2) Fiyat grafiği + RSI + MACD → 3 satırlı dashboard
# 3) Fibonacci seviyeler overlay olarak gösterilir
# 4) Bollinger Bands gösterilir
# 5) PNG olarak kaydedilir (mail'e eklenir)
# ============================================================

import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import matplotlib.patches as mpatches
import numpy as np
import pandas as pd
from datetime import datetime
import os

# Karanlık tema için matplotlib
plt.rcParams.update({
    'figure.facecolor': '#1a1a2e',
    'axes.facecolor': '#16213e',
    'axes.edgecolor': '#0f3460',
    'text.color': '#e2e8f0',
    'xtick.color': '#94a3b8',
    'ytick.color': '#94a3b8',
    'grid.color': '#1e293b',
    'axes.grid': True,
    'grid.alpha': 0.4,
    'font.size': 9,
})

# Renkler
COLOR_PRICE = '#00d4aa'
COLOR_SMA_SHORT = '#f59e0b'
COLOR_SMA_LONG = '#8b5cf6'
COLOR_BOLLINGER_UPPER = '#e11d48'
COLOR_BOLLINGER_LOWER = '#06b6d4'
COLOR_BOLLINGER_FILL = '#e11d4810'
COLOR_MACD_LINE = '#00d4aa'
COLOR_SIGNAL_LINE = '#f59e0b'
COLOR_HIST_POS = '#10b981'
COLOR_HIST_NEG = '#ef4444'
COLOR_RSI = '#a78bfa'
COLOR_FIB = '#fbbf24'
COLOR_SUPPORT = '#10b981'
COLOR_RESISTANCE = '#ef4444'


def create_stock_chart(ticker: str, df: pd.DataFrame, analysis: dict,
                       save_path: str = None) -> str:
    """
    Bir hisse için tam teknik analiz grafiği üretir.

    Layout:
    ┌─────────────────────────────────────┐
    │  Fiyat + Bollinger + SMA + Fibonacci │  (70% yükseklik)
    ├─────────────────────────────────────┤
    │  MACD + Signal + Histogram           │  (15%)
    ├─────────────────────────────────────┤
    │  RSI                                 │  (15%)
    └─────────────────────────────────────┘
    """
    if df.empty:
        return ""

    # Son 90 gün göster
    df_plot = df.tail(90).copy()
    close = df_plot["Close"].squeeze()
    high = df_plot["High"].squeeze()
    low = df_plot["Low"].squeeze()
    dates = df_plot.index

    fig, (ax1, ax2, ax3) = plt.subplots(
        3, 1, figsize=(14, 10),
        gridspec_kw={'height_ratios': [4, 1.5, 1.5]},
        sharex=True
    )

    # ─── AX1: FIYAT GRAFİĞİ ─────────────────────────────────

    # Fiyat çizgisi
    ax1.plot(dates, close, color=COLOR_PRICE, linewidth=1.8, label='Kapanış Fiyatı', zorder=3)

    # Bollinger Bands
    period = 20
    sma_bb = close.rolling(window=period).mean()
    std = close.rolling(window=period).std()
    upper = sma_bb + (std * 2)
    lower = sma_bb - (std * 2)

    ax1.plot(dates, upper, color=COLOR_BOLLINGER_UPPER, linewidth=0.8, alpha=0.7, linestyle='--', label='Bollinger Üst')
    ax1.plot(dates, lower, color=COLOR_BOLLINGER_LOWER, linewidth=0.8, alpha=0.7, linestyle='--', label='Bollinger Alt')
    ax1.fill_between(dates, upper, lower, color='#e11d48', alpha=0.05)

    # SMA 20 ve 50
    sma20 = close.rolling(window=20).mean()
    sma50 = close.rolling(window=50).mean()
    ax1.plot(dates, sma20, color=COLOR_SMA_SHORT, linewidth=1.0, alpha=0.8, label='SMA 20')
    ax1.plot(dates, sma50, color=COLOR_SMA_LONG, linewidth=1.0, alpha=0.8, label='SMA 50')

    # Fibonacci Seviyeler (Yatay çizgiler)
    fib = analysis.get("fibonacci", {})
    fib_levels_to_draw = [
        ("fib_0.236", "Fib 0.236", COLOR_FIB),
        ("fib_0.382", "Fib 0.382", COLOR_FIB),
        ("fib_0.500", "Fib 0.500", COLOR_FIB),
        ("fib_0.618", "Fib 0.618", COLOR_FIB),
        ("fib_0.786", "Fib 0.786", COLOR_FIB),
    ]

    current_price = float(close.iloc[-1])

    for fib_key, fib_label, color in fib_levels_to_draw:
        level = fib.get(fib_key)
        if level:
            # Fiyata yakın Fibonacci seviyelerini daha belirgin yap
            price_diff_pct = abs(level - current_price) / current_price * 100
            if price_diff_pct < 8:  # %8 yakın
                ax1.axhline(y=level, color=color, linewidth=1.2, alpha=0.8,
                           linestyle='-', zorder=2)
                ax1.text(dates[-1], level, f' {fib_label}: {level}',
                        color=color, fontsize=7.5, va='center', alpha=0.9)
            else:
                ax1.axhline(y=level, color=color, linewidth=0.5, alpha=0.3,
                           linestyle=':', zorder=1)

    # Mevcut fiyat markers
    ax1.scatter([dates[-1]], [current_price], color='white', s=60, zorder=5, edgecolors=COLOR_PRICE, linewidths=2)
    ax1.annotate(f'  Şimdi: {current_price:.2f}',
                xy=(dates[-1], current_price),
                color='white', fontsize=8.5, fontweight='bold', va='center')

    # Title ve legend
    score = analysis.get("score", 0)
    score_color = COLOR_HIST_POS if score >= 55 else COLOR_HIST_NEG if score <= 45 else '#f59e0b'

    ax1.set_title(f'{ticker}  |  Teknik Skor: {score}/100  |  Analiz: {datetime.now().strftime("%d %b %Y")}',
                 color='white', fontsize=13, fontweight='bold', pad=12)

    ax1.legend(loc='upper left', fontsize=7, frameon=True, facecolor='#1e293b',
              edgecolor='#334155', labelcolor='white')
    ax1.set_ylabel('Fiyat', color='#94a3b8')

    # Score badge
    badge = mpatches.FancyBboxPatch((0.78, 0.85), 0.20, 0.12,
                                     boxstyle="round,pad=0.02",
                                     facecolor='#1e293b', edgecolor=score_color,
                                     linewidth=2, transform=ax1.transAxes)
    ax1.add_patch(badge)
    ax1.text(0.885, 0.915, f'SKOR\n{score}/100',
            transform=ax1.transAxes, color=score_color,
            fontsize=9, fontweight='bold', ha='center', va='center')

    # ─── AX2: MACD ───────────────────────────────────────────

    ema_fast = close.ewm(span=12, adjust=False).mean()
    ema_slow = close.ewm(span=26, adjust=False).mean()
    macd_line = ema_fast - ema_slow
    signal_line = macd_line.ewm(span=9, adjust=False).mean()
    histogram = macd_line - signal_line

    ax2.plot(dates, macd_line, color=COLOR_MACD_LINE, linewidth=1.2, label='MACD')
    ax2.plot(dates, signal_line, color=COLOR_SIGNAL_LINE, linewidth=1.0, label='Signal')

    # Histogram bar chart
    hist_colors = [COLOR_HIST_POS if val >= 0 else COLOR_HIST_NEG for val in histogram]
    ax2.bar(dates, histogram, color=hist_colors, alpha=0.6, width=1, label='Histogram')

    ax2.axhline(y=0, color='#475569', linewidth=0.8)
    ax2.set_ylabel('MACD', color='#94a3b8')
    ax2.legend(loc='upper left', fontsize=7, frameon=True, facecolor='#1e293b',
              edgecolor='#334155', labelcolor='white')

    # ─── AX3: RSI ─────────────────────────────────────────────

    delta = close.diff()
    gain = delta.where(delta > 0, 0.0)
    loss = (-delta).where(delta < 0, 0.0)
    avg_gain = gain.rolling(window=14).mean()
    avg_loss = loss.rolling(window=14).mean()
    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))

    ax3.plot(dates, rsi, color=COLOR_RSI, linewidth=1.2, label='RSI 14')

    # Oversold / Overbought bölgeleri
    ax3.axhline(y=70, color=COLOR_RESISTANCE, linewidth=0.8, alpha=0.6, linestyle='--')
    ax3.axhline(y=30, color=COLOR_SUPPORT, linewidth=0.8, alpha=0.6, linestyle='--')
    ax3.fill_between(dates, 70, 100, color='#ef4444', alpha=0.06)
    ax3.fill_between(dates, 0, 30, color='#10b981', alpha=0.06)

    ax3.text(dates[0], 72, 'Overbought', color=COLOR_RESISTANCE, fontsize=7, alpha=0.8)
    ax3.text(dates[0], 18, 'Oversold', color=COLOR_SUPPORT, fontsize=7, alpha=0.8)

    current_rsi = float(rsi.iloc[-1]) if not pd.isna(rsi.iloc[-1]) else 50
    ax3.scatter([dates[-1]], [current_rsi], color='white', s=40, zorder=5,
               edgecolors=COLOR_RSI, linewidths=2)

    ax3.set_ylabel('RSI', color='#94a3b8')
    ax3.set_ylim(0, 100)
    ax3.legend(loc='upper left', fontsize=7, frameon=True, facecolor='#1e293b',
              edgecolor='#334155', labelcolor='white')

    # ─── X-Axis Format ────────────────────────────────────────

    ax3.xaxis.set_major_formatter(mdates.DateFormatter('%d %b'))
    ax3.xaxis.set_major_locator(mdates.WeekdayLocator(interval=2))
    plt.setp(ax3.xaxis.get_majorticklabels(), rotation=45, ha='right')

    # ─── Sinyal Summary Box ──────────────────────────────────

    signals = analysis.get("signals", [])
    signal_text = "\n".join(signals[:5])

    # Alt sağda signal summary ekle
    props = dict(boxstyle='round,pad=0.5', facecolor='#1e293b', edgecolor='#334155', alpha=0.9)
    ax1.text(0.02, 0.02, signal_text,
            transform=ax1.transAxes, fontsize=7,
            verticalalignment='bottom', bbox=props, color='#cbd5e1')

    plt.tight_layout(pad=1.5)

    # Kaydet
    if save_path is None:
        os.makedirs("charts", exist_ok=True)
        save_path = f"charts/{ticker.replace('.', '_')}_{datetime.now().strftime('%Y%m%d')}.png"

    plt.savefig(save_path, dpi=150, bbox_inches='tight',
               facecolor='#1a1a2e', edgecolor='none')
    plt.close()

    print(f"  📊 Grafik kaydedildi: {save_path}")
    return save_path


def generate_all_charts(top_stocks: list) -> list:
    """
    En iyi hisselerin grafiklerini üretir.
    top_stocks: [{"ticker": ..., "dataframe": ..., "analysis": ...}, ...]
    Döndürür: kaydedilen dosya yolları listesi
    """
    chart_paths = []

    for stock in top_stocks:
        ticker = stock.get("ticker", "")
        df = stock.get("dataframe", None)

        if df is None or df.empty:
            continue

        path = create_stock_chart(ticker, df, stock)
        if path:
            chart_paths.append(path)

    return chart_paths


if __name__ == "__main__":
    # Test: Bir hisse için grafik üret
    import sys
    sys.path.insert(0, '.')
    from technical_analyzer import analyze_stock

    ticker = "THYAO.IS"
    print(f"📊 {ticker} için test grafik üretiliyor...")

    result = analyze_stock(ticker)
    if "dataframe" in result and not result["dataframe"].empty:
        path = create_stock_chart(ticker, result["dataframe"], result)
        print(f"\n✅ Grafik oluşturuldu: {path}")
    else:
        print("❌ Veri bulunamadı.")
