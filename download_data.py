import streamlit as st
import xmltodict
import time
import pandas as pd
from datetime import datetime
from dateutil.relativedelta import relativedelta
import plotly.express as px 
import json
import requests

import warnings
warnings.simplefilter(action='ignore')

########################
#Streamlit styling
######################
st.set_page_config(
    page_title="IMF data",
    layout="wide",
    page_icon="images/dell_logo.png"
)

def local_css(file_name):
    with open(file_name) as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

local_css("style.css")
############################
st.logo("images/dell_logo.png",link="https://www.dell.com/en-us")
################
#Variables
#############
MAX_VARS=20
SLEEP_TIME=60*61
MAX_RETRIES=15
##################################
dict_variables={"Real GDP growth":"NGDP_RPCH","GDP per capita, current price":"NGDPDPC",
                "Inflation rate":"PCPIPCH","Unemployment rate":"LUR","Current account balance":"BCA",
                "General government net lending":"GGXCNL_NGDP","General government gross debt":"GGXWDG_NGDP"}

dict_countries={"Australia":"AUS","Austria":"AUT","Belgium":"BEL","Brazil":"BRA","Canada":"CAN","Switzerland":"CHE",
                 "Chile":"CHL", "China":"CHN", "Germany":"DEU", "Spain":"ESP", "Finland":"FIN", "France":"FRA", 
                 "United Kingdom":"GBR", "Italy":"ITA", "Japan":"JPN", "Korea":"KOR", "Mexico":"MEX", 
                 "Netherlands":"NLD", "Norway":"NOR", "New Zealand":"NZL", "Sweden":"SWE", "United States":"USA",
                 "South Africa":"ZAF", "Romania":"ROU", "Greece":"GRC"}

dict_3_to_2={"AUT":"AT","AUS":"AU","BEL":"BE","BRA":"BR","CAN":"CA","CHE":"CH","CHL":"CL","CHN":"CN","DEU":"DE","ESP":"ES",
                "FIN":"FI","FRA":"FR", "GBR":"GB", "ITA":"IT", "JPN":"JP", "KOR":"KR", "MEX":"MX", "NLD":"NL", "NOR":"NO",
                "NZL":"NZ","SWE":"SE","USA":"US","ZAF":"ZA","ROU":"RO"}

create_perc_vars=["GGXWDG_NGDP","NGDPDPC","BCA"]    

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
     
############
#Count views
#############
@st.cache_resource()
def page_views():
    return []
pageviews=page_views()

#####################
#Input form
####################
start=time.time()

with st.sidebar:
    start_date=st.date_input("Start date:",value=datetime(2022,1,1), 
                             min_value=datetime(1900,1,1),max_value=datetime(2030,1,1),format="MM/DD/YYYY")
    
    select_orig_variable=st.selectbox("Macro variable:",sorted(list(dict_variables.keys())),index=None)
    select_orig_countries=st.multiselect("Country:",sorted(list(dict_countries.keys())),sorted(list(dict_countries.keys()))[0])
    select_scale=st.selectbox("Choose scale:",sorted(["Monthly (interpolated)","Yearly (original)"]))

    btn=st.button("Submit")
