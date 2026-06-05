import pandas as pd


# =========================
# SAFE FLOAT CONVERTER
# =========================

def safe_float(value):

    try:

        if pd.isna(value):

            return 0

        value = str(value).replace(',', '')

        return float(value)

    except:

        return 0


# =========================
# FORMAT NUMBER
# =========================

def format_currency(value):

    try:

        return f"{value:,.2f}"

    except:

        return value


# =========================
# MONTH ORDER
# =========================

MONTH_ORDER = [

    'Jan', 'Feb', 'Mar', 'Apr',
    'May', 'Jun', 'Jul', 'Aug',
    'Sep', 'Oct', 'Nov', 'Dec'

]