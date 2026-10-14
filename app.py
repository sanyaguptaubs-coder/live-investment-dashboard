import io
import json
import sqlite3
import hashlib
from pathlib import Path
from datetime import date, datetime, timedelta

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
import yfinance as yf

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
)

# ============================================================
# BROKE — PORTFOLIO INTELLIGENCE
# ============================================================

APP_NAME = "BROKE"
INITIAL_CAPITAL = 10_000_000       # ₹1 crore
DEFAULT_TARGET = 17_500_000        # ₹1.75 crore

st.set_page_config(
    page_title="BROKE | Portfolio Intelligence",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ============================================================
# DARK BLACK + GOLD THEME — HIGH CONTRAST WHITE TEXT
# ============================================================

st.markdown("""
<style>
    :root {
        --bg: #0b0b0b;
        --panel: #171717;
        --panel2: #202020;
        --gold: #e1bb70;
        --white: #ffffff;
        --muted: #dedede;
        --border: #47413a;
    }

    html, body, [data-testid="stAppViewContainer"],
    [data-testid="stMain"], .main {
        background-color: var(--bg) !important;
        color: var(--white) !important;
    }

    [data-testid="stHeader"] {
        background-color: #0b0b0b !important;
    }

    [data-testid="stSidebar"] {
        background-color: #171715 !important;
        border-right: 1px solid var(--border);
    }

    [data-testid="stSidebar"] * {
        color: var(--white) !important;
    }

    /* Force readable white text throughout the dashboard */
    html, body, p, span, label, li, small,
    div, strong, em, caption {
        color: var(--white);
    }

    h1, h2, h3, h4, h5, h6 {
        color: var(--gold) !important;
        font-weight: 700 !important;
    }

    [data-testid="stMetricLabel"],
    [data-testid="stMetricValue"],
    [data-testid="stMetricDelta"],
    [data-testid="stMarkdownContainer"],
    [data-testid="stCaptionContainer"] {
        color: var(--white) !important;
    }

    [data-testid="stMetric"] {
        background: var(--panel) !important;
        border: 1px solid var(--border);
        padding: 18px;
        border-radius: 14px;
    }

    [data-testid="stMetricLabel"] p {
        color: #ffffff !important;
        opacity: 1 !important;
    }

    [data-testid="stMetricValue"] {
        color: #ffffff !important;
    }

    [data-testid="stMetricDelta"] {
        font-weight: 600 !important;
    }

    [data-testid="stTextInput"] input,
    [data-testid="stNumberInput"] input,
    [data-testid="stDateInput"] input,
    [data-testid="stSelectbox"] div[data-baseweb="select"],
    [data-testid="stMultiSelect"] div[data-baseweb="select"],
    [data-testid="stTextArea"] textarea {
        background-color: #242424 !important;
        color: #ffffff !important;
        border-color: #75654a !important;
    }

    [data-testid="stSelectbox"] *,
    [data-testid="stMultiSelect"] * {
        color: #ffffff !important;
    }

    [data-baseweb="popover"],
    [data-baseweb="menu"],
    [role="listbox"],
    [role="option"] {
        background-color: #202020 !important;
        color: #ffffff !important;
    }

    [data-testid="stRadio"] label,
    [data-testid="stCheckbox"] label {
        color: #ffffff !important;
    }

    [data-testid="stSidebar"] [data-testid="stRadio"] label {
        color: #ffffff !important;
        font-size: 15px;
    }

    .broke-brand {
        font-size: 34px;
        font-weight: 800;
        color: var(--gold) !important;
        letter-spacing: 2px;
    }

    .broke-subtitle {
        color: #ffffff !important;
        font-size: 15px;
        margin-top: -8px;
    }

    .broke-note {
        background: #1c1c1c;
        color: #ffffff !important;
        border: 1px solid var(--border);
        border-left: 4px solid var(--gold);
        border-radius: 8px;
        padding: 14px 16px;
        margin: 8px 0 18px 0;
    }

    .gold-text {
        color: var(--gold) !important;
    }

    .stButton button,
    .stDownloadButton button {
        background-color: #d8b366 !important;
        color: #111111 !important;
        font-weight: 700 !important;
        border: 1px solid #e8cc8f !important;
        border-radius: 8px !important;
    }

    .stButton button:hover,
    .stDownloadButton button:hover {
        background-color: #f0d08c !important;
        color: #000000 !important;
    }

    [data-testid="stDataFrame"],
    [data-testid="stTable"] {
        border: 1px solid var(--border);
    }

    hr {
        border-color: #484139 !important;
    }

    /* Ensure dataframe/table text remains legible */
    [data-testid="stDataFrame"] *,
    [data-testid="stTable"] * {
        color: #ffffff !important;
    }

    a {
        color: #f0cc83 !important;
    }

    [data-testid="stAlert"] {
        color: #ffffff !important;
    }

    /* HIGH-PRIORITY SIDEBAR FIX: readable dark text on light controls. */
    [data-testid="stSidebar"] [data-testid="stSelectbox"] [data-baseweb="select"],
    [data-testid="stSidebar"] [data-testid="stMultiSelect"] [data-baseweb="select"] {
        background: #f7f4ef !important;
        color: #111111 !important;
        -webkit-text-fill-color: #111111 !important;
    }

    [data-testid="stSidebar"] [data-testid="stSelectbox"] [data-baseweb="select"] *,
    [data-testid="stSidebar"] [data-testid="stMultiSelect"] [data-baseweb="select"] * {
        color: #111111 !important;
        -webkit-text-fill-color: #111111 !important;
    }

    [data-testid="stSidebar"] [data-testid="stMultiSelect"] [data-baseweb="tag"] {
        background-color: #b18b3e !important;
        color: #111111 !important;
    }

    [data-testid="stSidebar"] [data-testid="stMultiSelect"] [data-baseweb="tag"] *,
    [data-testid="stSidebar"] [data-testid="stMultiSelect"] [data-baseweb="tag"] svg {
        color: #111111 !important;
        fill: #111111 !important;
        stroke: #111111 !important;
        -webkit-text-fill-color: #111111 !important;
    }

    [data-testid="stSidebar"] [data-testid="stNumberInput"] input {
        background: #f7f4ef !important;
        color: #111111 !important;
        -webkit-text-fill-color: #111111 !important;
    }

    [data-testid="stSidebar"] [data-testid="stNumberInput"] button {
        background: #f7f4ef !important;
        color: #111111 !important;
        border-color: #f7f4ef !important;
    }

    [data-testid="stSidebar"] [data-testid="stNumberInput"] button *,
    [data-testid="stSidebar"] [data-testid="stNumberInput"] button svg,
    [data-testid="stSidebar"] [data-testid="stNumberInput"] button path {
        color: #111111 !important;
        fill: #111111 !important;
        stroke: #111111 !important;
        -webkit-text-fill-color: #111111 !important;
    }

    [data-baseweb="popover"] [role="listbox"],
    [data-baseweb="popover"] [role="option"],
    [data-baseweb="popover"] [role="option"] * {
        background-color: #f7f4ef !important;
        color: #111111 !important;
        -webkit-text-fill-color: #111111 !important;
    }

    /* FINAL HIGH-SPECIFICITY FIX: light sidebar controls use dark text.
       This overrides the general white-text rule applied to the sidebar. */
    [data-testid="stSidebar"] [data-testid="stSelectbox"] [data-baseweb="select"],
    [data-testid="stSidebar"] [data-testid="stSelectbox"] [data-baseweb="select"] div,
    [data-testid="stSidebar"] [data-testid="stSelectbox"] [data-baseweb="select"] span,
    [data-testid="stSidebar"] [data-testid="stSelectbox"] [data-baseweb="select"] input,
    [data-testid="stSidebar"] [data-testid="stSelectbox"] [data-baseweb="select"] svg {
        background-color: #f7f4ef !important;
        color: #111111 !important;
        fill: #111111 !important;
        stroke: #111111 !important;
        -webkit-text-fill-color: #111111 !important;
    }

    /* Keep selected multiselect chips gold with readable white text. */
    [data-testid="stSidebar"] [data-testid="stMultiSelect"] [data-baseweb="tag"],
    [data-testid="stSidebar"] [data-testid="stMultiSelect"] [data-baseweb="tag"] span,
    [data-testid="stSidebar"] [data-testid="stMultiSelect"] [data-baseweb="tag"] div {
        background-color: #b18b3e !important;
        color: #ffffff !important;
        -webkit-text-fill-color: #ffffff !important;
    }

    /* Make helper text such as the market-cap proxy note readable on dark panels. */
    [data-testid="stSidebar"] [data-testid="stCaptionContainer"],
    [data-testid="stSidebar"] [data-testid="stCaptionContainer"] p,
    [data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p {
        color: #dedede !important;
        -webkit-text-fill-color: #dedede !important;
    }

    /* MAIN-PAGE INPUT CONTRAST FIX: light controls must use dark text. */
    [data-testid="stMain"] [data-testid="stSelectbox"] [data-baseweb="select"],
    [data-testid="stMain"] [data-testid="stMultiSelect"] [data-baseweb="select"],
    [data-testid="stMain"] [data-testid="stDateInput"] input,
    [data-testid="stMain"] [data-testid="stTextInput"] input,
    [data-testid="stMain"] [data-testid="stNumberInput"] input {
        background: #f7f4ef !important;
        color: #111111 !important;
        -webkit-text-fill-color: #111111 !important;
        border-color: #b18b3e !important;
    }
    [data-testid="stMain"] [data-testid="stSelectbox"] [data-baseweb="select"] *,
    [data-testid="stMain"] [data-testid="stMultiSelect"] [data-baseweb="select"] *,
    [data-testid="stMain"] [data-testid="stDateInput"] input,
    [data-testid="stMain"] [data-testid="stTextInput"] input,
    [data-testid="stMain"] [data-testid="stNumberInput"] input {
        color: #111111 !important;
        -webkit-text-fill-color: #111111 !important;
    }
    /* Calendar popup: black month, weekday and date text on cream. */
    [data-baseweb="calendar"],
    [data-baseweb="calendar"] *,
    [data-baseweb="datepicker"] *,
    [data-baseweb="popover"] [role="grid"],
    [data-baseweb="popover"] [role="grid"] *,
    [data-baseweb="popover"] [role="gridcell"] button,
    [data-baseweb="popover"] [role="columnheader"] {
        color: #111111 !important;
        -webkit-text-fill-color: #111111 !important;
    }
    [data-baseweb="calendar"], [data-baseweb="datepicker"],
    [data-baseweb="popover"] [role="grid"] {
        background: #f7f4ef !important;
    }
    [data-baseweb="calendar"] [aria-selected="true"],
    [data-baseweb="popover"] [role="gridcell"] button[aria-selected="true"] {
        background: #b18b3e !important;
        color: #111111 !important;
    }
    [data-baseweb="calendar"] button:disabled,
    [data-baseweb="popover"] [role="gridcell"] button:disabled {
        color: #888888 !important;
        -webkit-text-fill-color: #888888 !important;
    }

/* ===== FINAL FIX: SIDEBAR DROPDOWN FONT COLOURS ===== */

/* Target horizon and Equity weighting dropdowns */
[data-testid="stSidebar"] [data-testid="stSelectbox"] [data-baseweb="select"],
[data-testid="stSidebar"] [data-testid="stSelectbox"] [data-baseweb="select"] *,
[data-testid="stSidebar"] [data-testid="stSelectbox"] [data-baseweb="select"] span,
[data-testid="stSidebar"] [data-testid="stSelectbox"] [data-baseweb="select"] div,
[data-testid="stSidebar"] [data-testid="stSelectbox"] [data-baseweb="select"] svg {
    color: #111111 !important;
    -webkit-text-fill-color: #111111 !important;
    fill: #111111 !important;
    stroke: #111111 !important;
}

/* Cream background for the dropdown */
[data-testid="stSidebar"] [data-testid="stSelectbox"] [data-baseweb="select"] {
    background-color: #F7F4EF !important;
}

/* Selected dropdown value */
[data-testid="stSidebar"] [data-testid="stSelectbox"] [data-baseweb="select"] [data-testid="stMarkdownContainer"],
[data-testid="stSidebar"] [data-testid="stSelectbox"] [data-baseweb="select"] [data-testid="stMarkdownContainer"] p {
    color: #111111 !important;
    -webkit-text-fill-color: #111111 !important;
}

/* Dropdown options when opened */
[data-baseweb="popover"] [role="listbox"],
[data-baseweb="popover"] [role="option"],
[data-baseweb="popover"] [role="option"] * {
    background-color: #F7F4EF !important;
    color: #111111 !important;
    -webkit-text-fill-color: #111111 !important;
}

/* Keep the explanatory note readable */
[data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p {
    color: #D6D6D6 !important;
    -webkit-text-fill-color: #D6D6D6 !important;
}

/* ===== BROKE SIDEBAR: SELECTED DROPDOWN TEXT FIX ===== */

/* Force selected values to black */
[data-testid="stSidebar"] [data-testid="stSelectbox"] [data-baseweb="select"] *,
[data-testid="stSidebar"] [data-testid="stSelectbox"] [role="combobox"],
[data-testid="stSidebar"] [data-testid="stSelectbox"] [role="combobox"] span,
[data-testid="stSidebar"] [data-testid="stSelectbox"] [role="combobox"] div,
[data-testid="stSidebar"] [data-testid="stSelectbox"] [role="combobox"] p {
    color: #111111 !important;
    -webkit-text-fill-color: #111111 !important;
}

/* Keep the select field cream-coloured */
[data-testid="stSidebar"] [data-testid="stSelectbox"] [data-baseweb="select"] > div {
    background-color: #F7F4EF !important;
}

/* Make the dropdown arrow dark */
[data-testid="stSidebar"] [data-testid="stSelectbox"] [data-baseweb="select"] svg {
    color: #111111 !important;
    fill: #111111 !important;
    stroke: #111111 !important;
}

/* Dropdown options */
[data-baseweb="popover"] [role="listbox"],
[data-baseweb="popover"] [role="option"],
[data-baseweb="popover"] [role="option"] * {
    color: #111111 !important;
    -webkit-text-fill-color: #111111 !important;
}

/* Preserve readable helper text in the dark sidebar */
[data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p {
    color: #BDBDBD !important;
    -webkit-text-fill-color: #BDBDBD !important;
}

/* ===== BROKE SIDEBAR: SELECTED DROPDOWN TEXT FIX ===== */

/* Force selected values to black */
[data-testid="stSidebar"] [data-testid="stSelectbox"] [data-baseweb="select"] *,
[data-testid="stSidebar"] [data-testid="stSelectbox"] [role="combobox"],
[data-testid="stSidebar"] [data-testid="stSelectbox"] [role="combobox"] span,
[data-testid="stSidebar"] [data-testid="stSelectbox"] [role="combobox"] div,
[data-testid="stSidebar"] [data-testid="stSelectbox"] [role="combobox"] p {
    color: #111111 !important;
    -webkit-text-fill-color: #111111 !important;
}

/* Keep the select field cream-coloured */
[data-testid="stSidebar"] [data-testid="stSelectbox"] [data-baseweb="select"] > div {
    background-color: #F7F4EF !important;
}

/* Make the dropdown arrow dark */
[data-testid="stSidebar"] [data-testid="stSelectbox"] [data-baseweb="select"] svg {
    color: #111111 !important;
    fill: #111111 !important;
    stroke: #111111 !important;
}

/* Dropdown options */
[data-baseweb="popover"] [role="listbox"],
[data-baseweb="popover"] [role="option"],
[data-baseweb="popover"] [role="option"] * {
    color: #111111 !important;
    -webkit-text-fill-color: #111111 !important;
}

/* Preserve readable helper text in the dark sidebar */
[data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p {
    color: #BDBDBD !important;
    -webkit-text-fill-color: #BDBDBD !important;
}

/* ===== TECHNICAL ANALYSIS DROPDOWN FONT FIX ===== */

/* Company selection and candlestick interval */
[data-testid="stSelectbox"] [data-baseweb="select"],
[data-testid="stSelectbox"] [data-baseweb="select"] *,
[data-testid="stSelectbox"] [role="combobox"],
[data-testid="stSelectbox"] [role="combobox"] *,
[data-testid="stSelectbox"] [data-baseweb="select"] input {
    color: #111111 !important;
    -webkit-text-fill-color: #111111 !important;
}

/* Cream background */
[data-testid="stSelectbox"] [data-baseweb="select"] > div {
    background-color: #F7F4EF !important;
}

/* Dropdown arrow */
[data-testid="stSelectbox"] [data-baseweb="select"] svg {
    color: #111111 !important;
    fill: #111111 !important;
    stroke: #111111 !important;
}

/* Options shown when the dropdown is opened */
[data-baseweb="popover"] [role="listbox"],
[data-baseweb="popover"] [role="option"],
[data-baseweb="popover"] [role="option"] * {
    color: #111111 !important;
    -webkit-text-fill-color: #111111 !important;
}
</style>
""", unsafe_allow_html=True)

# ============================================================
# PORTFOLIO UNIVERSE: 15 EQUITIES + DEBT INSTRUMENTS
# ============================================================

COMPANIES = {
    "Reliance Industries": "RELIANCE.NS",
    "HDFC Bank": "HDFCBANK.NS",
    "TCS": "TCS.NS",
    "ICICI Bank": "ICICIBANK.NS",
    "Infosys": "INFY.NS",
    "Bharti Airtel": "BHARTIARTL.NS",
    "ITC": "ITC.NS",
    "Larsen & Toubro": "LT.NS",
    "State Bank of India": "SBIN.NS",
    "Axis Bank": "AXISBANK.NS",
    "Kotak Mahindra Bank": "KOTAKBANK.NS",
    "Hindustan Unilever": "HINDUNILVR.NS",
    "Sun Pharmaceutical": "SUNPHARMA.NS",
    "Mahindra & Mahindra": "M&M.NS",
    "Maruti Suzuki": "MARUTI.NS",
}

DEBT_INSTRUMENTS = {
    "Nippon India ETF Nifty 8-13 yr G-Sec": "GILTBEES.NS",
    "Nippon India ETF Liquid BeES": "LIQUIDBEES.NS",
}

BENCHMARKS = {
    "Nifty 50": "^NSEI",
    "Nifty 500": "^CRSLDX",
    "Sensex": "^BSESN",
}

# Approximate relative allocation scores for market-cap-proxy mode.
# These are illustrative weights, not live market capitalisations.
MARKET_CAP_SCORES = {
    "RELIANCE.NS": 10,
    "HDFCBANK.NS": 10,
    "TCS.NS": 9,
    "ICICIBANK.NS": 8,
    "INFY.NS": 7,
    "BHARTIARTL.NS": 7,
    "ITC.NS": 6,
    "LT.NS": 6,
    "SBIN.NS": 6,
    "AXISBANK.NS": 5,
    "KOTAKBANK.NS": 5,
    "HINDUNILVR.NS": 5,
    "SUNPHARMA.NS": 5,
    "M&M.NS": 4,
    "MARUTI.NS": 4,
}

# ============================================================
# DATA HELPERS
# ============================================================

@st.cache_data(ttl=1800, show_spinner=False)
def download_history(tickers, start_date, end_date):
    """Download adjusted historical prices using yfinance."""
    if not tickers:
        return pd.DataFrame()

    end_exclusive = pd.Timestamp(end_date) + pd.Timedelta(days=1)

    raw = yf.download(
        tickers=list(tickers),
        start=str(start_date),
        end=str(end_exclusive.date()),
        auto_adjust=True,
        progress=False,
        group_by="column",
        threads=True,
    )

    if raw is None or raw.empty:
        return pd.DataFrame()

    if isinstance(raw.columns, pd.MultiIndex):
        if "Close" in raw.columns.get_level_values(0):
            prices = raw["Close"].copy()
        else:
            prices = raw.xs(
                raw.columns.get_level_values(0)[0],
                axis=1,
                level=0,
            )
    else:
        if "Close" in raw.columns:
            prices = raw[["Close"]].copy()
            prices.columns = [tickers[0]]
        else:
            prices = raw.copy()

    if isinstance(prices, pd.Series):
        prices = prices.to_frame()

    prices = prices.dropna(axis=1, how="all")
    prices = prices.sort_index().ffill()
    prices.index = pd.to_datetime(prices.index)
    return prices


@st.cache_data(ttl=900, show_spinner=False)
def download_ohlc(ticker, start_date, end_date):
    """Robustly download and normalise OHLCV data from yfinance.

    Tries yf.download first and Ticker.history as a fallback. Handles both
    MultiIndex column orders used by different yfinance versions.
    """
    start_ts = pd.Timestamp(start_date).normalize()
    end_ts = pd.Timestamp(end_date).normalize() + pd.Timedelta(days=1)  # yfinance end is exclusive
    errors = []

    def normalise(raw):
        if raw is None or raw.empty:
            return pd.DataFrame()
        frame = raw.copy()
        if isinstance(frame.columns, pd.MultiIndex):
            # Select the level that contains OHLC labels, regardless of order.
            selected = None
            for level in range(frame.columns.nlevels):
                labels = {str(x).strip().title() for x in frame.columns.get_level_values(level)}
                if {"Open", "High", "Low", "Close"}.issubset(labels):
                    selected = level
                    break
            if selected is not None:
                frame.columns = frame.columns.get_level_values(selected)
        frame.columns = [str(c).strip().title() for c in frame.columns]
        # A few yfinance releases can still leave duplicate field names.
        frame = frame.loc[:, ~pd.Index(frame.columns).duplicated(keep="first")]
        required = ["Open", "High", "Low", "Close"]
        if not all(c in frame.columns for c in required):
            return pd.DataFrame()
        keep = required + (["Volume"] if "Volume" in frame.columns else [])
        frame = frame[keep].copy()
        frame.index = pd.to_datetime(frame.index, errors="coerce")
        try:
            if frame.index.tz is not None:
                frame.index = frame.index.tz_localize(None)
        except (AttributeError, TypeError):
            pass
        frame = frame[~frame.index.isna()].sort_index()
        for col in keep:
            frame[col] = pd.to_numeric(frame[col], errors="coerce")
        return frame.dropna(subset=required)

    try:
        raw = yf.download(
            tickers=ticker,
            start=start_ts.strftime("%Y-%m-%d"),
            end=end_ts.strftime("%Y-%m-%d"),
            auto_adjust=True,
            progress=False,
            threads=False,
            group_by="column",
        )
        frame = normalise(raw)
        if not frame.empty:
            return frame
        errors.append("yf.download returned no usable OHLC columns/data")
    except Exception as exc:
        errors.append(f"yf.download: {exc}")

    try:
        raw = yf.Ticker(ticker).history(
            start=start_ts.strftime("%Y-%m-%d"),
            end=end_ts.strftime("%Y-%m-%d"),
            auto_adjust=True,
            actions=False,
        )
        frame = normalise(raw)
        if not frame.empty:
            return frame
        errors.append("Ticker.history returned no usable OHLC data")
    except Exception as exc:
        errors.append(f"Ticker.history: {exc}")

    # Empty frame is handled by the page with a useful diagnostic message.
    return pd.DataFrame(columns=["Open", "High", "Low", "Close", "Volume"])


def add_technical_indicators(frame):
    """Add common indicators to OHLC price data."""
    out = frame.copy()
    close = out["Close"]
    out["SMA 20"] = close.rolling(20).mean()
    out["SMA 50"] = close.rolling(50).mean()
    out["EMA 12"] = close.ewm(span=12, adjust=False).mean()
    out["EMA 26"] = close.ewm(span=26, adjust=False).mean()
    out["MACD"] = out["EMA 12"] - out["EMA 26"]
    out["MACD Signal"] = out["MACD"].ewm(span=9, adjust=False).mean()
    change = close.diff()
    gain = change.clip(lower=0).rolling(14).mean()
    loss = -change.clip(upper=0).rolling(14).mean()
    rs = gain / loss.replace(0, np.nan)
    out["RSI 14"] = 100 - (100 / (1 + rs))
    return out


def get_company_fundamentals(ticker):
    """Fetch available public company fundamentals from Yahoo Finance."""
    try:
        info = yf.Ticker(ticker).info or {}
        keys = {
            "Company": info.get("longName") or info.get("shortName") or ticker,
            "Sector": info.get("sector", "Not available"),
            "Industry": info.get("industry", "Not available"),
            "Market capitalisation (₹)": info.get("marketCap", np.nan),
            "Trailing P/E": info.get("trailingPE", np.nan),
            "Forward P/E": info.get("forwardPE", np.nan),
            "Price-to-book": info.get("priceToBook", np.nan),
            "ROE": info.get("returnOnEquity", np.nan),
            "ROA": info.get("returnOnAssets", np.nan),
            "Debt-to-equity": info.get("debtToEquity", np.nan),
            "Current ratio": info.get("currentRatio", np.nan),
            "Quick ratio": info.get("quickRatio", np.nan),
            "Profit margin": info.get("profitMargins", np.nan),
            "Operating margin": info.get("operatingMargins", np.nan),
            "Revenue growth": info.get("revenueGrowth", np.nan),
            "Earnings growth": info.get("earningsGrowth", np.nan),
            "Dividend yield": info.get("dividendYield", np.nan),
            "Beta (provider)": info.get("beta", np.nan),
            "Target mean price (₹)": info.get("targetMeanPrice", np.nan),
            "Currency": info.get("currency", "INR"),
        }
        return keys
    except Exception:
        return {}


def safe_float(value, default=0.0):
    try:
        value = float(value)
        return value if np.isfinite(value) else default
    except (TypeError, ValueError):
        return default


def money(value, decimals=2):
    """Format INR values in Indian crore/lakh units."""
    value = float(value)

    if abs(value) >= 10_000_000:
        return f"₹{value / 10_000_000:,.{decimals}f} Cr"
    if abs(value) >= 100_000:
        return f"₹{value / 100_000:,.{decimals}f} L"
    return f"₹{value:,.{decimals}f}"


def percentage(value):
    if pd.isna(value):
        return "N/A"
    return f"{value * 100:+.2f}%"


def compute_weights(
    equity_tickers,
    debt_tickers,
    equity_weight,
    debt_weight,
    cash_weight,
    method,
    prices,
):
    """Allocate the portfolio across equities, debt and cash."""
    assets = {}
    all_instruments = list(equity_tickers) + list(debt_tickers)

    if not all_instruments:
        return {"CASH": 1.0}

    if method == "Equal weighting":
        equity_scores = {
            ticker: 1.0 for ticker in equity_tickers
        }
    elif method == "Risk-based":
        equity_returns = prices[equity_tickers].pct_change().dropna(
            how="all"
        ) if equity_tickers else pd.DataFrame()

        equity_scores = {}
        for ticker in equity_tickers:
            if ticker in equity_returns:
                vol = equity_returns[ticker].std()
                equity_scores[ticker] = (
                    1.0 / vol if pd.notna(vol) and vol > 0 else 1.0
                )
            else:
                equity_scores[ticker] = 1.0
    else:
        equity_scores = {
            ticker: float(MARKET_CAP_SCORES.get(ticker, 1))
            for ticker in equity_tickers
        }

    if equity_tickers:
        score_total = sum(equity_scores.values()) or 1.0
        for ticker in equity_tickers:
            assets[ticker] = (
                equity_weight * equity_scores[ticker] / score_total
            )

    if debt_tickers:
        debt_each = debt_weight / len(debt_tickers)
        for ticker in debt_tickers:
            assets[ticker] = debt_each

    assets["CASH"] = cash_weight

    # Normalize to exactly 100% to avoid rounding/selection issues.
    total = sum(assets.values())
    if total <= 0:
        return {"CASH": 1.0}

    return {key: value / total for key, value in assets.items()}


def portfolio_series(prices, weights, initial_capital):
    """Create portfolio value series from weighted daily returns."""
    available = [
        ticker for ticker in weights
        if ticker != "CASH" and ticker in prices.columns
    ]

    if not available:
        idx = prices.index if not prices.empty else pd.DatetimeIndex([])
        return pd.Series(initial_capital, index=idx, name="Portfolio")

    returns = prices[available].pct_change().fillna(0)

    # Cash is assumed to earn 0% in this simplified simulation.
    weighted_returns = pd.Series(0.0, index=returns.index)
    for ticker in available:
        weighted_returns += returns[ticker] * weights[ticker]

    # The portfolio return includes the full portfolio weights;
    # cash contributes zero return in this model.
    series = initial_capital * (1 + weighted_returns).cumprod()
    series.name = "Portfolio Value"
    return series


def contribution_table(prices, weights, initial_capital):
    """Estimate holding-level contribution over the displayed period."""
    rows = []

    if prices.empty or len(prices) < 2:
        return pd.DataFrame(
            columns=["Instrument", "Type", "Weight", "Period Return",
                     "Contribution", "Contribution INR"]
        )

    for ticker, weight in weights.items():
        if ticker == "CASH":
            rows.append({
                "Instrument": "Cash reserve",
                "Type": "Cash",
                "Weight": weight,
                "Period Return": 0.0,
                "Contribution": 0.0,
                "Contribution INR": 0.0,
            })
            continue

        if ticker not in prices.columns:
            continue

        series = prices[ticker].dropna()
        if len(series) < 2 or series.iloc[0] == 0:
            continue

        period_return = series.iloc[-1] / series.iloc[0] - 1
        contribution = weight * period_return

        rows.append({
            "Instrument": ticker,
            "Type": "Debt" if ticker in DEBT_INSTRUMENTS.values()
                    else "Equity",
            "Weight": weight,
            "Period Return": period_return,
            "Contribution": contribution,
            "Contribution INR": initial_capital * contribution,
        })

    result = pd.DataFrame(rows)
    if not result.empty:
        result = result.sort_values(
            "Contribution", ascending=False
        )
    return result


def make_pdf_report(report_data, contribution_df, weekly_notes):
    """Build a downloadable PDF report."""
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=landscape(A4),
        rightMargin=30,
        leftMargin=30,
        topMargin=30,
        bottomMargin=30,
    )

    styles = getSampleStyleSheet()
    story = []

    story.append(Paragraph(
        "<b>BROKE | Weekly Portfolio Intelligence Report</b>",
        styles["Title"],
    ))
    story.append(Spacer(1, 12))
    story.append(Paragraph(
        f"Report generated: {date.today().strftime('%d %B %Y')}",
        styles["Normal"],
    ))
    story.append(Spacer(1, 12))

    for label, value in report_data.items():
        story.append(Paragraph(
            f"<b>{label}:</b> {value}",
            styles["Normal"],
        ))
        story.append(Spacer(1, 4))

    story.append(Spacer(1, 10))
    story.append(Paragraph("<b>Holding Contributions</b>", styles["Heading2"]))

    table_data = [[
        "Instrument", "Type", "Weight", "Period Return",
        "Contribution", "Contribution INR"
    ]]

    for _, row in contribution_df.iterrows():
        table_data.append([
            str(row["Instrument"]),
            str(row["Type"]),
            f'{row["Weight"] * 100:.2f}%',
            f'{row["Period Return"] * 100:+.2f}%',
            f'{row["Contribution"] * 100:+.2f}%',
            money(row["Contribution INR"]),
        ])

    table = Table(table_data, repeatRows=1)
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#d8b366")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.black),
        ("TEXTCOLOR", (0, 1), (-1, -1), colors.black),
        ("GRID", (0, 0), (-1, -1), 0.4, colors.grey),
        ("FONTSIZE", (0, 0), (-1, -1), 8),
        ("PADDING", (0, 0), (-1, -1), 5),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
    ]))
    story.append(table)
    story.append(Spacer(1, 12))

    story.append(Paragraph("<b>Weekly Movement Analysis</b>", styles["Heading2"]))
    for note in weekly_notes:
        story.append(Paragraph(f"• {note}", styles["Normal"]))
        story.append(Spacer(1, 5))

    story.append(Spacer(1, 12))
    story.append(Paragraph(
        "<b>Important limitations:</b> This is a simulated portfolio using "
        "historical adjusted market prices. The report identifies price "
        "movements and contribution, but price data alone cannot prove why "
        "a security moved. News, corporate announcements, market conditions, "
        "and other factors should be checked independently. Debt ETFs are "
        "market-traded instruments and are not the same as holding an "
        "individual bond to maturity. This report is for educational use, "
        "not investment advice.",
        styles["Normal"],
    ))

    doc.build(story)
    buffer.seek(0)
    return buffer.getvalue()