if btn:
    count=0
    printing_iter=10**(1)
    start_date = "12-01-%d"%start_date.year
    list_dates=list(pd.date_range(start=start_date,end="12-01-2030",freq="ME"))
    list_dates=[datetime.strftime(l,"%m-%d-%Y") for l in list_dates]
    list_dates=["%s-01-%s"%(l.split("-")[0],l.split("-")[2]) for l in list_dates]

    data=pd.DataFrame()
    data["date"]=list_dates
    progress_text="Downloading data"
    my_bar = st.progress(0, text=progress_text)
    if select_orig_variable=="All":
        ##########################
        select_countries=[dict_countries[select_country] for select_country in select_orig_countries]
        str_countries="/".join(select_countries)
        list_variables=list(dict_variables.values())
        str_variables="/".join(list_variables)
        n_iters=len(select_countries)*len(list_variables)
        url="https://www.imf.org/external/datamapper/api/v1/%s/%s"%(str_variables,str_countries)
        st.markdown("API link: %s"%url)
        flag_download=1
        try:
            #response=session.get(url)
            response=requests.get(url)
            data_dict=json.loads(response.content)
        except:
            flag_download=0

        if flag_download==1:
            if "values" in data_dict.keys():
                data_dict=data_dict["values"]
                ####################################
                for select_variable in data_dict.keys():
                    dict_country=data_dict[select_variable]
                    for select_country in dict_country.keys():
                        data_country=pd.DataFrame()
                        data_country["date"]=list(dict_country[select_country].keys())
                        data_country["date"]=["12-01-%s"%year for year in data_country["date"]]
                        data_country["%s_%s"%(select_country,select_variable)]=list(dict_country[select_country].values())
                        data=data.merge(data_country,on="date",how="left")
    
                        count+=1
                        if count%printing_iter==0:
                            my_bar.progress(count/n_iters, text="Downloading data")  
                
                my_bar.progress(1, text="Finished downloading")  
    
                if select_scale=="Yearly (original)":
                    st.subheader(":information_source: Download dataset")
                    st.download_button("Download button",data.to_csv(index=False),"Macro data.csv","text/csv",key='download-csv')
            else:
                st.subheader(":warning: Could not access the link.")
        else:
            st.subheader(":warning: Could not access the link.")
    else:
        select_variable=dict_variables[select_orig_variable]
        select_countries=[dict_countries[select_country] for select_country in select_orig_countries]
        str_countries="/".join(select_countries)
        n_iters=len(select_countries)
        url="https://www.imf.org/external/datamapper/api/v1/%s/%s"%(select_variable,str_countries)
        st.markdown("API link: %s"%url)
        flag_download=1
        try:
            response=requests.get(url)
            #response=session.get(url)
            data_dict=json.loads(response.content)
        except:
            flag_download=0
        if flag_download==1:
            if "values" in data_dict.keys():
                data_dict=data_dict["values"]
                ####################################
                dict_country=data_dict[select_variable]
                for select_country in select_countries:
                    data_country=pd.DataFrame()
                    data_country["date"]=list(dict_country[select_country].keys())
                    data_country["date"]=["12-01-%s"%year for year in data_country["date"]]
                    data_country["%s_%s"%(select_country,select_variable)]=list(dict_country[select_country].values())
                    data=data.merge(data_country,on="date",how="left")
    
                    count+=1
                    if count%printing_iter==0:
                        my_bar.progress(count/n_iters, text="Downloading data")  
                
                my_bar.progress(count/n_iters, text="Finished downloading")  
                if select_scale=="Yearly (original)":
                    macro_cols=[col for col in data.columns if col!="date"]
                    fig=px.line(data,x="date",y=macro_cols) 
                    st.subheader(":information_source: %s for %s"%(select_orig_variable,",".join(select_orig_countries)),divider="blue")
                    st.plotly_chart(fig)
                    st.subheader(":information_source: Download dataset")
                    st.download_button("Download button",data.to_csv(index=False),"Macro data.csv","text/csv",key='download-csv')
            else:
                st.subheader(":warning: Could not access the link.")
        else:
            st.subheader(":warning: Could not access the link.")

    if flag_download==1 and select_scale=="Monthly (interpolated)":
        macro_cols=[col for col in data.columns if col!="date" and select_variable in col]      
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
        data["date"]=data["date"].apply(lambda dt: create_date(dt))
        macro_cols=[col for col in data.columns if col!="date"]
        fig=px.line(data,x="date",y=macro_cols) 
        st.subheader(":information_source: %s for %s"%(select_orig_variable,",".join(select_orig_countries)),divider="blue")
        st.plotly_chart(fig)

        st.subheader(":information_source: Download dataset")
        st.download_button("Download button",data.to_csv(index=False),"Macro data.csv","text/csv",key='download-csv') 
        
    pageviews.append("ran")
else:
    st.subheader("Please choose inputs from the left side.")  
    