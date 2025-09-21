import streamlit as st
import requests
import pandas as pd
import numpy as np
import time
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
import json
import plotly.express as px

pd.options.plotting.backend = "plotly"

#############
#Import utilities depending on server
############
dict_forecast_variables={"Real GDP growth":"NGDP_RPCH", "Inflation rate, average consumer prices":"PCPIPCH",
                'Current account balance, percent of GDP':"BCA_NGDPD", 'Unemployment rate':"LUR",
                'General government gross debt':"GGXWDG_NGDP"}

dict_3_to_2={"AUT":"AT","AUS":"AU","BEL":"BE","CAN":"CA","CHE":"CH","CHL":"CL","DEU":"DE","ESP":"ES",
                "FIN":"FI","FRA":"FR", "GBR":"GB", "ITA":"IT", "JPN":"JP", "KOR":"KR", "MEX":"MX", "NLD":"NL", "NOR":"NO",
                "NZL":"NZ","SWE":"SE","USA":"US","ZAF":"ZA","ROU":"RO"}

dict_forecast_countries={"United Kingdom":"GBR", "Germany":"DEU", "Austria":"AUT", "Germany":"DEU", "Spain":"ESP", 
                         "Japan":"JPN", "Korea":"KOR", "Netherlands":"NLD", "Norway":"NOR", "Sweden":"SWE", 
                         "United States":"USA","Romania":"ROU"}
###########################################
all_macro_vars=list(dict_forecast_variables.values())
all_countries=list(dict_forecast_countries.values())
##################
#FUNCTIONS
##############
def create_date(dt):
    dt=datetime.strptime(dt,"%m-%d-%Y")
    str_dt=datetime.strftime(dt,"%Y-%m-%d")
    return str_dt

def expo_compounding(data,col):
    idx_na=None
    for i in range(data.shape[0]):
        if pd.isna(data[col].iloc[i]):
            idx_na=i
            break
    start=data[col].iloc[idx_na-2]
    end=data[col].iloc[idx_na-1]
    r=(end-start)/start
    n_nas=sum([1 for val in data[col] if pd.isna(val)])
    count=1
    for i in range(data.shape[0]):
        if pd.isna(data[col].iloc[i]):
            data[col].iloc[i]=((1+r)**(count))*end
            count+=1
    return data

def timming(since):
    time_elapsed=time.time()-since
    return round(time_elapsed,4)
########################
#Streamlit styling
######################
@st.cache_resource()
def count_views():
    return []
pageviews=count_views()
pageviews.append("view")
#####################################
dict_forecast_variables={"Real GDP growth":"NGDP_RPCH", "Inflation rate, average consumer prices":"PCPIPCH",
                'Current account balance, percent of GDP':"BCA_NGDPD", 'Unemployment rate':"LUR",
                'General government gross debt':"GGXWDG_NGDP"}

dict_3_to_2={"AUT":"AT","AUS":"AU","BEL":"BE","CAN":"CA","CHE":"CH","CHL":"CL","DEU":"DE","ESP":"ES",
                "FIN":"FI","FRA":"FR", "GBR":"GB", "ITA":"IT", "JPN":"JP", "KOR":"KR", "MEX":"MX", "NLD":"NL", "NOR":"NO",
                "NZL":"NZ","SWE":"SE","USA":"US","ZAF":"ZA","ROU":"RO"}

dict_forecast_countries={"United Kingdom":"GBR", "Germany":"DEU", "Austria":"AUT", "Germany":"DEU", "Spain":"ESP", 
                         "Japan":"JPN", "Korea":"KOR", "Netherlands":"NLD", "Norway":"NOR", "Sweden":"SWE", 
                         "United States":"USA","Romania":"ROU"}

drop_cols=["GGXWDG_NGDP_ROU"]
#################################
st.set_page_config(
    page_title="IMF dashboard",
    page_icon="images/dell_logo.png",
    layout="wide"
)

def local_css(file_name):
    with open(file_name) as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

local_css("style.css")
############################
st.logo("images/dell_logo.png",link="https://www.dell.com/en-us")
#####################
#Input form
####################
start=time.time()
with st.sidebar:
    start_date=st.date_input("Start date:",value=datetime(2022,1,1), 
                             min_value=datetime(1900,1,1),max_value=datetime(2030,1,1),format="MM/DD/YYYY")
    
    select_forecast_variable=st.selectbox("Macro variable:",sorted(list(dict_forecast_variables.keys())),index=None)
    select_forecast_country=st.selectbox("Country:",sorted(list(dict_forecast_countries.keys())),index=None)

    #shock_val=float(st.number_input("Shock value (%):",min_value=1,max_value=10,value=1.25,format="%.2f"))
    #shock_val=shock_val/100

    btn=st.button("Submit")
