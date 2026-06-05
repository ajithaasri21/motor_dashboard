import pandas as pd
import re

# =========================
# SAFE FLOAT CONVERTER
# =========================

def safe_float(value):

    try:

        if pd.isna(value):

            return 0.0

        value = str(value).replace(',', '').strip()

        if value == '':

            return 0.0

        return float(value)

    except:

        return 0.0


# =========================
# ERP DATA PROCESSOR
# =========================

def process_erp_file(filepath):

    # =========================
    # READ FINAL SHEET
    # =========================

    df = pd.read_excel(

        filepath,

        sheet_name='Final',

        header=[0, 1]

    )

    # =========================
    # FLATTEN MULTI HEADERS
    # =========================

    columns = []

    for col1, col2 in df.columns:

        col1 = str(col1).strip()
        col2 = str(col2).strip()

        if 'Unnamed' in col2:

            columns.append(col1)

        else:

            columns.append(f"{col1}_{col2}")

    df.columns = columns

    # =========================
    # CLEAN COLUMN NAMES
    # =========================

    cleaned_columns = []

    for col in df.columns:

        col = str(col)

        col = col.replace(' ', '_')
        col = col.replace('-', '_')
        col = col.replace('/', '_')
        col = col.replace('%', 'Percentage')
        col = col.replace('(', '')
        col = col.replace(')', '')
        col = col.replace('.', '')
        col = col.strip()

        cleaned_columns.append(col)

    df.columns = cleaned_columns

    # =========================
    # REMOVE EMPTY ROWS
    # =========================

    df.dropna(how='all', inplace=True)

    # =========================
    # FIND MASTER COLUMNS
    # =========================

    material_col = None
    customer_col = None

    for col in df.columns:

        if 'material' in col.lower():

            material_col = col

        if 'customer' in col.lower():

            customer_col = col

    # =========================
    # NORMALIZED RECORDS
    # =========================

    records = []

    # =========================
    # LOOP THROUGH COLUMNS
    # =========================

    for col in df.columns:

        # =========================
        # FIND YEAR + MONTH
        # =========================

        match = re.search(

            r'(\d{4})_(\d{2})',

            col

        )

        if match:

            year = match.group(1)

            month_num = match.group(2)

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

            month = month_map.get(

                month_num,

                month_num

            )

            # =========================
            # SALES / QTY COLUMNS
            # =========================

            if any(word in col.lower() for word in [

                'actual',
                'sales',
                'qty'

            ]):

                # =========================
                # LOOP THROUGH ROWS
                # =========================

                for _, row in df.iterrows():

                    # =========================
                    # QUANTITY
                    # =========================

                    qty = safe_float(

                        row.get(col, 0)

                    )

                    # =========================
                    # FIND SP COLUMN
                    # =========================

                    sp_col = None

                    possible_sp = [

                        col.replace('Actual_Qty', 'SP'),
                        col.replace('Qty', 'SP'),
                        col.replace('Sales', 'SP'),
                        col.replace('Actual', 'SP')

                    ]

                    for p in possible_sp:

                        if p in df.columns:

                            sp_col = p

                            break

                    # =========================
                    # SP VALUE
                    # =========================

                    sp = 0

                    if sp_col:

                        sp = safe_float(

                            row.get(sp_col, 0)

                        )

                    # =========================
                    # RM VALUE
                    # =========================

                    rm = 0

                    for rm_col in df.columns:

                        if (

                            'rm' in rm_col.lower()

                            and year in rm_col

                            and month_num in rm_col

                        ):

                            rm = safe_float(

                                row.get(rm_col, 0)

                            )

                            break

                    # =========================
                    # CALCULATIONS
                    # =========================

                    revenue = qty * sp

                    rm_cost = qty * rm

                    profit = revenue - rm_cost

                    # =========================
                    # APPEND RECORD
                    # =========================

                    records.append({

                        'Year': str(year),

                        'Month': str(month),

                        'Customer': str(

                            row.get(
                                customer_col,
                                ''
                            )

                        ).strip(),

                        'Material': str(

                            row.get(
                                material_col,
                                ''
                            )

                        ).strip(),

                        'Quantity': qty,

                        'SP': sp,

                        'RM': rm,

                        'Revenue': revenue,

                        'RM_Cost': rm_cost,

                        'Profit': profit

                    })

    # =========================
    # CREATE DATAFRAME
    # =========================

    normalized_df = pd.DataFrame(records)

    # =========================
    # REMOVE INVALID ROWS
    # =========================

    normalized_df = normalized_df[

        normalized_df['Customer']
        .astype(str)
        .str.lower() != 'nan'

    ]

    # =========================
    # FINAL CLEANUP
    # =========================

    normalized_df.fillna(0, inplace=True)

    return normalized_df