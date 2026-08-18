import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px

from datetime import datetime, timedelta

from data_fetcher import get_stock_data

from database import (
    initialize_database,
    admin_exists,
    create_user,
    authenticate_user,
    get_all_users,
    delete_user,
    reset_password,
    get_user_settings,
    save_user_settings
)


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
# INITIALIZE DATABASE
# ============================================================

initialize_database()


# ============================================================
# SESSION STATE
# ============================================================

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if "current_user" not in st.session_state:
    st.session_state.current_user = None


# ============================================================
# FIRST-TIME ADMIN ACCOUNT CREATION
# ============================================================

if not admin_exists():

    st.title("👑 Create Administrator Account")

    st.write(
        "This is the first time the dashboard is being used. "
        "Create your administrator account."
    )

    with st.form("create_first_admin"):

        admin_username = st.text_input(
            "Admin Username"
        )

        admin_password = st.text_input(
            "Admin Password",
            type="password"
        )

        confirm_admin_password = st.text_input(
            "Confirm Password",
            type="password"
        )

        create_admin_button = st.form_submit_button(
            "Create Administrator Account",
            use_container_width=True
        )

    if create_admin_button:

        if admin_password != confirm_admin_password:

            st.error(
                "Passwords do not match."
            )

        else:

            success, message = create_user(
                admin_username,
                admin_password,
                is_admin=True
            )

            if success:

                st.success(message)

                st.info(
                    "Administrator account created successfully. "
                    "Please refresh or continue to log in."
                )

                st.rerun()

            else:

                st.error(message)

    st.stop()


# ============================================================
# LOGIN SCREEN
# ============================================================

if not st.session_state.logged_in:

    st.title("📊 Investment Analytics Dashboard")

    st.subheader(
        "Secure Multi-User Investment Analytics Platform"
    )

    st.write(
        "Log in using your unique username and password."
    )

    st.divider()

    left, center, right = st.columns([1, 2, 1])

    with center:

        with st.form("login_form"):

            username = st.text_input(
                "Username"
            )

            password = st.text_input(
                "Password",
                type="password"
            )

            login_button = st.form_submit_button(
                "🔐 Login",
                use_container_width=True
            )

        if login_button:

            user = authenticate_user(
                username,
                password
            )

            if user is not None:

                st.session_state.logged_in = True

                st.session_state.current_user = user

                st.session_state.loaded_user_id = None

                st.success(
                    f"Welcome, {user['username']}!"
                )

                st.rerun()

            else:

                st.error(
                    "Invalid username or password."
                )

    st.stop()


# ============================================================
# CURRENT USER
# ============================================================

current_user = st.session_state.current_user

current_user_id = current_user["id"]


# ============================================================
# LOAD PRIVATE USER SETTINGS
# ============================================================

if (
    "loaded_user_id"
    not in st.session_state
    or
    st.session_state.loaded_user_id
    != current_user_id
):

    user_settings = get_user_settings(
        current_user_id
    )

    companies_dict = user_settings.get(
        "companies",
        {}
    )

    st.session_state.companies_df = pd.DataFrame(
        list(companies_dict.items()),
        columns=[
            "Company",
            "Ticker"
        ]
    )

    st.session_state.debt_name = (
        user_settings.get(
            "debt_name",
            "Bharat Bond ETF"
        )
    )

    st.session_state.debt_ticker = (
        user_settings.get(
            "debt_ticker",
            "EBBETF0433.NS"
        )
    )

    st.session_state.benchmark_name = (
        user_settings.get(
            "benchmark_name",
            "NIFTY 50"
        )
    )

    st.session_state.benchmark_ticker = (
        user_settings.get(
            "benchmark_ticker",
            "^NSEI"
        )
    )

    st.session_state.risk_free_rate = (
        float(
            user_settings.get(
                "risk_free_rate",
                7.0
            )
        )
    )

    st.session_state.period = (
        user_settings.get(
            "period",
            "1 Year"
        )
    )

    st.session_state.portfolio_amount = (
        float(
            user_settings.get(
                "portfolio_amount",
                100000
            )
        )
    )

    st.session_state.portfolio_assets = (
        user_settings.get(
            "portfolio_assets",
            []
        )
    )

    st.session_state.portfolio_weights = (
        user_settings.get(
            "portfolio_weights",
            {}
        )
    )

    st.session_state.loaded_user_id = (
        current_user_id
    )


