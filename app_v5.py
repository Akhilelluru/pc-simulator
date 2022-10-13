from collections import Counter
import numpy as np
import pandas as pd
import pyodbc
import streamlit as st
from io import BytesIO
from src.config import SQL_QRY

# Fixing the format of number in pandas DataFrames
pd.set_option('display.float_format', lambda x: '%.3f' % x)

# logo
st.image('image/Ab-inbev_logo.jfif', width=100)
# title
st.title('Tax Simulator')


# Initialize connection.
# Uses st.experimental_singleton to only run once.
@st.experimental_singleton
def init_connection():
    return pyodbc.connect(
        "DRIVER={ODBC Driver 17 for SQL Server};SERVER="
        + st.secrets["server"]
        + ";DATABASE="
        + st.secrets["database"]
        + ";UID="
        + st.secrets["username"]
        + ";PWD="
        + st.secrets["password"]
    )


# Call back variable initialization for Input submit Button
if "button_clicked" not in st.session_state:
    st.session_state["button_clicked"] = False

if "drivers_clicked" not in st.session_state:
    st.session_state["drivers_clicked"] = False


# inputs call-back function
def inputs_callback():
    st.session_state.button_clicked = True


def drivers_callback():
    st.session_state.drivers_clicked = True


# Perform query.
# Uses st.experimental_memo to only rerun when the query changes or after 10 min.
@st.experimental_memo(ttl=600)
def read_data(_query, _conn):
    return pd.read_sql_query(_query, _conn)


def derived_variables_calc(d):
    d["Nominal Income"] = d["Beer Sales"] + d["Other Incomes"]
    d["Net Revenue"] = d["Nominal Income"] - d["Discounts"]
    d["MACO"] = d["Net Revenue"] - d["Cost"]
    d["EBITDA"] = d["MACO"] - d["Expenses"]
    d["EBT"] = d["EBITDA"] - (d["Depreciation Amortization"] + \
               d["Cuentas Mayor"] + d["Inflationary Adjustments"] + d["Other Expenses"])
    d["PC"] = d["EBT"] / d["Nominal Income"]

    return d


def results_df_creation(selected_data, adjusted_data):
    # create dummy dataframe with column and index names
    column_names = ["Model", "Adjustment", "Final"]
    index_names = ["Beer Sales", "Discounts", "Net Revenue", "Cost", "MACO", "Expenses",
                   "EBITDA", "Depreciation Amortization", "Other Incomes", "Other Expenses",
                   "Cuentas Mayor", "Inflationary Adjustments", "EBT", "Nominal Income", "PC"]
    df = pd.DataFrame(index=index_names, columns=column_names)

    final = Counter(selected_data) + Counter(adjusted_data)
    selected_data = derived_variables_calc(selected_data)
    final = derived_variables_calc(final)

    df.loc[:, "Model"] = pd.Series(selected_data)
    df.loc[:, "Adjustment"] = pd.Series(adjusted_data)
    df.loc[:, "Final"] = pd.Series(final)

    return df

def to_excel(df):
    output = BytesIO()
    writer = pd.ExcelWriter(output, engine='xlsxwriter')
    df.to_excel(writer, index=False, sheet_name='Sheet1')
    workbook = writer.book
    worksheet = writer.sheets['Sheet1']
    format1 = workbook.add_format({'num_format': '0.00'})
    worksheet.set_column('A:A', None, format1)
    writer.save()
    processed_data = output.getvalue()
    return processed_data

