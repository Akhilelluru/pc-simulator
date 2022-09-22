from re import sub
import streamlit as st
import pandas as pd
import numpy as np
from collections import Counter
from io import BytesIO
import pyodbc

# Image
from PIL import Image

import warnings
warnings.filterwarnings("ignore") 

# Fixing the format of number in pandas DataFrames
pd.set_option('display.float_format', lambda x: '%.3f' % x)

print("start")
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

sql_conn = init_connection()

# Perform query.
# Uses st.experimental_memo to only rerun when the query changes or after 10 min.
@st.experimental_memo(ttl=600)
def read_data(_query, _conn):
    return pd.read_sql_query(_query, _conn)

# Call back variable Intialization for Input submit Button
if "button_clicked" not in st.session_state:    
    st.session_state.button_clicked = False
    st.session_state.drivers_clicked = False

# inputs call-back function
def inputs_callback():
    st.session_state.button_clicked = True

def drivers_callback():
    st.session_state.drivers_clicked = True

#@st.cache
#def read_input(filepath):
    
#    data = pd.read_excel(filepath)

#    return data

# @st.cache
# def convert_df(df):
#    return df.to_csv().encode('utf-8')


# data = read_input('data/dummy_file.xlsx')
#data = run_query('SELECT * FROM [abi_edw].[mx_tax_prof_coef_results] WITH(NOLOCK)')

def derived_variables_calc(d):
    
    d["Net Revenue"] = d["Beersales"] - d["Discounts"]
    d["MACO"] = d["Net Revenue"] - d["Cost"]
    d["EBIDA"] = d["MACO"] - d["Expenses"]
    d["EBT"] = d["EBIDA"] - d["Depreciation Amortization"] + d["Other Incomes"] - \
                d["Depreciation Amortization"] - d["Inflationary Adjustments"] - d["Other Expenses"]
    d["Nominal Income"] = d["Beersales"] + d["Other Incomes"]
    d["PC"] = d["EBT"] / d["Nominal Income"]

    return d

def results_df_creation(selected_data,adjusted_data):
    
    # create dummy dataframe with column and index names
    column_names = ["Model","Adjustment","Final"]
    index_names = ["Beersales","Discounts","Net Revenue","Cost","MACO","Expenses",\
                    "EBIDA","Depreciation Amortization","Other Incomes","Other Expenses",\
                    "Inflationary Adjustments","EBT","Nominal Income","PC"]
    df = pd.DataFrame(index=index_names,columns=column_names)

    Final = Counter(selected_data) + Counter(adjusted_data)
    selected_data = derived_variables_calc(selected_data)
    Final = derived_variables_calc(Final)

    df.loc[:,"Model"] = pd.Series(selected_data)
    df.loc[:,"Adjustment"] = pd.Series(adjusted_data)
    df.loc[:,"Final"] = pd.Series(Final)
    
    return df

