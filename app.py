from flask import Flask, render_template, request, send_file, redirect, url_for
import pandas as pd
import os
import re
import sqlite3

app = Flask(__name__)

# =========================
# CONFIG
# =========================

UPLOAD_FOLDER = 'uploads'
DOWNLOAD_FOLDER = 'downloads'
DB_NAME = 'erp_database.db'

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# CREATE FOLDERS

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

if not os.path.exists(DOWNLOAD_FOLDER):
    os.makedirs(DOWNLOAD_FOLDER)


# =========================
# CUSTOMER NAME NORMALIZATION
# =========================

CUSTOMER_MASTER = {
    # Subros variants
    'SUBROS LIMITED'    : 'Subros Limited',
    'SUBROS LTD'        : 'Subros Limited',
    'Subros Limited'    : 'Subros Limited',

    # Sanden Vikas variants
    'Sanden Vikas (India) Limited'     : 'Sanden Vikas (India) Pvt. Ltd',
    'SANDEN VIKAS (INDIA) PVT LTD'    : 'Sanden Vikas (India) Pvt. Ltd',
    'SANDEN VIKAS INDIA PRIVATE LIMITED' : 'Sanden Vikas (India) Pvt. Ltd',
    'Sanden Vikas (India) Pvt. Ltd'   : 'Sanden Vikas (India) Pvt. Ltd',

    # Tata Toyo variants
    'TATA TOYO RADIATOR LIMITED,'  : 'Tata Toyo Radiator Ltd',
    'TATA TOYO RADIATOR LTD'       : 'Tata Toyo Radiator Ltd',
    'TATA TOYO RADIATOR LTD.'      : 'Tata Toyo Radiator Ltd',
    'TATA TOYO RADIATOR LIMITED'   : 'Tata Toyo Radiator Ltd',

    # Mahle Anand variants
    'MAHLE ANAND Thermal Systems Private' : 'Mahle Anand Thermal Systems Pvt. Ltd',
    'Mahle Anand Thermal Systems Private' : 'Mahle Anand Thermal Systems Pvt. Ltd',

    # Hanon variants
    'HANON AUTOMOTIVE SYSTEMS INDIA PVT' : 'Hanon Automotive Systems India Pvt. Ltd',
    'Hanon Automotive Systems India Pvt' : 'Hanon Automotive Systems India Pvt. Ltd',

    # IFB variants — kept separate (different divisions)
    'IFB AUTOMOTIVE (P) LTD'             : 'IFB Automotive (P) Ltd',
    'IFB AUTOMOTIVE PVT LTD, (DOOR DIV)' : 'IFB Automotive Pvt. Ltd (Door Div)',
}

def normalize_customer(name):
    if not name or str(name).strip().lower() == 'nan':
        return name
    name = str(name).strip()
    return CUSTOMER_MASTER.get(name, name)


# =========================
# ERP DATA PROCESSOR
# =========================

