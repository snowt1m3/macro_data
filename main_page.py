import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import numpy as np
import time
from datetime import datetime, timedelta
import requests

pd.options.plotting.backend = "plotly"
#############
#Import utilities depending on server
############
dict_variables={"Real GDP growth":"NGDP_RPCH","GDP per capita, current price":"NGDPDPC",
                "Inflation rate":"PCPIPCH", "Unemployment rate":"LUR", "General government gross debt":"GGXWDG_NGDP"}

dict_3_to_2={"AUT":"AT","AUS":"AU","BEL":"BE","CAN":"CA","CHE":"CH","CHL":"CL","DEU":"DE","ESP":"ES",
                "FIN":"FI","FRA":"FR", "GBR":"GB", "ITA":"IT", "JPN":"JP", "KOR":"KR", "MEX":"MX", "NLD":"NL", "NOR":"NO",
                "NZL":"NZ","SWE":"SE","USA":"US","ZAF":"ZA"}

dict_countries={"United Kingdom":"GBR", "Germany":"DEU", "France":"FRA", "Austria":"AUT","Belgium":"BEL","Switzerland":"CHE", 
                "Germany":"DEU", "Spain":"ESP", "Finland":"FIN", "Italy":"ITA", "Japan":"JPN", "Korea":"KOR", 
                "Netherlands":"NLD", "Norway":"NOR", "Sweden":"SWE", "United States":"USA"}
#############################
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
#Caching
#####################
start=time.time()
#connect to GP prod
@st.cache_resource()
def count_views():
    return []
pageviews=count_views()
pageviews.append("view")
#####################
#Input form
####################
st.header("IMF dashboard")
col_top1, col_top2, col_top3 = st.columns(3)
col_top1.metric(label=":eyes: Views:",value=len(pageviews),delta=None)   
with col_top2:
    st.image("images/dell_logo.png",caption="Dell",width=64)
##############################
with st.expander(":grey_question: Info"):
    st.markdown(
'''
**Version: v0.5.0**
'''
)
#######################################    
min_date = datetime.strptime("01-01-2015","%d-%m-%Y")
max_date = datetime.today()

download_data=st.Page("download_data.py",title="Download data")
forecast_data=st.Page("forecast_data.py",title="Forecast data")

pg=st.navigation([download_data,forecast_data])
pg.run()
#############
#Time the whole code
###########
if "prev run" not in st.session_state:
    new_time=timming(start)
    st.session_state["prev run"]=new_time
    col_top3.metric(label="Ran in",value=new_time,delta=None)
else:
    new_time=timming(start)
    delta_time=new_time-st.session_state["prev run"]
    col_top3.metric(label="Ran in",value=timming(start),delta=delta_time,delta_color="inverse")
    st.session_state["prev run"]=new_time
    