# ============================================================

ARCHIVE_DB_PATH = Path(__file__).resolve().parent / "broke_weekly_reports.sqlite3"

def init_archive_db():
    with sqlite3.connect(ARCHIVE_DB_PATH) as con:
        con.execute("""
            CREATE TABLE IF NOT EXISTS weekly_reports (
                report_id INTEGER PRIMARY KEY AUTOINCREMENT,
                week_end TEXT NOT NULL,
                config_key TEXT NOT NULL,
                config_label TEXT NOT NULL,
                generated_at TEXT NOT NULL,
                report_data_json TEXT NOT NULL,
                contributions_json TEXT NOT NULL,
                notes_json TEXT NOT NULL,
                UNIQUE(week_end, config_key)
            )
        """)
        con.commit()

def save_archive_record(week_end, config_key, config_label, report_data, contribution_df, notes):
    init_archive_db()
    with sqlite3.connect(ARCHIVE_DB_PATH) as con:
        con.execute("""
            INSERT INTO weekly_reports
            (week_end, config_key, config_label, generated_at,
             report_data_json, contributions_json, notes_json)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(week_end, config_key) DO UPDATE SET
                config_label=excluded.config_label,
                generated_at=excluded.generated_at,
                report_data_json=excluded.report_data_json,
                contributions_json=excluded.contributions_json,
                notes_json=excluded.notes_json
        """, (
            str(week_end), config_key, config_label,
            datetime.now().isoformat(timespec="seconds"),
            json.dumps(report_data, ensure_ascii=False, default=str),
            contribution_df.to_json(orient="records", date_format="iso"),
            json.dumps(notes, ensure_ascii=False, default=str),
        ))
        con.commit()

