from tokenize import group
import pandas as pd
from sklearn.preprocessing import LabelEncoder, StandardScaler
import logging

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

    def add_averages(self, group, cols, windows):
        group = group.sort_values("Date")
        
        for window in windows:
            new_cols = [f"{col}_avg{window}" for col in cols]
            averages_stats = group[cols].rolling(window=window, closed='left').mean()
            group[new_cols] = averages_stats
            group = group.dropna(subset=new_cols) 
        
        return group
    
    def add_h2h_stats(self, group):
        opponents_grouped = group.groupby('opponent')
        for opponent, h2h_df in opponents_grouped:
            h2h_df = h2h_df.sort_values('Date')
            
            for index, row in h2h_df.iterrows():
                prev_matches = h2h_df[h2h_df['Date'] < row.Date]
                prev_matches_home = prev_matches[prev_matches['venue'] == 0]
                prev_matches_guest = prev_matches[prev_matches['venue'] == 1]

                group.loc[group['Date'] == row.Date, 'h2h_home_win'] = 0
                group.loc[group['Date'] == row.Date, 'h2h_home_draw'] = 0
                group.loc[group['Date'] == row.Date, 'h2h_home_loss'] = 0
                group.loc[group['Date'] == row.Date, 'h2h_guest_win'] = 0
                group.loc[group['Date'] == row.Date, 'h2h_guest_draw'] = 0
                group.loc[group['Date'] == row.Date, 'h2h_guest_loss'] = 0
                row[['h2h_home_win', 'h2h_home_draw', 'h2h_home_loss', 
                     'h2h_guest_win', 'h2h_guest_draw', 'h2h_guest_loss']] = pd.Series([0, 0, 0, 0, 0, 0])
                
                if prev_matches_home.shape[0] > 0:
                    group.loc[group['Date'] == row.Date, 'h2h_home_win'] = prev_matches_home['Win'].mean()
                    group.loc[group['Date'] == row.Date, 'h2h_home_draw'] = prev_matches_home['Draw'].mean()
                    group.loc[group['Date'] == row.Date, 'h2h_home_loss'] = prev_matches_home['Loss'].mean()
                if prev_matches_guest.shape[0] > 0:
                    group.loc[group['Date'] == row.Date, 'h2h_guest_win'] = prev_matches_guest['Win'].mean()
                    group.loc[group['Date'] == row.Date, 'h2h_guest_draw'] = prev_matches_guest['Draw'].mean()
                    group.loc[group['Date'] == row.Date, 'h2h_guest_loss'] = prev_matches_guest['Loss'].mean()

        return group
    
    def filter_dataset_4_stats(self, data, upcoming_matches_df):
        """
        Filter the dataset to include only matches that are relevant for statistics.
        """
        teams_set = set(upcoming_matches_df['HomeTeam']) | set(upcoming_matches_df['AwayTeam'])
        df, cols_4_avg = self.get_df_transformed(data, add_stats=False)  # Get DataFrame without additional stats
        df = df.sort_values(by='Date', ascending = False)

        last_matches = { team : df[df['team'] == team].head(15) for team in teams_set}

        h2h_matches = {}
        for team, opponent in upcoming_matches_df[['HomeTeam', 'AwayTeam']].itertuples(index=False, name=None):
            df_4_stats = df[(df['team'] == team) & (df['opponent'] == opponent)].sort_values(by='Date', ascending = False)
            h2h_matches[(team, opponent)] = df_4_stats

        return last_matches, h2h_matches, cols_4_avg
    
    def get_df_transformed(self, data, add_stats = True):
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

        # Add averages for last 5, 10, and 15 matches
        cols_4_avg = ["goals_for", "goals_against", "shots", "shots_on_target", "yellow_cards", "red_cards", "Win", "Loss", "Draw"] # , "fouls", "corners"
        if add_stats:
            # Add head 2 head statistics
            df_with_h2h = df.reindex(columns=df.columns.tolist() + 
                                    ['h2h_home_win', 'h2h_home_draw', 'h2h_home_loss', 
                                     'h2h_guest_win', 'h2h_guest_draw', 'h2h_guest_loss']) # 'h2h_win', 'h2h_loss',

            df_with_h2h = df_with_h2h.groupby('team').apply(lambda x: self.add_h2h_stats(x))
            df_with_h2h = df_with_h2h.droplevel('team')
            df_with_h2h.index = range(df_with_h2h.shape[0])
            
            df_with_h2h = df_with_h2h.reindex(columns=df_with_h2h.columns.tolist() + 
                                    [f"{col}_avg{window}" for window in [5, 10, 15] for col in cols_4_avg])  # Add columns for averages
            df_with_avg = df_with_h2h.groupby('team').apply(lambda x: self.add_averages(x, cols_4_avg, [5, 10, 15]))
            df_with_avg = df_with_avg.droplevel('team')
            df_with_avg.index = range(df_with_avg.shape[0])  # Reset index after groupby operation

            return df_with_avg, cols_4_avg
        return df, cols_4_avg

    def process_data(self, data, current_date=None):
        """
        Process the input data.
        This method should be overridden by subclasses to implement specific processing logic.
        Parameters:
            data (list[dict]): The input data to be processed.
            current_date (str): The current date for filtering the data.
        """
        if current_date is None:
            current_date = '2024-07-01'

        df_with_avg, cols_4_avg = self.get_df_transformed(data)
        df_with_avg = df_with_avg.fillna(0)

        le = LabelEncoder()
        df_with_avg['team_code'] = le.fit_transform(df_with_avg['team'])
        df_with_avg["opp_code"] = le.fit_transform(df_with_avg['opponent'])

        # Split the data into training and testing sets: test on >= 2024/2025 season
        train = df_with_avg[df_with_avg['Date'] < current_date]
        test = df_with_avg[df_with_avg['Date'] > current_date]

        predictors = ['venue', # , 'opp_code', 'team_code'
              'h2h_home_win', 'h2h_home_draw', 'h2h_home_loss', 'h2h_guest_win', 'h2h_guest_draw', 'h2h_guest_loss']
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

    def get_samples_to_predict_from_json(self, data, json_data) :
        df = pd.read_json(json_data)
        df['Date'] = pd.to_datetime(df['Date'], format='%d/%m/%Y')
        last_matches, h2h_matches, cols_4_avg = self.filter_dataset_4_stats(data, df)
        samples = []
        for team, opponent in h2h_matches.keys():
            h2h_df = h2h_matches[(team, opponent)]
            h2h_home = h2h_df[h2h_df['venue'] == 0]
            h2h_guest = h2h_df[h2h_df['venue'] == 1]
            samples.append({'team': team, 'opponent': opponent, 'venue': 0, 
                            'h2h_home_win': 0.5 if h2h_home.shape[0] == 0 else h2h_home['Win'].mean(),
                            'h2h_home_draw': 0 if h2h_home.shape[0] == 0 else h2h_home['Draw'].mean(), 
                            'h2h_home_loss': 0.5 if h2h_home.shape[0] == 0 else h2h_home['Loss'].mean(),
                            'h2h_guest_win': 0.5 if h2h_guest.shape[0] == 0 else h2h_guest['Win'].mean(),
                            'h2h_guest_draw': 0 if h2h_guest.shape[0] == 0 else h2h_guest['Draw'].mean(),
                            'h2h_guest_loss': 0.5 if h2h_guest.shape[0] == 0 else h2h_guest['Loss'].mean()})
            samples.append({'team': opponent, 'opponent': team, 'venue': 1, 
                            'h2h_home_win': 0.5 if h2h_guest.shape[0] == 0 else h2h_guest['Loss'].mean(),
                            'h2h_home_draw': 0 if h2h_guest.shape[0] == 0 else h2h_guest['Draw'].mean(), 
                            'h2h_home_loss': 0.5 if h2h_guest.shape[0] == 0 else h2h_guest['Win'].mean(),
                            'h2h_guest_win': 0.5 if h2h_home.shape[0] == 0 else h2h_home['Loss'].mean(),
                            'h2h_guest_draw': 0 if h2h_home.shape[0] == 0 else h2h_home['Draw'].mean(),
                            'h2h_guest_loss': 0.5 if h2h_home.shape[0] == 0 else h2h_home['Win'].mean()})
        for team, last_match in last_matches.items():
            for dict in list(filter(lambda x: x['team'] == team, samples)):
                for window in [5, 10, 15]:
                    for col in cols_4_avg:
                        dict[f"{col}_avg{window}"] = last_match.head(window)[col].mean()
        result = pd.DataFrame(samples).drop(columns=['team', 'opponent'])
        if result.shape[0] > 0:
            scaler = StandardScaler().set_output(transform="pandas")
            result = scaler.fit_transform(result)
        logging.info(f"Constructed features for prediction: {result}")
        return result