def process_erp_file(filepath):

    raw_df = pd.read_excel(
        filepath,
        sheet_name='Final',
        header=[0, 1]
    )

    raw_df.dropna(how='all', inplace=True)

    customer_col = None
    material_col = None

    for col in raw_df.columns:
        col_name = str(col[0]).strip().lower()

        if col_name == 'customer':
            customer_col = col

        if col_name == 'material description':
            material_col = col

    print("Customer Column =", customer_col)
    print("Material Column =", material_col)

    print("\n====== COLUMNS ======")

    for col in raw_df.columns:
        print(col, type(col))

    print("=====================\n")

    for col in raw_df.columns:
        if isinstance(col, tuple):
            print(col[1])

    month_map = {
        '01': 'Jan',
        '02': 'Feb',
        '03': 'Mar',
        '04': 'Apr',
        '05': 'May',
        '06': 'Jun',
        '07': 'Jul',
        '08': 'Aug',
        '09': 'Sep',
        '10': 'Oct',
        '11': 'Nov',
        '12': 'Dec'
    }

    # =========================
    # COLUMN DETECTION
    # =========================

    sales_columns = {}
    rm_columns = {}
    qty_columns = {}
    budget_columns = {}

    print("Customer Column =", customer_col)
    print("Material Column =", material_col)
    
    for col in raw_df.columns:

        level_1 = col[0]
        level_2 = str(col[1]).strip().lower()

        # skip non-date columns
        if not hasattr(level_1, 'year'):
            continue

        year = str(level_1.year)

        month_num = str(level_1.month).zfill(2)

        month = month_map.get(month_num)

        key = (year, month)

        # SALES
        if level_2 == 'actual':

          sales_columns[key] = col

        # QUANTITY
        elif level_2 == 'actual.1':

         qty_columns[key] = col

        # RM
        elif level_2 == 'raw material':

         rm_columns[key] = col

        # BUDGET
        elif level_2 == 'budget':

         budget_columns[key] = col

    # =========================
    # PROCESS DATA
    # =========================

    records = []

    all_keys = sorted(set(
        list(sales_columns.keys()) +
        list(rm_columns.keys()) +
        list(qty_columns.keys())
    ))

    for year, month in all_keys:

        sales_col = sales_columns.get((year, month))
        rm_col = rm_columns.get((year, month))
        qty_col = qty_columns.get((year, month))
        budget_col = budget_columns.get((year, month))

        for _, row in raw_df.iterrows():

            sales = 0
            rm = 0
            qty = 0
            budget = 0

            # SALES
            if sales_col:

                sales = row.get(sales_col, 0)

                if pd.isna(sales):
                    sales = 0

                try:
                    sales = float(sales)
                except:
                    sales = 0

            # RM
            if rm_col:

                rm = row.get(rm_col, 0)

                if pd.isna(rm):
                    rm = 0

                try:
                    rm = float(rm)
                except:
                    rm = 0

            # QTY
            if qty_col:

                qty = row.get(qty_col, 0)

                if pd.isna(qty):
                    qty = 0

                try:
                    qty = float(qty)
                except:
                    qty = 0

            # BUDGET
            if budget_col:

                budget = row.get(budget_col, 0)

                if pd.isna(budget):
                    budget = 0

                try:
                    budget = float(budget)
                except:
                    budget = 0

            profit = sales - rm

            customer = ''

            if customer_col:
                customer = str(
                    row.get(customer_col, '')
                ).strip()

            material = ''

            if material_col:
                material = str(
                    row.get(material_col, '')
                ).strip()

            if customer.lower() == 'nan' or customer == '':
                continue

            records.append({

                'Year': str(year),
                'Month': month,
                'Customer': customer,
                'Material': material,
                'Sales': round(sales, 2),
                'Budget': round(budget, 2),
                'RM': round(rm, 2),
                'Quantity': round(qty, 2),
                'Profit': round(profit, 2)

            })

    normalized_df = pd.DataFrame(records)

    if normalized_df.empty:
        return normalized_df

    normalized_df = normalized_df[
        ~(
            (normalized_df['Sales'] == 0) &
            (normalized_df['RM'] == 0) &
            (normalized_df['Quantity'] == 0)
        )
    ]

    normalized_df.reset_index(drop=True, inplace=True)

    return normalized_df

# =========================
# LOAD DATA
# =========================

def load_data():

    conn = sqlite3.connect(DB_NAME)

    df = pd.read_sql(
        "SELECT * FROM erp_data",
        conn
    )

    conn.close()

    df['Customer'] = df['Customer'].apply(normalize_customer)

    return df

# =========================
# INDEX
# =========================

@app.route('/')
def index():

    return render_template('index.html')

# =========================
# DASHBOARD
# =========================

@app.route('/dashboard', methods=['POST'])
def dashboard():
    if 'file' not in request.files:
        return "No file uploaded"

    file = request.files['file']

    if file.filename == '':
        return "No file selected"

    filepath = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
    file.save(filepath)

    df = process_erp_file(filepath)

    if df.empty:
        return "No valid ERP data found"

    conn = sqlite3.connect(DB_NAME)
    df.to_sql('erp_data', conn, if_exists='replace', index=False)
    conn.close()

    return redirect(url_for('dashboard_page'))

# =========================
# DASHBOARD PAGE
# =========================

