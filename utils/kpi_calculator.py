import pandas as pd

# =========================
# KPI CALCULATOR
# =========================

def calculate_kpis(df):

    total_sales = round(

        df['Revenue'].sum(),

        2

    )

    total_rm = round(

        df['RM_Cost'].sum(),

        2

    )

    total_profit = round(

        df['Profit'].sum(),

        2

    )

    total_qty = round(

        df['Quantity'].sum(),

        2

    )

    # PROFIT MARGIN

    if total_sales > 0:

        profit_margin = round(

            (total_profit / total_sales) * 100,

            2

        )

    else:

        profit_margin = 0

    # TOP CUSTOMER

    top_customer = (

        df.groupby('Customer')['Revenue']
        .sum()
        .idxmax()

    )

    # TOP PRODUCT

    top_product = (

        df.groupby('Material')['Revenue']
        .sum()
        .idxmax()

    )

    # MONTHLY SALES

    monthly_sales = (

        df.groupby('Month')['Revenue']
        .sum()

    )

    top_month = monthly_sales.idxmax()

    low_month = monthly_sales.idxmin()

    return {

        'total_sales': total_sales,

        'total_rm': total_rm,

        'total_profit': total_profit,

        'total_qty': total_qty,

        'profit_margin': profit_margin,

        'top_customer': top_customer,

        'top_product': top_product,

        'top_month': top_month,

        'low_month': low_month

    }