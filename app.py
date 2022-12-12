# from datetime import datetime
import numpy as np
import base64
from sqlalchemy.dialects.mssql import VARCHAR, INTEGER, NUMERIC, DATE, TIME
from src.config import *
from src.util import *

# Fixing the format of number in pandas DataFrames
pd.set_option('display.float_format', lambda x: '%.3f' % x)

# title
title = 'Tax Simulator'

# logo
LOGO_IMG = 'image/Ab-inbev_logo.jfif'

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


def main():
    # initialize connection
    sql_conn, sql_engine = init_connection()

    # initialize output connection
    sql_op_conn, sql_op_engine = init_op_connection()

    # read query # abi_stg.mx_tax_prof_coef_results
    all_data_except_bs_df = read_data(SQL_QRY, sql_conn)

    # get society id and name
    sc_cols = ['society', 'business_unity']
    sc_id_name_dict = {sc[0]: sc[1] for sc in all_data_except_bs_df[sc_cols].drop_duplicates().values}
    print(sc_id_name_dict)

    # read query # abi_edw.mx_tax_prof_coef_nominal_income_split
    bs_df = read_data(NI_SPLIT_SQL_QRY, sql_conn)

    # read query #abi_edw.mx_tax_prof_coef_results_final_clean
    clean_df = read_data(CLEAN_DATA_QRY, sql_conn)
    print(clean_df['component'].unique())

    # complete data
    data = pd.concat([all_data_except_bs_df, bs_df], ignore_index=True)
    print(data['component'].unique())

    # create col for driver selectbox
    data['type_n_val'] = data['model_type'] + ": " + data['forecast_number'].astype('str')

    # get filtered data
    dropdown_data = data.loc[data.component == 'NI', ['year', 'le', 'society', 'month']].drop_duplicates()

    # title
    st.title(title)

    with st.sidebar:
        # side bar class (CSS).
        st.markdown(
            """
            <style>
            .css-1vq4p4l {padding: 1rem 1rem 10rem;}
            .css-12oz5g7 {
                padding-top: 1rem;
                padding-left: 1rem;
                padding-right: 6rem;
            }
            .container {
                display: flex;
            }
            .logo-img {
                height: 60px;
                width: auto;
            }
            </style>
            """,
            unsafe_allow_html=True
        )
        # sidebar image
        st.markdown(
            f"""
            <div class="container">
                <img class="logo-img" src="data:image/png;base64,{base64.b64encode(open(LOGO_IMG, "rb").read()).decode()}"> 
            </div>
            """,
            unsafe_allow_html=True
        )

        # sidebar title
        st.sidebar.title("Parameters")

        # le select box
        yr_selectbox = st.selectbox(
            'Year',
            options=['select'] + sorted(dropdown_data['year'].unique(), reverse=True),
            key='yr_sbox'
        )

        # le select box
        if yr_selectbox != 'select':
            yr_box_value = st.session_state['yr_sbox']
            le_selectbox_options = ['select'] + sorted(
                dropdown_data[dropdown_data['year'] == yr_box_value]['le'].unique(), reverse=True)
        else:
            le_selectbox_options = ['select']
        le_selectbox = st.selectbox(
            'LE',
            options=le_selectbox_options,
            key='le_sbox'
        )

        # month select box -- based on LE selection
        if le_selectbox != 'select':
            yr_box_value = st.session_state['yr_sbox']
            le_box_value = st.session_state['le_sbox']
            month_selectbox_options = ['select'] + sorted(
                dropdown_data[(dropdown_data['year'] == yr_box_value) & (dropdown_data['le'] == le_box_value)][
                    'month'].unique(), reverse=True)
        else:
            month_selectbox_options = ['select']

        month_selectbox = st.selectbox(
            'Month',
            options=month_selectbox_options,
            key='month_sbox'
        )

        # society select box -- based on LE selection
        if le_selectbox != 'select':
            yr_box_value = st.session_state['yr_sbox']
            le_box_value = st.session_state['le_sbox']
            sc_selectbox_options = ['select'] + sorted(
                dropdown_data[(dropdown_data['year'] == yr_box_value) & (dropdown_data['le'] == le_box_value)][
                    'society'].unique(), reverse=False)
        else:
            sc_selectbox_options = ['select']

        sc_selectbox = st.selectbox(
            'Society',
            options=sc_selectbox_options,
            key='sc_sbox'
        )

        # Every form must have a submit button.
        input_submitted = st.button("Submit", on_click=inputs_callback)
        if input_submitted:
            society = sc_selectbox
            le = le_selectbox
            month = month_selectbox
            year = yr_selectbox
            # store the values in session, once "Submit" button clicked
            st.session_state['society'], st.session_state['le'], st.session_state['month'], st.session_state[
                'year'] = society, le, month, year

    # re-intializing the drivers input, if "submit" button is clicked
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

    if input_submitted or st.session_state.button_clicked:
        # fetch from the session
        society, le, month, year = st.session_state['society'], st.session_state['le'], st.session_state['month'], \
                                   st.session_state['year']

        # filter based on current selection
        d_filter = (data['society'] == society) & (data['le'] == le) & (data['month'] == month) & (data['year'] == year)
        data1 = data.loc[d_filter, :].set_index('model_type')

        # # create col for driver selectbox
        # data1['type_n_val'] = data1['model_type'] + ": " + data1['forecast_number'].astype('str')

        # write parameters as label
        # param (CSS).
        st.markdown(
            """
            <style>
            .param-container {
                    display: flex;
                    /*border: 1px solid #DCDCDC;*/
                    border-radius: 10px;
            }
            .param-label {
                background-color: #EEEEEE;
                border: 1px solid #DCDCDC;
                padding: 1.5% 5% 1.5% 5%;
                border-radius: 10px
            }
            </style>
            """,
            unsafe_allow_html=True
        )

        st.caption("Parameters selected")
        st.markdown(
            f"""
            <div class="param-container"> 
                <div class="param-label">
                    <label>Year:&nbsp</label><b>{year}</b>
                </div>&nbsp&nbsp         
                <div class="param-label">
                    <label>LE:&nbsp</label><b>{le}</b>
                </div>&nbsp&nbsp     
                <div class="param-label">
                    <label>Society:&nbsp</label><b>{society}</b>
                </div>&nbsp&nbsp                
                <div class="param-label">
                    <label>Month:&nbsp</label><b>{month}</b>
                </div>&nbsp&nbsp
            </div>
            
            """,
            unsafe_allow_html=True
        )
        st.caption("")
        # horizontal line to divide param with drivers
        st.markdown("""___""")
        st.caption("Adjust Drivers & Calculate P.C.")

        # Beer Sales
        bs_col1, bs_col2, bs_col3 = st.columns([1.5, 1, 1.5])

        with bs_col1:
            bs_option = st.selectbox(
                'Beer Sales(Mi Mxn)',
                [i for i in list(data1[data1['component'] == 'Beer_Sales']['type_n_val'])],
                format_func=format_func,
                key="BS_select"
            )

        with bs_col2:
            bs_adjusted_amount = st.number_input('Adjustment(Mi Mxn)', key="BS", step=1.0, format="%.4f")

        with bs_col3:
            bs_adjusted_amount = bs_adjusted_amount * pow(10, 6)
            bs_final = float(bs_option.split(": ")[1]) + bs_adjusted_amount
            st.metric(label="Final Beer Sales(Mi Mxn)", value=f'{float(bs_final / pow(10, 6)):,.2f}')

        # Discounts
        dis_col1, dis_col2, dis_col3 = st.columns([1.5, 1, 1.5])

        with dis_col1:
            dis_option = st.selectbox(
                'Discounts(Mi Mxn)',
                [i for i in list(data1[data1['component'] == 'Discounts']['type_n_val'])],
                format_func=format_func,
                key="dis_select"
            )

            with dis_col2:
                dis_adjusted_amount = st.number_input('Adjustment(Mi Mxn)', key="DIS", step=1.0, format="%.4f")

            with dis_col3:
                dis_adjusted_amount = dis_adjusted_amount * pow(10, 6)
                dis_final = float(dis_option.split(": ")[1]) + dis_adjusted_amount
                st.metric(label="Final Discounts(Mi Mxn)", value=f'{float(dis_final / pow(10, 6)):,.2f}')

        # Costs
        costs_col1, costs_col2, costs_col3 = st.columns([1.5, 1, 1.5])

        with costs_col1:
            costs_option = st.selectbox(
                'Costs(Mi Mxn)',
                [i for i in list(data1[data1['component'] == 'Costs']['type_n_val'])],
                format_func=format_func,
                key="costs_select"
            )

        with costs_col2:
            costs_adjusted_amount = st.number_input('Adjustment(Mi Mxn)', key="COST", step=1.0, format="%.4f")

        with costs_col3:
            costs_adjusted_amount = costs_adjusted_amount * pow(10, 6)
            costs_final = float(costs_option.split(": ")[1]) + costs_adjusted_amount
            st.metric(label="Final Costs(Mi Mxn)", value=f'{float(costs_final / pow(10, 6)):,.2f}')

        # Expenses
        exp_col1, exp_col2, exp_col3 = st.columns([1.5, 1, 1.5])

        with exp_col1:
            exp_option = st.selectbox(
                'Expenses(Mi Mxn)',
                [i for i in list(data1[data1['component'] == 'Expenses']['type_n_val'])],
                format_func=format_func,
                key="exp_select"
            )

        with exp_col2:
            exp_adjusted_amount = st.number_input('Adjustment(Mi Mxn)', key="EXP", step=1.0, format="%.4f")

        with exp_col3:
            exp_adjusted_amount = exp_adjusted_amount * pow(10, 6)
            exp_final = float(exp_option.split(": ")[1]) + exp_adjusted_amount
            st.metric(label="Final Expenses(Mi Mxn)", value=f'{float(exp_final / pow(10, 6)):,.2f}')

        # Depreciation & Amortization
        da_col1, da_col2, da_col3 = st.columns([1.5, 1, 1.5])

        with da_col1:
            da_option = st.selectbox(
                'Depreciation Amortization(Mi Mxn)',
                [i for i in
                 list(data1[data1['component'] == 'Depreciation Amortization']['type_n_val'])],
                format_func=format_func,
                key="DA_select"
            )

        with da_col2:
            da_adjusted_amount = st.number_input('Adjustment(Mi Mxn)', key="DA", step=1.0, format="%.4f")

        with da_col3:
            da_adjusted_amount = da_adjusted_amount * pow(10, 6)
            da_final = float(da_option.split(": ")[1]) + da_adjusted_amount
            st.metric(label="Final Depreciation Amortization(Mi Mxn)", value=f'{float(da_final / pow(10, 6)):,.2f}')

        # Other Expenses
        oth_exp_col1, oth_exp_col2, oth_exp_col3 = st.columns([1.5, 1, 1.5])

        with oth_exp_col1:
            oth_exp_option = st.selectbox(
                'Other Expenses(Mi Mxn)',
                [i for i in list(data1[data1['component'] == 'Other Expenses']['type_n_val'])],
                format_func=format_func,
                key="oth_exp_select"
            )

        with oth_exp_col2:
            oth_exp_adjusted_amount = st.number_input('Adjustment(Mi Mxn)', key="OTH_EXP", step=1.0, format="%.4f")

        with oth_exp_col3:
            oth_exp_adjusted_amount = oth_exp_adjusted_amount * pow(10, 6)
            oth_exp_final = float(oth_exp_option.split(": ")[1]) + oth_exp_adjusted_amount
            st.metric(label="Final Other Expenses(Mi Mxn)", value=f'{float(oth_exp_final / pow(10, 6)):,.2f}')

        # Ledger Accounts
        la_col1, la_col2, la_col3 = st.columns([1.5, 1, 1.5])

        with la_col1:
            la_option = st.selectbox(
                'Cuentas Mayor(Mi Mxn)',
                [i for i in list(data1[data1['component'] == 'Ledger Account']['type_n_val'])],
                format_func=format_func,
                key="la_select"
            )

        with la_col2:
            la_adjusted_amount = st.number_input('Adjustment(Mi Mxn)', key="LA", step=1.0, format="%.4f")

        with la_col3:
            la_adjusted_amount = la_adjusted_amount * pow(10, 6)
            la_final = float(la_option.split(": ")[1]) + la_adjusted_amount
            st.metric(label="Final Cuentas Mayor(Mi Mxn)", value=f'{float(la_final / pow(10, 6)):,.2f}')

        # Inflationary Adjustments
        ia_col1, ia_col2, ia_col3 = st.columns([1.5, 1, 1.5])

        with ia_col1:
            ia_option = st.selectbox(
                'Inflationary Adjustments(Mi Mxn)',
                [i for i in list(data1[data1['component'] == 'Inflationary Adjustments']['type_n_val'])],
                format_func=format_func,
                key="IA_select"
            )

        with ia_col2:
            ia_adjusted_amount = st.number_input('Adjustment(Mi Mxn)', key="IA", step=1.0, format="%.4f")

        with ia_col3:
            ia_adjusted_amount = ia_adjusted_amount * pow(10, 6)
            ia_final = float(ia_option.split(": ")[1]) + ia_adjusted_amount
            st.metric(label="Final Inflationary Adjustments(Mi Mxn)", value=f'{float(ia_final / pow(10, 6)):,.2f}')

        # draw a line
        st.markdown("""___""")

        # Nominal Income
        ni_col1, ni_col2, ni_col3 = st.columns([1.5, 1, 1.5])
        with ni_col1:
            ni_option = st.selectbox(
                'Nominal Income(Mi Mxn)',
                [i for i in list(data1[data1['component'] == 'NI']['type_n_val'])],
                format_func=format_func,
                key="NI_select"
            )

        with ni_col2:
            ni_adjusted_amount = st.number_input('Adjustment(Mi Mxn)', key="NI", step=1.0, format="%.4f")

        with ni_col3:
            ni_adjusted_amount = ni_adjusted_amount * pow(10, 6)
            ni_final = float(ni_option.split(": ")[1]) + ni_adjusted_amount
            st.metric(label="Final Nominal Income(Mi Mxn)", value=f'{float(ni_final / pow(10, 6)):,.2f}')

        # Taxable Income
        ti_col1, ti_col2, ti_col3 = st.columns([1.5, 1, 1.5])

        with ti_col2:
            # Transfer Price Adjustment
            adjustment_final = (
                    ni_adjusted_amount + dis_adjusted_amount + costs_adjusted_amount + exp_adjusted_amount +
                    da_adjusted_amount + oth_exp_adjusted_amount + la_adjusted_amount + ia_adjusted_amount
            )
            tpa_final = adjustment_final
            st.metric(label="Transfer Price Adjustment(Mi Mxn)", value=f'{float(tpa_final / pow(10, 6)):,.2f}')

        with ti_col3:
            # Taxable Income
            deduction_final = (dis_final + costs_final + exp_final + da_final +
                               oth_exp_final + la_final + ia_final)

            ti_final = ni_final + deduction_final
            st.metric(label="Final Taxable Income(Mi Mxn)", value=f'{float(ti_final / pow(10, 6)):,.2f}')

        # Profit Coefficient.
        # driver value and it's type
        bs_type, bs_opt_value = bs_option.split(": ")
        ni_type, ni_opt_value = ni_option.split(": ")
        cost_type, cost_opt_value = costs_option.split(": ")
        exp_type, exp_opt_value = exp_option.split(": ")
        dis_type, dis_opt_value = dis_option.split(": ")
        oth_exp_type, oth_exp_opt_value = oth_exp_option.split(": ")
        da_type, da_opt_value = da_option.split(": ")
        ia_type, ia_opt_value = ia_option.split(": ")
        la_type, la_opt_value = la_option.split(": ")

        # selected values
        selected_data = {
            "Beer Sales": float(bs_opt_value),
            "Nominal Income": float(ni_opt_value),
            "Costs": float(cost_opt_value),
            "Expenses": float(exp_opt_value),
            "Discounts": float(dis_opt_value),
            "Other Expenses": float(oth_exp_opt_value),
            "Depreciation Amortization": float(da_opt_value),
            "Inflationary Adjustments": float(ia_opt_value),
            "Cuentas Mayor": float(la_opt_value)
        }
        # adjusted values
        adjusted_data = {
            "Beer Sales": bs_adjusted_amount,
            "Nominal Income": ni_adjusted_amount,
            "Costs": costs_adjusted_amount,
            "Expenses": exp_adjusted_amount,
            "Discounts": dis_adjusted_amount,
            "Other Expenses": oth_exp_adjusted_amount,
            "Depreciation Amortization": da_adjusted_amount,
            "Inflationary Adjustments": ia_adjusted_amount,
            "Cuentas Mayor": la_adjusted_amount
        }

        # calculations
        output_df = results_df_creation(selected_data, adjusted_data)
        binary_df = format_download_data(output_df)
        op_df = to_excel(binary_df)

        # prepare data for dB push, only if month is december
        if month == 12:
            # selected model types for different drivers.
            selected_values_dict = {
                'Beer_Sales': bs_type,
                'NI': ni_type,
                'Costs': cost_type,
                'Expenses': exp_type,
                'Discounts': dis_type,
                'Other Expenses': oth_exp_type,
                'Ledger Account': la_type,
                'Depreciation Amortization': da_type,
                'Inflationary Adjustments': ia_type
            }
            # final values ( store only for the month of dec)
            final_data_dict = {
                'Beer_Sales': bs_final,
                'NI': ni_final,
                'Costs': costs_final,
                'Expenses': exp_final,
                'Discounts': dis_final,
                'Other Expenses': oth_exp_final,
                'Ledger Account': la_final,
                'Depreciation Amortization': da_final,
                'Inflationary Adjustments': ia_final
            }
            # convert selected_values_dict to df
            selected_values_df = pd.DataFrame(selected_values_dict.items(), columns=['component', 'model_type'])
            # add sc and le
            selected_values_df['society'] = society
            selected_values_df['le'] = le
            print(data['component'].unique())

            # forecast values of drivers based on model type selection
            forecast_df = data.merge(selected_values_df, how='inner', on=['society', 'component', 'model_type', 'le'])
            # rename col
            forecast_df.rename({'forecast_number': 'value'}, axis=1, inplace=True)
            # update december month values based on adjustments
            forecast_df.loc[forecast_df.month == month, 'value'] = forecast_df['component'].map(final_data_dict)

            # actual values of drivers based on model type selection
            actual_df = clean_df.merge(selected_values_df, how='inner', on=['society', 'component', 'le'])

            # merge actual and forecast
            prep_df = pd.concat([actual_df, forecast_df], ignore_index=True)

            # select cols
            prep_cols = ['society', 'component', 'le', 'year', 'month', 'model_type', 'value']
            prep_df = prep_df[prep_cols]

            # le
            current_le_month, _, _ = le.partition('+')
            prep_df['filter_flag'] = np.where(prep_df['component'] == 'Inflationary Adjustments',
                                              np.where(prep_df['month'] >= (int(current_le_month) - 1), 1, 0),
                                              np.where(prep_df['month'] >= int(current_le_month), 1, 0))

            prep_df['le'] = np.where(prep_df['component'] == 'Inflationary Adjustments',
                                     np.where(prep_df['month'] == (int(current_le_month) - 1), 'actual', prep_df['le']),
                                     np.where(prep_df['month'] == int(current_le_month), 'actual', prep_df['le']))

            # get monthly values
            sort_cols = ['society', 'component', 'year', 'month', 'model_type']
            prep_df = prep_df.sort_values(by=sort_cols)
            grp_cols = ['society', 'component', 'model_type']
            prep_df['value_diff'] = prep_df.groupby(grp_cols)['value'].diff()

            # derive metric cols
            prep_df['forecast_number'] = np.where(prep_df['le'] != 'actual', prep_df.value, np.nan)
            prep_df['monthly_forecast'] = np.where(prep_df['le'] != 'actual', prep_df.value_diff, np.nan)
            prep_df['actual_number'] = np.where(prep_df['le'] == 'actual', prep_df.value, np.nan)
            prep_df['monthly_actual'] = np.where(prep_df['le'] == 'actual', prep_df.value_diff, np.nan)

            # filter (current month + forecast months)
            month_filter = (prep_df['filter_flag'] == 1)
            prep_df = prep_df[month_filter]

            # map society with name
            prep_df['business_unity'] = prep_df['society'].map(sc_id_name_dict)

            # add cols
            prep_df['country'] = COUNTRY
            prep_df['DLTDT'] = DLTDT
            prep_df['DLTTM'] = DLTTM

            # final cols for dB
            db_cols = ['country', 'society', 'business_unity', 'year', 'month', 'component', 'forecast_number',
                       'monthly_forecast', 'actual_number', 'monthly_actual', 'model_type', 'DLTDT', 'DLTTM', 'le']
            sql_table_df = prep_df[db_cols]
            # column types for sql table.
            col_types = {"country": VARCHAR(25),
                         "society": VARCHAR(50),
                         "business_unity": VARCHAR(50),
                         "year": INTEGER,
                         "month": INTEGER,
                         "component": VARCHAR(25),
                         "forecast_number": NUMERIC(17, 4),
                         "monthly_forecast": NUMERIC(17, 4),
                         "actual_number": NUMERIC(17, 4),
                         "monthly_actual": NUMERIC(17, 4),
                         "DLTDT": DATE,
                         "DLTTM": TIME,
                         "le": VARCHAR(10)
                         }

            # convert to binary data # https://stackoverflow.com/questions/69228482/error-while-downloading-the-dataframe
            # -from-streamlit-web-application-after-data
            tmp_df_op = to_excel(sql_table_df, index=False)

        # draw a line
        st.markdown("""___""")

        # pc columns
        pc_col1, pc_col2, pc_col3, pc_col4 = st.columns([1, 1, 1, 1.5])

        # push to db
        with pc_col1:
            # push to db if month is 12
            if month == 12:
                # data prep for dB
                upload_btn = st.button(label="Upload", key="upload_btn", help='click to push data to dB.',
                                       disabled=False)
                if upload_btn:
                    insert_data_to_dB(sql_table_df, conn=sql_op_engine,
                                      table_name=OP_TBL_NAME,
                                      schema_name=OP_TBL_SCHEMA_NAME,
                                      data_type=col_types)
        # pc download
        with pc_col2:
            # push to db if month is 12
            if month == 12:
                export_file_name = f'pc_{str(le)}_{str(society)}_{str(month)}_dB.xlsx'
                st.download_button(label='📥 Download dB Data',
                                   data=tmp_df_op,
                                   file_name=export_file_name
                                   )

        # pc download
        with pc_col3:
            # export df
            export_file_name = f'pc_{str(le)}_{str(society)}_{str(month)}.xlsx'
            st.download_button(label='📥 Download PC',
                               data=op_df,
                               file_name=export_file_name
                               )

        # pc value
        with pc_col4:
            pc = (ti_final / ni_final)
            # print(pc)
            st.metric(label="Profit Coefficient", value=f'{pc:.2%}')


if __name__ == '__main__':
    try:
        main()
    except Exception as ex:
        st.error('There is an error. Please re-load the page.', icon="🚨")
        print(ex)
