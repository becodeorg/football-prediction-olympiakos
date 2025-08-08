import streamlit as st

import pandas as pd 
from api import fetch_data_from_api
from utils.functions import render_matches
from utils.lists_variables import teamname_mapping

############################################
############### IMPORT DATAS ###############
############################################
# Dataframe for past seasons
datas = fetch_data_from_api()
df = pd.DataFrame(datas)
df.replace(teamname_mapping, inplace=True)

df['Date'] = pd.to_datetime(df['Date'], format='mixed', dayfirst=True)

# Dataframe for matches to predict
matches_to_predict = pd.read_csv('new_predictions.csv')
matches_to_predict.replace(teamname_mapping, inplace=True)
matches_to_predict['Date'] = pd.to_datetime(matches_to_predict['Date'], format='%d/%m/%Y', dayfirst=True, errors='coerce')
matches = matches_to_predict.to_dict('records')

############################################
############# CONFIG STREAMLIT #############
############################################

st.set_page_config(
    page_title="Predictions Jupiler Pro League 2025 - 2026",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Css
def load_css(path):
    with open(path) as f:
        css = f.read()
    st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)

load_css("style.css")

# Title
st.markdown(
    "<h1 style='text-align: center;'>Jupiler Pro League 2025 - 2026</h1>",
    unsafe_allow_html=True
)

# Tabs
tab_labels = [f"{m['HomeTeam']} - {m['AwayTeam']}" for m in matches]
tabs = st.tabs(tab_labels)

###############################################
############# INTERFACE STREAMLIT #############
###############################################
for idx, (tab, match) in enumerate(zip(tabs, matches)):
    with tab:
        render_matches(match, df, uid=idx)