# ============================================================
# SAVE USER SETTINGS FUNCTION
# ============================================================

def save_current_user_settings():

    companies_dictionary = dict(
        zip(
            st.session_state.companies_df[
                "Company"
            ],
            st.session_state.companies_df[
                "Ticker"
            ]
        )
    )

    settings = {

        "companies":
            companies_dictionary,

        "debt_name":
            st.session_state.debt_name,

        "debt_ticker":
            st.session_state.debt_ticker,

        "benchmark_name":
            st.session_state.benchmark_name,

        "benchmark_ticker":
            st.session_state.benchmark_ticker,

        "risk_free_rate":
            st.session_state.risk_free_rate,

        "period":
            st.session_state.period,

        "portfolio_amount":
            st.session_state.portfolio_amount,

        "portfolio_assets":
            st.session_state.portfolio_assets,

        "portfolio_weights":
            st.session_state.portfolio_weights
    }

    return save_user_settings(
        current_user_id,
        settings
    )


# ============================================================
# SIDEBAR
# ============================================================

period_options = [
    "1 Month",
    "3 Months",
    "6 Months",
    "1 Year",
    "3 Years",
    "5 Years",
    "All Data"
]

with st.sidebar:

    st.title("📊 Dashboard")

    st.success(
        f"👤 {current_user['username']}"
    )

    if current_user["is_admin"]:

        st.caption(
            "👑 Administrator Account"
        )

    else:

        st.caption(
            "🔒 Private User Account"
        )

    st.divider()

    st.subheader(
        "⚙️ Analysis Settings"
    )

    current_period = (
        st.session_state.period
    )

    if current_period not in period_options:
        current_period = "1 Year"

    period = st.selectbox(
        "Analysis Period",
        period_options,
        index=period_options.index(
            current_period
        )
    )

    st.session_state.period = period

    risk_free_rate = st.number_input(
        "Risk-Free Rate (%)",
        min_value=0.0,
        max_value=25.0,
        value=float(
            st.session_state.risk_free_rate
        ),
        step=0.5
    )

    st.session_state.risk_free_rate = (
        risk_free_rate
    )

    st.divider()

    st.subheader(
        "📈 Current Benchmark"
    )

    st.write(
        st.session_state.benchmark_name
    )

    st.caption(
        st.session_state.benchmark_ticker
    )

    st.divider()

    st.subheader(
        "📁 Current Assets"
    )

    st.metric(
        "Equity Companies",
        len(
            st.session_state.companies_df
        )
    )

    st.write(
        "Debt Instrument:"
    )

    st.caption(
        st.session_state.debt_name
    )

    st.divider()

    if st.button(
        "💾 Save My Settings",
        use_container_width=True
    ):

        success, message = (
            save_current_user_settings()
        )

        if success:
            st.success(
                "Your private settings have been saved."
            )
        else:
            st.error(message)

    st.divider()

    if st.button(
        "🚪 Logout",
        use_container_width=True
    ):

        keys_to_remove = [
            "logged_in",
            "current_user",
            "loaded_user_id",
            "companies_df",
            "debt_name",
            "debt_ticker",
            "benchmark_name",
            "benchmark_ticker",
            "risk_free_rate",
            "period",
            "portfolio_results",
            "comparison_results"
        ]

        for key in keys_to_remove:

            if key in st.session_state:
                del st.session_state[key]

        st.session_state.logged_in = False
        st.session_state.current_user = None

        st.rerun()


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
# HELPER FUNCTIONS
# ============================================================

def filter_data_by_period(data):

    if data is None or data.empty:
        return pd.DataFrame()

    if start_date is not None:
        return data[
            data.index >= start_date
        ].copy()

    return data.copy()


