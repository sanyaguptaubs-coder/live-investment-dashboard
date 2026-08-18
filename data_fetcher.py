import yfinance as yf
import pandas as pd


def get_stock_data(ticker):

    try:

        data = yf.download(
            ticker,
            period="max",
            auto_adjust=True,
            progress=False
        )

        if data.empty:

            return pd.DataFrame()


        # Fix MultiIndex columns returned by yfinance

        if isinstance(
            data.columns,
            pd.MultiIndex
        ):

            data.columns = (
                data.columns
                .get_level_values(0)
            )


        return data


    except Exception as e:

        print(
            f"Error downloading {ticker}: {e}"
        )

        return pd.DataFrame()