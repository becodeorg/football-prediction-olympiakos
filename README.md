[![Review Assignment Due Date](https://classroom.github.com/assets/deadline-readme-button-22041afd0340ce965d47ae6ef1cefeee28c7c493a6346c4f15d667ab976d596c.svg)](https://classroom.github.com/a/2jqnWWV_)
# Football Match Prediction Project (Belgian Jupiler Pro League)

- Repository: `football-prediction`
- Type of Challenge: `Consolidation`
- Duration: `7 days`
- Deadline: `dd/mm/yyyy 3PM`
- Team challenge: Team (4)

## Learning Objectives

Build an end-to-end system that predicts football match outcomes using scraping, scheduling, machine learning, and data visualization.

At the end of this challenge, you should:

- Be able to scrape and process data from football websites.
- Be able to train a machine learning model on historical match data.
- Be able to create a Streamlit app for live data visualization and predictions.
- Be able to manage the entire data pipeline, scheduling for automation.

## The Mission

Your mission is to build a prediction system for the Belgian Jupiler Pro League football matches. You'll combine historical match data with scraped real-time data (odds, recent matches) to predict the outcome of upcoming games.

### Dataset

An old CSV containing match results from 5 years will be provided it comes from [this website](https://www.football-data.co.uk/), with the following key columns:

- Date = Match Date (dd/mm/yy)
- Time = Match Kick-off Time
- HomeTeam = Home Team
- AwayTeam = Away Team
- FTHG = Full Time Home Team Goals
- FTAG = Full Time Away Team Goals
- FTR = Full Time Result (H=Home Win, D=Draw, A=Away Win)

Additional statistics are included (shots, fouls, cards, etc.), which you can use to train your model. There also are historical odds given for each matches, the definitions of all columns is given [here](https://www.football-data.co.uk/notes.txt).

**NOTE**: There is no point in using the stats of match X to predict the outcome of match X. If you try to predict the outcome of a football game before it happens, you have to look at how each team has been performing recently. You could, for example, use an average of the outcomes and stats of previous matches S,T,U,V,W to predict the outcome of X. Hence, this dataset is not a FEATURES | TARGET dataset. These have to be carved out.

This dataset is what the Data Engineers have to re-generate for the Data Analysts and Scientists. Consider it the bridge in the team.

### Must-have features

- **Model Training and Scheduling Retraining**:
  - Train a machine learning model on historical match data to predict the outcome of future matches

- **Dashboard**:
  - Display upcoming week matches and predicted outcomes using a machine learning model.
  - Show outcome odds for the upcoming matches.
  - Display stats for each team over the last 5 matches (goals, shots, etc.).

- **Scraper**:
  - Build a scraper to fetch recent match data.

- **Automation**:
  - Automate scraping using a scheduling tool to update the data periodically (Airflow, python scheduler, Azure Functions timer_trigger).
  - You could also periodically retrain the model with recent match data and updated statistics.

### Nice-to-have features

- **Automated Betting Simulation**:
  - Make a scraper on betting odds for matches ahead of time to choose what to bet on.

- **Model Exploration**:
  - Investigate adding additional features (e.g., possession stats, player absences) to improve model accuracy. Or notify things on the dashboard

- **Database**:
  - Historical match data could be stored in a database if needed

### Some tips and content to support you

- **Hosting database**: 
  - [Heroku Postgres](https://www.heroku.com/postgres)
  - [ElephantSQL](https://www.elephantsql.com/)
  - [SummaryOfOptions](https://gist.github.com/bmaupin/0ce79806467804fdbbf8761970511b8c)
  - [AzureSQLDatabase](https://azure.microsoft.com/en-us/products/azure-sql/database)

- **Bookmaker odds**: Scrape odds from the following sources:
  - [WhoScored](https://www.whoscored.com/)
  - [SportsGambler](https://www.sportsgambler.com/)
  - [OddsChecker](https://www.oddschecker.com/)
  - [BetFirst](https://betfirst.dhnet.be/)

## Deliverables

1. **GitHub Repository**:
   - Publish your code on GitHub.
   - Include a README with:
     - Project description
     - Installation steps
     - Usage instructions
     - (Optional visuals)
     - (Contributors)
     - (Timeline)
     - (Challenges and solutions)

2. **App**:
   - A dashboard displaying match predictions, team stats, and upcoming matches with odds.

3. **Presentation**:
   - How did you approach the problem?
   - Who did what in the team?
   - What were the challenges and how did you solve them?

### Steps

1. **Set up repository** and study the project requirements.
2. **Split the work**:
   - Build a web scraper. - DE
   - Set up the hosting. - DE
   - Automate scraping and model updates using a scheduling tool. - DE
   - Train your prediction model using historical data. - DA
   - Build and deploy the dashboard. - DA

## A final note of encouragement

_"Success is not the key to happiness. Happiness is the key to success. If you love what you are doing, you will be successful."_
\- Albert Schweitzer

![You've got this!](https://i.giphy.com/media/JWuBH9rCO2uZuHBFpm/giphy.gif)
