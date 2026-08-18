import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px

from datetime import datetime, timedelta
from data_fetcher import get_stock_data


# ============================================================
# PAGE CONFIGURATION
# ============================================================

st.set_page_config(
    page_title="Investment Analytics Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)


# ============================================================
# CUSTOM CSS
# ============================================================

st.markdown(
    """
    <style>

    .stApp {
        background-color: #F4F7FB;
    }

    .block-container {
        max-width: 1450px;
        padding-top: 2rem;
        padding-bottom: 5rem;
    }

    section[data-testid="stSidebar"] {
        background-color: #FFFFFF;
        border-right: 1px solid #E1E7EF;
    }

    h1 {
        color: #173B63;
        font-weight: 800;
    }

    h2, h3 {
        color: #173B63;
        font-weight: 700;
        padding-top: 1rem;
    }

    div[data-testid="stMetric"] {
        background-color: white;
        border: 1px solid #E1E7EF;
        border-radius: 15px;
        padding: 18px;
        box-shadow: 0px 4px 15px rgba(0, 0, 0, 0.05);
    }

    .stButton > button {
        background-color: #1F5A91;
        color: white;
        border: none;
        border-radius: 8px;
        font-weight: 600;
        padding: 0.5rem 1rem;
    }

    .stButton > button:hover {
        background-color: #173B63;
        color: white;
    }

    hr {
        border-color: #DDE3EA;
    }

    details {
        background-color: white;
        border: 1px solid #E1E7EF;
        border-radius: 12px;
        margin-bottom: 10px;
    }

    </style>
    """,
    unsafe_allow_html=True
)


# ============================================================
# DEFAULT COMPANIES
# ============================================================

DEFAULT_COMPANIES = {
    "Reliance Industries": "RELIANCE.NS",
    "TCS": "TCS.NS",
    "Infosys": "INFY.NS",
    "HDFC Bank": "HDFCBANK.NS",
    "ICICI Bank": "ICICIBANK.NS",
    "State Bank of India": "SBIN.NS",
    "ITC": "ITC.NS",
    "Larsen & Toubro": "LT.NS",
    "Bharti Airtel": "BHARTIARTL.NS",
    "Axis Bank": "AXISBANK.NS",
    "Hindustan Unilever": "HINDUNILVR.NS",
    "Maruti Suzuki": "MARUTI.NS",
    "Sun Pharma": "SUNPHARMA.NS",
    "Tata Motors": "TATAMOTORS.NS",
    "Adani Enterprises": "ADANIENT.NS"
}


# ============================================================
# SESSION STATE
# ============================================================

if "companies_df" not in st.session_state:

    st.session_state.companies_df = pd.DataFrame({
        "Company": list(DEFAULT_COMPANIES.keys()),
        "Ticker": list(DEFAULT_COMPANIES.values())
    })


if "debt_name" not in st.session_state:
    st.session_state.debt_name = "Bharat Bond ETF"


if "debt_ticker" not in st.session_state:
    st.session_state.debt_ticker = "EBBETF0433.NS"


# ============================================================
# BENCHMARK
# ============================================================

benchmark = "^NSEI"


# ============================================================
# SIDEBAR
# ============================================================

with st.sidebar:

    st.title("📊 Dashboard")

    st.caption(
        "Equity • Debt • Risk • Return • Portfolio"
    )

    st.divider()

    st.subheader("⚙️ Analysis Settings")

    period = st.selectbox(
        "Analysis Period",
        [
            "1 Month",
            "3 Months",
            "6 Months",
            "1 Year",
            "3 Years",
            "5 Years",
            "All Data"
        ]
    )

    risk_free_rate = st.number_input(
        "Risk-Free Rate (%)",
        min_value=0.0,
        max_value=25.0,
        value=7.0,
        step=0.5
    )

    st.divider()

    st.subheader("📁 Current Assets")

    st.metric(
        "Equity Companies",
        len(st.session_state.companies_df)
    )

    st.write("Debt Instrument:")

    st.caption(
        st.session_state.debt_name
    )


# ============================================================
# DATE RANGE
# ============================================================

end_date = datetime.today()

if period == "1 Month":
    start_date = end_date - timedelta(days=30)

elif period == "3 Months":
    start_date = end_date - timedelta(days=90)

elif period == "6 Months":
    start_date = end_date - timedelta(days=180)

elif period == "1 Year":
    start_date = end_date - timedelta(days=365)

elif period == "3 Years":
    start_date = end_date - timedelta(days=365 * 3)

elif period == "5 Years":
    start_date = end_date - timedelta(days=365 * 5)

else:
    start_date = None


# ============================================================
# HELPER FUNCTION
# ============================================================

def filter_data_by_period(data):

    if data is None or data.empty:
        return pd.DataFrame()

    if start_date is not None:
        return data[data.index >= start_date].copy()

    return data.copy()


def get_close_series(data, name):

    if data is None or data.empty:
        return None

    if "Close" not in data.columns:
        return None

    close = data["Close"]

    # Handles Yahoo Finance MultiIndex columns
    if isinstance(close, pd.DataFrame):
        close = close.iloc[:, 0]

    close = pd.Series(close).dropna()

    if len(close) < 2:
        return None

    close.name = name

    return close


# ============================================================
# DASHBOARD HEADER
# ============================================================

st.title("📊 Investment Analytics Dashboard")

st.subheader(
    "Equity • Risk • Return • Debt • Portfolio Analysis"
)

st.write(
    "Analyze company performance, compare investments, "
    "measure risk-adjusted returns, evaluate debt instruments "
    "and build your own investment portfolio."
)

st.divider()


# ============================================================
# COMPANY MANAGEMENT
# ============================================================

with st.expander("⚙️ Manage Companies"):

    st.write(
        "Add new companies, remove existing companies, "
        "or change their Yahoo Finance tickers."
    )

    edited_companies = st.data_editor(
        st.session_state.companies_df,
        num_rows="dynamic",
        use_container_width=True
    )

    if st.button("💾 Save Company Changes"):

        edited_companies = edited_companies.dropna()

        edited_companies["Company"] = (
            edited_companies["Company"]
            .astype(str)
            .str.strip()
        )

        edited_companies["Ticker"] = (
            edited_companies["Ticker"]
            .astype(str)
            .str.strip()
            .str.upper()
        )

        edited_companies = edited_companies[
            (edited_companies["Company"] != "")
            &
            (edited_companies["Ticker"] != "")
        ]

        st.session_state.companies_df = (
            edited_companies.reset_index(drop=True)
        )

        st.success("Companies updated successfully.")

        st.rerun()


# ============================================================
# DEBT INSTRUMENT CUSTOMIZATION
# ============================================================

with st.expander("💰 Customize Debt Instrument"):

    new_debt_name = st.text_input(
        "Debt Instrument Name",
        value=st.session_state.debt_name
    )

    new_debt_ticker = st.text_input(
        "Yahoo Finance Ticker",
        value=st.session_state.debt_ticker
    )

    if st.button("💾 Save Debt Instrument"):

        if (
            new_debt_name.strip() != ""
            and
            new_debt_ticker.strip() != ""
        ):

            st.session_state.debt_name = (
                new_debt_name.strip()
            )

            st.session_state.debt_ticker = (
                new_debt_ticker.strip().upper()
            )

            st.success(
                "Debt instrument updated successfully."
            )

            st.rerun()

        else:

            st.error(
                "Please enter both name and ticker."
            )


# ============================================================
# COMPANY DICTIONARY
# ============================================================

company_df = st.session_state.companies_df.copy()

company_df = company_df.dropna()

company_df["Company"] = (
    company_df["Company"]
    .astype(str)
    .str.strip()
)

company_df["Ticker"] = (
    company_df["Ticker"]
    .astype(str)
    .str.strip()
    .str.upper()
)

company_df = company_df[
    (company_df["Company"] != "")
    &
    (company_df["Ticker"] != "")
]

companies = dict(
    zip(
        company_df["Company"],
        company_df["Ticker"]
    )
)


if len(companies) == 0:

    st.error(
        "Please add at least one company."
    )

    st.stop()


# ============================================================
# COMPANY SELECTION
# ============================================================

col1, col2 = st.columns([4, 1])

with col1:

    selected_company = st.selectbox(
        "🔍 Select Company for Detailed Analysis",
        list(companies.keys())
    )

with col2:

    st.metric(
        "Benchmark",
        "NIFTY 50"
    )


ticker = companies[selected_company]

debt_instrument_name = st.session_state.debt_name

debt_instrument_ticker = st.session_state.debt_ticker


# ============================================================
# FETCH MAIN DATA
# ============================================================

with st.spinner("Fetching live market data..."):

    data = get_stock_data(ticker)

    benchmark_data = get_stock_data(benchmark)

    debt_data = get_stock_data(
        debt_instrument_ticker
    )


filtered_data = filter_data_by_period(data)

filtered_benchmark = filter_data_by_period(
    benchmark_data
)

filtered_debt = filter_data_by_period(
    debt_data
)


# ============================================================
# VALIDATE MAIN DATA
# ============================================================

company_close = get_close_series(
    filtered_data,
    selected_company
)

benchmark_close = get_close_series(
    filtered_benchmark,
    "NIFTY 50"
)

debt_close = get_close_series(
    filtered_debt,
    debt_instrument_name
)


if company_close is None:

    st.error(
        "Insufficient data for selected company."
    )

    st.stop()


if benchmark_close is None:

    st.error(
        "Insufficient benchmark data."
    )

    st.stop()


# ============================================================
# COMPANY CALCULATIONS
# ============================================================

latest_price = float(
    company_close.iloc[-1]
)

previous_price = float(
    company_close.iloc[-2]
)

first_price = float(
    company_close.iloc[0]
)


daily_return = (
    (latest_price - previous_price)
    /
    previous_price
) * 100


overall_return = (
    (latest_price - first_price)
    /
    first_price
) * 100


benchmark_first = float(
    benchmark_close.iloc[0]
)

benchmark_latest = float(
    benchmark_close.iloc[-1]
)


benchmark_return = (
    (benchmark_latest - benchmark_first)
    /
    benchmark_first
) * 100


# ============================================================
# BETA CALCULATION
# ============================================================

aligned_data = pd.concat(
    [
        company_close.rename("Company"),
        benchmark_close.rename("Market")
    ],
    axis=1,
    join="inner"
).dropna()


company_returns = (
    aligned_data["Company"]
    .pct_change()
    .dropna()
)

market_returns = (
    aligned_data["Market"]
    .pct_change()
    .dropna()
)


aligned_returns = pd.concat(
    [
        company_returns.rename("Company"),
        market_returns.rename("Market")
    ],
    axis=1,
    join="inner"
).dropna()


market_variance = (
    aligned_returns["Market"].var()
)


if market_variance != 0:

    beta = (
        aligned_returns["Company"].cov(
            aligned_returns["Market"]
        )
        /
        market_variance
    )

else:

    beta = 0


# ============================================================
# VOLATILITY
# ============================================================

daily_returns = (
    company_close
    .pct_change()
    .dropna()
)


volatility = (
    daily_returns.std()
    *
    np.sqrt(252)
    *
    100
)


# ============================================================
# ANNUALIZED RETURN
# ============================================================

total_days = (
    company_close.index[-1]
    -
    company_close.index[0]
).days


total_years = total_days / 365


if total_years > 0:

    annualized_return = (
        (
            latest_price
            /
            first_price
        )
        **
        (1 / total_years)
        -
        1
    ) * 100

else:

    annualized_return = overall_return


# ============================================================
# MARKET ANNUALIZED RETURN
# ============================================================

benchmark_days = (
    benchmark_close.index[-1]
    -
    benchmark_close.index[0]
).days


benchmark_years = benchmark_days / 365


if benchmark_years > 0:

    annualized_market_return = (
        (
            benchmark_latest
            /
            benchmark_first
        )
        **
        (1 / benchmark_years)
        -
        1
    ) * 100

else:

    annualized_market_return = benchmark_return


# ============================================================
# SHARPE RATIO
# ============================================================

if volatility != 0:

    sharpe_ratio = (
        annualized_return
        -
        risk_free_rate
    ) / volatility

else:

    sharpe_ratio = 0


# ============================================================
# TREYNOR RATIO
# ============================================================

if beta != 0:

    treynor_ratio = (
        annualized_return
        -
        risk_free_rate
    ) / beta

else:

    treynor_ratio = 0


# ============================================================
# CAPM + JENSEN'S ALPHA
# ============================================================

expected_return = (
    risk_free_rate
    +
    beta
    *
    (
        annualized_market_return
        -
        risk_free_rate
    )
)


alpha = (
    annualized_return
    -
    expected_return
)


# ============================================================
# DEBT CALCULATIONS
# ============================================================

debt_return = 0
debt_annualized_return = 0
debt_volatility = 0
debt_sharpe = 0
debt_latest = 0


if debt_close is not None:

    debt_latest = float(
        debt_close.iloc[-1]
    )

    debt_first = float(
        debt_close.iloc[0]
    )


    debt_return = (
        (
            debt_latest
            -
            debt_first
        )
        /
        debt_first
    ) * 100


    debt_daily_returns = (
        debt_close
        .pct_change()
        .dropna()
    )


    debt_volatility = (
        debt_daily_returns.std()
        *
        np.sqrt(252)
        *
        100
    )


    debt_days = (
        debt_close.index[-1]
        -
        debt_close.index[0]
    ).days


    debt_years = debt_days / 365


    if debt_years > 0:

        debt_annualized_return = (
            (
                debt_latest
                /
                debt_first
            )
            **
            (1 / debt_years)
            -
            1
        ) * 100

    else:

        debt_annualized_return = debt_return


    if debt_volatility != 0:

        debt_sharpe = (
            debt_annualized_return
            -
            risk_free_rate
        ) / debt_volatility


# ============================================================
# NAVIGATION LABELS
# ============================================================

st.divider()

nav1, nav2, nav3, nav4, nav5, nav6 = st.columns(6)

with nav1:
    st.caption("📊 Overview")

with nav2:
    st.caption("📈 Company Analysis")

with nav3:
    st.caption("🏆 Comparison")

with nav4:
    st.caption("💰 Debt Instrument")

with nav5:
    st.caption("💼 Portfolio Builder")

with nav6:
    st.caption("📋 Market Data")

st.divider()


# ============================================================
# OVERVIEW
# ============================================================

st.header("📊 Overview")

st.write(
    f"Performance summary for **{selected_company}** "
    f"during the selected **{period}** period."
)


c1, c2, c3, c4 = st.columns(4)

c1.metric(
    "Latest Price",
    f"₹{latest_price:,.2f}"
)

c2.metric(
    "Daily Return",
    f"{daily_return:.2f}%"
)

c3.metric(
    "Company Return",
    f"{overall_return:.2f}%"
)

c4.metric(
    "NIFTY 50 Return",
    f"{benchmark_return:.2f}%"
)


st.subheader("Risk & Performance")


c5, c6, c7, c8, c9 = st.columns(5)

c5.metric(
    "Beta",
    f"{beta:.2f}"
)

c6.metric(
    "Volatility",
    f"{volatility:.2f}%"
)

c7.metric(
    "Annualized Return",
    f"{annualized_return:.2f}%"
)

c8.metric(
    "Sharpe Ratio",
    f"{sharpe_ratio:.2f}"
)

c9.metric(
    "Jensen's Alpha",
    f"{alpha:.2f}%"
)


c10, c11 = st.columns(2)

c10.metric(
    "Treynor Ratio",
    f"{treynor_ratio:.2f}"
)

c11.metric(
    "CAPM Expected Return",
    f"{expected_return:.2f}%"
)


st.divider()


# ============================================================
# COMPANY ANALYSIS
# ============================================================

st.header("📈 Company Analysis")


price_chart = pd.DataFrame({
    "Date": company_close.index,
    "Close Price": company_close.values
})


fig_price = px.line(
    price_chart,
    x="Date",
    y="Close Price",
    title=f"{selected_company} Historical Price"
)

fig_price.update_layout(
    template="plotly_white"
)

st.plotly_chart(
    fig_price,
    use_container_width=True
)


# ============================================================
# COMPANY VS NIFTY 50
# ============================================================

comparison_data = pd.concat(
    [
        company_close.rename(selected_company),
        benchmark_close.rename("NIFTY 50")
    ],
    axis=1,
    join="inner"
).dropna()


normalized = (
    comparison_data
    /
    comparison_data.iloc[0]
) * 100


normalized = normalized.reset_index()

normalized = normalized.rename(
    columns={
        normalized.columns[0]: "Date"
    }
)


normalized_long = normalized.melt(
    id_vars="Date",
    var_name="Investment",
    value_name="Growth"
)


fig_growth = px.line(
    normalized_long,
    x="Date",
    y="Growth",
    color="Investment",
    title="Growth of ₹100 Investment"
)

fig_growth.update_layout(
    template="plotly_white"
)

st.plotly_chart(
    fig_growth,
    use_container_width=True
)


st.divider()


# ============================================================
# COMPANY COMPARISON
# ============================================================

st.header("🏆 Company Comparison")

st.write(
    "Compare return and volatility across all companies."
)


if st.button("🔄 Generate Company Comparison"):

    comparison_results = []

    progress = st.progress(0)

    total_companies = len(companies)


    for index, (
        company_name,
        company_ticker
    ) in enumerate(companies.items()):

        try:

            company_data = get_stock_data(
                company_ticker
            )

            company_data = filter_data_by_period(
                company_data
            )

            company_close_temp = get_close_series(
                company_data,
                company_name
            )


            if company_close_temp is None:
                continue


            first = float(
                company_close_temp.iloc[0]
            )

            latest = float(
                company_close_temp.iloc[-1]
            )


            company_return = (
                (latest - first)
                /
                first
            ) * 100


            daily = (
                company_close_temp
                .pct_change()
                .dropna()
            )


            company_volatility = (
                daily.std()
                *
                np.sqrt(252)
                *
                100
            )


            comparison_results.append({

                "Company": company_name,

                "Ticker": company_ticker,

                "Return (%)": round(
                    company_return,
                    2
                ),

                "Volatility (%)": round(
                    company_volatility,
                    2
                )

            })


        except Exception:
            pass


        progress.progress(
            int(
                ((index + 1) / total_companies)
                * 100
            )
        )


    progress.empty()

    st.session_state.comparison_results = (
        pd.DataFrame(comparison_results)
    )


if "comparison_results" in st.session_state:

    comparison_df = (
        st.session_state.comparison_results
    )


    if not comparison_df.empty:

        st.dataframe(
            comparison_df,
            use_container_width=True
        )


        fig_compare = px.scatter(
            comparison_df,
            x="Volatility (%)",
            y="Return (%)",
            text="Company",
            title="Risk vs Return Analysis"
        )

        fig_compare.update_traces(
            textposition="top center"
        )

        fig_compare.update_layout(
            template="plotly_white"
        )

        st.plotly_chart(
            fig_compare,
            use_container_width=True
        )


st.divider()


# ============================================================
# DEBT INSTRUMENT
# ============================================================

st.header("💰 Debt Instrument")

st.write(
    f"Current instrument: **{debt_instrument_name}**"
)

st.caption(
    f"Ticker: {debt_instrument_ticker}"
)


if debt_close is not None:

    d1, d2, d3, d4 = st.columns(4)

    d1.metric(
        "Latest Price",
        f"₹{debt_latest:,.2f}"
    )

    d2.metric(
        "Return",
        f"{debt_return:.2f}%"
    )

    d3.metric(
        "Annualized Return",
        f"{debt_annualized_return:.2f}%"
    )

    d4.metric(
        "Sharpe Ratio",
        f"{debt_sharpe:.2f}"
    )


    debt_chart = pd.DataFrame({
        "Date": debt_close.index,
        "Close Price": debt_close.values
    })


    fig_debt = px.line(
        debt_chart,
        x="Date",
        y="Close Price",
        title=f"{debt_instrument_name} Price Trend"
    )

    fig_debt.update_layout(
        template="plotly_white"
    )

    st.plotly_chart(
        fig_debt,
        use_container_width=True
    )

else:

    st.warning(
        "No market data found for this debt ticker. "
        "Please check the ticker."
    )


st.divider()


# ============================================================
# PORTFOLIO BUILDER
# ============================================================

st.header("💼 Portfolio Builder")

st.write(
    "Select assets, assign weights, and analyze the historical "
    "performance and risk characteristics of your portfolio."
)


all_assets = list(companies.keys())

if debt_close is not None:
    all_assets.append(
        debt_instrument_name
    )


selected_assets = st.multiselect(
    "Select Assets for Portfolio",
    all_assets,
    default=[
        selected_company
    ]
)


investment_amount = st.number_input(
    "Total Investment Amount (₹)",
    min_value=1000.0,
    value=100000.0,
    step=5000.0
)


allocation_method = st.radio(
    "Allocation Method",
    [
        "Equal Weight",
        "Custom Weight"
    ],
    horizontal=True
)


if selected_assets:

    weights = {}

    # --------------------------------------------------------
    # EQUAL WEIGHT
    # --------------------------------------------------------

    if allocation_method == "Equal Weight":

        equal_weight = (
            100
            /
            len(selected_assets)
        )

        for asset in selected_assets:

            weights[asset] = equal_weight

        st.info(
            f"Each selected asset receives "
            f"{equal_weight:.2f}% allocation."
        )


    # --------------------------------------------------------
    # CUSTOM WEIGHT
    # --------------------------------------------------------

    else:

        st.subheader(
            "Custom Portfolio Allocation"
        )

        weight_columns = st.columns(
            min(3, len(selected_assets))
        )


        for index, asset in enumerate(
            selected_assets
        ):

            with weight_columns[
                index % len(weight_columns)
            ]:

                weights[asset] = st.number_input(
                    f"{asset} Weight (%)",
                    min_value=0.0,
                    max_value=100.0,
                    value=round(
                        100
                        /
                        len(selected_assets),
                        2
                    ),
                    key=f"weight_{asset}"
                )


    total_weight = sum(
        weights.values()
    )


    st.metric(
        "Total Allocation",
        f"{total_weight:.2f}%"
    )


    # --------------------------------------------------------
    # PORTFOLIO ALLOCATION TABLE
    # --------------------------------------------------------

    allocation_df = pd.DataFrame({
        "Asset": list(weights.keys()),
        "Weight (%)": list(weights.values())
    })


    allocation_df[
        "Investment Amount (₹)"
    ] = (
        allocation_df["Weight (%)"]
        /
        100
        *
        investment_amount
    )


    st.subheader(
        "Portfolio Allocation"
    )


    col1, col2 = st.columns(2)


    with col1:

        fig_pie = px.pie(
            allocation_df,
            names="Asset",
            values="Weight (%)",
            title="Portfolio Allocation"
        )

        fig_pie.update_layout(
            template="plotly_white"
        )

        st.plotly_chart(
            fig_pie,
            use_container_width=True
        )


    with col2:

        st.dataframe(
            allocation_df,
            use_container_width=True
        )


    # --------------------------------------------------------
    # PORTFOLIO VALIDATION
    # --------------------------------------------------------

    if abs(total_weight - 100) > 0.01:

        st.warning(
            "Total allocation must equal 100% "
            "before portfolio analysis can be calculated."
        )

    else:

        st.success(
            "Portfolio allocation is valid."
        )


        # ====================================================
        # FETCH DATA FOR PORTFOLIO
        # ====================================================

        if st.button(
            "📊 Analyze Portfolio Performance"
        ):

            portfolio_prices = []

            progress_bar = st.progress(0)

            total_assets = len(
                selected_assets
            )


            for index, asset in enumerate(
                selected_assets
            ):

                try:

                    # EQUITY ASSET
                    if asset in companies:

                        asset_ticker = (
                            companies[asset]
                        )

                        asset_data = get_stock_data(
                            asset_ticker
                        )

                        asset_data = (
                            filter_data_by_period(
                                asset_data
                            )
                        )

                        asset_close = (
                            get_close_series(
                                asset_data,
                                asset
                            )
                        )


                    # DEBT ASSET
                    elif (
                        asset
                        ==
                        debt_instrument_name
                    ):

                        asset_close = debt_close.copy()


                    else:

                        asset_close = None


                    if asset_close is not None:

                        portfolio_prices.append(
                            asset_close.rename(
                                asset
                            )
                        )


                except Exception:

                    pass


                progress_bar.progress(
                    int(
                        (
                            (index + 1)
                            /
                            total_assets
                        )
                        *
                        100
                    )
                )


            progress_bar.empty()


            # =================================================
            # COMBINE PORTFOLIO DATA
            # =================================================

            if len(portfolio_prices) < 1:

                st.error(
                    "Unable to fetch sufficient portfolio data."
                )

            else:

                portfolio_price_df = pd.concat(
                    portfolio_prices,
                    axis=1,
                    join="inner"
                ).dropna()


                if len(portfolio_price_df) < 2:

                    st.error(
                        "Insufficient common historical data "
                        "for the selected assets."
                    )

                else:

                    # =========================================
                    # DAILY RETURNS
                    # =========================================

                    portfolio_daily_returns = (
                        portfolio_price_df
                        .pct_change()
                        .dropna()
                    )


                    weight_vector = np.array(
                        [
                            weights[asset]
                            /
                            100
                            for asset in
                            portfolio_price_df.columns
                        ]
                    )


                    # =========================================
                    # PORTFOLIO DAILY RETURN
                    # =========================================

                    portfolio_returns = (
                        portfolio_daily_returns
                        .dot(weight_vector)
                    )


                    # =========================================
                    # PORTFOLIO GROWTH
                    # =========================================

                    portfolio_growth = (
                        (1 + portfolio_returns)
                        .cumprod()
                        *
                        investment_amount
                    )


                    # =========================================
                    # PORTFOLIO TOTAL RETURN
                    # =========================================

                    portfolio_total_return = (
                        (
                            portfolio_growth.iloc[-1]
                            /
                            investment_amount
                        )
                        -
                        1
                    ) * 100


                    # =========================================
                    # PORTFOLIO VOLATILITY
                    # =========================================

                    portfolio_volatility = (
                        portfolio_returns.std()
                        *
                        np.sqrt(252)
                        *
                        100
                    )


                    # =========================================
                    # PORTFOLIO ANNUALIZED RETURN
                    # =========================================

                    portfolio_days = (
                        portfolio_growth.index[-1]
                        -
                        portfolio_growth.index[0]
                    ).days


                    portfolio_years = (
                        portfolio_days
                        /
                        365
                    )


                    if portfolio_years > 0:

                        portfolio_annualized_return = (
                            (
                                portfolio_growth.iloc[-1]
                                /
                                investment_amount
                            )
                            **
                            (
                                1
                                /
                                portfolio_years
                            )
                            -
                            1
                        ) * 100

                    else:

                        portfolio_annualized_return = (
                            portfolio_total_return
                        )


                    # =========================================
                    # PORTFOLIO SHARPE RATIO
                    # =========================================

                    if portfolio_volatility != 0:

                        portfolio_sharpe = (
                            portfolio_annualized_return
                            -
                            risk_free_rate
                        ) / portfolio_volatility

                    else:

                        portfolio_sharpe = 0


                    # =========================================
                    # PORTFOLIO BETA
                    # =========================================

                    portfolio_returns_named = (
                        portfolio_returns.rename(
                            "Portfolio"
                        )
                    )


                    benchmark_returns = (
                        benchmark_close
                        .pct_change()
                        .dropna()
                        .rename("Market")
                    )


                    portfolio_beta_data = pd.concat(
                        [
                            portfolio_returns_named,
                            benchmark_returns
                        ],
                        axis=1,
                        join="inner"
                    ).dropna()


                    market_variance_portfolio = (
                        portfolio_beta_data[
                            "Market"
                        ].var()
                    )


                    if (
                        market_variance_portfolio
                        != 0
                    ):

                        portfolio_beta = (
                            portfolio_beta_data[
                                "Portfolio"
                            ].cov(
                                portfolio_beta_data[
                                    "Market"
                                ]
                            )
                            /
                            market_variance_portfolio
                        )

                    else:

                        portfolio_beta = 0


                    # =========================================
                    # PORTFOLIO CAPM RETURN
                    # =========================================

                    portfolio_capm_return = (
                        risk_free_rate
                        +
                        portfolio_beta
                        *
                        (
                            annualized_market_return
                            -
                            risk_free_rate
                        )
                    )


                    # =========================================
                    # PORTFOLIO ALPHA
                    # =========================================

                    portfolio_alpha = (
                        portfolio_annualized_return
                        -
                        portfolio_capm_return
                    )


                    # =========================================
                    # SAVE RESULTS
                    # =========================================

                    st.session_state[
                        "portfolio_results"
                    ] = {

                        "growth":
                            portfolio_growth,

                        "total_return":
                            portfolio_total_return,

                        "annualized_return":
                            portfolio_annualized_return,

                        "volatility":
                            portfolio_volatility,

                        "sharpe":
                            portfolio_sharpe,

                        "beta":
                            portfolio_beta,

                        "capm":
                            portfolio_capm_return,

                        "alpha":
                            portfolio_alpha,

                        "final_value":
                            portfolio_growth.iloc[-1]
                    }


# ============================================================
# DISPLAY PORTFOLIO ANALYSIS
# ============================================================

if (
    "portfolio_results"
    in st.session_state
):

    results = st.session_state[
        "portfolio_results"
    ]


    st.subheader(
        "📊 Portfolio Performance Analysis"
    )


    p1, p2, p3, p4 = st.columns(4)

    p1.metric(
        "Portfolio Value",
        f"₹{results['final_value']:,.2f}"
    )

    p2.metric(
        "Total Return",
        f"{results['total_return']:.2f}%"
    )

    p3.metric(
        "Annualized Return",
        f"{results['annualized_return']:.2f}%"
    )

    p4.metric(
        "Portfolio Volatility",
        f"{results['volatility']:.2f}%"
    )


    p5, p6, p7, p8 = st.columns(4)

    p5.metric(
        "Portfolio Beta",
        f"{results['beta']:.2f}"
    )

    p6.metric(
        "Portfolio Sharpe Ratio",
        f"{results['sharpe']:.2f}"
    )

    p7.metric(
        "CAPM Expected Return",
        f"{results['capm']:.2f}%"
    )

    p8.metric(
        "Portfolio Alpha",
        f"{results['alpha']:.2f}%"
    )


    # ========================================================
    # PORTFOLIO VS NIFTY 50
    # ========================================================

    portfolio_growth = results["growth"]


    benchmark_for_portfolio = (
        benchmark_close.reindex(
            portfolio_growth.index
        ).dropna()
    )


    common_dates = (
        portfolio_growth.index.intersection(
            benchmark_for_portfolio.index
        )
    )


    portfolio_common = (
        portfolio_growth.loc[
            common_dates
        ]
    )


    benchmark_common = (
        benchmark_for_portfolio.loc[
            common_dates
        ]
    )


    if len(common_dates) > 1:

        benchmark_growth = (
            benchmark_common
            /
            benchmark_common.iloc[0]
            *
            investment_amount
        )


        portfolio_chart_df = pd.DataFrame({

            "Date": common_dates,

            "Portfolio":
                portfolio_common.values,

            "NIFTY 50":
                benchmark_growth.values

        })


        portfolio_chart_long = (
            portfolio_chart_df.melt(
                id_vars="Date",
                var_name="Investment",
                value_name="Portfolio Value"
            )
        )


        fig_portfolio_growth = px.line(
            portfolio_chart_long,
            x="Date",
            y="Portfolio Value",
            color="Investment",
            title="Portfolio Growth vs NIFTY 50"
        )


        fig_portfolio_growth.update_layout(
            template="plotly_white"
        )


        st.plotly_chart(
            fig_portfolio_growth,
            use_container_width=True
        )


    # ========================================================
    # PORTFOLIO INTERPRETATION
    # ========================================================

    st.subheader(
        "📌 Portfolio Summary"
    )


    if results["total_return"] > benchmark_return:

        st.success(
            "Your portfolio has outperformed "
            "the NIFTY 50 over the selected period."
        )

    else:

        st.info(
            "Your portfolio has underperformed "
            "the NIFTY 50 over the selected period."
        )


    if results["beta"] > 1:

        st.warning(
            "Portfolio beta is above 1, indicating that "
            "the portfolio is historically more sensitive "
            "to market movements than the NIFTY 50."
        )

    elif results["beta"] < 1:

        st.success(
            "Portfolio beta is below 1, indicating relatively "
            "lower historical sensitivity to market movements."
        )

    else:

        st.info(
            "Portfolio beta is approximately equal to 1."
        )


st.divider()


# ============================================================
# MARKET DATA
# ============================================================

st.header("📋 Market Data")

st.write(
    f"Historical market data for **{selected_company}**."
)


st.dataframe(
    filtered_data.tail(50),
    use_container_width=True
)


st.download_button(
    label="⬇️ Download Market Data as CSV",
    data=filtered_data.to_csv(),
    file_name=f"{selected_company}_market_data.csv",
    mime="text/csv"
)


# ============================================================
# FOOTER
# ============================================================

st.divider()

st.caption(
    "Investment Analytics Dashboard • "
    "Equity • Debt • Risk • Return • Portfolio Analysis"
)