@app.route('/dashboard-page')
def dashboard_page():

    if not os.path.exists(DB_NAME):
        return "Upload ERP file first"

    df = load_data()

    return render_template(
        'dashboard.html',
        years=sorted(
            df['Year']
            .dropna()
            .astype(str)
            .unique()
        ),
        customers=sorted(
            df['Customer']
            .dropna()
            .unique()
            .tolist()
        ),
        selected_year='All',
        selected_customer='All',
        table_data=[]
    )

# =========================
# RENDER DASHBOARD
# =========================

def render_dashboard(df, selected_year='All', selected_customer='All'):

    total_sales = round(
        float(df['Sales'].sum()),
        2
    )

    total_rm = round(
        float(df['RM'].sum()),
        2
    )

    total_profit = round(
        float(df['Profit'].sum()),
        2
    )

    total_budget = round(
        float(df['Budget'].sum()),
        2
    )

    budget_variance = round(
        total_sales - total_budget,
        2
    )

    if total_sales > 0:

        rm_percentage = round(
            (total_rm / total_sales) * 100,
            2
        )

        overall_profit_margin = round(
            (total_profit / total_sales) * 100,
            2
        )

    else:

        rm_percentage = 0
        overall_profit_margin = 0

    month_order = [

        'Jan', 'Feb', 'Mar', 'Apr',
        'May', 'Jun', 'Jul', 'Aug',
        'Sep', 'Oct', 'Nov', 'Dec'

    ]

    monthly_sales = (

        df.groupby('Month')['Sales']
        .sum()
        .reindex(month_order, fill_value=0)

    )

    monthly_budget = (

        df.groupby('Month')['Budget']
        .sum()
        .reindex(month_order, fill_value=0)

    )

    monthly_profit = (

        df.groupby('Month')['Profit']
        .sum()
        .reindex(month_order, fill_value=0)

    )

    monthly_rm = (

    df.groupby('Month')['RM']
    .sum()
    .reindex(month_order, fill_value=0)

    )

    budget_variance_values = []

    for sales, budget in zip(
       monthly_sales.tolist(),
       monthly_budget.tolist()
    ):

       budget_variance_values.append(
          round(sales - budget, 2)
       )


    # =========================
    # PROFIT MARGIN %
    # =========================

    profit_margin_values = []

    for sales, profit in zip(
        monthly_sales.tolist(),
        monthly_profit.tolist()
    ):

      if sales > 0:

         margin = round(
            (profit / sales) * 100,
            2
         )

      else:

         margin = 0

      profit_margin_values.append(margin)


    # =========================
    # CHART
    # =========================

    chart = {

        'labels': monthly_sales.index.tolist(),

        'values': monthly_sales.values.tolist(),

        'budget': monthly_budget.values.tolist()

    }

    # =========================
    # TOP CUSTOMER
    # =========================

    top_customer = "N/A"

    if not df.empty:

        customer_sales = (

            df.groupby('Customer')['Sales']
            .sum()
            .sort_values(ascending=False)

        )

        customer_sales = customer_sales[
            customer_sales > 0
        ]

        if not customer_sales.empty:

            top_customer = customer_sales.index[0]

    # =========================
    # TOP PRODUCT
    # =========================

    top_product = "N/A"

    if not df.empty:

        valid_products = df[
            df['Material'].notna()
        ]

        valid_products = valid_products[
            valid_products['Material'].astype(str).str.strip() != ''
        ]

    if not valid_products.empty:

        product_sales = (

            valid_products
            .groupby('Material')['Sales']
            .sum()
            .sort_values(ascending=False)

        )

        if not product_sales.empty:

            top_product = str(product_sales.index[0])

    # =========================
    # TOP MONTH
    # =========================

    top_month = "N/A"

    if monthly_sales.sum() > 0:

        top_month = monthly_sales.idxmax()

    # Get all years from full database
    master_df = load_data()

    years = sorted(
        master_df['Year']
        .dropna()
        .astype(str)
        .unique()
    )

    print(profit_margin_values)
    print(len(profit_margin_values))

    print("monthly_sales =", monthly_sales.tolist())
    print("monthly_profit =", monthly_profit.tolist())
    
    print("PROFIT MARGIN VALUES =", profit_margin_values)

    return render_template(

     'dashboard.html',

     total_sales=total_sales,
     total_rm=total_rm,
     total_profit=total_profit,
     total_budget=total_budget,
     budget_variance=budget_variance,
     rm_percentage=rm_percentage,
     overall_profit_margin=overall_profit_margin,
     profit_margin_values=profit_margin_values,
     top_customer=top_customer,
     top_product=top_product,
     top_month=top_month,

     chart=chart,
     years=years,

     total_quantity=round(
        float(df['Quantity'].sum()),
        2
     ),

     customers=sorted(
        master_df['Customer']
        .dropna()
        .unique()
        .tolist()
    ),

     highest_sales_month=monthly_sales.idxmax(),

     lowest_sales_month=monthly_sales.idxmin(),

     best_customer=top_customer,

     best_product = str(top_product),

     table_data=df.head(100).to_dict(
        orient='records'
     ),

    selected_year=selected_year,
    selected_customer=selected_customer

)


