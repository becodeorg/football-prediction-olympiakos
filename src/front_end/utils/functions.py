import csv
import json
import pandas as pd
import numpy as np
import altair as alt 
import streamlit as st

import streamlit_shadcn_ui as ui
from utils.lists_variables import folder_matches_cols, stats_cols

#############################
### JSON | CSV CONVERSION ###
#############################

# CSV to JSON
def csv_to_json(datapath, outputpath):
    with open(f'{datapath}', mode='r', newline='', encoding='utf-8') as csvfile:
        data = list(csv.DictReader(csvfile))

    with open(f'{outputpath}', mode='w', encoding='utf-8') as jsonfile:
        json.dump(data, jsonfile, indent=4)

# JSON to CSV
def json_to_csv(jsonpath, outputpath):
    json_data = pd.read_json(jsonpath)
    headers = json_data[0].keys()

    with open(f'{outputpath}', 'w', newline='\n') as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=headers)
        writer.writeheader()
        writer.writerows(json_data)

#############################
### TABLES FOR DASHBOARD ####
#############################

# 18 former matches 
def former_18_matches(teamname, match_date, df):
    """datas = fetch_data_from_api()
    df = pd.DataFrame(datas)"""
    df['Date'] = pd.to_datetime(df['Date'], format='mixed', dayfirst=True)
    mask_team = (df['Home_team'] == teamname) | (df['Away_team'] == teamname)
    #df['Date'] = pd.to_datetime(df['Date'], format='%Y-%m-%d %H:%M:%S', dayfirst=True)
    
    match_date = pd.to_datetime(match_date, dayfirst= True)
    mask_date = df['Date'] < match_date
    mask_total = mask_team & mask_date

    df = df.loc[mask_total, stats_cols]
    df_18_sorted = df.sort_values('Date', ascending=False)
    df_18_sorted = df_18_sorted.head(18)
    df_18_sorted['Date'] = df_18_sorted['Date'].dt.strftime('%d-%m-%Y')
    df_18_sorted['Teamname'] = teamname

    df_18_sorted['goals'] = np.where(
    df_18_sorted['Home_team'] == teamname,
    df_18_sorted['Home_goals_(FT)'],
    df_18_sorted['Away_goals_(FT)']
    )

    # Pourcentage target shots / targets 
        # 1) string to numeric, with "" replaced by 0 when there is no shots 
    df_18_sorted['Home_shots'] = df_18_sorted['Home_shots'].replace('', np.nan)
    home_shots = pd.to_numeric(df_18_sorted['Home_shots'], errors='coerce').fillna(0)
    
    df_18_sorted['Home_shots_on_target'] = df_18_sorted['Home_shots_on_target'].replace('', np.nan)
    home_target = pd.to_numeric(df_18_sorted['Home_shots_on_target'], errors='coerce').fillna(0)

    df_18_sorted['Away_shots'] = df_18_sorted['Away_shots'].replace('', np.nan)
    away_shots = pd.to_numeric(df_18_sorted['Away_shots'], errors='coerce').fillna(0)

    df_18_sorted['Away_shots_on_target'] = df_18_sorted['Away_shots_on_target'].replace('', np.nan)
    away_target = pd.to_numeric(df_18_sorted['Away_shots_on_target'], errors='coerce').fillna(0)

        # 2) avoid division per zero error
    home_percentage = np.where(home_shots > 0, (home_target / home_shots) * 100, 0)
    away_percentage = np.where(away_shots > 0, (away_target / away_shots) * 100, 0)

        # 3) get the pourcentage
    df_18_sorted['on_target_pourcentage'] = np.where(
        df_18_sorted['Home_team'] == teamname,
        home_percentage.astype(float),
        away_percentage.astype(float)
    )

    df_18_sorted['fouls'] = np.where(
        df_18_sorted['Home_team'] == teamname,
        df_18_sorted['Home_fouls'],
        df_18_sorted['Away_fouls']
    )

    df_18_sorted['corners'] = np.where(
        df_18_sorted['Home_team'] == teamname,
        df_18_sorted['Home_corners'],
        df_18_sorted['Away_corners']
    )

    df_18_sorted['yellow_cards'] = np.where(
        df_18_sorted['Home_team'] == teamname,
        df_18_sorted['Home_yellow_cards'],
        df_18_sorted['Away_yellow_cards']
    )

    df_18_sorted['red_cards'] = np.where(
        df_18_sorted['Home_team'] == teamname,
        df_18_sorted['Home_red_cards'],
        df_18_sorted['Away_red_cards']
    )

    return df_18_sorted