def main():
    st.image('image/Ab-inbev_logo.jfif', width=100)
    st.title('Tax Simulator')

    sql_query = "SELECT * FROM [abi_edw].[mx_tax_prof_coef_results] WITH(NOLOCK) where dltdt = '2022-07-15' order by dltdt"
    data = read_data(sql_query, sql_conn)
    #print(list(data.society.unique()))

    with st.form(key = "inputs"):
        col1, col2, col3,col4 = st.columns(4)
        with col1:
            SOCIETY = st.selectbox(
            'Society',
            list(data['society'].unique()),
            key=1
                 )

        with col2:
            LE = st.selectbox(
            'LE',
            list(data['LE'].unique()),
            key=2
                )    

        with col3:
            Month = st.selectbox(
            'Month',
            list(data['month'].unique()),
            key=3
        )

        with col4:
            # Every form must have a submit button.
            input_submitted = st.form_submit_button("Submit",on_click = inputs_callback)
            if input_submitted:
                SOCIETY = SOCIETY
                LE = LE
                Month = Month
    
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

    data1 = data[(data['society']==SOCIETY) & (data['LE']==LE) & (data['month']==Month)]

    Selected_data = dict()
    
    if input_submitted or st.session_state.button_clicked:
    # Beer Sales
        bs_col1, bs_col2,bs_col3= st.columns([2,1,2])
        with bs_col1:
            bs_option = st.selectbox(
            'Beer Sales(Mi Mxn)',
            [f'{int(i/pow(10,6)):,}' for i in list(data1[data1['component']=='Beer_Sales']['forecaster_number'])],
            key="BS_select")

        with bs_col2:
            bs_Adjusted_Amount = st.number_input('Adjustment(Mi Mxn)',key="BS",format="%.4f") 

        with bs_col3:
                BS_FINAL = int(bs_option.replace(',','')) + bs_Adjusted_Amount
                st.metric(label="Final Beer Sales(Mi Mxn)", value=f'{BS_FINAL:,}')

        # other Incomes
        OI_col1,OI_col2,OI_col3 =  st.columns([2,1,2])
        with OI_col1:
            oi_option = st.selectbox(
            'Other Income(Mi Mxn)',
            [f'{int(i/pow(10,6)):,}' for i in list(np.array(data1[data1['component']=='NI']['forecaster_number']) - \
                np.array(data1[data1['component']=='Beer_Sales']['forecaster_number']))],
            key="OI_select"
            )

        with OI_col2:
            oi_Adjusted_Amount = st.number_input('Adjustment(Mi Mxn)',key="OI",format="%.4f")

        with OI_col3:
            OI_FINAL = int(oi_option.replace(',','')) + oi_Adjusted_Amount
            st.metric(label="Final Other Income(Mi Mxn)", value=f'{OI_FINAL:,}')
        
        # Cost
        cost_col1, cost_col2,cost_col3= st.columns([2,1,2])

        with cost_col1:
            cost_option = st.selectbox(
                'Cost(Mi Mxn)',
                [f'{int(i/pow(10,6)):,}' for i in list(data1[data1['component']=='Costs']['forecaster_number'])],
                key="cost_select"
                )

        with cost_col2:
            cost_Adjusted_Amount = st.number_input('Adjustment(Mi Mxn)',key="COST",format="%.4f") 
        
        with cost_col3:
            COST_FINAL = int(cost_option.replace(',','')) + cost_Adjusted_Amount
            st.metric(label="Final Cost(Mi Mxn)", value=f'{COST_FINAL:,}')
        
        # Expenes
        exp_col1, exp_col2,exp_col3= st.columns([2,1,2])

        with exp_col1:
            exp_option = st.selectbox(
                'Expenses(Mi Mxn)',
                [f'{int(i/pow(10,6)):,}' for i in list(data1[data1['component']=='Expenses']['forecaster_number'])],
                key="exp_select"
                )

        with exp_col2:
            exp_Adjusted_Amount = st.number_input('Adjustment(Mi Mxn)',key="EXP",format="%.4f") 
        
        with exp_col3:
            EXP_FINAL = int(exp_option.replace(',','')) + exp_Adjusted_Amount
            st.metric(label="Final Expenses(Mi Mxn)", value=f'{EXP_FINAL:,}')
            
        # Discounts
        dis_col1, dis_col2,dis_col3= st.columns([2,1,2])

        with dis_col1:
            dis_option = st.selectbox(
                'Discounts(Mi Mxn)',
                [f'{int(i/pow(10,6)):,}' for i in list(data1[data1['component']=='Discounts']['forecaster_number'])],
                key="dis_select"
                )

            with dis_col2:
                dis_Adjusted_Amount = st.number_input('Adjusted Amount(Mi Mxn)',key="DIS",format="%.4f") 
            
            with dis_col3:
                DIS_FINAL = int(dis_option.replace(',','')) + dis_Adjusted_Amount
                st.metric(label="Final Discounts(Mi Mxn)", value=f'{DIS_FINAL:,}')
                
        # Other Expenses
        oth_exp_col1, oth_exp_col2,oth_exp_col3= st.columns([2,1,2])

        with oth_exp_col1:
            oth_exp_option = st.selectbox(
                'Other Expenses(Mi Mxn)',
                [f'{int(i/pow(10,6)):,}' for i in list(data1[data1['component']=='Other expenses']['forecaster_number'])],
                key="oth_exp_select"
                )

        with oth_exp_col2:
            oth_exp_Adjusted_Amount = st.number_input('Adjusted(Mi Mxn)',key="OTH_EXP",format="%.4f") 
        
        with oth_exp_col3:
            OTH_EXP_FINAL = int(oth_exp_option.replace(',','')) + oth_exp_Adjusted_Amount
            st.metric(label="Final Other Expenses(Mi Mxn)", value=f'{OTH_EXP_FINAL:,}')
        
        # Depreciation & Amortization
        da_col1, da_col2,da_col3= st.columns([2,1,2])

        with da_col1:
            da_option = st.selectbox(
                'Depreciation Amortization(Mi Mxn)',
                [f'{int(i/pow(10,6)):,}' for i in list(data1[data1['component']=='Depreciation Amortization']['forecaster_number'])],
                key="DA_select"
                )

        with da_col2:
            da_Adjusted_Amount = st.number_input('Adjusted(Mi Mxn)',key="DA",format="%.4f") 
        
        with da_col3:
            DA_FINAL = int(da_option.replace(',','')) + da_Adjusted_Amount
            st.metric(label="Final Depreciation Amortization(Mi Mxn)", value=f'{DA_FINAL:,}')

        # Inflationary Adjustments
        ia_col1, ia_col2,ia_col3= st.columns([2,1,2])

        with ia_col1:
            ia_option = st.selectbox(
                'Inflationary Adjustments(Mi Mxn)',
                [f'{int(i/pow(10,6)):,}' for i in list(data1[data1['component']=='Inflationary Adjustments']['forecaster_number'])],
                key="IA_select"
                )

        with ia_col2:
            ia_Adjusted_Amount = st.number_input('Adjusted(Mi Mxn)',key="IA",format="%.4f") 
        
        with ia_col3:
            IA_FINAL = int(ia_option.replace(',','')) + ia_Adjusted_Amount
            st.metric(label="Final Inflationary Adjustments(Mi Mxn)", value=f'{IA_FINAL:,}')

        # # Ledger Accounts
        # IA_col1, ia_col2,ia_col3= st.columns([2,1,2])

        # with ia_col1:
        #     ia_option = st.selectbox(
        #         'Inflationary Adjustments(Mi Mxn)',
        #         [f'{int(i/pow(10,6)):,}' for i in list(data1[data1['component']=='Inflationary Adjustments']['forecaster_number'])],
        #         key="IA_select"
        #         )

        # with ia_col2:
        #     ia_Adjusted_Amount = st.number_input('Adjusted(Mi Mxn)',key="IA",format="%.4f") 
        
        # with ia_col3:
        #     IA_FINAL = int(ia_option.replace(',','')) + ia_Adjusted_Amount
        #     st.metric(label="Final Inflationary Adjustments(Mi Mxn)", value=f'{IA_FINAL:,}')
            
        #Declare a form and call methods directly on the returned object
        drivers_submit_button =  st.button("drivers_inputs_Submit")


        if drivers_submit_button:
            NI_FINAL = BS_FINAL + OI_FINAL
            EBT = NI_FINAL - COST_FINAL - EXP_FINAL - DIS_FINAL - OTH_EXP_FINAL
            PC = 100 * (EBT/NI_FINAL)

            selected_data ={
                "Beersales":int(bs_option.replace(',','')),
                "Other Incomes":int(oi_option.replace(',','')),
                "Cost":int(cost_option.replace(',','')),
                "Expenses":int(exp_option.replace(',','')),
                "Discounts" : int(dis_option.replace(',','')),
                "Other Expenses":int(oth_exp_option.replace(',','')),
                "Depreciation Amortization":int(da_option.replace(',','')),
                "Inflationary Adjustments" : int(ia_option.replace(',','')),
            }
            Adjusted_data = {
                "Beersales":bs_Adjusted_Amount,
                "Other Incomes":oi_Adjusted_Amount,
                "Cost":cost_Adjusted_Amount,
                "Expenses":exp_Adjusted_Amount,
                "Discounts" : dis_Adjusted_Amount,
                "Other Expenses":oth_exp_Adjusted_Amount,
                "Depreciation Amortization":da_Adjusted_Amount,
                "Inflationary Adjustments":ia_Adjusted_Amount
            }

            output_df = results_df_creation(selected_data,Adjusted_data)

            # st.dataframe(output_df)

            # output_encoded = convert_df(output_df)
            # st.download_button(
            #     label = "Press to Download",
            #     data = output_encoded,
            #     file_name = "file.csv",
            #     mime = "text/csv",
            #     key='download-csv'
            #     )
            
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
            
            df_xlsx = to_excel(output_df)
            st.download_button(label='📥 Download Current Result',
                                data=df_xlsx ,
                                file_name= 'df_test.xlsx')

            
if __name__=='__main__':
    main()