# =========================
# DASHBOARD FILTER
# =========================

@app.route('/dashboard-filter')
def dashboard_filter():

    if not os.path.exists(DB_NAME):
        return "Upload ERP file first"

    master_df = load_data()

    selected_year = request.args.get('year', 'All')
    selected_customer = request.args.get('customer', 'All')

    df = master_df.copy()

    if selected_year != 'All':
        df = df[
            df['Year'].astype(str) == str(selected_year)
        ]

    if selected_customer != 'All':
        df = df[
            df['Customer'] == selected_customer
        ]

    return render_dashboard(
        df,
        selected_year,
        selected_customer
    )


# =========================
# SALES PAGE
# =========================

@app.route('/sales')
def sales_page():

    if not os.path.exists(DB_NAME):
        return "Upload ERP file first"

    df = load_data()

    selected_year = request.args.get('year', 'All')
    selected_month = request.args.get('month', 'All')

    if selected_year != 'All':
        df = df[df['Year'].astype(str) == str(selected_year)]

    if selected_month != 'All':
        df = df[df['Month'] == selected_month]


    month_order = [

        'Jan', 'Feb', 'Mar', 'Apr',
        'May', 'Jun', 'Jul', 'Aug',
        'Sep', 'Oct', 'Nov', 'Dec'

    ]

    monthly_sales = (

        df.groupby('Month')['Sales']
        .sum()
        .reindex(month_order, fill_value=0)

    )

    monthly_profit = (

        df.groupby('Month')['Profit']
        .sum()
        .reindex(month_order, fill_value=0)

    )

    monthly_rm = (

        df.groupby('Month')['RM']
        .sum()
        .reindex(month_order, fill_value=0)

    )

    monthly_quantity = (

        df.groupby('Month')['Quantity']
        .sum()
        .reindex(month_order, fill_value=0)

    )

    monthly_budget = (

        df.groupby('Month')['Budget']
        .sum()
        .reindex(month_order, fill_value=0)

    )

    budget_variance_values = []

    for sales, budget in zip(
        monthly_sales.tolist(),
        monthly_budget.tolist()
    ):

       budget_variance_values.append(
         round(sales - budget, 2)
    )
       
    product_customer = (
        df.groupby(['Material', 'Customer'])
        .agg({
            'Sales': 'sum',
            'Profit': 'sum'
        })
        .reset_index()
    )

    product_customer['Margin %'] = (
           product_customer['Profit'] / product_customer['Sales']
    ) * 100

    product_customer['Margin %'] = product_customer['Margin %'].fillna(0).round(2)

    product_customer = product_customer.sort_values(
       by='Profit',
       ascending=False
    )

    # =========================
    # YOY GROWTH
    # =========================

    full_df = load_data()

    # =========================
    # GROWTH %
    # =========================

    growth = 0
    current_sales = 0
    previous_sales = 0

    current_year = None
    previous_year = None
    current_df = pd.DataFrame()
    previous_df = pd.DataFrame()

    if selected_year != 'All':
        current_year = str(selected_year)
        previous_year = str(int(current_year) - 1)

        current_df = full_df[full_df['Year'].astype(str) == current_year]
        previous_df = full_df[full_df['Year'].astype(str) == previous_year]

        if selected_month != 'All':
           current_df = current_df[current_df['Month'] == selected_month]
           previous_df = previous_df[previous_df['Month'] == selected_month]

        current_sales = current_df['Sales'].sum()
        previous_sales = previous_df['Sales'].sum()

        if previous_sales != 0:
           growth = round(((current_sales - previous_sales) / previous_sales) * 100, 2)

    yearly_sales = (

        full_df.groupby('Year')['Sales']
        .sum()
        .sort_index()

    )

    yoy_labels = yearly_sales.index.astype(str).tolist()

    yoy_values = yearly_sales.values.tolist()

    yoy_growth = []

    previous = None

    for value in yoy_values:

        if previous is None:

            yoy_growth.append(0)

        else:

            year_growth = (

                (value - previous) / previous

            ) * 100 if previous != 0 else 0

            yoy_growth.append(
                round(year_growth, 2)
            )

        previous = value

    years = sorted(

        full_df['Year']
        .dropna()
        .astype(str)
        .unique()

    )

    
    # =========================
    # TOP LOSS PRODUCTS
    # =========================

    top_loss_products = (

        df.groupby('Material')['Profit']
        .sum()
        .sort_values()
        .head(10)
        .reset_index()

    )

    top_loss_labels = top_loss_products[
        'Material'
    ].tolist()

    top_loss_values = top_loss_products[
        'Profit'
    ].tolist()


    # =========================
    # TOP PRODUCTS
    # =========================

    top_products_df = (
        df[df['Material'].notna()]
        .groupby('Material')['Sales']
        .sum()
        .sort_values(ascending=False)
        .head(10)
    )

    top_product_labels = (
       top_products_df.index.astype(str).tolist()
    )

    top_product_values = (
       top_products_df.values.tolist()
    )

    # =========================
    # TOP PRODUCT SALES
    # =========================

    top_products_df = (
        df[df['Material'].notna()]
        .groupby('Material')['Sales']
        .sum()
        .sort_values(ascending=False)
        .head(10)
    )

    top_product_labels = (
        top_products_df.index.astype(str).tolist()
    )

    top_product_values = (
        top_products_df.values.tolist()
    )

    # =========================
    # GROWTH LABEL
    # =========================

    growth_label = ""

    if selected_year != "All":
        growth_label = f"{selected_year} vs {int(selected_year)-1}"

    # =========================
    # SALES RM GAP
    # =========================

    sales_rm_gap = []

    for sales, rm in zip(
        monthly_sales.tolist(),
        monthly_rm.tolist()
    ):

        sales_rm_gap.append(
            round(sales - rm, 2)
        )

    return render_template(

        'sales.html',

        yoy_labels=yoy_labels,
        yoy_growth=yoy_growth,

        total_sales=round(
            float(df['Sales'].sum()),
            2
        ),

        total_profit=round(
            float(df['Profit'].sum()),
            2
        ),

        table_data=df.head(100).to_dict(
            orient='records'
        ),

        top_month=monthly_sales.idxmax(),

        growth=growth,

        growth_label=growth_label,

        labels=monthly_sales.index.tolist(),

        budget_variance_values=budget_variance_values,

        values=monthly_sales.tolist(),

        profit_values=monthly_profit.tolist(),

        years=years,

        selected_year=selected_year,

        selected_month=selected_month,

        top_loss_labels=top_loss_labels,

        top_loss_values=top_loss_values,

        monthly_rm=monthly_rm.tolist(),

        top_product_labels=top_product_labels,

        product_customer=product_customer.to_dict(orient='records'),

        top_product_values=top_product_values,

        monthly_quantity=monthly_quantity.tolist(),

        sales_rm_gap=sales_rm_gap

    )