def load_archive_records():
    init_archive_db()
    with sqlite3.connect(ARCHIVE_DB_PATH) as con:
        con.row_factory = sqlite3.Row
        rows = con.execute(
            "SELECT * FROM weekly_reports ORDER BY week_end DESC, generated_at DESC"
        ).fetchall()
    return [dict(row) for row in rows]

def backfill_weekly_archive(
    portfolio_series_data, prices, weights, benchmark_prices,
    benchmark_ticker, benchmark_name, target_value, target_years,
    equity_allocation_pct, debt_allocation_pct, cash_allocation_pct,
    weighting_method, history_label,
):
    """Backfill historical weeks from available prices and persist in SQLite."""
    config = {
        "weights": {k: round(float(v), 8) for k, v in sorted(weights.items())},
        "benchmark": benchmark_ticker, "target": target_value,
        "horizon": target_years, "equity": equity_allocation_pct,
        "debt": debt_allocation_pct, "cash": cash_allocation_pct,
        "method": weighting_method, "period": history_label,
    }
    config_key = hashlib.sha256(
        json.dumps(config, sort_keys=True).encode("utf-8")
    ).hexdigest()[:16]
    config_label = (
        f"{benchmark_name} | {weighting_method} | "
        f"{equity_allocation_pct}/{debt_allocation_pct}/{cash_allocation_pct} "
        "equity/debt/cash"
    )
    portfolio_data = portfolio_series_data.dropna().sort_index()
    groups = [
        g for _, g in portfolio_data.groupby(
            portfolio_data.index.to_period("W-FRI")
        ) if not g.empty
    ]
    if len(groups) < 2:
        return config_key, config_label, 0

    benchmark_prices_series = pd.Series(dtype=float)
    if benchmark_prices is not None and not benchmark_prices.empty and benchmark_ticker in benchmark_prices:
        benchmark_prices_series = benchmark_prices[benchmark_ticker].dropna()
    benchmark_returns = benchmark_prices_series.pct_change().dropna()
    saved = 0

    for i in range(1, len(groups)):
        prev_date, end_date = pd.Timestamp(groups[i-1].index[-1]), pd.Timestamp(groups[i].index[-1])
        prev_value, end_value = float(groups[i-1].iloc[-1]), float(groups[i].iloc[-1])
        if prev_value == 0:
            continue
        week_return = end_value / prev_value - 1
        week_change = end_value - prev_value

        rows = []
        for ticker, weight in weights.items():
            if ticker == "CASH":
                rows.append({
                    "Instrument": "Cash reserve", "Type": "Cash",
                    "Weight": float(weight), "Period Return": 0.0,
                    "Contribution": 0.0, "Contribution INR": 0.0,
                })
                continue
            if ticker not in prices.columns:
                continue
            series = prices[ticker].dropna()
            before = series.loc[series.index <= prev_date]
            through = series.loc[series.index <= end_date]
            if before.empty or through.empty or float(before.iloc[-1]) == 0:
                continue
            ret = float(through.iloc[-1] / before.iloc[-1] - 1)
            contribution = float(weight) * ret
            rows.append({
                "Instrument": ticker,
                "Type": "Debt" if ticker in DEBT_INSTRUMENTS.values() else "Equity",
                "Weight": float(weight), "Period Return": ret,
                "Contribution": contribution,
                "Contribution INR": INITIAL_CAPITAL * contribution,
            })
        contrib = pd.DataFrame(rows)
        if not contrib.empty:
            contrib = contrib.sort_values("Contribution", ascending=False)

        bench_week = np.nan
        prior_bench = benchmark_prices_series.loc[benchmark_prices_series.index <= prev_date]
        week_bench = benchmark_prices_series.loc[
            (benchmark_prices_series.index > prev_date)
            & (benchmark_prices_series.index <= end_date)
        ]
        if not prior_bench.empty and not week_bench.empty and prior_bench.iloc[-1] != 0:
            bench_week = float(week_bench.iloc[-1] / prior_bench.iloc[-1] - 1)

        portfolio_returns = portfolio_data.pct_change().dropna().loc[:end_date].tail(252)
        bench_returns = benchmark_returns.loc[:end_date].tail(252)
        aligned = pd.concat([
            portfolio_returns.rename("Portfolio"),
            bench_returns.rename("Benchmark")
        ], axis=1, join="inner").dropna()
        beta = np.nan
        if len(aligned) > 1 and aligned["Benchmark"].var(ddof=1) > 0:
            beta = float(aligned["Portfolio"].cov(aligned["Benchmark"]) / aligned["Benchmark"].var(ddof=1))

        vol = float(portfolio_returns.std(ddof=1) * np.sqrt(252)) if len(portfolio_returns) > 1 else np.nan
        bench_vol = float(bench_returns.std(ddof=1) * np.sqrt(252)) if len(bench_returns) > 1 else np.nan
        past = portfolio_data.loc[:end_date]
        dd = float((past / past.cummax() - 1).min()) if not past.empty else np.nan

        notes = [
            f"Portfolio movement for this week: {percentage(week_return)}, approximately {money(week_change)}."
        ]
        if not contrib.empty:
            eligible = contrib[contrib["Type"].isin(["Equity", "Debt"])]
            winners = eligible[eligible["Contribution"] > 0].nlargest(3, "Contribution")
            losers = eligible[eligible["Contribution"] < 0].nsmallest(3, "Contribution")
            if not winners.empty:
                notes.append("Largest positive contributors: " + ", ".join(
                    f'{r["Instrument"]} ({percentage(r["Period Return"])})'
                    for _, r in winners.iterrows()
                ) + ".")
            if not losers.empty:
                notes.append("Largest negative contributors: " + ", ".join(
                    f'{r["Instrument"]} ({percentage(r["Period Return"])})'
                    for _, r in losers.iterrows()
                ) + ".")
        if pd.notna(bench_week):
            notes.append(f"{benchmark_name} returned {percentage(bench_week)} over the same weekly interval.")
        notes.append(
            "Historical reconstruction using currently selected holdings and weights; "
            "it was not necessarily saved during that historical week. Price movements "
            "alone do not establish the cause of gains or losses."
        )

        report = {
            "Report week ending": str(end_date.date()),
            "Report type": "Historical reconstruction from available prices",
            "Initial simulated investment": money(INITIAL_CAPITAL),
            "Portfolio value at week end": money(end_value),
            "Weekly P&L": money(week_change),
            "Weekly return": percentage(week_return),
            "Annualised portfolio volatility": percentage(vol),
            "Maximum drawdown to date": percentage(dd),
            "Portfolio beta vs benchmark": f"{beta:.2f}" if pd.notna(beta) else "N/A",
            "Annualised benchmark volatility": percentage(bench_vol),
            "Benchmark weekly return": percentage(bench_week),
            "Benchmark": benchmark_name,
            "Target value": money(target_value),
            "Target horizon": f"{target_years} years",
            "Equity / Debt / Cash": f"{equity_allocation_pct}% / {debt_allocation_pct}% / {cash_allocation_pct}%",
            "Weighting method": weighting_method,
            "Historical data window": history_label,
            "Archive note": "Reconstructed from historical prices using current selected holdings and weights.",
        }
        save_archive_record(end_date.date(), config_key, config_label, report, contrib, notes)
        saved += 1
    return config_key, config_label, saved


