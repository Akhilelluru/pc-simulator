import streamlit as st
import pandas as pd
import numpy as np
import pyodbc

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

sql_query = "SELECT * FROM [abi_edw].[mx_tax_prof_coef_results] WITH(NOLOCK) where dltdt = '2022-07-15' order by dltdt"
data = read_data(sql_query, sql_conn)
print(list(data.society.unique()))

if "button_clicked" not in st.session_state:    
    st.session_state.button_clicked = False
    
def callback():
    st.session_state.button_clicked = True

# Image
from PIL import Image

## header and Logo
col1, col2 = st.columns(2)

with col1:
    st.image('image/Ab-inbev_logo.jfif', width=100)

with col2:
    st.title('Tax Stimulator')


with st.form(key = "inputs"):
    col1, col2, col3,col4 = st.columns(4)
    with col1:
        SOCIETY = st.selectbox(
            'Society',
            list(data['society'].unique()),
            key=1                 
        )
    with col2:
        RUN_DATE = st.selectbox(
            'Run_date',
            ["6/7/2022","6/8/2022"],
            key=2
        )
    with col3:
        LE = st.selectbox(
            'LE',
            ["5+5","6+6"],
            key=3
        )
    
    with col4:
        # Every form must have a submit button.
        input_submitted = st.form_submit_button("Submit",on_click = callback)
        if input_submitted:
            SOCIETY = SOCIETY
            RUN_DATE = RUN_DATE
            LE = LE

if input_submitted or st.session_state.button_clicked:
    
    # Beer Sales
    bs_col1, bs_col2,bs_col3= st.columns(3)

    with bs_col1:
        bs_option = st.selectbox(
            'Beer Sales',
            [8795874,7845788,8795642],
            key="BS"
            )

    with bs_col2:
        bs_Adjusted_Amount = st.number_input('Adjustment',key="BS") 
    
    with bs_col3:
        BS_FINAL = bs_option + bs_Adjusted_Amount
        st.metric(label="Final Beer Sales", value=BS_FINAL)
    
    # Nominal Income
    NI_col1,NI_col2,NI_col3 =  st.columns(3)
    
    with NI_col1:
        ni_option = st.selectbox(
            'Nominal Income',
            [1450402,15005624,1478987],
            key="NI"
            )

    with NI_col2:
        ni_Adjusted_Amount = st.number_input('Adjustment',key="NI")
        
    with NI_col3:
        NI_FINAL =ni_option + ni_Adjusted_Amount
        st.metric(label="Final Nominal Income", value=NI_FINAL)
    
    # Cost
    cost_col1, cost_col2,cost_col3= st.columns(3)

    with cost_col1:
        cost_option = st.selectbox(
            'Cost',
            [30000,333333,356545],
            key="cost"
            )

    with cost_col2:
        cost_Adjusted_Amount = st.number_input('Adjustment',key="cost") 
    
    with cost_col3:
        COST_FINAL = cost_option + cost_Adjusted_Amount
        st.metric(label="Final Cost", value=COST_FINAL)
    
    # Expenes
    exp_col1, exp_col2,exp_col3= st.columns(3)

    with exp_col1:
        exp_option = st.selectbox(
            'Expenses',
            [54540,78954,65789],
            key="exp"
            )

    with exp_col2:
        exp_Adjusted_Amount = st.number_input('Adjustment',key="exp") 
    
    with exp_col3:
        EXP_FINAL = exp_option + exp_Adjusted_Amount
        st.metric(label="Final Expenses", value=EXP_FINAL)
        
    # Discounts
    dis_col1, dis_col2,dis_col3= st.columns(3)

    with dis_col1:
        dis_option = st.selectbox(
            'Discounts',
            [54540,78954,657894],
            key="dis"
            )

    with dis_col2:
        dis_Adjusted_Amount = st.number_input('Adjusted Amount',key="dis") 
    
    with dis_col3:
        DIS_FINAL = dis_option + dis_Adjusted_Amount
        st.metric(label="Final Discounts", value=DIS_FINAL)
        
    # Other Expenses
    oth_exp_col1, oth_exp_col2,oth_exp_col3= st.columns(3)

    with oth_exp_col1:
        oth_exp_option = st.selectbox(
            'Other Expenses',
            [54524,78954,657894],
            key="oth_exp"
            )

    with oth_exp_col2:
        oth_exp_Adjusted_Amount = st.number_input('Adjusted Amount',key="oth_exp") 
    
    with oth_exp_col3:
        OTH_EXP_FINAL = oth_exp_option + oth_exp_Adjusted_Amount
        st.metric(label="Final Other Expenses", value=OTH_EXP_FINAL)
    
#     # Other drivers
#     IA_col1, DA_col2,LA_col3= st.columns([1,1,1])

#     with IA_col1:
#         IA_FINAL = st.number_input('Inflation Adjusments',key="IA") 

#     with DA_col2:
#         DA_FINAL = st.number_input('Depreciation & Amortization',key="DA") 
        
#     with oth_exp_col3:
#         LA_FINAL = st.number_input('Ledger Accounts',key="LA") 
    
    # Declare a form and call methods directly on the returned object
    drivers_submit_button =  st.button("drivers_inputs_Submit")
    
    print("drivers_submit_button",drivers_submit_button)
    if drivers_submit_button:
        BS_FINAL = bs_option + bs_Adjusted_Amount
        NI_FINAL = ni_option + ni_Adjusted_Amount
        st.write("BEER_sales",BS_FINAL)
        st.write("Nominal_Income",NI_FINAL)