# =========================
# CUSTOMERS PAGE
# =========================

@app.route('/customers')
def customers_page():
    if not os.path.exists(DB_NAME):
        return "Upload ERP file first"

    df = load_data()

    selected_year = request.args.get('year', 'All')
    selected_customer = request.args.get('customer', 'All')

    if selected_year != 'All':
        df = df[df['Year'].astype(str) == str(selected_year)]

    if selected_customer != 'All':
        df = df[df['Customer'] == selected_customer]

    customer_data = (
        df.groupby('Customer')['Sales']
        .sum()
        .sort_values(ascending=False)
        .head(10)
    )

    customer_table = customer_data.reset_index().to_dict(orient='records')

    full_df = load_data()

    years = sorted(full_df['Year'].dropna().astype(str).unique())
    customer_list = sorted(full_df['Customer'].dropna().unique())

    best_customer = customer_data.index[0] if not customer_data.empty else "N/A"

    return render_template(
        'customers.html',
        customer_labels=customer_data.index.tolist(),
        customer_values=customer_data.values.tolist(),
        customer_table=customer_table,
        customer_list=customer_list,
        years=years,
        selected_year=selected_year,
        selected_customer=selected_customer,
        best_customer=best_customer
    )


# =========================
# REPORTS PAGE
# =========================