# stats from former 18 matches
def stats(dataframe_18_matches, teamname):
    mask_home = dataframe_18_matches['Home_team'] == teamname
    mask_away = dataframe_18_matches['Away_team'] == teamname

    # Win
    wins_home = ((mask_home) & (dataframe_18_matches['Full_time_result_(H/D/A)'] == 'H')).sum()
    wins_away = ((mask_away) & (dataframe_18_matches['Full_time_result_(H/D/A)'] == 'A')).sum()
    wins = wins_home + wins_away

    # Loss
    losses_home = ((mask_home) & (dataframe_18_matches['Full_time_result_(H/D/A)'] == 'A')).sum()
    losses_away = ((mask_away) & (dataframe_18_matches['Full_time_result_(H/D/A)'] == 'H')).sum()
    losses = losses_home + losses_away

    # Draws
    draws = ((dataframe_18_matches['Full_time_result_(H/D/A)'] == 'D')).sum()

    # Calculation
    total = len(dataframe_18_matches) 

    if total > 0:
        win_rate   = round(wins / total * 100, 2)
        loss_rate  = round(losses / total * 100, 2)
        draw_rate  = round(draws / total * 100, 2)
        total_goals = dataframe_18_matches['goals'].sum()  
        avg_goals  = round(total_goals / total, 2)
        
    else:
        win_rate   = 0.0
        loss_rate  = 0.0
        draw_rate  = 0.0
        avg_goals  = 0.0
        total_goals = 0.0
        print(f"Aucun match trouvé pour cette équipe dans la période demandée")

    print(f""" For the last {total} matchs of {teamname} :
    • Win rate  : {win_rate}%
    • Loss rate    : {loss_rate}%
    • Draft rate  : {draw_rate}%
    • Total goals : {total_goals} goals
    • {avg_goals} goal / match    """)

    return win_rate, loss_rate, draw_rate, total_goals, avg_goals


# Side tables with 5 folder matches
def create_side_table(teamname, match_date, dataframe):
    df = dataframe.copy().reset_index(drop=True)
    mask_team = (df['Home_team'] == teamname) | (df['Away_team'] == teamname)
    df['Date'] = pd.to_datetime(df['Date'], format='%d-%m-%Y', dayfirst=True)
    
    mask_date = df['Date'] < match_date
    mask_total = mask_team & mask_date
    df = df.loc[mask_total, folder_matches_cols]

    df_sorted = df.sort_values('Date', ascending=False)
    df_5_sorted = df_sorted.head(5)

    side_df = pd.DataFrame(columns=['Date', 'Home team', 'Score', 'Away team'])
    homegoals = df_5_sorted['Home_goals_(FT)'].astype(str)
    awaygoals = df_5_sorted['Away_goals_(FT)'].astype(str)
    
    side_df['Score'] = homegoals + " - " + awaygoals  
    side_df['Date'] = df_5_sorted['Date'].dt.strftime('%d-%m')
    side_df['Home team'] = df_5_sorted['Home_team']
    side_df['Away team'] = df_5_sorted['Away_team']

    return side_df