# SIDEBAR
# ============================================================

st.sidebar.markdown(
    '<div class="broke-brand">BROKE</div>',
    unsafe_allow_html=True,
)
st.sidebar.markdown(
    '<div class="broke-subtitle">Portfolio Intelligence</div>',
    unsafe_allow_html=True,
)
st.sidebar.divider()

page = st.sidebar.radio(
    "Navigate",
    [
        "Command Center",
        "Holdings & Allocation",
        "Weekly Intelligence",
        "Risk Lab",
        "Technical Analysis",
        "Fundamentals & Valuation",
        "Investment Theories & Metrics",
        "Target Simulator",
        "Report Archive",
        "Data Diagnostics",
    ],
)

st.sidebar.divider()
st.sidebar.markdown("### Portfolio Settings")

target = st.sidebar.number_input(
    "Portfolio target (₹)",
    min_value=1_000_000,
    max_value=1_000_000_000,
    value=DEFAULT_TARGET,
    step=500_000,
    help="₹1.75 crore is 17500000.",
)

horizon_years = st.sidebar.selectbox(
    "Target horizon",
    [1, 2, 3, 5, 10],
    index=3,
    format_func=lambda x: f"{x} year{'s' if x > 1 else ''}",
)

weight_method = st.sidebar.selectbox(
    "Equity weighting",
    ["Market-cap proxy", "Equal weighting", "Risk-based"],
)

st.sidebar.caption(
    "Market-cap proxy uses illustrative relative scores, not live "
    "market capitalisation."
)

st.sidebar.markdown("### Asset Allocation")

equity_pct = st.sidebar.slider(
    "Equity allocation (%)", 0, 95, 70
)
debt_pct = st.sidebar.slider(
    "Debt allocation (%)", 0, 90, 25
)

if equity_pct + debt_pct > 100:
    st.sidebar.error("Equity + debt cannot exceed 100%.")
    st.stop()

cash_pct = 100 - equity_pct - debt_pct

st.sidebar.markdown(
    f"**Cash reserve:** {cash_pct}%"
)
st.sidebar.caption(
    "Equity + debt + cash always equals 100%."
)

st.sidebar.markdown("### Portfolio Universe")

selected_company_names = st.sidebar.multiselect(
    "Select companies (up to 15)",
    list(COMPANIES.keys()),
    default=list(COMPANIES.keys()),
    max_selections=15,
)

selected_debt_names = st.sidebar.multiselect(
    "Select debt instruments",
    list(DEBT_INSTRUMENTS.keys()),
    default=list(DEBT_INSTRUMENTS.keys()),
)

benchmark_name = st.sidebar.selectbox(
    "Benchmark",
    list(BENCHMARKS.keys()),
    index=0,
)

period_choice = st.sidebar.selectbox(
    "Historical analysis period",
    ["3 months", "6 months", "1 year", "2 years", "5 years"],
    index=2,
)

period_days = {
    "3 months": 92,
    "6 months": 183,
    "1 year": 365,
    "2 years": 730,
    "5 years": 1825,
}[period_choice]

today = date.today()
default_end = today
default_start = today - timedelta(days=period_days)
st.sidebar.markdown("### Custom Analysis Dates")
start_date = st.sidebar.date_input(
    "Start date", value=default_start, max_value=today - timedelta(days=1),
    key="broke_start_date",
)
end_date = st.sidebar.date_input(
    "End date", value=default_end, min_value=start_date, max_value=today,
    key="broke_end_date",
)
if start_date >= end_date:
    st.sidebar.error("End date must be after the start date.")
    st.stop()
st.sidebar.caption(
    "The selected dates control the price analysis, weekly report and technical chart. "
    "A few earlier observations are fetched where possible for indicators."
)

selected_equities = [
    COMPANIES[name] for name in selected_company_names
]
selected_debt = [
    DEBT_INSTRUMENTS[name] for name in selected_debt_names
]
selected_tickers = selected_equities + selected_debt

if not selected_tickers:
    st.warning("Select at least one company or debt instrument.")
    st.stop()

# ============================================================
# LOAD MARKET DATA
# ============================================================

with st.spinner("Loading historical market data..."):
    # Fetch an additional 90 calendar days before the selected start date
    # so rolling indicators and boundary returns have sufficient observations.
    fetch_start_date = start_date - timedelta(days=90)
    full_price_data = download_history(
        selected_tickers, fetch_start_date, end_date
    )
    full_benchmark_data = download_history(
        [BENCHMARKS[benchmark_name]], fetch_start_date, end_date
    )
    price_data = full_price_data.loc[
        (full_price_data.index.date >= start_date)
        & (full_price_data.index.date <= end_date)
    ].copy() if not full_price_data.empty else pd.DataFrame()
    benchmark_data = full_benchmark_data.loc[
        (full_benchmark_data.index.date >= start_date)
        & (full_benchmark_data.index.date <= end_date)
    ].copy() if not full_benchmark_data.empty else pd.DataFrame()

if price_data.empty:
    st.error(
        "Market data could not be downloaded. Check your internet "
        "connection or ticker availability, then try again."
    )
    st.stop()

available_tickers = [
    ticker for ticker in selected_tickers
    if ticker in price_data.columns
]

missing_tickers = [
    ticker for ticker in selected_tickers
    if ticker not in price_data.columns
]

selected_equities = [
    ticker for ticker in selected_equities
    if ticker in available_tickers
]
selected_debt = [
    ticker for ticker in selected_debt
    if ticker in available_tickers
]

weights = compute_weights(
    selected_equities,
    selected_debt,
    equity_pct / 100,
    debt_pct / 100,
    cash_pct / 100,
    weight_method,
    price_data,
)

portfolio = portfolio_series(
    price_data, weights, INITIAL_CAPITAL
)

if portfolio.empty or portfolio.dropna().empty:
    st.error("Not enough price data to calculate portfolio performance.")
    st.stop()

portfolio = portfolio.dropna()
current_value = float(portfolio.iloc[-1])
total_return = current_value / INITIAL_CAPITAL - 1
total_profit_loss = current_value - INITIAL_CAPITAL

daily_returns = portfolio.pct_change().dropna()
annual_volatility = (
    daily_returns.std() * np.sqrt(252)
    if len(daily_returns) > 1 else np.nan
)

running_peak = portfolio.cummax()
drawdown_series = portfolio / running_peak - 1
max_drawdown = (
    float(drawdown_series.min())
    if not drawdown_series.empty else np.nan
)

# Selected analysis interval: report start-to-end movement.
weekly_start_value = float(portfolio.iloc[0])
weekly_end_value = float(portfolio.iloc[-1])
weekly_return = (
    weekly_end_value / weekly_start_value - 1
    if weekly_start_value else 0.0
)
weekly_change = weekly_end_value - weekly_start_value

contributions = contribution_table(
    price_data[available_tickers], weights, INITIAL_CAPITAL
)

benchmark_return = np.nan
benchmark_beta = np.nan
benchmark_volatility = np.nan
benchmark_ticker = BENCHMARKS[benchmark_name]
benchmark_daily_returns = pd.Series(dtype=float)

if (
    not benchmark_data.empty
    and benchmark_ticker in benchmark_data.columns
):
    bench = benchmark_data[benchmark_ticker].dropna()

    if len(bench) > 1:
        benchmark_return = float(bench.iloc[-1] / bench.iloc[0] - 1)
        benchmark_daily_returns = bench.pct_change().rename("Benchmark")

        beta_frame = pd.concat(
            [
                daily_returns.rename("Portfolio"),
                benchmark_daily_returns,
            ],
            axis=1,
            join="inner",
        ).dropna()

        benchmark_variance = (
            beta_frame["Benchmark"].var(ddof=1)
            if len(beta_frame) > 1
            else np.nan
        )

        if pd.notna(benchmark_variance) and benchmark_variance > 0:
            benchmark_beta = float(
                beta_frame["Portfolio"].cov(beta_frame["Benchmark"])
                / benchmark_variance
            )

        valid_benchmark_returns = benchmark_daily_returns.dropna()
        if len(valid_benchmark_returns) > 1:
            benchmark_volatility = float(
                valid_benchmark_returns.std(ddof=1) * np.sqrt(252)
            )

annual_volatility = (
    float(daily_returns.std(ddof=1) * np.sqrt(252))
    if len(daily_returns) > 1
    else np.nan
)

# ============================================================
# MOVEMENT EXPLANATIONS
# ============================================================

def build_weekly_notes():
    notes = []

    notes.append(
        f"The portfolio's movement over the selected interval ({start_date} to {end_date}) is "
        f"{percentage(weekly_return)}, equal to approximately "
        f"{money(weekly_change)}."
    )

    if contributions.empty:
        notes.append(
            "Holding-level attribution is unavailable because there "
            "is not enough historical data."
        )
        return notes

    valid = contributions[
        contributions["Type"].isin(["Equity", "Debt"])
    ].copy()

    if valid.empty:
        notes.append("No investable holdings have sufficient price data.")
        return notes

    best = valid.sort_values(
        "Contribution", ascending=False
    ).head(3)
    worst = valid.sort_values(
        "Contribution", ascending=True
    ).head(3)

    positive = valid[valid["Contribution"] > 0]
    negative = valid[valid["Contribution"] < 0]

    if not positive.empty:
        winners = ", ".join(
            f'{row["Instrument"]} ({percentage(row["Period Return"])})'
            for _, row in positive.sort_values(
                "Contribution", ascending=False
            ).head(3).iterrows()
        )
        notes.append(
            "Largest positive contributors over the selected period: "
            + winners + "."
        )

    if not negative.empty:
        losers = ", ".join(
            f'{row["Instrument"]} ({percentage(row["Period Return"])})'
            for _, row in negative.sort_values(
                "Contribution"
            ).head(3).iterrows()
        )
        notes.append(
            "Largest negative contributors over the selected period: "
            + losers + ". These price declines reduced the portfolio's "
            "calculated return."
        )

    if weekly_return > 0:
        notes.append(
            "The portfolio rose over the latest available trading week. "
            "Positive weighted price movements outweighed negative "
            "movements during this interval."
        )
    elif weekly_return < 0:
        notes.append(
            "The portfolio fell over the latest available trading week. "
            "Negative weighted price movements outweighed positive "
            "movements during this interval."
        )
    else:
        notes.append(
            "The portfolio was approximately flat over the latest "
            "available trading week."
        )

    if not pd.isna(benchmark_return):
        relative = total_return - benchmark_return
        notes.append(
            f"Over the full selected period, portfolio return was "
            f"{percentage(total_return)} and {benchmark_name} return was "
            f"{percentage(benchmark_return)}. The difference was "
            f"{percentage(relative)}."
        )

    notes.append(
        "These are performance-based explanations, not proof of the "
        "underlying cause. Confirm specific causes by checking relevant "
        "company announcements, earnings, sector developments, interest "
        "rates, and broader market news."
    )

    return notes


