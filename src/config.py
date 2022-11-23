# sql query to pull data *
# https://stackoverflow.com/questions/5243596/python-sql-query-string-formatting
from datetime import datetime

SQL_QRY = ("select "
               "src.society, src.year, src.month, "
               "src.model_type,	src.le,	src.component, src.business_unity, "
               "isnull(src.forecast_number,0.00) as forecast_number "
           "from "
                "abi_stg.mx_tax_prof_coef_results src "
           "inner join "
                "( "
                   "select "
                       "society, component, model_type, le, max(CAST(dltdt AS DATETIME) + CAST(dlttm AS DATETIME)) as load_dttm  "
                       "from "
                       "abi_stg.mx_tax_prof_coef_results "
                       "group by "
                       "society, component, model_type, le "
               ") dest "
           "on "
               "src.society = dest.society "
               "and src.component = dest.component "
               "and src.model_type = dest.model_type "
               "and src.le = dest.le "
               "and (CAST(src.dltdt AS DATETIME) + CAST(src.dlttm AS DATETIME)) = dest.load_dttm "
            "where " 
                "src.component not in ('Beer_Sales') ")

NI_SPLIT_SQL_QRY = ("select "
                        "src.society, src.year, src.month, "
                        "src.model_type,	src.le, 'Beer_Sales' as component, "
                        "isnull(src.amount,0.00) as forecast_number "
                    "from "
                        "abi_edw.mx_tax_prof_coef_nominal_income_split src "
                    "inner join "
                        "( "
                            "select "
                                "society, subdriver, model_type, le, max(CAST(dltdt AS DATETIME) + CAST(dlttm AS DATETIME)) as load_dttm "
                            "from "
                                "abi_edw.mx_tax_prof_coef_nominal_income_split WITH(NOLOCK) "
                            "group by "
                                "society, subdriver, model_type, le "
                        ") dest "
                    "on "
                        "src.society = dest.society "
                        "and src.subdriver = dest.subdriver "
                        "and src.model_type = dest.model_type "
                        "and src.le = dest.le "
                        "and CAST(src.dltdt AS DATETIME) + CAST(src.dlttm AS DATETIME) = dest.load_dttm "
                    "where src.subdriver in ('PP_006001') ")

CLEAN_DATA_QRY = ("select "
                    "src.society, src.component, "
                    "src.le, src.year, src.month, "
                    "isnull(src.value,0.00) as value "
                "from " 
                    "abi_edw.mx_tax_prof_coef_results_final_clean src "
                "inner join "
                    "( "
                        "select " 
                            "society, component, le, " 
                            "max(CAST(dltdt AS DATETIME) + CAST(dlttm AS DATETIME)) as load_dttm "
                        "from "
                            "abi_edw.mx_tax_prof_coef_results_final_clean WITH(NOLOCK) "
                        "group by "
                            "society, component, le "
                    ") dest "
                "on "
                    "src.society = dest.society "
                    "and src.component = dest.component "
                    "and src.le = dest.le "
                    "and CAST(src.dltdt AS DATETIME) + CAST(src.dlttm AS DATETIME) = dest.load_dttm "
                "where "
	                "datefromparts(src.year, src.month, 01) > DATEADD(month, -3, GETDATE()) ")

# output setting
# columns
COUNTRY = 'MEXICO'
DLTDT = datetime.now(tz=None).strftime("%Y-%m-%d")
DLTTM = datetime.now(tz=None).strftime("%H:%M:%S")
# table name
OP_TBL_NAME = 'mx_tax_prof_coef_results_final'
OP_TBL_SCHEMA_NAME = 'abi_edw'