if btn:
    count=0
    shock_val=0.0125
    printing_iter=10**(1)
    if select_forecast_variable is not None and select_forecast_country is not None:
        select_forecast_variable=dict_forecast_variables[select_forecast_variable]
        select_forecast_country=dict_forecast_countries[select_forecast_country]
        select_macro="%s_%s"%(select_forecast_variable,select_forecast_country)
    
        #start_date="%d-%d-%d"%(start_date.month,start_date.day,start_date.year)
        #st.markdown(start_date.year)
        
        list_dates=list(pd.date_range(start="%d-%d-%d"%(start_date.month,start_date.day,start_date.year),end="12-01-2030",freq="ME"))
        list_dates=[datetime.strftime(l,"%m-%d-%Y") for l in list_dates]
        list_dates=["%s-01-%s"%(l.split("-")[0],l.split("-")[2]) for l in list_dates]
        end_time=datetime.today().timestamp()
        
        n_iters=1
        url="https://www.imf.org/external/datamapper/api/v1/%s/%s"%(select_forecast_variable,select_forecast_country)
        print("API link: %s"%url)
        flag_download=1
        try:
            #response=session.get(url)
            response=requests.get(url)
            data_dict=json.loads(response.content)
        except:
            flag_download=0
    
        data=pd.DataFrame()
        data["date"]=list_dates
        if flag_download==1:
            if "values" in data_dict.keys():
                data_dict=data_dict["values"]
                ######################################
                for select_variable in data_dict.keys():
                    dict_country=data_dict[select_variable]
                    for select_country in dict_country.keys():
                        data_country=pd.DataFrame()
                        data_country["date"]=list(dict_country[select_country].keys())
                        data_country["date"]=["12-01-%s"%year for year in data_country["date"]]
                        data_country["%s_%s"%(select_variable,select_country)]=list(dict_country[select_country].values())
                        data=data.merge(data_country,on="date",how="left")
                #######################################
                macro_cols=[col for col in data.columns if col!="date"]      
                data.interpolate(method="linear",inplace=True,limit_direction="backward")
                nrows=data.shape[0]
                for col in data.columns:
                    if sum([1 for val in data[col] if pd.isna(val)>=1]):
                        data=expo_compounding(data,col)
                data=data.iloc[1:] 
                data.reset_index(inplace=True,drop=True)
                all_countries=[]
                for col in data.columns:
                    if col!="date":
                        all_countries.append(col.split("_")[-1])      
                all_countries=list(set(all_countries))   
                data_orig=data.copy(deep=False)
                data["date"]=data["date"].apply(lambda dt: create_date(dt))
                #######################
                st.markdown("Link: %s"%url)
                #######################################
                data["time"]=data["date"].apply(lambda dt: datetime.strptime(dt,"%Y-%m-%d").timestamp())
                data_orig=data.copy(deep=False)
                df_imf_forecast=data_orig.loc[data["time"]>=end_time]
                df_imf_forecast.reset_index(inplace=True,drop=True)
        
                data=data.loc[data["time"]<=end_time]
                data.reset_index(inplace=True,drop=True)
                data_orig=data_orig.loc[data_orig["time"]<=end_time]
                data_orig.reset_index(inplace=True,drop=True)
                
                data.index = pd.DatetimeIndex(data["date"])
                data.drop(columns=["date","time"],inplace=True)
                ###############################################
                shock_val=0.0125 #quarterly shock value
        
                df_imf_pos=pd.DataFrame()
                df_imf_neg=pd.DataFrame()
                df_imf_pos["date"]=list(df_imf_forecast["date"])
                df_imf_neg["date"]=list(df_imf_forecast["date"])
                for col in df_imf_forecast.columns:
                    if col not in ["date","time"]:
                        if "PCPIPCH" in col or "LUR" in col or "GGXWDG_NGDP" in col:
                            df_imf_neg[col]=[((1+shock_val)**(i/3))*df_imf_forecast[col].iloc[i] if df_imf_forecast[col].iloc[i]>0 else ((1-shock_val)**(i/3))*df_imf_forecast[col].iloc[i] for i in range(df_imf_forecast.shape[0])]
                            df_imf_pos[col]=[((1-shock_val)**(i/3))*df_imf_forecast[col].iloc[i] if df_imf_forecast[col].iloc[i]>0 else ((1+shock_val)**(i/3))*df_imf_forecast[col].iloc[i] for i in range(df_imf_forecast.shape[0])]
                        else:
                            df_imf_pos[col]=[((1+shock_val)**(i/3))*df_imf_forecast[col].iloc[i] if df_imf_forecast[col].iloc[i]>0 else ((1-shock_val)**(i/3))*df_imf_forecast[col].iloc[i] for i in range(df_imf_forecast.shape[0])]
                            df_imf_neg[col]=[((1-shock_val)**(i/3))*df_imf_forecast[col].iloc[i] if df_imf_forecast[col].iloc[i]>0 else ((1+shock_val)**(i/3))*df_imf_forecast[col].iloc[i] for i in range(df_imf_forecast.shape[0])]
         
        
                plot_data=pd.DataFrame()
                plot_data["date"]=list(data_orig["date"])+list(df_imf_forecast["date"])
                plot_data[select_macro]=list(data_orig[select_macro])+[None]*df_imf_forecast.shape[0]
                plot_data["IMF forecast %s"%select_macro]=[None]*data_orig.shape[0]+list(df_imf_forecast[select_macro])
                plot_data["optimistic %s"%select_macro]=[None]*data_orig.shape[0]+list(df_imf_pos[select_macro])
                plot_data["pessimistic %s"%select_macro]=[None]*data_orig.shape[0]+list(df_imf_neg[select_macro])
                
                
                fig=px.line(plot_data,x="date",y=[select_macro,"IMF forecast %s"%select_macro,"optimistic %s"%select_macro,"pessimistic %s"%select_macro])
                st.plotly_chart(fig)
            else:
                st.subheader(":warning: could not aceess the link.")
        else:
            st.subheader(":warning: Could not aceess the link.")
    else:
        st.subheader(":warning: Please choose inputs from the left side.")  
        
        ###################################################
else:
    st.subheader(":warning: Please choose inputs from the left side.")  