weekly_notes = build_weekly_notes()

# Automatically reconstruct and persist each available historical trading week.
# The SQLite file remains on disk between local app runs.
archive_config_key, archive_config_label, archived_week_count = (
    backfill_weekly_archive(
        portfolio_series_data=portfolio,
        prices=price_data[available_tickers],
        weights=weights,
        benchmark_prices=benchmark_data,
        benchmark_ticker=benchmark_ticker,
        benchmark_name=benchmark_name,
        target_value=target,
        target_years=horizon_years,
        equity_allocation_pct=equity_pct,
        debt_allocation_pct=debt_pct,
        cash_allocation_pct=cash_pct,
        weighting_method=weight_method,
        history_label=period_choice,
    )
)

# ============================================================
# HEADER
# ============================================================

st.markdown(
    '<div class="broke-brand">BROKE | Command Center</div>',
    unsafe_allow_html=True,
)

st.markdown(
    f'<p style="color:#ffffff !important;font-size:16px;">'
    f'Simulated ₹1 crore portfolio | Target: {money(target)} | '
    f'Analysis: {start_date} to {end_date}</p>',
    unsafe_allow_html=True,
)

st.markdown(
    '<div class="broke-note">'
    'Educational portfolio simulation using historical market prices. '
    'Returns are not guaranteed and are not a prediction of future returns.'
    '</div>',
    unsafe_allow_html=True,
)

# ============================================================
# COMMAND CENTER
# ============================================================

if page == "Command Center":
    c1, c2, c3, c4, c5 = st.columns(5)

    c1.metric(
        "Current portfolio value",
        money(current_value),
        percentage(total_return),
        delta_color="normal",
    )
    c2.metric(
        "Latest weekly P&L",
        money(weekly_change),
        percentage(weekly_return),
        delta_color="normal",
    )
    c3.metric(
        "Annualised volatility",
        percentage(annual_volatility),
        help="Sample standard deviation of daily portfolio returns annualised using 252 trading days.",
    )
    c4.metric(
        "Target progress",
        f"{min(current_value / target * 100, 999):.2f}%"
        if target else "N/A",
    )
    c5.metric(
        "Remaining to target",
        money(max(target - current_value, 0)),
    )

    st.markdown("## Portfolio Growth")

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=portfolio.index,
        y=portfolio.values,
        mode="lines",
        name="Portfolio value",
        line=dict(color="#e1bb70", width=3),
        fill="tozeroy",
        fillcolor="rgba(225,187,112,0.10)",
    ))
    fig.add_hline(
        y=target,
        line_dash="dash",
        line_color="#ffffff",
        annotation_text="Target",
        annotation_font_color="#ffffff",
    )
    fig.update_layout(
        template="plotly_dark",
        paper_bgcolor="#0b0b0b",
        plot_bgcolor="#171717",
        font=dict(color="#ffffff"),
        xaxis_title="Date",
        yaxis_title="Portfolio value (₹)",
        hovermode="x unified",
        margin=dict(l=10, r=10, t=25, b=10),
        legend=dict(font=dict(color="#ffffff")),
    )
    fig.update_yaxes(tickformat=",.0f", gridcolor="#383838")
    fig.update_xaxes(gridcolor="#383838")
    st.plotly_chart(fig, use_container_width=True)

    left, right = st.columns([1, 1])

    with left:
        st.markdown("## Asset Allocation")
        allocation = pd.DataFrame([
            {"Asset Class": "Equity", "Weight": equity_pct},
            {"Asset Class": "Debt", "Weight": debt_pct},
            {"Asset Class": "Cash", "Weight": cash_pct},
        ])
        allocation = allocation[allocation["Weight"] > 0]

        pie = px.pie(
            allocation,
            names="Asset Class",
            values="Weight",
            hole=0.55,
            color="Asset Class",
            color_discrete_map={
                "Equity": "#e1bb70",
                "Debt": "#999999",
                "Cash": "#555555",
            },
        )
        pie.update_layout(
            template="plotly_dark",
            paper_bgcolor="#0b0b0b",
            plot_bgcolor="#171717",
            font=dict(color="#ffffff"),
            legend=dict(font=dict(color="#ffffff")),
        )
        pie.update_traces(
            textfont_color="#ffffff",
            textinfo="percent",
        )
        st.plotly_chart(pie, use_container_width=True)

    with right:
        st.markdown("## Weekly Intelligence")
        for note in weekly_notes[:5]:
            st.markdown(f"- {note}")

    st.markdown("## Key Risk Indicators")
    r1, r2, r3 = st.columns(3)
    r1.metric(
        "Annualised volatility",
        percentage(annual_volatility),
    )
    r2.metric(
        "Maximum drawdown",
        percentage(max_drawdown),
    )
    r3.metric(
        "Total P&L since start",
        money(total_profit_loss),
    )

# ============================================================
# HOLDINGS & ALLOCATION
# ============================================================

elif page == "Holdings & Allocation":
    st.markdown("## Holdings & Allocation")

    rows = []
    for ticker, weight in weights.items():
        if ticker == "CASH":
            rows.append({
                "Instrument": "Cash reserve",
                "Ticker": "CASH",
                "Asset class": "Cash",
                "Weight": weight,
                "Latest price (₹)": np.nan,
                "Estimated allocation (₹)": INITIAL_CAPITAL * weight,
            })
            continue

        price = (
            float(price_data[ticker].dropna().iloc[-1])
            if ticker in price_data and price_data[ticker].notna().any()
            else np.nan
        )

        asset_type = (
            "Debt" if ticker in DEBT_INSTRUMENTS.values()
            else "Equity"
        )

        rows.append({
            "Instrument": ticker,
            "Ticker": ticker,
            "Asset class": asset_type,
            "Weight": weight,
            "Latest price (₹)": price,
            "Estimated allocation (₹)": INITIAL_CAPITAL * weight,
        })

    holdings = pd.DataFrame(rows)
    holdings["Weight (%)"] = holdings["Weight"] * 100
    holdings["Estimated allocation (₹)"] = (
        holdings["Estimated allocation (₹)"].round(2)
    )

    st.dataframe(
        holdings[[
            "Instrument", "Ticker", "Asset class", "Weight (%)",
            "Latest price (₹)", "Estimated allocation (₹)"
        ]],
        use_container_width=True,
        hide_index=True,
    )

    st.markdown("### Weighting methodology")
    if weight_method == "Market-cap proxy":
        st.write(
            "Equity allocation is distributed using predefined relative "
            "scores intended to approximate a market-cap-style approach. "
            "These scores are illustrative and are not current market caps."
        )
    elif weight_method == "Equal weighting":
        st.write(
            "Each selected equity receives an equal share of the equity "
            "allocation. Debt instruments split the debt allocation equally."
        )
    else:
        st.write(
            "Equity weights are based on inverse historical volatility: "
            "lower-volatility stocks receive higher relative weights. "
            "This is a simplified risk-based method, not a guarantee of lower risk."
        )

    st.markdown("### Debt instrument and credit-risk limitations")
    if selected_debt:
        st.write(
            "The selected debt holdings are exchange-traded debt/liquid ETFs. Their traded prices can be affected by interest-rate changes, duration, liquidity and the quality of the underlying securities. "
            "An ETF is not the same as a single bond with a fixed maturity value, and its market price can fluctuate."
        )
        st.write(
            "This version does not independently verify live issuer credit ratings, yield-to-maturity, duration, credit spreads or default probabilities. "
            "For a complete credit-risk assessment, use the latest fund factsheet, underlying portfolio disclosure, bond terms and rating-agency report."
        )
    else:
        st.info("No debt instrument is selected. Add a debt ETF to review its price behaviour and allocation.")

    st.markdown("### Holding contribution")
    if not contributions.empty:
        chart = px.bar(
            contributions,
            x="Instrument",
            y="Contribution",
            color="Contribution",
            color_continuous_scale=["#dc6969", "#777777", "#e1bb70"],
            title="Estimated contribution to portfolio return",
        )
        chart.update_layout(
            template="plotly_dark",
            paper_bgcolor="#0b0b0b",
            plot_bgcolor="#171717",
            font=dict(color="#ffffff"),
            coloraxis_showscale=False,
        )
        chart.update_yaxes(tickformat=".2%")
        st.plotly_chart(chart, use_container_width=True)

        st.dataframe(
            contributions,
            use_container_width=True,
            hide_index=True,
        )

# ============================================================
# WEEKLY INTELLIGENCE
# ============================================================

elif page == "Weekly Intelligence":
    st.markdown("## Weekly Intelligence Report")

    st.write(
        f"The report analyses the selected interval from {start_date} to {end_date}. "
        "For weekly interpretation, choose a seven-day interval; longer date ranges "
        "show start-to-end performance across that full period. Market holidays and "
        "missing observations can affect the number of sessions included."
    )

    m1, m2, m3, m4, m5 = st.columns(5)
    m1.metric("Weekly P&L", money(weekly_change), percentage(weekly_return))
    m2.metric("Latest value", money(current_value))
    m3.metric("Full-period return", percentage(total_return))
    m4.metric("Annualised volatility", percentage(annual_volatility))
    m5.metric(
        "Portfolio beta vs. " + benchmark_name,
        f"{benchmark_beta:.2f}" if pd.notna(benchmark_beta) else "N/A",
    )

    st.markdown("### Why did the portfolio move?")
    for i, note in enumerate(weekly_notes, start=1):
        st.markdown(f"**{i}.** {note}")

    st.markdown("### Biggest contributors")
    if not contributions.empty:
        st.dataframe(
            contributions[[
                "Instrument", "Type", "Weight",
                "Period Return", "Contribution", "Contribution INR"
            ]],
            use_container_width=True,
            hide_index=True,
        )

    st.markdown("### Weekly price movement")
    if len(portfolio) > 1:
        weekly_chart = px.line(
            portfolio.tail(30).reset_index(),
            x=portfolio.tail(30).index,
            y=portfolio.tail(30).values,
            title="Portfolio value — latest available observations",
        )
        weekly_chart.update_layout(
            template="plotly_dark",
            paper_bgcolor="#0b0b0b",
            plot_bgcolor="#171717",
            font=dict(color="#ffffff"),
            xaxis_title="Date",
            yaxis_title="Portfolio value (₹)",
        )
        st.plotly_chart(weekly_chart, use_container_width=True)

    st.markdown("### Understanding the reasons")
    st.markdown("""
    The report separates **measured performance** from **possible causes**:

    - **Measured performance:** historical prices, weighted returns,
      holding-level contribution, and benchmark comparison.
    - **Possible causes to investigate:** earnings announcements, company
      guidance, sector trends, interest-rate changes, macroeconomic data,
      and broader market movements.
    - **Evidence limitation:** price movements alone cannot establish
      causation. Check company filings and reliable news before assigning
      a specific cause to a gain or loss.
    """)

    report_data = {
        "Initial investment": money(INITIAL_CAPITAL),
        "Current estimated value": money(current_value),
        "Total profit/loss": money(total_profit_loss),
        "Full-period return": percentage(total_return),
        "Latest weekly P&L": money(weekly_change),
        "Latest weekly return": percentage(weekly_return),
        "Target value": money(target),
        "Target horizon": f"{horizon_years} years",
        "Annualised portfolio volatility": percentage(annual_volatility),
        "Maximum drawdown": percentage(max_drawdown),
        "Portfolio beta vs benchmark": (
            f"{benchmark_beta:.2f}" if pd.notna(benchmark_beta) else "N/A"
        ),
        "Annualised benchmark volatility": percentage(benchmark_volatility),
        "Benchmark": benchmark_name,
        "Benchmark return": percentage(benchmark_return),
        "Equity / Debt / Cash": (
            f"{equity_pct}% / {debt_pct}% / {cash_pct}%"
        ),
        "Weighting method": weight_method,
        "Historical period": period_choice,
        "Selected analysis interval": f"{start_date} to {end_date}",
        "Data source": "Yahoo Finance via yfinance; figures may be incomplete or delayed",
    }

    st.markdown("### Download the report")
    pdf_bytes = make_pdf_report(
        report_data, contributions, weekly_notes
    )

    st.download_button(
        "Download Weekly PDF Report",
        data=pdf_bytes,
        file_name=f"BROKE_weekly_report_{date.today()}.pdf",
        mime="application/pdf",
        use_container_width=True,
    )

    report_csv = contributions.to_csv(index=False).encode("utf-8")
    st.download_button(
        "Download Contribution CSV",
        data=report_csv,
        file_name=f"BROKE_contributions_{date.today()}.csv",
        mime="text/csv",
        use_container_width=True,
    )

    text_report = [
        "BROKE | WEEKLY PORTFOLIO INTELLIGENCE REPORT",
        f"Generated: {date.today()}",
        "",
    ]
    text_report.extend(
        f"{key}: {value}" for key, value in report_data.items()
    )
    text_report.extend(["", "WEEKLY MOVEMENT ANALYSIS"])
    text_report.extend(f"- {note}" for note in weekly_notes)
    text_report.extend([
        "",
        "LIMITATION: Historical price contribution does not prove causation.",
        "Educational simulation only; not investment advice.",
    ])

    st.download_button(
        "Download Plain-Text Report",
        data="\n".join(text_report),
        file_name=f"BROKE_report_{date.today()}.txt",
        mime="text/plain",
        use_container_width=True,
    )

