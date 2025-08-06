import logging
import datetime
import pyodbc
import json
import pandas as pd
import requests
import logging
import io

class DataLoader:
    """
    A class to download data from a specified URL using the requests library.
    This class handles GET requests, error handling, and JSON parsing.
    """
    column_mapping = {
            'Div': 'Division',
            'Date': 'MatchDate',
            'Time': 'MatchTime',
            'HomeTeam': 'HomeTeam',
            'AwayTeam': 'AwayTeam',
            'FTHG': 'FTHG',
            'FTAG': 'FTAG',
            'FTR': 'FTR',
            'HTHG': 'HTHG',
            'HTAG': 'HTAG',
            'HTR': 'HTR',
            'HS': 'HS',
            'AS': 'AS',
            'HST': 'HST',
            'AST': 'AST',
            'HF': 'HF',
            'AF': 'AF',
            'HC': 'HC',
            'AC': 'AC',
            'HY': 'HY',
            'AY': 'AY',
            'HR': 'HR',
            'AR': 'AR',
            'AvgH': 'AvgH',
            'AvgD': 'AvgD',
            'AvgA': 'AvgA',
            'Avg>2.5': 'Avg_Over_2_5',
            'Avg<2.5': 'Avg_Under_2_5',
            'AvgAHH': 'AvgAHH',
            'AvgAHA': 'AvgAHA',
            'AvgCH': 'AvgCH',
            'AvgCD': 'AvgCD',
            'AvgCA': 'AvgCA',
            'AvgC>2.5': 'AvgC_Over_2_5',
            'AvgC<2.5': 'AvgC_Under_2_5',
            'AvgCAHH': 'AvgCAHH',
            'AvgCAHA': 'AvgCAHA'
        }
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
    
    def fetch_csv_from_url(self,url: str) -> str:
        """
        Fetches CSV data from a given URL and returns it as a string.

        This function uses the 'requests' library to make an HTTP GET request.
        It handles potential errors like network issues or bad status codes.

        Args:
            url (str): The URL of the CSV file.

        Returns:
            str: The content of the CSV file as a string, or an empty string if an error occurs.
        """
        try:
            response = requests.get(url)
            response.raise_for_status()  # Raise an exception for bad status codes (4xx or 5xx)
            return response.text
        except requests.exceptions.RequestException as e:
            logging.error(f"DataLoader::fetch_csv_from_url::Error fetching CSV from URL: {e}")
            return ""

    def prepare_csv_to_json(self,csv_data: str) -> str:
        """
        Takes CSV data as a string, renames its columns using a predefined mapping,
        and returns a JSON string of the processed data.

        This function is designed to be a direct replacement for the processing logic
        in your original Azure Function, but it uses pandas for efficiency and robustness.

        Args:
            csv_data (str): The raw CSV data as a single string.

        Returns:
            str: A JSON string of the processed data, or a JSON error message.
        """
        if not csv_data:
            return json.dumps({"status": "error", "message": "No CSV data provided."})
        
        try:
            # Use io.StringIO to treat the string data as a file-like object for pandas
            csv_file_like_object = io.StringIO(csv_data)
            
            # Read the CSV data into a pandas DataFrame
            df = pd.read_csv(csv_file_like_object)

            # Rename columns directly to match the SQL table schema.
            # `errors='ignore'` will prevent an error if a column in the mapping
            # is not found in the DataFrame.
            df.rename(columns=self.column_mapping, inplace=True, errors='ignore')
            
            # Convert the 'MatchDate' column to the correct 'YYYY-MM-DD' format for SQL.
            # Errors='coerce' will turn un-parsable dates into NaT (Not a Time), which will
            # become 'null' in the final JSON.
            df['MatchDate'] = pd.to_datetime(df['MatchDate'], format='%d/%m/%Y', errors='coerce').dt.strftime('%Y-%m-%d')
            
            # The stored procedure expects the JSON data as an array of objects.
            # `to_json(orient='records')` is the most efficient way to achieve this.
            json_payload = df.to_json(orient='records', indent=4)
            return json_payload
            
        except Exception as e:
            return json.dumps({"status": "error", "message": f"An error occurred during CSV processing: {str(e)}"})

    def process_and_insert_data(self,csv_url: str, sql_connection_string: str, stored_procedure_name: str) -> int:
        """
        Fetches a CSV from a URL, processes the data, and inserts it into
        a SQL Server database using a stored procedure.

        Args:
            csv_url (str): The URL of the CSV file.
            sql_connection_string (str): The connection string for the SQL Server database.
            stored_procedure_name (str): The name of the stored procedure to call.
        """
        # 1. Fetch the CSV data from the URL
        print("Fetching CSV from URL...")
        csv_data = self.fetch_csv_from_url(csv_url)
        if not csv_data:
            print("Failed to fetch CSV. Aborting data pipeline.")
            return

        # 2. Process the CSV data into a JSON string
        print("Processing CSV data into JSON format...")
        json_payload = self.prepare_csv_to_json(csv_data)

        # Check if processing was successful.
        try:
            # A simple check to see if the JSON is valid and not an error message
            json_data = json.loads(json_payload)
            if isinstance(json_data, dict) and json_data.get("status") == "error":
                print(f"Error during data processing: {json_data.get('message')}")
                return
            total_rows_processed = len(json_data)
            logging.info(f"DataLoader::load_from_database::Successfully processed {total_rows_processed} records.")
        except json.JSONDecodeError:
            logging.error("DataLoader::load_from_database::An error occurred during JSON parsing after processing.")
            return

        # 3. Insert data into SQL Server using pyodbc
        logging.info(f"DataLoader::load_from_database::Connecting to SQL Server to execute stored procedure '{stored_procedure_name}'...")
        cnxn = None
        cursor = None
        try:
            # Connect to SQL Server. autocommit=False allows for transaction management.
            cnxn = pyodbc.connect(sql_connection_string, autocommit=False)
            cursor = cnxn.cursor()

            # Execute the stored procedure. The '?' acts as a placeholder for the @jsonData parameter.
            # {CALL dbo.UpsertFootballMatches(?)} is the ODBC syntax for calling a stored procedure with parameters.
            cursor.execute(f"{{CALL {stored_procedure_name}(?)}}", json_payload)
            result = cursor.fetchone()
            inserted_rows_count = 0
            # Vérifie si un résultat a été retourné et l'affiche
            if result:
                inserted_rows_count = result[0] # Ou result.InsertedRowsCount
                print(f"DataLoader::load_from_database::New inserted rows count: {inserted_rows_count}")
            cnxn.commit()  # Commit the transaction if successful
            
            logging.info(f"DataLoader::load_from_database::Successfully executed '{stored_procedure_name}' for {total_rows_processed} records.")

            return inserted_rows_count
            
        except pyodbc.Error as db_error:
            # Handle database-specific errors
            if cnxn:
                cnxn.rollback() # Rollback the transaction on error
            logging.error(f"DataLoader::load_from_database::Database error executing stored procedure: {str(db_error)}")
        except Exception as e:
            logging.error(f"DataLoader::load_from_database::An unexpected error occurred during database operation: {str(e)}")
        finally:
            # Ensure cursor and connection are closed
            if cursor:
                cursor.close()
            if cnxn:
                cnxn.close()
            logging.info("DataLoader::load_from_database::Database connection closed.")