def get_close_series(data, name):

    if data is None or data.empty:
        return None

    if "Close" not in data.columns:
        return None

    close = data["Close"]

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

st.title(
    "📊 Investment Analytics Dashboard"
)

st.subheader(
    "Equity • Risk • Return • Debt • Portfolio Analysis"
)

st.write(
    f"Welcome, **{current_user['username']}**. "
    "Your companies, benchmark, debt instrument and "
    "settings are private to your account."
)

st.divider()


# ============================================================
# ADMIN PANEL
# ============================================================

if current_user["is_admin"]:

    with st.expander(
        "👑 Admin Panel — Manage User Accounts"
    ):

        st.subheader(
            "➕ Create New User"
        )

        with st.form(
            "create_user_form",
            clear_on_submit=True
        ):

            new_username = st.text_input(
                "Unique Username"
            )

            new_password = st.text_input(
                "Password",
                type="password"
            )

            confirm_password = st.text_input(
                "Confirm Password",
                type="password"
            )

            create_account = (
                st.form_submit_button(
                    "Create Account"
                )
            )

        if create_account:

            if new_password != confirm_password:

                st.error(
                    "Passwords do not match."
                )

            else:

                success, message = create_user(
                    new_username,
                    new_password,
                    is_admin=False
                )

                if success:
                    st.success(message)
                else:
                    st.error(message)

        st.divider()

        st.subheader(
            "👥 Existing Users"
        )

        users = get_all_users()

        users_dataframe = pd.DataFrame(
            [
                {
                    "ID": user["id"],
                    "Username": user["username"],
                    "Administrator":
                        "Yes"
                        if user["is_admin"]
                        else "No",
                    "Created":
                        user["created_at"]
                }
                for user in users
            ]
        )

        st.dataframe(
            users_dataframe,
            use_container_width=True
        )

        non_admin_users = [
            user
            for user in users
            if not user["is_admin"]
        ]

        if non_admin_users:

            st.divider()

            st.subheader(
                "🔑 Reset User Password"
            )

            reset_user = st.selectbox(
                "Select User",
                non_admin_users,
                format_func=lambda x:
                    x["username"],
                key="reset_user"
            )

            new_user_password = st.text_input(
                "New Password",
                type="password",
                key="new_user_password"
            )

            if st.button(
                "Update Password"
            ):

                success, message = reset_password(
                    reset_user["id"],
                    new_user_password
                )

                if success:
                    st.success(message)
                else:
                    st.error(message)

            st.divider()

            st.subheader(
                "🗑️ Delete User"
            )

            delete_selected_user = st.selectbox(
                "Select User to Delete",
                non_admin_users,
                format_func=lambda x:
                    x["username"],
                key="delete_selected_user"
            )

            confirm_delete = st.checkbox(
                "I understand that this will permanently "
                "delete this user's saved settings."
            )

            if st.button(
                "Delete Selected User"
            ):

                if confirm_delete:

                    success, message = delete_user(
                        delete_selected_user["id"]
                    )

                    if success:
                        st.success(message)
                        st.rerun()
                    else:
                        st.error(message)

                else:

                    st.warning(
                        "Please confirm deletion first."
                    )


# ============================================================
# COMPANY MANAGEMENT
# ============================================================

with st.expander(
    "⚙️ Manage Companies"
):

    st.write(
        "Add, remove or edit companies and their "
        "Yahoo Finance tickers."
    )

    edited_companies = st.data_editor(
        st.session_state.companies_df,
        num_rows="dynamic",
        use_container_width=True,
        key="company_editor"
    )

    if st.button(
        "💾 Save Company Changes"
    ):

        edited_companies = (
            edited_companies.dropna()
        )

        if not edited_companies.empty:

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

            edited_companies = (
                edited_companies[
                    (
                        edited_companies[
                            "Company"
                        ] != ""
                    )
                    &
                    (
                        edited_companies[
                            "Ticker"
                        ] != ""
                    )
                ]
            )

        st.session_state.companies_df = (
            edited_companies.reset_index(
                drop=True
            )
        )

        success, message = (
            save_current_user_settings()
        )

        if success:
            st.success(
                "Your private company list has been saved."
            )

        st.rerun()


