import pandas as pd
import logging
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder, StandardScaler
import numpy as np
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

    def process_data(self, data):
        """
        Process the input data.
        This method should be overridden by subclasses to implement specific processing logic.
        """
        # Select key columns for analysis - based on the actual column names from the uploaded file
        # Renaming columns for consistency
        # new_column_names = {
        #     'Home_team': 'HomeTeam',
        #     'Away_team': 'AwayTeam',
        #     'Home_goals_(FT)': 'FTHG',
        #     'Away_goals_(FT)': 'FTAG',
        #     'Full_time_result_(H/D/A)': 'FTR',
        #     'Home_shots': 'HS',
        #     'Away_shots': 'AS',
        #     'Home_shots_on_target': 'HST',
        #     'Away_shots_on_target': 'AST',
        #     'Home_fouls': 'HF',
        #     'Away_fouls': 'AF',
        #     'Home_corners': 'HC',
        #     'Away_corners': 'AC',
        #     'Home_yellow_cards': 'HY',
        #     'Away_yellow_cards': 'AY',
        #     'Home_red_cards': 'HR',
        #     'Away_red_cards': 'AR',
        #     'MatchDate': 'Date',
        #     'MatchTime': 'Time'
        # }
        df = pd.DataFrame(data)
        # cols = df.columns.tolist()
        # Display basic information
        logging.info("\nDataLoader::process_data -> Dataset Info:")
        logging.info(f"DataLoader::process_data -> {df.info()}")
        logging.info("\nDataLoader::process_data -> First 5 rows:")
        logging.info(f"DataLoader::process_data -> {df.head()}")
        logging.info("\nDataLoader::process_data -> Column Names:")
        logging.info(f"DataLoader::process_data -> {df.columns.tolist()}")

        #df = df.rename(columns=new_column_names)
        #cols = df.columns.tolist()
        key_columns = ['Date', 'HomeTeam', 'AwayTeam', 'FTHG', 'FTAG', 'FTR', 'HS', 'AS', 'HST', 'AST', 'HF', 'AF', 'HC', 'AC', 'HY', 'AY', 'HR', 'AR']
        df_key = df[key_columns]

        # Convert Date to datetime
        #df_key['Date'] = pd.to_datetime(df_key['Date'], format='%d/%m/%Y')
        df_key['Date'] = pd.to_datetime(df_key['Date'], format='%Y-%m-%d')
        # Summary statistics
        logging.info(f'DataLoader::process_data -> Summary Statistics:')
        logging.info(f'DataLoader::process_data ->{df_key.describe()}')

        # Check for missing values
        logging.info(f'DataLoader::process_data -> Missing Values:')
        logging.info(f'DataLoader::process_data ->{df_key.isnull().sum()}')

        # Apply feature engineering
        df_features = df_key.copy()
        for idx, row in df_features.iterrows():
            home_stats = self.calculate_team_stats(df_key, row['HomeTeam'], row['Date'])
            away_stats = self.calculate_team_stats(df_key, row['AwayTeam'], row['Date'])

            df_features.loc[idx, 'home_avg_goals_scored'] = home_stats['avg_goals_scored']
            df_features.loc[idx, 'home_avg_goals_conceded'] = home_stats['avg_goals_conceded']
            df_features.loc[idx, 'home_win_rate'] = home_stats['win_rate']
            df_features.loc[idx, 'home_shots_on_target'] = home_stats['shots_on_target']

            df_features.loc[idx, 'away_avg_goals_scored'] = away_stats['avg_goals_scored']
            df_features.loc[idx, 'away_avg_goals_conceded'] = away_stats['avg_goals_conceded']
            df_features.loc[idx, 'away_win_rate'] = away_stats['win_rate']
            df_features.loc[idx, 'away_shots_on_target'] = away_stats['shots_on_target']

        logging.info("\nFeature Engineered DataFrame (First 5 rows):")
        logging.info(f"DataLoader::process_data -> {df_features.head()}")

        # 4. Data Preprocessing
        logging.info("\nDataLoader::process_data -> Preprocessing the data...")

        # Handle missing values
        df_features = df_features.fillna(0)

        # Encode team names
        le_home = LabelEncoder()
        le_away = LabelEncoder()
        df_features['HomeTeam'] = le_home.fit_transform(df_features['HomeTeam'])
        df_features['AwayTeam'] = le_away.fit_transform(df_features['AwayTeam'])

        # Encode match outcome (FTR: H=2, D=1, A=0)
        outcome_mapping = {'H': 2, 'D': 1, 'A': 0}
        df_features['FTR'] = df_features['FTR'].map(outcome_mapping)

        # Select features for modeling
        features = ['HomeTeam', 'AwayTeam', 'HS', 'AS', 'HST', 'AST', 'HF', 'AF', 'HC', 'AC', 'HY', 'AY', 'HR', 'AR',
                    'home_avg_goals_scored', 'home_avg_goals_conceded', 'home_win_rate', 'home_shots_on_target',
                    'away_avg_goals_scored', 'away_avg_goals_conceded', 'away_win_rate', 'away_shots_on_target']
        X = df_features[features]
        y = df_features['FTR']

        # Normalize numerical features
        scaler = StandardScaler()
        X = scaler.fit_transform(X)

        # Split the data
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

        logging.info("\nShape of Training and Testing Sets:")
        logging.info(f"X_train: {X_train.shape}, X_test: {X_test.shape}, y_train: {y_train.shape}, y_test: {y_test.shape}")

        return X_train, X_test, y_train, y_test


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