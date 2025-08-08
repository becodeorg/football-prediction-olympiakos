import pandas as pd
import logging
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder, StandardScaler
import numpy as np
import logging
from datetime import datetime

class DataProcessor:
    """
    This class processes data retrieved from various sources.
    It includes methods for filtering, transforming, and validating data.
    """

    def __init__(self):
        """
        Initialize the DataProcessor.
        """
        pass

    def add_h2h_stats(self, group):
        groups_by_opponent = group.groupby('opponent')
        for h2h_group_name in groups_by_opponent.groups:
            h2h_group = groups_by_opponent.get_group(h2h_group_name)
            # group.iloc[group.opponent == h2h_group_name, group.columns.get_loc("h2h_win")] = h2h_group['Win'].mean()
            # group.iloc[group.opponent == h2h_group_name, group.columns.get_loc("h2h_loss")] = h2h_group['Loss'].mean()
            groups_by_venue = h2h_group.groupby('venue')
            venues = list(groups_by_venue.groups.keys())
            if len(venues) == 1:
                if 1 - venues[0] == 0: # missing value
                    group.iloc[group.opponent == h2h_group_name, group.columns.get_loc("h2h_home_win")] = 0.5
                    group.iloc[group.opponent == h2h_group_name, group.columns.get_loc("h2h_home_loss")] = 0.5
                else:
                    group.iloc[group.opponent == h2h_group_name, group.columns.get_loc("h2h_guest_win")] = 0.5
                    group.iloc[group.opponent == h2h_group_name, group.columns.get_loc("h2h_guest_loss")] = 0.5
            for venue in venues:
                venue_group = groups_by_venue.get_group(venue)
                if venue == 0:
                    group.iloc[group.opponent == h2h_group_name, group.columns.get_loc("h2h_home_win")] = venue_group['Win'].mean()
                    group.iloc[group.opponent == h2h_group_name, group.columns.get_loc("h2h_home_loss")] = venue_group['Loss'].mean()
                else:
                    group.iloc[group.opponent == h2h_group_name, group.columns.get_loc("h2h_guest_win")] = venue_group['Win'].mean()
                    group.iloc[group.opponent == h2h_group_name, group.columns.get_loc("h2h_guest_loss")] = venue_group['Loss'].mean()
        return group
    
    def add_averages(self, group, cols, windows):
        group = group.sort_values("Date")
        
        for window in windows:
            new_cols = [f"{col}_avg{window}" for col in cols]
            averages_stats = group[cols].rolling(window=window, closed='left').mean()
            group[new_cols] = averages_stats
            group = group.dropna(subset=new_cols)
        
        return group
    
    def get_df_transformed(self, data):
        df = pd.DataFrame(data)
        # cols = df.columns.tolist()
        # Display basic information
        # print("\nDataset Info:")
        # print(df.info())
        # print("\nFirst 5 rows:")
        # print(df.head())
        # print("\nColumn Names:")
        # print(df.columns.tolist())

        columns_to_retain_hosts = ['Date',
                                    'HomeTeam', 'AwayTeam', 
                                    'FTHG', 'FTAG',
                                    'HS', 'HST',
                                    'HF', 'HC',
                                    'HY', 'HR',
                                    'FTR']
        columns_to_retain_guests = ['Date',
                                'HomeTeam', 'AwayTeam', 
                                    'FTHG', 'FTAG',
                                    'AS', 'AST',
                                    'AF', 'AC',
                                    'AY', 'AR',
                                    'FTR']
            
        df_hosts = df[columns_to_retain_hosts].rename(columns={'HomeTeam': 'team', 'AwayTeam' : 'opponent',
                                                        'FTHG': 'goals_for', 'FTAG': 'goals_against',
                                                        'HS': 'shots', 'HST': 'shots_on_target',
                                                        'HF': 'fouls', 'HC': 'corners',
                                                        'HY': 'yellow_cards', 'HR': 'red_cards',
                                                        'FTR': 'result'})

        df_guests = df[columns_to_retain_guests].rename(columns={'HomeTeam': 'opponent', 'AwayTeam' : 'team',
                                                        'FTHG': 'goals_against', 'FTAG': 'goals_for',
                                                        'AS': 'shots', 'AST': 'shots_on_target',
                                                        'AF': 'fouls', 'AC': 'corners',
                                                        'AY': 'yellow_cards', 'AR': 'red_cards',
                                                            'FTR': 'result'})
        df_hosts["venue"] = 0 # Home
        df_guests["venue"] = 1 # Away

        # Win = 1, Draw = 0, Loss = -1
        df_hosts.result = df_hosts.result.apply(lambda x: 1 if x == 'H' else (0 if x == 'D' else -1))
        df_guests.result = df_guests.result.apply(lambda x: 1 if x == 'A' else (0 if x == 'D' else -1))

        df = pd.concat([df_hosts, df_guests])

        df["Win"] = df['result'].apply(lambda x: 1 if x == 1 else 0)
        df["Loss"] = df['result'].apply(lambda x: 1 if x == -1 else 0)
        df["Draw"] = df['result'].apply(lambda x: 1 if x == 0 else 0)

        # Add head 2 head statistics
        df_with_h2h = df.reindex(columns=df.columns.tolist() + 
                                  ['h2h_home_win', 'h2h_home_loss', 'h2h_guest_win', 'h2h_guest_loss']) # 'h2h_win', 'h2h_loss',

        df_with_h2h = df_with_h2h.groupby('team').apply(lambda x: self.add_h2h_stats(x))
        df_with_h2h = df_with_h2h.droplevel('team')
        df_with_h2h.index = range(df_with_h2h.shape[0])

        # Add averages for last 5, 10, and 15 matches
        cols_4_avg = ["goals_for", "goals_against", "shots", "shots_on_target", "yellow_cards", "red_cards", "Win", "Loss", "Draw"] # , "fouls", "corners"
        
        df_with_avg = df_with_h2h.groupby('team').apply(lambda x: self.add_averages(x, cols_4_avg, [5, 10, 15]))
        df_with_avg = df_with_avg.droplevel('team')
        df_with_avg.index = range(df_with_avg.shape[0])  # Reset index after groupby operation

        return df_with_avg, cols_4_avg

    def process_data(self, data, current_date=None):
        """
        Process the input data.
        This method should be overridden by subclasses to implement specific processing logic.
        Parameters:
            data (list[dict]): The input data to be processed.
            current_date (str): The current date for filtering the data.
        """
        df_with_avg, cols_4_avg = self.get_df_transformed(data)
        df_with_avg = df_with_avg.fillna(0)

        le = LabelEncoder()
        df_with_avg['team_code'] = le.fit_transform(df_with_avg['team'])
        df_with_avg["opp_code"] = le.fit_transform(df_with_avg['opponent'])

        # Split the data into training and testing sets: test on >= 2024/2025 season
        if current_date is None:
            current_date = '2024-07-01'
        train = df_with_avg[df_with_avg['Date'] < current_date]
        test = df_with_avg[df_with_avg['Date'] > current_date]

        predictors = ['venue', # , 'opp_code','team_code', 'avg_odds'
              #'shots', 'shots_on_target', 'fouls', 'corners', 'yellow_cards', 'red_cards', 
              'h2h_home_win', 'h2h_home_loss', 'h2h_guest_win', 'h2h_guest_loss']
        predictors += [f"{col}_avg{window}" for window in [5, 10, 15] for col in cols_4_avg]

        print(f"Predictors count: {len(predictors)}")

        X_train = train[predictors]
        X_test = test[predictors]
        y_train = train['result']
        y_test = test['result']

        scaler = StandardScaler().set_output(transform="pandas")
        X_train = scaler.fit_transform(X_train)
        if X_test.shape[0] > 0:
            X_test = scaler.transform(X_test)

        print(f"X_train shape: {X_train.shape}, Y_train shape: {y_train.shape}")
        print(f"X_test shape: {X_test.shape}, Y_test shape: {y_test.shape}")

        return X_train, X_test, y_train, y_test

    

    def construct_features_for_prediction(self, data, date, homeTeam, awayTeam,currentDate=datetime.today().strftime('%Y-%m-%d')):
        """
        Construct features from the DataFrame.
        This method can be used to create additional features or modify existing ones.
        """
        if isinstance(date, pd.Timestamp):
            date = date.strftime('%Y-%m-%d')

        currentDate = currentDate#datetime.today().strftime('%Y-%m-%d')
        if data[-1]['Date'] >= currentDate:
            data = [dict for dict in data if dict['Date'] < currentDate]

        data.append({'Date': date, 'HomeTeam': homeTeam, 'AwayTeam': awayTeam})
        df, cols_4_avg = self.get_df_transformed(data)
        df = df.fillna(0)

        predictors = ['venue', # , 'opp_code','team_code', 'avg_odds'
              #'shots', 'shots_on_target', 'fouls', 'corners', 'yellow_cards', 'red_cards', 
              'h2h_home_win', 'h2h_home_loss', 'h2h_guest_win', 'h2h_guest_loss']
        predictors += [f"{col}_avg{window}" for window in [5, 10, 15] for col in cols_4_avg]

        X_test = pd.concat(
            [df[(df['Date'] == date) & (df['team'] == homeTeam) & (df['opponent'] == awayTeam)],
            df[(df['Date'] == date) & (df['team'] == awayTeam) & (df['opponent'] == homeTeam)]])[predictors]
        # print(f'{date} - {homeTeam} vs {awayTeam}')
        # print(X_test)
        if X_test.shape[0] > 0:
            scaler = StandardScaler().set_output(transform="pandas")
            X_test = scaler.fit_transform(X_test)
        logging.info(f"Constructed features for prediction: {X_test}")

        return X_test
    
    def get_samples_to_predict(self, data, filename = './data/futur_matches.csv') :
        df = pd.read_csv(filename)
        df['Date'] = pd.to_datetime(df['Date'], format='%d/%m/%Y')

        currentDate = datetime.today().strftime('%Y-%m-%d')


        return [self.construct_features_for_prediction(data, row.Date, row.HomeTeam, row.AwayTeam,currentDate) for row in df.itertuples()]
    
    def get_samples_to_predict_from_json(self, data, json_data) :
        df = pd.read_json(json_data)
        df['Date'] = pd.to_datetime(df['Date'], format='%d/%m/%Y')

        currentDate = datetime.today().strftime('%Y-%m-%d')


        return [self.construct_features_for_prediction(data, row.Date, row.HomeTeam, row.AwayTeam,currentDate) for row in df.itertuples()]
    
    # Function to calculate historical team statistics (last 5 matches)
    def calculate_team_stats(self,df, team, date, window=5):
        past_matches = df[df['Date'] < date]
        home_matches = past_matches[past_matches['HomeTeam'] == team].tail(window)
        away_matches = past_matches[past_matches['AwayTeam'] == team].tail(window)

        stats = {
            'avg_goals_scored': 0,
            'avg_goals_conceded': 0,
            'win_rate': 0,
            'shots_on_target': 0
        }

        if len(home_matches) + len(away_matches) > 0:
            home_goals_scored = home_matches['FTHG'].sum()
            home_goals_conceded = home_matches['FTAG'].sum()
            away_goals_scored = away_matches['FTAG'].sum()
            away_goals_conceded = away_matches['FTHG'].sum()

            stats['avg_goals_scored'] = (home_goals_scored + away_goals_scored) / (len(home_matches) + len(away_matches))
            stats['avg_goals_conceded'] = (home_goals_conceded + away_goals_conceded) / (len(home_matches) + len(away_matches))

            home_wins = len(home_matches[home_matches['FTR'] == 'H'])
            away_wins = len(away_matches[away_matches['FTR'] == 'A'])
            stats['win_rate'] = (home_wins + away_wins) / (len(home_matches) + len(away_matches))

            home_shots = home_matches['HST'].sum()
            away_shots = away_matches['AST'].sum()
            stats['shots_on_target'] = (home_shots + away_shots) / (len(home_matches) + len(away_matches))

        return stats