# Detailled stats from 5 former matchs 
def create_side_stats(teamname, match_date, dataframe):
    df = dataframe.copy()
    mask_team = (df['Home_team'] == teamname) | (df['Away_team'] == teamname)
    df['Date'] = pd.to_datetime(df['Date'], format='%d-%m-%Y', dayfirst=True)
    
    mask_date = df['Date'] < match_date
    mask_total = mask_team & mask_date
    df = df.loc[mask_total, :].copy()
    
    df_sorted = df.sort_values('Date', ascending=False)
    df_5_sorted = df_sorted.head(5).copy()

    homegoals = df_5_sorted['Home_goals_(FT)'].astype(str)
    awaygoals = df_5_sorted['Away_goals_(FT)'].astype(str)
    
    df_5_sorted['Score'] = homegoals + " - " + awaygoals  
    df_5_sorted['Date'] = df_5_sorted['Date'].dt.strftime('%d-%m-%Y')

    return df_5_sorted.reset_index(drop=False)

# Team ranking

def build_classement(df):
    df_25 = df[df['Date'] >= pd.to_datetime('2025-07-25')] # first day of jupiler pro league 25_26
    teams = pd.unique(df_25[['Home_team' , 'Away_team']].values.ravel()).tolist()
    lignes = []

    for team in teams:
        mask_team = (df_25['Home_team'] == team) | (df_25['Away_team'] == team)
        df_team = df_25[mask_team]
        df_home = df_25[df_25['Home_team'] == team]
        df_away = df_25[df_25['Away_team'] == team]

        win_home = ((df_25['Home_team'] == team) & (df_25['Full_time_result_(H/D/A)'] == "H")).sum()
        win_away = ((df_25['Away_team'] == team) & (df_25['Full_time_result_(H/D/A)'] == "A")).sum()
        draft = (df_team['Full_time_result_(H/D/A)'] == "D").sum()
        wins = win_home + win_away

        shots_home = df_home['Home_shots'].sum()
        shots_away = df_away['Away_shots'].sum()
        shots = shots_home + shots_away
        points = (wins * 3) + (draft * 1)
        tours = df_team['Date'].nunique()

        lignes.append({
             'Team' : team, 
             "Tours" : tours,
             "Points" : points,
             "Total shots" : shots}
        )

        classement = pd.DataFrame(lignes)
        classement = classement.sort_values(by=['Points','Tours', 'Total shots'], ascending=[False, True, False]).reset_index(drop=True)
        classement = classement[['Team', "Tours", "Points"]]
    return classement

#############################
##### GRAPHIC ELEMENTS ######
#############################

# Win / Loose / Draft rate 
def make_donut(input_response, input_text, input_color):
    # 1. Couleurs (parfait)
    if input_color == 'green':
        chart_color = ['#27AE60', "#0E572C"]
    elif input_color == 'grey':
        chart_color = ["#DDDDDD", "#999999"]
    elif input_color == 'red':
        chart_color = ['#E74C3C', '#781F16']
    else:
        chart_color = ['#29b5e8', '#155F7A']

    # 2. DataFrame
    source = pd.DataFrame({
        "Topic": [input_text, ''],
        "value": [input_response, 100 - input_response]
    })

    # 3. Le donut - RAYONS CORRECTS !
    donut = alt.Chart(source).mark_arc(
        innerRadius=10,    # hole radius
        outerRadius=20,    # exterior radius
        #cornerRadius=3
    ).encode(
        theta=alt.Theta(field="value", type="quantitative"),
        color=alt.Color("Topic:N",
                        scale=alt.Scale(
                            domain=[input_text, ''],
                            range=chart_color),
                        legend=None)
    ).properties(
        width=60, height=60
    )

    text = alt.Chart(pd.DataFrame({'label': [f"{input_response:.0f}%"]})).mark_text(
        align='center',
        baseline='middle',
        fontSize=8,
        fontWeight='bold',
        color=chart_color[0]
    ).encode(
        text='label:N',
        x=alt.value(20),   # width/2
        y=alt.value(20)    # height/2
    )
    chart = (donut + text).resolve_scale(color='independent')
    
    # delete white spacing (before / after)
    chart = chart.configure_view(
        stroke=None,
        strokeWidth=0
    ).configure(
        padding=0,
        background='transparent'
    ).properties(
        width=60, 
        height=60,
        padding=0
    )
    
    return chart

