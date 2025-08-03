import logging
import datetime
import pyodbc

class DataLoader:
    """
    A class to download data from a specified URL using the requests library.
    This class handles GET requests, error handling, and JSON parsing.
    """

    def __init__(self, url=None,sql_connection_string=None):
        """
        Initialize the DataDownloader with a URL.
        """
        self.url = url
        self.sql_connection_string = sql_connection_string  # Placeholder for SQL connection string

    

    def load_from_database(self):
        """
        Load data from a database connection.
        This method is a placeholder for future implementation.
        """
        logging.info("DataLoader::load_from_database::Attempting to load data from the database...")
        if not self.sql_connection_string:
            logging.error("DataLoader::load_from_database::SQL_CONNECTION_STRING environment variable is not set. Please ensure local.settings.json or Azure App Settings are configured.")
            return None

        cnxn = None
        cursor = None
        matches_list = []
        try:
            cnxn = pyodbc.connect(self.sql_connection_string)
            cursor = cnxn.cursor()

            # Execute the SELECT query
            cursor.execute("""SELECT [MatchDate] as [Date], [HomeTeam], [AwayTeam], [FTHG], [FTAG], [FTR], [HS], [AS], [HST], [AST], [HF], [AF], [HC], [AC], [HY], [AY], [HR], [AR]
                              FROM [dbo].[FootballMatches]""")
            
            # Fetch all column names from the cursor description
            columns = [column[0] for column in cursor.description]
            
            # Fetch all rows and convert them to a list of dictionaries
            
            for row in cursor.fetchall():
                match_dict = {}
                for i, col_name in enumerate(columns):
                    # Ensure date and time objects are converted to strings if needed
                    if isinstance(row[i], datetime.date):
                        match_dict[col_name] = row[i].strftime('%Y-%m-%d')
                    elif isinstance(row[i], datetime.time):
                        match_dict[col_name] = row[i].strftime('%H:%M:%S')
                    else:
                        match_dict[col_name] = row[i]

                matches_list.append(match_dict)
            
            logging.info(f'DataLoader::load_from_database::Successfully retrieved {len(matches_list)} records from FootballMatches.')
            
           

        except pyodbc.Error as db_error:
            sqlstate = db_error.args[0]
            logging.error(f"DataLoader::load_from_database::Database error retrieving data: SQLSTATE={sqlstate}, Error={db_error}", exc_info=True)
            return None

        except Exception as e:
            logging.error(f"DataLoader::load_from_database::An unexpected error occurred during data retrieval: {e}", exc_info=True)
            
        finally:
            if cursor:
                cursor.close()
            if cnxn:
                cnxn.close()

        return matches_list