# import library
import numpy as np
import pandas as pd
from sqlalchemy.engine import URL
from sqlalchemy import create_engine
import pyodbc
import streamlit as st
from collections import Counter
from io import BytesIO


# Initialize connection.
# Uses st.experimental_singleton to only run once.
@st.experimental_singleton
def init_connection():
    connection_url = URL.create(
        "mssql+pyodbc",
        username=st.secrets['username'],
        password=st.secrets['password'],
        host=st.secrets['server'],
        database=st.secrets['database'],
        query={
            "driver": "ODBC Driver 17 for SQL Server",
            "autocommit": "True",
        },
    )
    engine = create_engine(connection_url).execution_options(
        isolation_level="AUTOCOMMIT"
    )
    sql_engine = create_engine(connection_url, echo=True)
    conn = sql_engine.raw_connection(sql_engine)
    return conn, sql_engine


# Perform query.
# Uses st.experimental_memo, only rerun when the query changes or after 10 min.
@st.experimental_memo
def read_data(sql_query, _conn):
    return pd.read_sql_query(sql_query, _conn)


def format_func(x: object):
    m_type, m_value = x.split(": ")
    m_value_float = float(m_value)
    disp_val = f'{m_type}: {m_value_float / pow(10, 6):,.2f}'
    return disp_val


def derived_variables_calc(d):
    """

    :param dict d:
    :return: dict
    """

    d["Net Revenue"] = d["Nominal Income"] + d["Discounts"]  # discount is coming as negative values
    d["MACO"] = d["Net Revenue"] + d["Costs"]
    d["EBITDA"] = d["MACO"] + d["Expenses"]
    deductions = d["Depreciation Amortization"] + d["Cuentas Mayor"] + d["Inflationary Adjustments"] + d[
        "Other Expenses"]

    d["EBT"] = d["EBITDA"] + deductions
    d["PC"] = (d["EBT"] / d["Nominal Income"])
    return d


def results_df_creation(selected_data, adjusted_data):
    """
    https://stackoverflow.com/questions/30506219/is-there-a-counter-in-python-that-can-accumulate-negative-values
    :param selected_data:
    :param adjusted_data:
    :return: df
    """
    # create dummy dataframe with column and index names
    column_names = ["model values", "adjustments", "final values"]
    index_names = ["Beer Sales", "Discounts", "Net Revenue", "Costs", "MACO", "Expenses",
                   "EBITDA", "Depreciation Amortization", "Other Expenses",
                   "Cuentas Mayor", "Inflationary Adjustments", "EBT", "Nominal Income", "PC"]

    df = pd.DataFrame(index=index_names, columns=column_names)
    # calculate final values
    final = Counter()
    selected_counter = Counter(selected_data)
    adjusted_counter = Counter(adjusted_data)

    # sum; final= selected_data + adjusted_data
    final.update(selected_counter)
    final.update(adjusted_counter)

    # derive metrics
    selected_data = derived_variables_calc(selected_data)
    final = derived_variables_calc(final)

    # final df
    df.loc[:, "model values"] = pd.Series(selected_data)
    df.loc[:, "adjustments"] = pd.Series(adjusted_data)
    df.loc[:, "final values"] = pd.Series(final)

    return df


def format_download_data(df):
    # format df output
    tmp_df = df.copy()

    # drivers
    driver_df = tmp_df.iloc[tmp_df.index != 'PC']
    pc_df = tmp_df.iloc[tmp_df.index == 'PC']

    # apply formatting
    # driver
    driver_df = driver_df.applymap(lambda x: f'{(0 if np.isnan(x) else x) / pow(10, 6):,.2f}')
    # pc
    pc_df = pc_df.applymap(lambda x: f'{(0 if np.isnan(x) else x):.2%}')

    # concat
    op_df = pd.concat([driver_df, pc_df])
    return op_df


def to_excel(df, index=True):
    """

    :param df:
    :return: DataFrame
    """
    # output
    output = BytesIO()
    writer = pd.ExcelWriter(output, engine='xlsxwriter')
    df.to_excel(writer, index=index, sheet_name='Sheet1')
    writer.save()
    processed_data = output.getvalue()
    return processed_data


def insert_data_to_dB(df, table_name, schema_name, data_type, conn, mode='append'):
    df.to_sql(table_name, conn, schema=schema_name, dtype=data_type, if_exists=mode, index=False)
    print('data pushed successfully.')