# For the darker color on the sides

#############################
#### INTERFACE STREAMLIT ####
#############################

def render_matches(matches_to_predict, df, uid):
    ###################
    ## DECLARATIONS ###
    ###################
    home, away = matches_to_predict['HomeTeam'], matches_to_predict['AwayTeam']
    match_date = matches_to_predict['Date']

    if pd.isna(match_date):
        date_pred = "Date not available"
    else:
        date_pred = match_date.strftime('%d-%m-%Y')
    
    # Rates for 18 former matchs
    home_18_matches = former_18_matches(home, match_date, df)
    away_18_matches = former_18_matches(away, match_date, df)

    rates_home = stats(home_18_matches, home)
    rates_away = stats(away_18_matches, away)

    win_home_rate = make_donut(rates_home[0], 'Win rate', 'green')
    loose_home_rate = make_donut(rates_home[1], 'Loose rate', 'red')
    drawes_home_rate = make_donut(rates_home[2], 'Draw rate', 'grey')
    win_away_rate = make_donut(rates_away[0], 'Win rate', 'green')
    loose_away_rate = make_donut(rates_away[1], 'Loose rate', 'red')
    drawes_away_rate = make_donut(rates_away[2], 'Draw rate', 'grey')

    # Side tables for 5 latest matchs
    side_home = create_side_table(home, match_date, df)
    side_away = create_side_table(away, match_date, df)

    # Detailed statistics for 5 latest matches
    home_5_matches = home_18_matches[:5]
    away_5_matches = away_18_matches[:5]

    home_stats = create_side_stats(home, match_date, home_5_matches)
    away_stats = create_side_stats(away, match_date, away_5_matches)

    # Ranking
    classement = build_classement(df)

    ###################
    ##### COLUMNS #####
    ###################
    home_team, pronostics, away_team = st.columns(3)

    with home_team:
        st.markdown(f"<h1 style='text-align: center;'>{home}</h1>", unsafe_allow_html=True)
        st.markdown(f"<h4 style='font-size: 14px; text-align: center; border-top:1px solid #ccc; margin-bottom:4px'> 18 former matchs :</h4>", unsafe_allow_html=True)
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.altair_chart(win_home_rate, use_container_width=True)
        with col2:
            st.altair_chart(loose_home_rate, use_container_width=True)
        with col3:
            st.altair_chart(drawes_home_rate, use_container_width=True)
        
        st.markdown(f"<h4 style='font-size: 14px; text-align: center; padding-bottom:4px; border-bottom:1px solid #ccc; margin-bottom:4px'></h4>", unsafe_allow_html=True)
        st.markdown(f"<h6 style='font-size: 10px; margin-top: -30px;text-align: center'>  Shots on target: {home_18_matches['on_target_pourcentage'].mean():.1f}%&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;Total goals: {home_18_matches['goals'].sum()}&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;Goals/matchs: {home_18_matches['goals'].mean():.1f}</h6>", unsafe_allow_html=True)

        # SIDE TABLE FOR HOME TEAM
        st.markdown(f"<h4 style='font-size: 14px; text-align: center; margin-bottom:4px'> 5 latest matchs :</h4>", unsafe_allow_html=True)
        ui.table(data=side_home, maxHeight=300, key=f"table_home_{uid}")
        expander = st.expander(label=f"Detailled stats for {matches_to_predict['HomeTeam']}", icon=None)
        detailled_stats = {}
        for i in range(len(home_stats)):
            detailled_stats[f"{home_stats.iloc[i]['Home_team']} - {home_stats.iloc[i]['Away_team']}"] = (f"Yellow cards : {home_stats.iloc[i]['yellow_cards']} | Red cards: {home_stats.iloc[i]['red_cards']} | Fouls: {home_stats.iloc[i]['fouls']} | Corners: {home_stats.iloc[i]['corners']}")

        for key, value in detailled_stats.items():
            expander.markdown(f"""
                <p style="font-size:14px; font-weight:bold; margin:8px 0 4px 0;
                padding-bottom:4px;  border-bottom:1px solid #ccc; ">
                {key}
                </p>

                <p style=" font-size:12px; color:#555; margin:0 0 12px 0; line-height:1.4;">
                {value}
                </p>""", unsafe_allow_html=True)
            
    with pronostics:
        # MATCH GENERAL INFORMATION
        st.markdown(f"<h4 style='text-align: center;margin-top:23px'>{date_pred}</h2>", unsafe_allow_html=True)

        # MATCH PRONOSTICS
        st.markdown(f"<p style='text-align: center;font-weight:150'><strong>{matches_to_predict['win_team']}</strong> should win.</p>", unsafe_allow_html=True)
        
        winrate, looserate, drawrate = st.columns(3)
        with winrate:
            ui.metric_card(title="Win chances", content=f"{(matches_to_predict['win_rate'] * 100):.1f}", description="%", key=f"card1_{uid}")
        with looserate:
            ui.metric_card(title="Loose chances", content=f"{(matches_to_predict['loose_rate'] * 100):.1f}", description="%", key=f"card2_{uid}")
        with drawrate:
            ui.metric_card(title="Draw chances", content=f"{(matches_to_predict['draw_rate'] * 100):.1f}", description="%", key=f"card3_{uid}")

        # RANKING 
        st.markdown(f"<h2 style='text-align:center;font-weight:200'> Ranking </h2>", unsafe_allow_html=True)
        col1, col2, col3 = st.columns([1, 6, 1])  # adjust ratios as needed

        with col2:
            st.dataframe(classement, hide_index=True, width=300, height=595)        

    with away_team:
        st.markdown(f"<h1 style='text-align: center;'>{away}</h1>", unsafe_allow_html=True)
        st.markdown(f"<h4 style='font-size: 14px; text-align: center; border-top:1px solid #ccc; margin-bottom:4px'> 18 former matchs :</h4>", unsafe_allow_html=True)
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.altair_chart(win_away_rate, use_container_width=True)
        with col2:
            st.altair_chart(loose_away_rate, use_container_width=True)
        with col3:
            st.altair_chart(drawes_away_rate, use_container_width=True)

        st.markdown(f"<h4 style='font-size: 14px; text-align: center; padding-bottom:4px; border-bottom:1px solid #ccc; margin-bottom:4px'></h4>", unsafe_allow_html=True)
        st.markdown(f"<h6 style='font-size: 10px; margin-top: -30px;text-align: center'>  Shots on target: {away_18_matches['on_target_pourcentage'].mean():.1f}%&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;Total goals: {away_18_matches['goals'].sum()}&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;Goals/matchs: {away_18_matches['goals'].mean():.1f}</h6>", unsafe_allow_html=True)

        # SIDE TABLE FOR AWAY TEAM
        st.markdown(f"<h4 style='font-size: 14px; text-align: center; margin-bottom:4px'> 5 latest matchs :</h4>", unsafe_allow_html=True)
        ui.table(side_away, maxHeight=300, key=f"table_away_{uid}")

        expander = st.expander(label=f"Detailled stats for {matches_to_predict['AwayTeam']}", icon=None)
        detailled_stats = {}
        for i in range(len(away_stats)):
            detailled_stats[f"{away_stats.iloc[i]['Home_team']} - {away_stats.iloc[i]['Away_team']}"] = (f"Yellow cards : {away_stats.iloc[i]['yellow_cards']} | Red cards: {away_stats.iloc[i]['red_cards']} | Fouls: {away_stats.iloc[i]['fouls']} | Corners: {away_stats.iloc[i]['corners']}")

        for key, value in detailled_stats.items():
            expander.markdown(f"""
                <p style="font-size:14px; font-weight:bold; margin:8px 0 4px 0;
                padding-bottom:4px;  border-bottom:1px solid #ccc; ">
                {key}
                </p>

                <p style=" font-size:12px; color:#555; margin:0 0 12px 0; line-height:1.4;">
                {value}
                </p>""", unsafe_allow_html=True)

