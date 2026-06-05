# =========================
# MONTHLY SALES CHART
# =========================

def get_monthly_sales_chart(df):

    month_order = [

        'Jan', 'Feb', 'Mar', 'Apr',
        'May', 'Jun', 'Jul', 'Aug',
        'Sep', 'Oct', 'Nov', 'Dec'

    ]

    monthly = (

        df.groupby('Month')['Revenue']
        .sum()
        .reindex(month_order, fill_value=0)

    )

    return {

        'labels': monthly.index.tolist(),

        'values': monthly.values.tolist()

    }


# =========================
# MONTHLY PROFIT CHART
# =========================

def get_monthly_profit_chart(df):

    month_order = [

        'Jan', 'Feb', 'Mar', 'Apr',
        'May', 'Jun', 'Jul', 'Aug',
        'Sep', 'Oct', 'Nov', 'Dec'

    ]

    monthly = (

        df.groupby('Month')['Profit']
        .sum()
        .reindex(month_order, fill_value=0)

    )

    return {

        'labels': monthly.index.tolist(),

        'values': monthly.values.tolist()

    }


# =========================
# CUSTOMER CHART
# =========================

def get_customer_chart(df):

    customer_data = (

        df.groupby('Customer')['Revenue']
        .sum()
        .sort_values(ascending=False)
        .head(10)

    )

    return {

        'labels': customer_data.index.tolist(),

        'values': customer_data.values.tolist()

    }


# =========================
# PRODUCT CHART
# =========================

def get_product_chart(df):

    product_data = (

        df.groupby('Material')['Profit']
        .sum()
        .sort_values(ascending=False)
        .head(10)

    )

    return {

        'labels': product_data.index.tolist(),

        'values': product_data.values.tolist()

    }