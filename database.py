import sqlite3
import hashlib
import secrets
import json
from datetime import datetime


# ============================================================
# DATABASE CONFIGURATION
# ============================================================

DATABASE_NAME = "investment_dashboard.db"


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
# DEFAULT USER SETTINGS
# ============================================================

DEFAULT_SETTINGS = {
    "companies": DEFAULT_COMPANIES.copy(),

    "debt_name": "Bharat Bond ETF",
    "debt_ticker": "EBBETF0433.NS",

    "benchmark_name": "NIFTY 50",
    "benchmark_ticker": "^NSEI",

    "risk_free_rate": 7.0,

    "period": "1 Year",

    "portfolio_amount": 100000,

    "portfolio_weights": {},

    "portfolio_assets": []
}


# ============================================================
# DATABASE CONNECTION
# ============================================================

def get_connection():

    connection = sqlite3.connect(
        DATABASE_NAME,
        check_same_thread=False
    )

    connection.row_factory = sqlite3.Row

    return connection


# ============================================================
# PASSWORD HASHING
# ============================================================

def hash_password(password, salt=None):

    if salt is None:

        salt = secrets.token_hex(16)

    password_hash = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt.encode("utf-8"),
        100000
    )

    return (
        salt
        + "$"
        + password_hash.hex()
    )


def verify_password(
    password,
    stored_password
):

    try:

        salt, password_hash = (
            stored_password.split("$")
        )

        new_hash = hashlib.pbkdf2_hmac(
            "sha256",
            password.encode("utf-8"),
            salt.encode("utf-8"),
            100000
        ).hex()

        return secrets.compare_digest(
            password_hash,
            new_hash
        )

    except Exception:

        return False


# ============================================================
# INITIALIZE DATABASE
# ============================================================

def initialize_database():

    connection = get_connection()

    cursor = connection.cursor()

    # --------------------------------------------------------
    # USERS TABLE
    # --------------------------------------------------------

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS users (

            id INTEGER
            PRIMARY KEY AUTOINCREMENT,

            username TEXT
            UNIQUE NOT NULL,

            password_hash TEXT
            NOT NULL,

            is_admin INTEGER
            DEFAULT 0,

            created_at TEXT
            NOT NULL

        )
        """
    )

    # --------------------------------------------------------
    # USER SETTINGS TABLE
    # --------------------------------------------------------

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS user_settings (

            user_id INTEGER
            PRIMARY KEY,

            settings_json TEXT
            NOT NULL,

            updated_at TEXT
            NOT NULL,

            FOREIGN KEY(user_id)
            REFERENCES users(id)

        )
        """
    )

    connection.commit()

    connection.close()


# ============================================================
# CHECK WHETHER USERNAME EXISTS
# ============================================================

def username_exists(username):

    connection = get_connection()

    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT id
        FROM users
        WHERE username = ?
        """,
        (username.strip(),)
    )

    user = cursor.fetchone()

    connection.close()

    return user is not None


# ============================================================
# CREATE USER
# ============================================================

def create_user(
    username,
    password,
    is_admin=False
):

    username = username.strip()

    # --------------------------------------------------------
    # VALIDATE USERNAME
    # --------------------------------------------------------

    if len(username) < 3:

        return (
            False,
            "Username must contain at least 3 characters."
        )

    if " " in username:

        return (
            False,
            "Username cannot contain spaces."
        )

    # --------------------------------------------------------
    # VALIDATE PASSWORD
    # --------------------------------------------------------

    if len(password) < 6:

        return (
            False,
            "Password must contain at least 6 characters."
        )

    connection = get_connection()

    cursor = connection.cursor()

    try:

        # ----------------------------------------------------
        # CREATE USER
        # ----------------------------------------------------

        cursor.execute(
            """
            INSERT INTO users
            (
                username,
                password_hash,
                is_admin,
                created_at
            )

            VALUES (?, ?, ?, ?)
            """,
            (
                username,
                hash_password(password),
                1 if is_admin else 0,
                datetime.now().isoformat()
            )
        )

        user_id = cursor.lastrowid

        # ----------------------------------------------------
        # CREATE PRIVATE SETTINGS
        # ----------------------------------------------------

        default_settings_copy = json.loads(
            json.dumps(DEFAULT_SETTINGS)
        )

        cursor.execute(
            """
            INSERT INTO user_settings
            (
                user_id,
                settings_json,
                updated_at
            )

            VALUES (?, ?, ?)
            """,
            (
                user_id,
                json.dumps(
                    default_settings_copy
                ),
                datetime.now().isoformat()
            )
        )

        connection.commit()

        return (
            True,
            f"Account '{username}' created successfully."
        )

    except sqlite3.IntegrityError:

        return (
            False,
            "This username already exists. "
            "Please choose another username."
        )

    except Exception as error:

        return (
            False,
            f"Error creating account: {error}"
        )

    finally:

        connection.close()


# ============================================================
# AUTHENTICATE USER
# ============================================================

def authenticate_user(
    username,
    password
):

    connection = get_connection()

    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT *
        FROM users
        WHERE username = ?
        """,
        (
            username.strip(),
        )
    )

    user = cursor.fetchone()

    connection.close()

    # --------------------------------------------------------
    # USER DOES NOT EXIST
    # --------------------------------------------------------

    if user is None:

        return None

    # --------------------------------------------------------
    # VERIFY PASSWORD
    # --------------------------------------------------------

    if verify_password(
        password,
        user["password_hash"]
    ):

        return dict(user)

    return None