@app.route('/reports')
def reports_page():

    if not os.path.exists(DB_NAME):

        return "Upload ERP file first"

    df = load_data()

    years = sorted(
        df['Year']
        .astype(str)
        .unique()
    )

    months = [

        'Jan', 'Feb', 'Mar', 'Apr',
        'May', 'Jun', 'Jul', 'Aug',
        'Sep', 'Oct', 'Nov', 'Dec'

    ]

    selected_year = request.args.get(
        'year',
        ''
    )

    selected_month = request.args.get(
        'month',
        'All'
    )

    return render_template(

        'reports.html',

        years=years,

        months=months,

        selected_year=selected_year,

        selected_month=selected_month

    )


# =========================
# DOWNLOAD REPORT
# =========================

@app.route('/download-report/<report_type>/<file_type>')
def download_report(report_type, file_type):

    if not os.path.exists(DB_NAME):

        return "No ERP data loaded"

    df = load_data()

    year = request.args.get('year')
    month = request.args.get('month')

    # =========================
    # FILTER YEAR
    # =========================

    if year and year != 'All':

        df = df[
            df['Year'].astype(str) == str(year)
        ]

    # =========================
    # FILTER MONTH
    # =========================

    if month and month != 'All':

        df = df[
            df['Month'] == month
        ]

    # =========================
    # REPORT TYPE
    # =========================

    if report_type == 'sales':

        report_df = df[[

            'Year',
            'Month',
            'Customer',
            'Material',
            'Sales'

        ]]

    elif report_type == 'customer':

        report_df = (

            df.groupby('Customer')[

                ['Sales', 'Profit']

            ]

            .sum()
            .reset_index()

        )

    elif report_type == 'product':

        report_df = (

            df.groupby('Material')[

                ['Sales', 'Profit']

            ]

            .sum()
            .reset_index()

        )

    elif report_type == 'rm':

        report_df = df[[

            'Year',
            'Month',
            'Customer',
            'RM'

        ]]

    elif report_type == 'profit':

        report_df = df[[

            'Year',
            'Month',
            'Customer',
            'Profit'

        ]]

    else:

        report_df = df

    # =========================
    # FILE NAME
    # =========================

    parts = [f"{report_type}_report"]

    if year and year != 'All':
       parts.append(str(year))

    if month and month != 'All':
       parts.append(str(month))

    file_name = "_".join(parts)

    # =========================
    # EXPORT EXCEL
    # =========================

    if file_type == 'excel':

        output_path = os.path.join(
            DOWNLOAD_FOLDER,
            f"{file_name}.xlsx"
        )

        report_df.to_excel(
            output_path,
            index=False
        )

        return send_file(
            output_path,
            as_attachment=True
        )

    # =========================
    # EXPORT CSV
    # =========================

    elif file_type == 'csv':

        output_path = os.path.join(
            DOWNLOAD_FOLDER,
            f"{file_name}.csv"
        )

        report_df.to_csv(
            output_path,
            index=False
        )

        return send_file(
            output_path,
            as_attachment=True
        )

    return "Invalid file type"

# =========================
# RUN APP
# =========================

if __name__ == "__main__":
    import os

    port = int(os.environ.get("PORT", 5000))

    app.run(
        host="0.0.0.0",
        port=port
    )