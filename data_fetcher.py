import yfinance as yf
import pandas as pd


# ============================================================
# FETCH STOCK / INDEX / ETF DATA
# ============================================================

def get_stock_data(ticker):

    try:

        data = yf.download(
            ticker,
            period="max",
            auto_adjust=True,
            progress=False
        )

        # Return empty DataFrame if no data is available
        if data.empty:

            return pd.DataFrame()

        # ----------------------------------------------------
        # FIX MULTIINDEX COLUMNS
        # ----------------------------------------------------
        # yfinance may return columns like:
        #
        # ('Close', 'RELIANCE.NS')
        #
        # This converts them into:
        #
        # Close
        # High
        # Low
        # Open
        # Volume
        # ----------------------------------------------------

        if isinstance(data.columns, pd.MultiIndex):

            data.columns = (
                data.columns
                .get_level_values(0)
            )

        # Remove duplicate columns if any
        data = data.loc[
            :,
            ~data.columns.duplicated()
        ]

        # Sort data by date
        data = data.sort_index()

        return data

    except Exception as error:

        print(
            f"Error downloading {ticker}: {error}"
        )

        return pd.DataFrame()


# ============================================================
# GET LATEST AVAILABLE PRICE
# ============================================================

def get_latest_price(ticker):

    data = get_stock_data(ticker)

    if data.empty:

        return None

    if "Close" not in data.columns:

        return None

    try:

        return float(
            data["Close"]
            .dropna()
            .iloc[-1]
        )

    except Exception:

        return None