# ============================================================
# DEBT INSTRUMENT
# ============================================================

with st.expander(
    "💰 Customize Debt Instrument"
):

    new_debt_name = st.text_input(
        "Debt Instrument Name",
        value=st.session_state.debt_name
    )

    new_debt_ticker = st.text_input(
        "Yahoo Finance Ticker",
        value=st.session_state.debt_ticker
    )

    if st.button(
        "💾 Save Debt Instrument"
    ):

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

            save_current_user_settings()

            st.success(
                "Debt instrument saved successfully."
            )

            st.rerun()

        else:

            st.error(
                "Please enter both name and ticker."
            )


# ============================================================
# BENCHMARK CUSTOMIZATION
# ============================================================

with st.expander(
    "📈 Customize Benchmark"
):

    benchmark_options = {
        "NIFTY 50": "^NSEI",
        "SENSEX": "^BSESN",
        "NIFTY Bank": "^NSEBANK",
        "NIFTY IT": "^CNXIT",
        "S&P 500": "^GSPC",
        "NASDAQ Composite": "^IXIC",
        "Dow Jones": "^DJI",
        "Custom Benchmark": ""
    }

    current_benchmark_name = (
        st.session_state.benchmark_name
    )

    if (
        current_benchmark_name
        in benchmark_options
    ):
        benchmark_index = list(
            benchmark_options.keys()
        ).index(
            current_benchmark_name
        )
    else:
        benchmark_index = list(
            benchmark_options.keys()
        ).index(
            "Custom Benchmark"
        )

    selected_benchmark_option = (
        st.selectbox(
            "Select Benchmark",
            list(
                benchmark_options.keys()
            ),
            index=benchmark_index
        )
    )

    if (
        selected_benchmark_option
        == "Custom Benchmark"
    ):

        new_benchmark_name = st.text_input(
            "Custom Benchmark Name",
            value=(
                st.session_state
                .benchmark_name
            )
        )

        new_benchmark_ticker = st.text_input(
            "Yahoo Finance Benchmark Ticker",
            value=(
                st.session_state
                .benchmark_ticker
            )
        )

    else:

        new_benchmark_name = (
            selected_benchmark_option
        )

        new_benchmark_ticker = (
            benchmark_options[
                selected_benchmark_option
            ]
        )

    if st.button(
        "💾 Save Benchmark"
    ):

        if (
            new_benchmark_name.strip() != ""
            and
            new_benchmark_ticker.strip() != ""
        ):

            st.session_state.benchmark_name = (
                new_benchmark_name.strip()
            )

            st.session_state.benchmark_ticker = (
                new_benchmark_ticker
                .strip()
                .upper()
            )

            save_current_user_settings()

            st.success(
                "Benchmark updated successfully."
            )

            st.rerun()

        else:

            st.error(
                "Please enter both benchmark name "
                "and ticker."
            )


# ============================================================
# COMPANY DICTIONARY
# ============================================================

company_df = (
    st.session_state.companies_df.copy()
)

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
    (
        company_df["Company"] != ""
    )
    &
    (
        company_df["Ticker"] != ""
    )
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
        st.session_state.benchmark_name
    )


ticker = companies[selected_company]

debt_instrument_name = (
    st.session_state.debt_name
)

debt_instrument_ticker = (
    st.session_state.debt_ticker
)

benchmark = (
    st.session_state.benchmark_ticker
)

benchmark_name = (
    st.session_state.benchmark_name
)


# ============================================================
# FETCH MARKET DATA
# ============================================================

with st.spinner(
    "Fetching live market data..."
):

    data = get_stock_data(
        ticker
    )

    benchmark_data = get_stock_data(
        benchmark
    )

    debt_data = get_stock_data(
        debt_instrument_ticker
    )


filtered_data = filter_data_by_period(
    data
)

filtered_benchmark = filter_data_by_period(
    benchmark_data
)