# ============================================================
# RISK LAB
# ============================================================

elif page == "Risk Lab":
    st.markdown("## Risk Lab")

    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Annualised portfolio volatility", percentage(annual_volatility))
    c2.metric("Maximum drawdown", percentage(max_drawdown))
    c3.metric(
        "Portfolio beta vs. " + benchmark_name,
        f"{benchmark_beta:.2f}" if pd.notna(benchmark_beta) else "N/A",
        help="Covariance of daily portfolio and benchmark returns divided by benchmark return variance.",
    )
    c4.metric("Annualised benchmark volatility", percentage(benchmark_volatility))
    c5.metric("Total return", percentage(total_return))

    st.markdown("### What the volatility measurement means")
    st.write(
        "Annualised volatility is the sample standard deviation of daily "
        "portfolio returns multiplied by the square root of 252 trading days. "
        "It measures the scale of historical fluctuations; it does not "
        "predict future returns or the probability of a loss."
    )

    if pd.notna(benchmark_beta):
        if benchmark_beta > 1:
            beta_text = "historically more sensitive to benchmark movements"
        elif benchmark_beta < 1:
            beta_text = "historically less sensitive to benchmark movements"
        else:
            beta_text = "historically similarly sensitive to benchmark movements"
        st.info(
            f"Estimated beta: {benchmark_beta:.2f}. The portfolio was "
            f"{beta_text} over the selected historical period."
        )
    else:
        st.warning(
            "Beta is unavailable: there are insufficient overlapping daily "
            "returns or the benchmark return variance is zero."
        )

    st.markdown("### Holding-level beta and volatility")
    holding_risk_rows = []
    benchmark_daily_for_risk = benchmark_daily_returns.dropna()
    for ticker in [t for t in weights if t != "CASH" and t in price_data.columns]:
        asset_ret = price_data[ticker].pct_change().dropna()
        asset_vol = asset_ret.std(ddof=1) * np.sqrt(252) if len(asset_ret) > 1 else np.nan
        aligned_asset = pd.concat(
            [asset_ret.rename("Asset"), benchmark_daily_for_risk.rename("Benchmark")],
            axis=1, join="inner"
        ).dropna()
        asset_beta = np.nan
        if len(aligned_asset) > 1 and aligned_asset["Benchmark"].var(ddof=1) > 0:
            asset_beta = aligned_asset["Asset"].cov(aligned_asset["Benchmark"]) / aligned_asset["Benchmark"].var(ddof=1)
        asset_series = price_data[ticker].dropna()
        asset_period_return = asset_series.iloc[-1] / asset_series.iloc[0] - 1 if len(asset_series) > 1 and asset_series.iloc[0] else np.nan
        holding_risk_rows.append({
            "Ticker": ticker,
            "Asset class": "Debt ETF" if ticker in DEBT_INSTRUMENTS.values() else "Equity",
            "Portfolio weight": weights.get(ticker, 0.0),
            "Period return": asset_period_return,
            "Annualised volatility": asset_vol,
            "Beta vs benchmark": asset_beta,
        })
    if holding_risk_rows:
        holding_risk = pd.DataFrame(holding_risk_rows)
        holding_risk["Portfolio weight"] = holding_risk["Portfolio weight"].map(lambda x: f"{x*100:.2f}%")
        holding_risk["Period return"] = holding_risk["Period return"].map(percentage)
        holding_risk["Annualised volatility"] = holding_risk["Annualised volatility"].map(percentage)
        holding_risk["Beta vs benchmark"] = holding_risk["Beta vs benchmark"].map(lambda x: f"{x:.2f}" if pd.notna(x) else "N/A")
        st.dataframe(holding_risk, use_container_width=True, hide_index=True)

    rolling_volatility = daily_returns.rolling(21).std(ddof=1) * np.sqrt(252)
    rolling_volatility = rolling_volatility.dropna()

    st.markdown("### Rolling 21-day annualised volatility")
    if not rolling_volatility.empty:
        rolling_vol_frame = pd.DataFrame({
            "Date": rolling_volatility.index,
            "Annualised volatility": rolling_volatility.values,
        })
        rolling_vol_chart = px.line(
            rolling_vol_frame,
            x="Date",
            y="Annualised volatility",
            title="How portfolio volatility changed over time",
        )
        rolling_vol_chart.update_layout(
            template="plotly_dark",
            paper_bgcolor="#0b0b0b",
            plot_bgcolor="#171717",
            font=dict(color="#ffffff"),
        )
        rolling_vol_chart.update_yaxes(tickformat=".0%")
        st.plotly_chart(rolling_vol_chart, use_container_width=True)
    else:
        st.info(
            "At least 22 daily portfolio observations are needed for the "
            "rolling volatility chart."
        )

    st.markdown("### Drawdown over time")
    drawdown_frame = pd.DataFrame({
        "Date": drawdown_series.index,
        "Drawdown": drawdown_series.values,
    })

    drawdown_chart = px.area(
        drawdown_frame,
        x="Date",
        y="Drawdown",
        title="Portfolio drawdown from previous peak",
    )
    drawdown_chart.update_layout(
        template="plotly_dark",
        paper_bgcolor="#0b0b0b",
        plot_bgcolor="#171717",
        font=dict(color="#ffffff"),
    )
    drawdown_chart.update_yaxes(tickformat=".0%")
    st.plotly_chart(drawdown_chart, use_container_width=True)

    st.markdown("### Daily return distribution")
    if not daily_returns.empty:
        hist = px.histogram(
            x=daily_returns.values,
            nbins=35,
            title="Distribution of daily portfolio returns",
            labels={"x": "Daily return"},
        )
        hist.update_layout(
            template="plotly_dark",
            paper_bgcolor="#0b0b0b",
            plot_bgcolor="#171717",
            font=dict(color="#ffffff"),
        )
        hist.update_xaxes(tickformat=".1%")
        st.plotly_chart(hist, use_container_width=True)

    st.markdown("### Risk definitions")
    st.markdown("""
    - **Volatility:** annualised standard deviation of daily returns.
      Higher volatility indicates larger historical fluctuations.
    - **Maximum drawdown:** largest decline from a previous portfolio peak.
    - **Historical risk:** these measurements describe the selected
      historical period and may not represent future risk.
    """)

# ============================================================
# TECHNICAL ANALYSIS — CANDLESTICKS, SMA, RSI, MACD
# ============================================================

elif page == "Technical Analysis":
    st.markdown("## Technical Analysis")
    st.write(
        "Candlesticks show open, high, low and close prices for each trading session. "
        "Indicators are descriptive tools and should not be treated as certain buy/sell signals."
    )
    available_for_chart = [
        name for name, ticker in COMPANIES.items()
        if ticker in selected_tickers
    ]
    if not available_for_chart:
        available_for_chart = list(COMPANIES.keys())
    chart_company = st.selectbox(
        "Choose company for candlestick analysis",
        available_for_chart,
        key="technical_company",
    )
    chart_ticker = COMPANIES[chart_company]
    candle_period = st.selectbox(
        "Candlestick interval",
        ["Daily", "Weekly"],
        key="candle_interval",
        help="Weekly candles aggregate each trading week into one OHLC candle.",
    )
    with st.spinner("Loading OHLC data and calculating technical indicators..."):
        ohlc = download_ohlc(chart_ticker, start_date - timedelta(days=90), end_date)

    if ohlc.empty:
        st.warning(
            f"OHLC data could not be loaded for {chart_company} ({chart_ticker}) "
            f"from {start_date} to {end_date}. Check your internet connection, "
            "Yahoo Finance availability, ticker symbol and selected dates. "
            "Try refreshing the app or selecting a longer date range."
        )
        with st.expander("Technical data troubleshooting"):
            st.write("The chart requires Open, High, Low and Close prices from Yahoo Finance.")
            st.code("py -m pip install --upgrade yfinance pandas plotly")
            st.write("If all companies fail, the issue is likely connectivity or Yahoo Finance availability rather than the chart itself.")
    else:
        if candle_period == "Weekly":
            aggregation = {"Open":"first", "High":"max", "Low":"min", "Close":"last"}
            if "Volume" in ohlc.columns:
                aggregation["Volume"] = "sum"
            ohlc = ohlc.resample("W-FRI").agg(aggregation).dropna(subset=["Open","High","Low","Close"])
        technical = add_technical_indicators(ohlc)
        technical_display = technical.loc[
            (technical.index.date >= start_date) & (technical.index.date <= end_date)
        ].copy()

        if technical_display.empty:
            st.warning("No candles fall inside the selected dates. Check the date range and ticker availability.")
        else:
            last_close = float(technical_display["Close"].iloc[-1])
            previous_close = (
                float(technical_display["Close"].iloc[-2])
                if len(technical_display) > 1 else last_close
            )
            move = last_close / previous_close - 1 if previous_close else np.nan
            t1, t2, t3, t4 = st.columns(4)
            t1.metric("Latest close", f"₹{last_close:,.2f}", percentage(move))
            t2.metric("SMA 20", f"₹{technical_display['SMA 20'].iloc[-1]:,.2f}" if pd.notna(technical_display["SMA 20"].iloc[-1]) else "N/A")
            t3.metric("SMA 50", f"₹{technical_display['SMA 50'].iloc[-1]:,.2f}" if pd.notna(technical_display["SMA 50"].iloc[-1]) else "N/A")
            latest_rsi = technical_display["RSI 14"].iloc[-1]
            t4.metric("RSI (14)", f"{latest_rsi:.1f}" if pd.notna(latest_rsi) else "N/A")

            candle_fig = go.Figure()
            candle_fig.add_trace(go.Candlestick(
                x=technical_display.index,
                open=technical_display["Open"],
                high=technical_display["High"],
                low=technical_display["Low"],
                close=technical_display["Close"],
                name=chart_company,
                increasing_line_color="#34c98b",
                decreasing_line_color="#f06464",
                increasing_fillcolor="#34c98b",
                decreasing_fillcolor="#f06464",
            ))
            candle_fig.add_trace(go.Scatter(
                x=technical_display.index, y=technical_display["SMA 20"],
                mode="lines", name="SMA 20", line=dict(color="#e1bb70", width=1.8)
            ))
            candle_fig.add_trace(go.Scatter(
                x=technical_display.index, y=technical_display["SMA 50"],
                mode="lines", name="SMA 50", line=dict(color="#69b9ff", width=1.8)
            ))
            candle_fig.update_layout(
                template="plotly_dark", paper_bgcolor="#0b0b0b", plot_bgcolor="#171717",
                font=dict(color="#ffffff"), xaxis_title="Date", yaxis_title="Price (₹)",
                xaxis_rangeslider_visible=False, hovermode="x unified",
                margin=dict(l=10,r=10,t=25,b=10),
            )
            st.plotly_chart(candle_fig, use_container_width=True)

            indicator_col1, indicator_col2 = st.columns(2)
            with indicator_col1:
                rsi_fig = go.Figure()
                rsi_fig.add_trace(go.Scatter(
                    x=technical_display.index, y=technical_display["RSI 14"],
                    mode="lines", name="RSI 14", line=dict(color="#c9a7ff", width=2)
                ))
                rsi_fig.add_hline(y=70, line_dash="dash", line_color="#f06464")
                rsi_fig.add_hline(y=30, line_dash="dash", line_color="#34c98b")
                rsi_fig.update_layout(
                    title="Relative Strength Index (14)", template="plotly_dark",
                    paper_bgcolor="#0b0b0b", plot_bgcolor="#171717",
                    font=dict(color="#ffffff"), yaxis=dict(range=[0,100]),
                )
                st.plotly_chart(rsi_fig, use_container_width=True)
            with indicator_col2:
                macd_fig = go.Figure()
                macd_fig.add_trace(go.Scatter(
                    x=technical_display.index, y=technical_display["MACD"],
                    mode="lines", name="MACD", line=dict(color="#e1bb70", width=2)
                ))
                macd_fig.add_trace(go.Scatter(
                    x=technical_display.index, y=technical_display["MACD Signal"],
                    mode="lines", name="Signal", line=dict(color="#69b9ff", width=2)
                ))
                macd_fig.update_layout(
                    title="MACD (12, 26, 9)", template="plotly_dark",
                    paper_bgcolor="#0b0b0b", plot_bgcolor="#171717",
                    font=dict(color="#ffffff"),
                )
                st.plotly_chart(macd_fig, use_container_width=True)

            st.markdown("### Technical interpretation")
            if pd.notna(latest_rsi):
                if latest_rsi >= 70:
                    st.write(f"RSI is {latest_rsi:.1f}, often described as an overbought zone. This alone is not a sell signal.")
                elif latest_rsi <= 30:
                    st.write(f"RSI is {latest_rsi:.1f}, often described as an oversold zone. This alone is not a buy signal.")
                else:
                    st.write(f"RSI is {latest_rsi:.1f}, within the commonly used 30–70 range.")
            sma20 = technical_display["SMA 20"].iloc[-1]
            sma50 = technical_display["SMA 50"].iloc[-1]
            if pd.notna(sma20) and pd.notna(sma50):
                if sma20 > sma50:
                    st.write("SMA 20 is above SMA 50, indicating a positive short-to-medium-term trend in this sample.")
                else:
                    st.write("SMA 20 is below SMA 50, indicating a weaker short-to-medium-term trend in this sample.")
            st.caption(
                "Candlesticks and indicators are based on adjusted Yahoo Finance OHLC data. "
                "Technical signals can fail, and this page does not predict prices."
            )
            st.download_button(
                "Download technical data (CSV)",
                data=technical_display.to_csv().encode("utf-8"),
                file_name=f"BROKE_technical_{chart_ticker.replace('^','')}_{start_date}_{end_date}.csv",
                mime="text/csv",
            )

