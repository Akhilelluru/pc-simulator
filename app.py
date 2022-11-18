# from datetime import datetime
import numpy as np
import base64

import pandas as pd

from src.config import SQL_QRY, COUNTRY, DLTTM, DLTDT, NI_SPLIT_SQL_QRY
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
    sql_conn = init_connection()

    # read query # abi_stg.mx_tax_prof_coef_results
    all_data_except_bs_df = read_data(SQL_QRY, sql_conn)

    # read query # abi_edw.mx_tax_prof_coef_nominal_income_split
    bs_df = read_data(NI_SPLIT_SQL_QRY, sql_conn)

    # complete data
    data = pd.concat([all_data_except_bs_df, bs_df], ignore_index=True)
    # print(data['component'].unique())

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

        # # other Incomes
        # oi_col1, oi_col2, oi_col3 = st.columns([1.5, 1, 1.5])
        # oi_values = ((data1[data1['component'] == 'NI']['forecast_number']) - \
        #              (data1[data1['component'] == 'Beer_Sales']['forecast_number'])).reset_index().astype(str).apply(
        #     ': '.join, axis=1)
        #
        # with oi_col1:
        #     oi_option = st.selectbox(
        #         'Other Income(Mi Mxn)',
        #         [i for i in
        #          list(oi_values)],
        #         format_func=format_func,
        #         key="OI_select"
        #     )
        #
        # with oi_col2:
        #     oi_adjusted_amount = st.number_input('Adjustment(Mi Mxn)', key="OI", step=1.0, format="%.4f")
        #
        # with oi_col3:
        #     oi_adjusted_amount = oi_adjusted_amount * pow(10, 6)
        #     oi_final = float(oi_option.split(": ")[1]) + oi_adjusted_amount
        #     st.metric(label="Final Other Income(Mi Mxn)", value=f'{float(oi_final / pow(10, 6)):,.2f}')
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

        with ti_col3:
            # Taxable Income
            deduction_final = (dis_final + costs_final + exp_final + da_final +
                               oth_exp_final + la_final + ia_final)
            print(f'deductions{deduction_final}, NI: {ni_final}')
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
        op_df = to_excel(output_df)

        # draw a line
        st.markdown("""___""")

        # pc columns
        pc_col1, pc_col2, pc_col3 = st.columns([1.5, 1, 1.5])

        # push to db
        with pc_col1:
            # push to db if month is 12
            if month == 12:
                print('data pushed to dB successfully.')
                # data prep for dB
                data_prep = data1[(data1.component == 'Beer_Sales') & (data1.index == bs_type)]
                print(f'hello:, {data_prep}')
                # st.button(label="Push to dB Table", help="click to push finalize data to table.",
                #           # on_click=insert_to_table,
                #
                #           )

        #pc download
        with pc_col2:
            # export df
            export_file_name = f'pc_{str(le)}_{str(society)}_{str(month)}.xlsx'
            st.download_button(label='📥 Download',
                               data=op_df,
                               file_name=export_file_name
                               )

        # pc value
        with pc_col3:

            pc = (ti_final / ni_final)
            print(pc)
            st.metric(label="Profit Coefficient", value=f'{pc:.2%}')

        #
        # #######
        #
        # sample_qry = f"select left(society, 4) as society_id, year, month," \
        #              f" pp_001001 as NI, pp_006001 as Beer_Sales " \
        #              f"from [abi_stg].[mx_tax_prof_coef_nominal_income]" \
        #              f"where year = {year} and month = {int(le[0])} and left(society, 4) = {society}"
        # prev_month_sc_data = read_data(sample_qry, sql_conn)
        # print(f'test--{prev_month_sc_data}')
        # print(data1)
        #
        # qry2 = f""


if __name__ == '__main__':
    main()