filtered_debt = filter_data_by_period(
    debt_data
)


# ============================================================
# VALIDATE DATA
# ============================================================

company_close = get_close_series(
    filtered_data,
    selected_company
)

benchmark_close = get_close_series(
    filtered_benchmark,
    benchmark_name
)

debt_close = get_close_series(
    filtered_debt,
    debt_instrument_name
)

if company_close is None:

    st.error(
        "Insufficient data for the selected company."
    )

    st.stop()

if benchmark_close is None:

    st.error(
        f"Insufficient data for benchmark: "
        f"{benchmark_name}"
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
    (
        latest_price
        -
        previous_price
    )
    /
    previous_price
) * 100

overall_return = (
    (
        latest_price
        -
        first_price
    )
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
    (
        benchmark_latest
        -
        benchmark_first
    )
    /
    benchmark_first
) * 100


# ============================================================
# BETA
# ============================================================

aligned_data = pd.concat(
    [
        company_close.rename(
            "Company"
        ),
        benchmark_close.rename(
            "Market"
        )
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
        company_returns.rename(
            "Company"
        ),
        market_returns.rename(
            "Market"
        )
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
# BENCHMARK ANNUALIZED RETURN
# ============================================================

benchmark_days = (
    benchmark_close.index[-1]
    -
    benchmark_close.index[0]
).days

benchmark_years = (
    benchmark_days / 365
)

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

    annualized_market_return = (
        benchmark_return
    )


# ============================================================
# RISK METRICS
# ============================================================

risk_free_rate = (
    st.session_state.risk_free_rate
)

if volatility != 0:

    sharpe_ratio = (
        annualized_return
        -
        risk_free_rate
    ) / volatility

else:

    sharpe_ratio = 0


if beta != 0:

    treynor_ratio = (
        annualized_return
        -
        risk_free_rate
    ) / beta

else:

    treynor_ratio = 0


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

        debt_annualized_return = (
            debt_return
        )

    if debt_volatility != 0:

        debt_sharpe = (
            debt_annualized_return
            -
            risk_free_rate
        ) / debt_volatility


# ============================================================
# NAVIGATION
# ============================================================

st.divider()

nav1, nav2, nav3, nav4, nav5, nav6 = (
    st.columns(6)
)

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
    f"Performance summary for "
    f"**{selected_company}** "
    f"during the selected "
    f"**{period}** period."
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
    f"{benchmark_name} Return",
    f"{benchmark_return:.2f}%"
)

st.subheader(
    "Risk & Performance"
)

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

price_chart = pd.DataFrame(
    {
        "Date": company_close.index,
        "Close Price": company_close.values
    }
)

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
# COMPANY VS BENCHMARK
# ============================================================

comparison_data = pd.concat(
    [
        company_close.rename(
            selected_company
        ),
        benchmark_close.rename(
            benchmark_name
        )
    ],
    axis=1,
    join="inner"
).dropna()

if len(comparison_data) > 1:

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
    "Compare return and volatility "
    "across all your selected companies."
)