# ============================================================
# FUNDAMENTALS & VALUATION
# ============================================================

elif page == "Fundamentals & Valuation":
    st.markdown("## Fundamentals, Financial Ratios & Valuation")
    st.write(
        "Company metrics are retrieved from the available Yahoo Finance profile. "
        "Coverage can be incomplete, and provider figures should be checked against annual reports or exchange filings."
    )
    fundamental_names = list(COMPANIES.keys())
    fundamental_company = st.selectbox(
        "Select company", fundamental_names, key="fundamental_company"
    )
    fundamental_ticker = COMPANIES[fundamental_company]
    with st.spinner("Fetching available company fundamentals..."):
        fundamentals = get_company_fundamentals(fundamental_ticker)

    if fundamentals:
        rows = []
        for label, value in fundamentals.items():
            if isinstance(value, (float, int, np.floating, np.integer)):
                if pd.isna(value):
                    display_value = "Not available"
                elif label in ["ROE", "ROA", "Profit margin", "Operating margin", "Revenue growth", "Earnings growth", "Dividend yield"]:
                    display_value = f"{value * 100:.2f}%"
                elif label == "Market capitalisation (₹)":
                    display_value = money(value)
                else:
                    display_value = f"{value:,.2f}"
            else:
                display_value = str(value)
            rows.append({"Metric": label, "Value": display_value})
        st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

    st.markdown("### Historical financial statement trend")
    try:
        company_object = yf.Ticker(fundamental_ticker)
        financials = company_object.financials
        if financials is not None and not financials.empty:
            desired_rows = [
                label for label in [
                    "Total Revenue", "Operating Income", "Net Income",
                    "Gross Profit", "EBITDA"
                ] if label in financials.index
            ]
            if desired_rows:
                trend = financials.loc[desired_rows].copy()
                trend.columns = [str(pd.Timestamp(col).date()) if not pd.isna(col) else str(col) for col in trend.columns]
                trend = trend.T.reset_index().rename(columns={"index": "Financial period"})
                st.dataframe(trend, use_container_width=True, hide_index=True)
                for metric in ["Total Revenue", "Operating Income", "Net Income"]:
                    if metric in financials.index:
                        series = financials.loc[metric].dropna()
                        if len(series) >= 2:
                            newest, older = float(series.iloc[0]), float(series.iloc[1])
                            if older != 0:
                                st.write(f"{metric}: latest reported value is {percentage(newest / older - 1)} compared with the previous available annual period.")
            else:
                st.info("The provider did not return standard annual revenue/profit rows for this company.")
        else:
            st.info("Annual financial statement data is not available from the selected data provider.")
    except Exception:
        st.info("Could not retrieve annual financial statements. Verify figures from the company's annual report or NSE/BSE filings.")

    st.markdown("### Ratio interpretation and risk flags")
    if fundamentals:
        flag_messages = []
        pe = fundamentals.get("Trailing P/E", np.nan)
        roe = fundamentals.get("ROE", np.nan)
        de = fundamentals.get("Debt-to-equity", np.nan)
        cr = fundamentals.get("Current ratio", np.nan)
        margin = fundamentals.get("Profit margin", np.nan)
        if pd.notna(pe) and pe > 35:
            flag_messages.append("Trailing P/E is relatively high (above 35); compare with peers and expected growth rather than treating it alone as overvaluation.")
        if pd.notna(roe) and roe < 0.08:
            flag_messages.append("Reported ROE is below 8%; review profitability, capital structure and sector norms.")
        if pd.notna(de) and de > 150:
            flag_messages.append("Debt-to-equity is above 150% in the provider's reported units; verify the provider's definition and compare with sector peers.")
        if pd.notna(cr) and cr < 1:
            flag_messages.append("Current ratio is below 1; investigate short-term liquidity and working capital.")
        if pd.notna(margin) and margin < 0:
            flag_messages.append("Reported profit margin is negative; examine recent results and one-off items.")
        if flag_messages:
            for flag in flag_messages:
                st.warning(flag)
        else:
            st.info("No simple threshold flag was triggered from the available fields. This is not proof that the company is low-risk.")
    st.caption("Ratio thresholds are screening prompts only. Appropriate levels vary by industry, accounting treatment and reporting period.")

    st.markdown("### Valuation tools")
    val1, val2 = st.columns(2)
    with val1:
        current_price = st.number_input(
            "Current market price per share (₹)", min_value=0.0, value=100.0, step=1.0,
            key="ddm_price"
        )
        annual_dividend = st.number_input(
            "Expected next-year dividend per share (₹)", min_value=0.0, value=3.0, step=0.25,
            key="ddm_dividend"
        )
        dividend_growth = st.number_input(
            "Expected constant dividend growth (%)", min_value=-20.0, max_value=30.0,
            value=5.0, step=0.5, key="ddm_growth"
        ) / 100
        cost_equity = st.number_input(
            "Required return / cost of equity (%)", min_value=0.1, max_value=50.0,
            value=12.0, step=0.5, key="ddm_cost"
        ) / 100
        if cost_equity > dividend_growth:
            ddm_value = annual_dividend / (cost_equity - dividend_growth)
            st.metric("DDM estimated value per share", f"₹{ddm_value:,.2f}")
            if current_price > 0:
                st.metric("DDM implied upside/downside", percentage(ddm_value/current_price - 1))
        else:
            st.warning("For the Gordon Growth DDM, required return must be greater than dividend growth.")
    with val2:
        st.markdown("#### P/E scenario valuation")
        eps = st.number_input("Earnings per share (₹)", min_value=0.0, value=10.0, step=0.5, key="pe_eps")
        peer_pe = st.number_input("Assumed peer/sector P/E", min_value=0.0, value=20.0, step=0.5, key="pe_multiple")
        pe_value = eps * peer_pe
        st.metric("P/E-based estimated value", f"₹{pe_value:,.2f}")
        if current_price > 0:
            st.metric("P/E implied upside/downside", percentage(pe_value/current_price - 1))
        st.caption("EPS and peer P/E are user assumptions. Replace them with sourced figures before using the result.")

    st.markdown("### Investment cash-flow analysis: ROI, NPV and IRR")
    st.caption("Enter the initial investment and future cash flows. These are scenario calculations, not forecasts.")
    cf1, cf2, cf3 = st.columns(3)
    with cf1:
        initial_outflow = st.number_input("Initial investment (₹)", min_value=1.0, value=100000.0, step=1000.0, key="cashflow_initial")
    with cf2:
        annual_cashflow = st.number_input("Annual cash inflow (₹)", min_value=0.0, value=18000.0, step=1000.0, key="cashflow_annual")
    with cf3:
        cashflow_years = st.number_input("Years", min_value=1, max_value=30, value=5, step=1, key="cashflow_years")
    discount_rate = st.number_input("Discount rate (%)", min_value=0.0, max_value=100.0, value=10.0, step=0.5, key="cashflow_discount") / 100
    cashflows = [-float(initial_outflow)] + [float(annual_cashflow)] * int(cashflow_years)
    npv_value = sum(cf / ((1 + discount_rate) ** period) for period, cf in enumerate(cashflows))
    roi_value = (sum(cashflows[1:]) - initial_outflow) / initial_outflow
    irr_value = np.nan
    # npf is optional; use numpy_financial if installed, otherwise bisection IRR.
    try:
        import numpy_financial as npf
        irr_value = float(npf.irr(cashflows))
    except Exception:
        def npv_at_rate(rate):
            return sum(cf / ((1 + rate) ** period) for period, cf in enumerate(cashflows))
        low, high = -0.999, 10.0
        try:
            if npv_at_rate(low) * npv_at_rate(high) <= 0:
                for _ in range(250):
                    mid = (low + high) / 2
                    if npv_at_rate(low) * npv_at_rate(mid) <= 0:
                        high = mid
                    else:
                        low = mid
                irr_value = (low + high) / 2
            else:
                irr_value = np.nan
        except Exception:
            irr_value = np.nan
    fm1, fm2, fm3 = st.columns(3)
    fm1.metric("ROI over full scenario", percentage(roi_value))
    fm2.metric("NPV at selected discount rate", money(npv_value))
    fm3.metric("IRR", percentage(irr_value) if pd.notna(irr_value) else "Not solvable")
    st.caption("The simple ROI above compares total undiscounted inflows with the initial outlay. NPV discounts each cash flow; IRR solves for a rate that makes NPV zero.")

# ============================================================
# INVESTMENT THEORIES & PERFORMANCE METRICS
# ============================================================