# ============================================================
# GET USER BY ID
# ============================================================

def get_user_by_id(user_id):

    connection = get_connection()

    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT
            id,
            username,
            is_admin,
            created_at

        FROM users

        WHERE id = ?
        """,
        (user_id,)
    )

    user = cursor.fetchone()

    connection.close()

    if user is None:

        return None

    return dict(user)


# ============================================================
# GET ALL USERS
# ============================================================

def get_all_users():

    connection = get_connection()

    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT
            id,
            username,
            is_admin,
            created_at

        FROM users

        ORDER BY
            is_admin DESC,
            username ASC
        """
    )

    users = [
        dict(row)
        for row in cursor.fetchall()
    ]

    connection.close()

    return users


# ============================================================
# DELETE USER
# ============================================================

def delete_user(user_id):

    connection = get_connection()

    cursor = connection.cursor()

    try:

        # Delete private settings first

        cursor.execute(
            """
            DELETE FROM user_settings
            WHERE user_id = ?
            """,
            (user_id,)
        )

        # Delete user

        cursor.execute(
            """
            DELETE FROM users
            WHERE id = ?
            """,
            (user_id,)
        )

        connection.commit()

        return (
            True,
            "User deleted successfully."
        )

    except Exception as error:

        return (
            False,
            f"Error deleting user: {error}"
        )

    finally:

        connection.close()


# ============================================================
# RESET PASSWORD
# ============================================================

def reset_password(
    user_id,
    new_password
):

    if len(new_password) < 6:

        return (
            False,
            "Password must contain at least 6 characters."
        )

    connection = get_connection()

    cursor = connection.cursor()

    try:

        cursor.execute(
            """
            UPDATE users

            SET password_hash = ?

            WHERE id = ?
            """,
            (
                hash_password(new_password),
                user_id
            )
        )

        connection.commit()

        return (
            True,
            "Password updated successfully."
        )

    except Exception as error:

        return (
            False,
            f"Error updating password: {error}"
        )

    finally:

        connection.close()


# ============================================================
# GET USER SETTINGS
# ============================================================

def get_user_settings(user_id):

    connection = get_connection()

    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT settings_json

        FROM user_settings

        WHERE user_id = ?
        """,
        (user_id,)
    )

    row = cursor.fetchone()

    connection.close()

    # --------------------------------------------------------
    # NO SETTINGS FOUND
    # --------------------------------------------------------

    if row is None:

        return json.loads(
            json.dumps(DEFAULT_SETTINGS)
        )

    try:

        saved_settings = json.loads(
            row["settings_json"]
        )

        # Deep copy defaults

        merged_settings = json.loads(
            json.dumps(DEFAULT_SETTINGS)
        )

        # Add saved values

        merged_settings.update(
            saved_settings
        )

        return merged_settings

    except Exception:

        return json.loads(
            json.dumps(DEFAULT_SETTINGS)
        )


# ============================================================
# SAVE USER SETTINGS
# ============================================================

def save_user_settings(
    user_id,
    settings
):

    connection = get_connection()

    cursor = connection.cursor()

    try:

        cursor.execute(
            """
            INSERT INTO user_settings
            (
                user_id,
                settings_json,
                updated_at
            )

            VALUES (?, ?, ?)

            ON CONFLICT(user_id)

            DO UPDATE SET

                settings_json =
                    excluded.settings_json,

                updated_at =
                    excluded.updated_at
            """,
            (
                user_id,
                json.dumps(settings),
                datetime.now().isoformat()
            )
        )

        connection.commit()

        return (
            True,
            "Settings saved successfully."
        )

    except Exception as error:

        return (
            False,
            f"Error saving settings: {error}"
        )

    finally:

        connection.close()


# ============================================================
# GET DEFAULT SETTINGS
# ============================================================

def get_default_settings():

    return json.loads(
        json.dumps(DEFAULT_SETTINGS)
    )


# ============================================================
# CHECK IF ANY ADMIN EXISTS
# ============================================================

def admin_exists():

    connection = get_connection()

    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT id
        FROM users
        WHERE is_admin = 1
        LIMIT 1
        """
    )

    admin = cursor.fetchone()

    connection.close()

    return admin is not None