if st.button(
    "🔄 Generate Company Comparison"
):

    comparison_results = []

    progress = st.progress(0)

    total_companies = len(
        companies
    )

    for index, (
        company_name,
        company_ticker
    ) in enumerate(
        companies.items()
    ):

        try:

            company_data = get_stock_data(
                company_ticker
            )

            company_data = (
                filter_data_by_period(
                    company_data
                )
            )

            temp_close = get_close_series(
                company_data,
                company_name
            )

            if temp_close is not None:

                first = float(
                    temp_close.iloc[0]
                )

                latest = float(
                    temp_close.iloc[-1]
                )

                company_return = (
                    (
                        latest
                        -
                        first
                    )
                    /
                    first
                ) * 100

                daily = (
                    temp_close
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

                comparison_results.append(
                    {
                        "Company":
                            company_name,

                        "Ticker":
                            company_ticker,

                        "Return (%)":
                            round(
                                company_return,
                                2
                            ),

                        "Volatility (%)":
                            round(
                                company_volatility,
                                2
                            )
                    }
                )

        except Exception:
            pass

        progress.progress(
            int(
                (
                    (index + 1)
                    /
                    total_companies
                )
                *
                100
            )
        )

    progress.empty()

    st.session_state.comparison_results = (
        pd.DataFrame(
            comparison_results
        )
    )


if (
    "comparison_results"
    in st.session_state
):

    comparison_df = (
        st.session_state
        .comparison_results
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
    f"Current instrument: "
    f"**{debt_instrument_name}**"
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

    debt_chart = pd.DataFrame(
        {
            "Date": debt_close.index,
            "Close Price": debt_close.values
        }
    )

    fig_debt = px.line(
        debt_chart,
        x="Date",
        y="Close Price",
        title=(
            f"{debt_instrument_name} "
            "Price Trend"
        )
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
    "Select assets, assign weights, and analyze "
    "the historical performance and risk "
    "characteristics of your portfolio."
)

all_assets = list(
    companies.keys()
)

if debt_close is not None:

    all_assets.append(
        debt_instrument_name
    )


default_assets = [
    asset
    for asset in
    st.session_state.portfolio_assets
    if asset in all_assets
]

if not default_assets:

    default_assets = [
        selected_company
    ]


selected_assets = st.multiselect(
    "Select Assets for Portfolio",
    all_assets,
    default=default_assets
)

st.session_state.portfolio_assets = (
    selected_assets
)


investment_amount = st.number_input(
    "Total Investment Amount (₹)",
    min_value=1000.0,
    value=float(
        st.session_state.portfolio_amount
    ),
    step=5000.0
)

st.session_state.portfolio_amount = (
    investment_amount
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

    if allocation_method == "Equal Weight":

        equal_weight = (
            100
            /
            len(selected_assets)
        )

        for asset in selected_assets:

            weights[asset] = (
                equal_weight
            )

        st.info(
            f"Each selected asset receives "
            f"{equal_weight:.2f}% allocation."
        )

    else:

        st.subheader(
            "Custom Portfolio Allocation"
        )

        weight_columns = st.columns(
            min(
                3,
                len(selected_assets)
            )
        )

        for index, asset in enumerate(
            selected_assets
        ):

            previous_weight = (
                st.session_state
                .portfolio_weights
                .get(
                    asset,
                    round(
                        100
                        /
                        len(selected_assets),
                        2
                    )
                )
            )

            with weight_columns[
                index % len(weight_columns)
            ]:

                weights[asset] = (
                    st.number_input(
                        f"{asset} Weight (%)",
                        min_value=0.0,
                        max_value=100.0,
                        value=float(
                            previous_weight
                        ),
                        key=f"weight_{asset}"
                    )
                )

    st.session_state.portfolio_weights = (
        weights
    )

    total_weight = sum(
        weights.values()
    )

    st.metric(
        "Total Allocation",
        f"{total_weight:.2f}%"
    )

    allocation_df = pd.DataFrame(
        {
            "Asset":
                list(weights.keys()),

            "Weight (%)":
                list(weights.values())
        }
    )

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

    portfolio_col1, portfolio_col2 = (
        st.columns(2)
    )

    with portfolio_col1:

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

    with portfolio_col2:

        st.dataframe(
            allocation_df,
            use_container_width=True
        )

    if abs(
        total_weight - 100
    ) > 0.01:

        st.warning(
            "Total allocation must equal 100% "
            "before portfolio analysis."
        )

    else:

        st.success(
            "Portfolio allocation is valid."
        )

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

                    if asset in companies:

                        asset_data = (
                            get_stock_data(
                                companies[asset]
                            )
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

                    elif (
                        asset
                        ==
                        debt_instrument_name
                    ):

                        asset_close = (
                            debt_close.copy()
                        )

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

            if len(portfolio_prices) < 1:

                st.error(
                    "Unable to fetch sufficient "
                    "portfolio data."
                )

            else:

                portfolio_price_df = pd.concat(
                    portfolio_prices,
                    axis=1,
                    join="inner"
                ).dropna()

                if len(
                    portfolio_price_df
                ) < 2:

                    st.error(
                        "Insufficient common historical "
                        "data for selected assets."
                    )

                else:

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

                    portfolio_returns = (
                        portfolio_daily_returns
                        .dot(weight_vector)
                    )

                    portfolio_growth = (
                        (
                            1
                            +
                            portfolio_returns
                        )
                        .cumprod()
                        *
                        investment_amount
                    )

                    portfolio_total_return = (
                        (
                            portfolio_growth.iloc[-1]
                            /
                            investment_amount
                        )
                        -
                        1
                    ) * 100

                    portfolio_volatility = (
                        portfolio_returns.std()
                        *
                        np.sqrt(252)
                        *
                        100
                    )

                    portfolio_days = (
                        portfolio_growth.index[-1]
                        -
                        portfolio_growth.index[0]
                    ).days

                    portfolio_years = (
                        portfolio_days / 365
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

                    if portfolio_volatility != 0:

                        portfolio_sharpe = (
                            portfolio_annualized_return
                            -
                            risk_free_rate
                        ) / portfolio_volatility

                    else:

                        portfolio_sharpe = 0

                    portfolio_returns_named = (
                        portfolio_returns.rename(
                            "Portfolio"
                        )
                    )

                    benchmark_returns = (
                        benchmark_close
                        .pct_change()
                        .dropna()
                        .rename(
                            "Market"
                        )
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

                    portfolio_alpha = (
                        portfolio_annualized_return
                        -
                        portfolio_capm_return
                    )

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
                            portfolio_growth.iloc[-1],

                        "investment_amount":
                            investment_amount
                    }

                    save_current_user_settings()


# ============================================================
# DISPLAY PORTFOLIO RESULTS
# ============================================================

if (
    "portfolio_results"
    in st.session_state
):

    results = (
        st.session_state[
            "portfolio_results"
        ]
    )

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

    portfolio_growth = (
        results["growth"]
    )

    investment_amount_results = (
        results["investment_amount"]
    )

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
            investment_amount_results
        )

        portfolio_chart_df = pd.DataFrame(
            {
                "Date":
                    common_dates,

                "Portfolio":
                    portfolio_common.values,

                benchmark_name:
                    benchmark_growth.values
            }
        )

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
            title=(
                f"Portfolio Growth vs "
                f"{benchmark_name}"
            )
        )

        fig_portfolio_growth.update_layout(
            template="plotly_white"
        )

        st.plotly_chart(
            fig_portfolio_growth,
            use_container_width=True
        )

    st.subheader(
        "📌 Portfolio Summary"
    )

    if (
        results["total_return"]
        >
        benchmark_return
    ):

        st.success(
            f"Your portfolio has outperformed "
            f"{benchmark_name} over the "
            f"selected period."
        )

    else:

        st.info(
            f"Your portfolio has underperformed "
            f"{benchmark_name} over the "
            f"selected period."
        )

    if results["beta"] > 1:

        st.warning(
            f"Portfolio beta is above 1, indicating "
            f"greater historical sensitivity to "
            f"{benchmark_name}."
        )

    elif results["beta"] < 1:

        st.success(
            "Portfolio beta is below 1, indicating "
            "relatively lower historical sensitivity "
            "to market movements."
        )

    else:

        st.info(
            "Portfolio beta is approximately "
            "equal to 1."
        )


st.divider()


# ============================================================
# MARKET DATA
# ============================================================

st.header("📋 Market Data")

st.write(
    f"Historical market data for "
    f"**{selected_company}**."
)

st.dataframe(
    filtered_data.tail(50),
    use_container_width=True
)

st.download_button(
    label="⬇️ Download Market Data as CSV",
    data=filtered_data.to_csv(),
    file_name=(
        f"{selected_company}_market_data.csv"
    ),
    mime="text/csv"
)


# ============================================================
# FOOTER
# ============================================================

st.divider()

st.caption(
    "Investment Analytics Dashboard • "
    "Equity • Debt • Risk • Return • "
    "Portfolio Analysis"
)