elif page == "Investment Theories & Metrics":
    st.markdown("## Investment Theories & Performance Metrics")
    st.write("Use this section to connect portfolio evidence with the theories named in the assignment.")

    risk_free_rate = st.number_input(
        "Annual risk-free rate (%)", min_value=0.0, max_value=30.0, value=7.0, step=0.25,
        key="theory_risk_free"
    ) / 100
    portfolio_return_annual = (1 + total_return) ** (252 / max(len(daily_returns), 1)) - 1 if total_return > -1 and len(daily_returns) > 0 else np.nan
    market_return_annual = (
        (1 + benchmark_return) ** (252 / max(len(benchmark_daily_returns.dropna()), 1)) - 1
        if pd.notna(benchmark_return) and benchmark_return > -1 and len(benchmark_daily_returns.dropna()) > 0
        else np.nan
    )
    sharpe = (
        (daily_returns.mean() * 252 - risk_free_rate) / annual_volatility
        if pd.notna(annual_volatility) and annual_volatility > 0 else np.nan
    )
    alpha = (
        portfolio_return_annual - (
            risk_free_rate + benchmark_beta * (market_return_annual - risk_free_rate)
        )
        if pd.notna(portfolio_return_annual) and pd.notna(market_return_annual) and pd.notna(benchmark_beta)
        else np.nan
    )
    tm1, tm2, tm3 = st.columns(3)
    tm1.metric("Sharpe Ratio", f"{sharpe:.2f}" if pd.notna(sharpe) else "N/A")
    tm2.metric("CAPM / Jensen's Alpha", percentage(alpha) if pd.notna(alpha) else "N/A")
    tm3.metric("Portfolio Beta", f"{benchmark_beta:.2f}" if pd.notna(benchmark_beta) else "N/A")
    st.caption("Alpha and Sharpe are historical estimates. Annualisation can be unstable for short date ranges.")

    st.markdown("### Modern Portfolio Theory (MPT)")
    valid_assets = [t for t in weights if t != "CASH" and t in price_data.columns]
    if len(valid_assets) >= 2:
        asset_returns = price_data[valid_assets].pct_change().dropna(how="all")
        corr = asset_returns.corr()
        corr_fig = px.imshow(
            corr, text_auto=".2f", aspect="auto", color_continuous_scale="RdBu",
            zmin=-1, zmax=1, title="Selected assets: return correlation matrix"
        )
        corr_fig.update_layout(
            template="plotly_dark", paper_bgcolor="#0b0b0b", plot_bgcolor="#171717",
            font=dict(color="#ffffff")
        )
        st.plotly_chart(corr_fig, use_container_width=True)
        st.write("MPT uses diversification and correlations to understand how holdings may combine to affect portfolio risk. Correlations change over time.")
    else:
        st.info("Select at least two assets to calculate correlations.")

    st.markdown("### Capital Asset Pricing Model (CAPM)")
    st.latex(r"E(R_i) = R_f + \\beta_i(E(R_m)-R_f)")
    if pd.notna(benchmark_beta) and pd.notna(market_return_annual):
        expected_capm = risk_free_rate + benchmark_beta * (market_return_annual - risk_free_rate)
        st.write(f"Using the selected period's annualised benchmark return, the CAPM expected portfolio return is approximately {percentage(expected_capm)}.")
    st.write("CAPM links expected return with the risk-free rate, beta and market risk premium. Historical alpha compares observed return with this estimate.")

    st.markdown("### Efficient Market Hypothesis (EMH)")
    st.write("EMH suggests that prices incorporate available information to varying degrees. This dashboard can compare price movements with public information, but it cannot prove market efficiency from a short sample.")

    st.markdown("### Behavioral Finance")
    st.write("Review possible behavioural risks such as overconfidence, loss aversion, herd behaviour and excessive concentration. Compare your intended allocation with actual weights before making changes.")
    concentration = sum(float(w) ** 2 for t, w in weights.items() if t != "CASH")
    st.metric("Equity/debt holding concentration (HHI)", f"{concentration:.3f}")
    st.caption("Higher HHI indicates weights are more concentrated. Cash is excluded from this concentration measure.")

    st.markdown("### Arbitrage Pricing Theory (APT)")
    st.write("APT explains returns through exposure to several common factors, such as market returns, interest rates, inflation, currency movements and energy prices. This version presents the framework; a robust APT regression requires consistent factor time series, which are not automatically assumed here.")

    st.markdown("### Dividend Discount Model (DDM)")
    st.write("A DDM estimate is available on the Fundamentals & Valuation page. It is most useful for firms with meaningful, reasonably predictable dividends and is sensitive to growth and required-return assumptions.")

    st.markdown("### ROI, NPV and IRR")
    st.write("ROI, NPV and IRR scenario calculators are available on the Fundamentals & Valuation page. Use clearly sourced or explicitly assumed cash flows, not an assumption that past stock returns will repeat.")

# ============================================================
# TARGET SIMULATOR
# ============================================================

elif page == "Target Simulator":
    st.markdown("## Target Simulator")

    current_target_progress = current_value / target if target > 0 else 0
    remaining = max(target - current_value, 0)

    c1, c2, c3 = st.columns(3)
    c1.metric("Starting investment", money(INITIAL_CAPITAL))
    c2.metric("Current estimated value", money(current_value))
    c3.metric("Target amount", money(target))

    st.progress(min(max(current_target_progress, 0.0), 1.0))
    st.write(f"Current progress: **{current_target_progress * 100:.2f}%**")
    st.write(f"Amount remaining to target: **{money(remaining)}**")

    if current_value > 0 and target > current_value:
        required_annual_return = (
            (target / current_value) ** (1 / horizon_years) - 1
        )
        st.metric(
            "Required annual return from current value",
            percentage(required_annual_return),
        )
        st.caption(
            "This is a mathematical scenario, not a forecast or guarantee."
        )

    st.markdown("### Illustrative future value scenarios")
    annual_scenarios = [-0.05, 0.00, 0.05, 0.08, 0.10, 0.12, 0.15]

    scenario_rows = []
    for rate in annual_scenarios:
        future_value = current_value * ((1 + rate) ** horizon_years)
        scenario_rows.append({
            "Assumed annual return": rate,
            "Years": horizon_years,
            "Illustrative future value": future_value,
            "Difference from target": future_value - target,
        })

    scenario_df = pd.DataFrame(scenario_rows)
    scenario_df["Assumed annual return"] = (
        scenario_df["Assumed annual return"].map(
            lambda x: f"{x * 100:.1f}%"
        )
    )
    scenario_df["Illustrative future value"] = (
        scenario_df["Illustrative future value"].map(money)
    )
    scenario_df["Difference from target"] = (
        scenario_df["Difference from target"].map(money)
    )

    st.dataframe(
        scenario_df,
        use_container_width=True,
        hide_index=True,
    )

    st.warning(
        "Scenario values assume a constant annual return and exclude "
        "taxes, fees, additional contributions, and real-world volatility. "
        "They are not predictions."
    )

# ============================================================
# REPORT ARCHIVE
# ============================================================

elif page == "Report Archive":
    st.markdown("## Report Archive")

    st.write(
        "Weekly reports are stored in a local SQLite database beside app.py. "
        "The app reconstructs historical weekly reports from available price "
        "history and the currently selected portfolio holdings and weights."
    )

    st.info(
        "Historical reports created on the first run are reconstructed from "
        "historical prices. They are not original reports that were actually "
        "saved during those past weeks. Reports generated from now on are "
        "retained in the local archive and updated when the same week's "
        "market data changes."
    )

    archive_records = load_archive_records()

    if not archive_records:
        st.warning(
            "No weekly reports are available yet. Select a historical period "
            "of at least 3 months and wait for market data to load."
        )
    else:
        st.markdown(f"### Saved reports: {len(archive_records)}")

        archive_table_rows = []
        for record in archive_records:
            saved_report = json.loads(record["report_data_json"])
            archive_table_rows.append({
                "Week ending": record["week_end"],
                "Benchmark": saved_report.get("Benchmark", ""),
                "Configuration": record["config_label"],
                "Weekly return": saved_report.get("Weekly return", ""),
                "Weekly P&L": saved_report.get("Weekly P&L", ""),
                "Portfolio value": saved_report.get(
                    "Portfolio value at week end", ""
                ),
                "Saved / refreshed": record["generated_at"],
            })

        archive_table = pd.DataFrame(archive_table_rows)
        st.dataframe(
            archive_table.head(100),
            use_container_width=True,
            hide_index=True,
        )

        report_options = {}
        for record in archive_records:
            label = (
                f'{record["week_end"]} | {record["config_label"]} '
                f'| report #{record["report_id"]}'
            )
            report_options[label] = record

        st.markdown("### Open a previous weekly report")
        chosen_label = st.selectbox(
            "Choose report by week and portfolio configuration",
            list(report_options.keys()),
        )

        chosen_record = report_options[chosen_label]
        chosen_report_data = json.loads(
            chosen_record["report_data_json"]
        )
        chosen_contribution_records = json.loads(
            chosen_record["contributions_json"]
        )
        chosen_contributions = pd.DataFrame(
            chosen_contribution_records
        )
        chosen_notes = json.loads(chosen_record["notes_json"])

        st.markdown(
            f'### Report for week ending {chosen_record["week_end"]}'
        )

        for key, value in chosen_report_data.items():
            st.write(f"**{key}:** {value}")

        st.markdown("#### Weekly movement analysis")
        for note in chosen_notes:
            st.markdown(f"- {note}")

        st.markdown("#### Holding-level contribution")
        if chosen_contributions.empty:
            st.info("No holding-level contribution data was saved for this report.")
        else:
            st.dataframe(
                chosen_contributions,
                use_container_width=True,
                hide_index=True,
            )

        chosen_pdf = make_pdf_report(
            chosen_report_data,
            chosen_contributions,
            chosen_notes,
        )

        safe_week = chosen_record["week_end"].replace("-", "")
        st.download_button(
            "Download selected weekly report (PDF)",
            data=chosen_pdf,
            file_name=f"BROKE_weekly_report_{safe_week}.pdf",
            mime="application/pdf",
            use_container_width=True,
            key=f'archive_pdf_{chosen_record["report_id"]}',
        )

        chosen_text = [
            "BROKE | ARCHIVED WEEKLY PORTFOLIO REPORT",
            f'Week ending: {chosen_record["week_end"]}',
            f'Configuration: {chosen_record["config_label"]}',
            "",
        ]
        chosen_text.extend(
            f"{key}: {value}"
            for key, value in chosen_report_data.items()
        )
        chosen_text.extend(["", "WEEKLY MOVEMENT ANALYSIS"])
        chosen_text.extend(f"- {note}" for note in chosen_notes)

        st.download_button(
            "Download selected weekly report (TXT)",
            data="\\n".join(chosen_text),
            file_name=f"BROKE_weekly_report_{safe_week}.txt",
            mime="text/plain",
            use_container_width=True,
            key=f'archive_txt_{chosen_record["report_id"]}',
        )

        if not chosen_contributions.empty:
            st.download_button(
                "Download selected contributions (CSV)",
                data=chosen_contributions.to_csv(index=False).encode("utf-8"),
                file_name=f"BROKE_contributions_{safe_week}.csv",
                mime="text/csv",
                use_container_width=True,
                key=f'archive_csv_{chosen_record["report_id"]}',
            )

    st.markdown("### Current portfolio snapshot")
    snapshot = pd.DataFrame([{
        "Report date": str(date.today()),
        "Initial investment": INITIAL_CAPITAL,
        "Current estimated value": round(current_value, 2),
        "Total P&L": round(total_profit_loss, 2),
        "Full-period return": total_return,
        "Weekly P&L": round(weekly_change, 2),
        "Weekly return": weekly_return,
        "Annualised volatility": annual_volatility,
        "Portfolio beta": benchmark_beta,
        "Benchmark volatility": benchmark_volatility,
        "Target": target,
        "Benchmark": benchmark_name,
        "Weighting method": weight_method,
    }])

    st.dataframe(
        snapshot,
        use_container_width=True,
        hide_index=True,
    )

    st.download_button(
        "Download Current Snapshot (CSV)",
        data=snapshot.to_csv(index=False).encode("utf-8"),
        file_name=f"BROKE_snapshot_{date.today()}.csv",
        mime="text/csv",
    )

    st.caption(f"Local archive database: {ARCHIVE_DB_PATH}")


# ============================================================
# DATA DIAGNOSTICS
# ============================================================

elif page == "Data Diagnostics":
    st.markdown("## Data Diagnostics")

    d1, d2, d3 = st.columns(3)
    d1.metric("Requested instruments", len(selected_tickers))
    d2.metric("Instruments with data", len(available_tickers))
    d3.metric("Trading observations", len(price_data))

    st.markdown("### Instrument availability")
    diagnostic_rows = []

    for ticker in selected_tickers:
        available = ticker in price_data.columns
        series = price_data[ticker].dropna() if available else pd.Series(
            dtype=float
        )
        diagnostic_rows.append({
            "Ticker": ticker,
            "Asset class": (
                "Debt" if ticker in DEBT_INSTRUMENTS.values()
                else "Equity"
            ),
            "Data available": "Yes" if available and not series.empty else "No",
            "Observations": len(series),
            "Latest price": (
                float(series.iloc[-1])
                if len(series) else np.nan
            ),
            "Latest date": (
                str(series.index[-1].date())
                if len(series) else "Unavailable"
            ),
        })

    st.dataframe(
        pd.DataFrame(diagnostic_rows),
        use_container_width=True,
        hide_index=True,
    )

    if missing_tickers:
        st.warning(
            "No usable price history was returned for: "
            + ", ".join(missing_tickers)
        )

    st.markdown("### Price data preview")
    st.dataframe(
        price_data.tail(10),
        use_container_width=True,
    )

    st.markdown("### Data limitations")
    st.markdown("""
    - Prices are retrieved from Yahoo Finance through `yfinance`.
    - Data may be delayed, incomplete, adjusted, or unavailable for some tickers.
    - Historical returns exclude taxes, brokerage, slippage, and most trading costs.
    - Cash is assumed to earn zero return.
    - Debt ETF prices can fluctuate and do not guarantee principal protection.
    """)

# ============================================================
# FOOTER
# ============================================================

st.divider()
st.markdown(
    '<p style="color:#ffffff !important;font-size:12px;">'
    'BROKE Portfolio Intelligence | Educational simulation only. '
    'Market data may be delayed or incomplete. Not investment advice.'
    '</p>',
    unsafe_allow_html=True,
)