def main():
    # initialize connection
    sql_conn = init_connection()

    # read query
    data = read_data(SQL_QRY, sql_conn)

    with st.form(key="inputs"):
        col1, col2, col3 = st.columns(3)
        with col1:
            sc_selectbox = st.selectbox(
                'Society',
                sorted(data['society'].unique()),
                key=1
            )

        with col2:
            le_selectbox = st.selectbox(
                'LE',
                sorted(data['le'].unique()),
                key=2
            )

        with col3:
            month_selectbox = st.selectbox(
                'Month',
                sorted(data['month'].unique()),
                key=3
            )

        # Every form must have a submit button.
        input_submitted = st.form_submit_button("Submit", on_click=inputs_callback)
        if input_submitted:
            society = sc_selectbox
            le = le_selectbox
            month = month_selectbox
            # store the values in session, once "Submit" button clicked
            st.session_state['society'], st.session_state['le'], st.session_state['month'] = society, le, month



    # Reintializing the drivers input
    if input_submitted:
        st.session_state.BS = 0
        st.session_state.OI = 0
        st.session_state.COST = 0
        st.session_state.EXP = 0
        st.session_state.DIS = 0
        st.session_state.OTH_EXP = 0
        st.session_state.DA = 0
        st.session_state.IA = 0
        st.session_state.LA = 0

    # with st.form(key="drivers", clear_on_submit=False):
    if input_submitted or st.session_state.button_clicked:
        # fetch from the session
        society, le, month = st.session_state['society'], st.session_state['le'], st.session_state['month']

        # filter based on current selection
        data1 = data[(data['society'] == society) & (data['le'] == le) & (data['month'] == month)]

        # Beer Sales
        bs_col1, bs_col2, bs_col3 = st.columns([1.5, 1, 1.5])
        with bs_col1:
            bs_option = st.selectbox(
                'Beer Sales(Mi Mxn)',
                [f'{float(i / pow(10, 6)):,.2f}' for i in
                 list(data1[data1['component'] == 'Beer_Sales']['forecast_number'])],
                key="BS_select")

        with bs_col2:
            bs_adjusted_amount = st.number_input('Adjustment(Mi Mxn)', key="BS", format="%.4f")

        with bs_col3:
            bs_final = float(bs_option.replace(',', '')) + bs_adjusted_amount
            st.metric(label="Final Beer Sales(Mi Mxn)", value=f'{bs_final:,.2f}')

        # other Incomes
        oi_col1, oi_col2, oi_col3 = st.columns([1.5, 1, 1.5])
        with oi_col1:
            oi_option = st.selectbox(
                'Other Income(Mi Mxn)',
                [f'{float(i / pow(10, 6)):,.2f}' for i in
                 list(np.array(data1[data1['component'] == 'NI']['forecast_number']) - \
                      np.array(data1[data1['component'] == 'Beer_Sales']['forecast_number']))],
                key="OI_select"
            )

        with oi_col2:
            oi_adjusted_amount = st.number_input('Adjustment(Mi Mxn)', key="OI", format="%.4f")

        with oi_col3:
            oi_final = float(oi_option.replace(',', '')) + oi_adjusted_amount
            st.metric(label="Final Other Income(Mi Mxn)", value=f'{oi_final:,.2f}')

        # Cost
        cost_col1, cost_col2, cost_col3 = st.columns([1.5, 1, 1.5])

        with cost_col1:
            cost_option = st.selectbox(
                'Cost(Mi Mxn)',
                [f'{float(i / pow(10, 6)):,.2f}' for i in list(data1[data1['component'] == 'Costs']['forecast_number'])],
                key="cost_select"
            )

        with cost_col2:
            cost_adjusted_amount = st.number_input('Adjustment(Mi Mxn)', key="COST", format="%.4f")

        with cost_col3:
            cost_final = float(cost_option.replace(',', '')) + cost_adjusted_amount
            st.metric(label="Final Cost(Mi Mxn)", value=f'{cost_final:,.2f}')

        # Expenses
        exp_col1, exp_col2, exp_col3 = st.columns([1.5, 1, 1.5])

        with exp_col1:
            exp_option = st.selectbox(
                'Expenses(Mi Mxn)',
                [f'{float(i / pow(10, 6)):,.2f}' for i in list(data1[data1['component'] == 'Expenses']['forecast_number'])],
                key="exp_select"
            )

        with exp_col2:
            exp_adjusted_amount = st.number_input('Adjustment(Mi Mxn)', key="EXP", format="%.4f")

        with exp_col3:
            exp_final = float(exp_option.replace(',', '')) + exp_adjusted_amount
            st.metric(label="Final Expenses(Mi Mxn)", value=f'{exp_final:,.2f}')

        # Discounts
        dis_col1, dis_col2, dis_col3 = st.columns([1.5, 1, 1.5])

        with dis_col1:
            dis_option = st.selectbox(
                'Discounts(Mi Mxn)',
                [f'{float((-1*i) / pow(10, 6)):,.2f}' for i in list(data1[data1['component'] == 'Discounts']['forecast_number'])],
                key="dis_select"
            )

            with dis_col2:
                dis_adjusted_amount = st.number_input('Adjustment(Mi Mxn)', key="DIS", format="%.4f")

            with dis_col3:
                dis_final = float(dis_option.replace(',', '')) + dis_adjusted_amount
                st.metric(label="Final Discounts(Mi Mxn)", value=f'{dis_final:,.2f}')

        # Other Expenses
        oth_exp_col1, oth_exp_col2, oth_exp_col3 = st.columns([1.5, 1, 1.5])

        with oth_exp_col1:
            oth_exp_option = st.selectbox(
                'Other Expenses(Mi Mxn)',
                [f'{float(i / pow(10, 6)):,.2f}' for i in
                 list(data1[data1['component'] == 'Other Expenses']['forecast_number'])],
                key="oth_exp_select"
            )

        with oth_exp_col2:
            oth_exp_adjusted_amount = st.number_input('Adjustment(Mi Mxn)', key="OTH_EXP", format="%.4f")

        with oth_exp_col3:
            oth_exp_final = float(oth_exp_option.replace(',', '')) + oth_exp_adjusted_amount
            st.metric(label="Final Other Expenses(Mi Mxn)", value=f'{oth_exp_final:,.2f}')

        # Depreciation & Amortization
        da_col1, da_col2, da_col3 = st.columns([1.5, 1, 1.5])

        with da_col1:
            da_option = st.selectbox(
                'Depreciation Amortization(Mi Mxn)',
                [f'{float((-1*i) / pow(10, 6)):,.2f}' for i in
                 list(data1[data1['component'] == 'Depreciation Amortization']['forecast_number'])],
                key="DA_select"
            )

        with da_col2:
            da_adjusted_amount = st.number_input('Adjustment(Mi Mxn)', key="DA", format="%.4f")

        with da_col3:
            da_final = float(da_option.replace(',', '')) + da_adjusted_amount
            st.metric(label="Final Depreciation Amortization(Mi Mxn)", value=f'{da_final:,.2f}')

        # Inflationary Adjustments
        ia_col1, ia_col2, ia_col3 = st.columns([1.5, 1, 1.5])

        with ia_col1:
            ia_option = st.selectbox(
                'Inflationary Adjustments(Mi Mxn)',
                [f'{float(i / pow(10, 6)):,.2f}' for i in
                 list(data1[data1['component'] == 'Inflationary Adjustments']['forecast_number'])],
                key="IA_select"
            )

        with ia_col2:
            ia_adjusted_amount = st.number_input('Adjustment(Mi Mxn)', key="IA", format="%.4f")

        with ia_col3:
            ia_final = float(ia_option.replace(',', '')) + ia_adjusted_amount
            st.metric(label="Final Inflationary Adjustments(Mi Mxn)", value=f'{ia_final:,.2f}')

        # Ledger Accounts
        la_col1, la_col2, la_col3 = st.columns([1.5, 1, 1.5])

        with la_col1:
            la_option = st.selectbox(
                'Cuentas Mayor(Mi Mxn)',
                [f'{float((-1*i) / pow(10, 6)):,.2f}' for i in
                 list(data1[data1['component'] == 'Ledger Account']['forecast_number'])],
                key="la_select"
            )

        with la_col2:
            la_adjusted_amount = st.number_input('Adjustment(Mi Mxn)', key="LA", format="%.4f")

        with la_col3:
            la_final = float(la_option.replace(',', '')) + la_adjusted_amount
            st.metric(label="Final Cuentas Mayor(Mi Mxn)", value=f'{la_final:,.2f}')

        # Declare a form and call methods directly on the returned object
        # drivers_submit_button = st.form_submit_button("Calculate P.C.", on_click=drivers_callback)
        drivers_submit_button = st.button("Calculate P.C.", on_click=drivers_callback)

        if drivers_submit_button or st.session_state.drivers_clicked:
            print('submit button clicked!!!')
            ni_final = bs_final + oi_final
            ebitda = ni_final - cost_final - exp_final - dis_final - oth_exp_final - da_final - ia_final - la_final
            pc = 100 * (ebitda / ni_final)
            print(pc)

            selected_data = {
                "Beer Sales": float(bs_option.replace(',', '')),
                "Other Incomes": float(oi_option.replace(',', '')),
                "Cost": float(cost_option.replace(',', '')),
                "Expenses": float(exp_option.replace(',', '')),
                "Discounts": float(dis_option.replace(',', '')),
                "Other Expenses": float(oth_exp_option.replace(',', '')),
                "Depreciation Amortization": float(da_option.replace(',', '')),
                "Inflationary Adjustments": float(ia_option.replace(',', '')),
                "Cuentas Mayor": float(la_option.replace(',', ''))
            }
            adjusted_data = {
                "Beer Sales": bs_adjusted_amount,
                "Other Incomes": oi_adjusted_amount,
                "Cost": cost_adjusted_amount,
                "Expenses": exp_adjusted_amount,
                "Discounts": dis_adjusted_amount,
                "Other Expenses": oth_exp_adjusted_amount,
                "Depreciation Amortization": da_adjusted_amount,
                "Inflationary Adjustments": ia_adjusted_amount,
                "Cuentas Mayor": la_adjusted_amount
            }

            output_df = results_df_creation(selected_data, adjusted_data)

            st.dataframe(output_df)

            #
            # output_encoded = convert_df(output_df)
            # st.download_button(
            #     label = "Press to Download",
            #     data = output_encoded,
            #     file_name = "file.csv",
            #     mime = "text/csv",
            #     key='download-csv'
            #     )

            df_xlsx = to_excel(output_df)
            st.download_button(label='📥 Download Current Result',
                               data=df_xlsx,
                               file_name='df_test.xlsx')


if __name__ == '__main__':
    main()
