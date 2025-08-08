import azure.functions as func
import logging
import os
import json
import csv
import io
import datetime
import pyodbc
import requests
from modules.loader.DataLoader import DataLoader
from modules.processor.DataProcessor import DataProcessor
from modules.model.LinRegModel import LinRegModel
from modules.ModelBlobStorage import ModelBlobStorage
import pandas as pd


app = func.FunctionApp(http_auth_level=func.AuthLevel.ANONYMOUS)
@app.route(route="test", methods=["GET"])
def test(req: func.HttpRequest) -> func.HttpResponse:
    """
    A simple HTTP trigger function that returns a greeting message.
    This function checks for a 'name' parameter in the query string or in the request body.
    If the 'name' parameter is provided, it returns a personalized greeting.
    """
    logging.info('Python HTTP trigger function processed a request.')
    name = req.params.get('name')
    if not name:
        try:
            req_body = req.get_json()
        except ValueError:
            pass
        else:
            name = req_body.get('name')

    if name:
        return func.HttpResponse(f"Hello, {name}. This HTTP triggered function executed successfully.")
    else:
        return func.HttpResponse(
             "This HTTP triggered function executed successfully. Pass a name in the query string or in the request body for a personalized response.",
             status_code=200
        )
    

@app.route(route="get_datas", methods=["GET"])
def get_datas(req: func.HttpRequest) -> func.HttpResponse:
    """ Function to retrieve football match data from the database using pyodbc.
    This function is triggered by an HTTP GET request and retrieves all data from the FootballMatches table.
    
    Args:
        req (func.HttpRequest): The HTTP request object.
    
    Returns:
        func.HttpResponse: A JSON response containing the list of football matches.
    """
    logging.info('get_datas::Retrieving football matches from database using pyodbc.')

    sql_connection_string = get_sql_connection_string()

    cnxn = None
    cursor = None
    try:
        cnxn = pyodbc.connect(sql_connection_string)
        cursor = cnxn.cursor()

        # Execute the SELECT query
        cursor.execute("SELECT * FROM [dbo].[FootballMatches]")
        
        # Fetch all column names from the cursor description
        columns = [column[0] for column in cursor.description]
        
        # Fetch all rows and convert them to a list of dictionaries
        matches_list = []
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
            # Map database column names back to CSV format
            csv_formatted_match = map_db_to_csv_format(match_dict)
            matches_list.append(csv_formatted_match)
        
        logging.info(f'get_datas::Successfully retrieved {len(matches_list)} records from FootballMatches.')
        
        return func.HttpResponse(
            json.dumps(matches_list, default=str), # default=str handles non-JSON serializable types
            mimetype="application/json"
        )

    except pyodbc.Error as db_error:
        sqlstate = db_error.args[0]
        logging.error(f"get_datas::Database error retrieving data: SQLSTATE={sqlstate}, Error={db_error}", exc_info=True)
        return func.HttpResponse(
            json.dumps({"status": "error", "message": f"Database operation failed: {str(db_error)}"}),
            mimetype="application/json",
            status_code=500
        )
    except Exception as e:
        logging.error(f"get_datas::An unexpected error occurred during data retrieval: {e}", exc_info=True)
        return func.HttpResponse(
            json.dumps({"status": "error", "message": f"An unexpected error occurred: {str(e)}"}),
            mimetype="application/json",
            status_code=500
        )
    finally:
        if cursor:
            cursor.close()
        if cnxn:
            cnxn.close()

@app.route(route="upload_football_matches_csv", methods=["POST"])
# The @app.sql_output binding is removed as we will use pyodbc directly
def upload_football_matches_csv(req: func.HttpRequest) -> func.HttpResponse:

    """
    HTTP trigger function to receive a CSV file and populate the FootballMatches database table.
    Expects CSV data directly in the request body.
    
    Args:
        req (func.HttpRequest): The HTTP request object containing the CSV data.
        # outputFootballMatches binding parameter is removed as we use pyodbc directly
        
    Returns:
        func.HttpResponse: A JSON response indicating success or failure.
    """
    logging.info('upload_football_matches_csv::Python HTTP trigger function processed a CSV upload request using pyodbc.')

    # Get connection string from environment variables
    sql_connection_string = get_sql_connection_string()

    cnxn = None
    cursor = None
    try:
        # Read the CSV content from the request body as a UTF-8 string
        csv_data = req.get_body().decode('utf-8')
        logging.info('upload_football_matches_csv::decoded CSV data successfully.')
        
        # Use io.StringIO to treat the string as a file-like object, which csv.DictReader can use
        csv_file = io.StringIO(csv_data)
        logging.info('upload_football_matches_csv::created StringIO object for CSV data.')
        
        # Use csv.DictReader to automatically map CSV headers to dictionary keys
        reader = csv.DictReader(csv_file)
        logging.info('upload_football_matches_csv::created CSV DictReader object.')

        # Log the detected headers to ensure DictReader is seeing them correctly
        logging.info(f'upload_football_matches_csv::Detected CSV headers: {reader.fieldnames}')

        matches_to_insert = []
        logging.info('upload_football_matches_csv::initialized matches_to_insert list.')
        
        # Define a helper function to safely convert values to INT
        def safe_to_int(val):
            try:
                # Convert to float first, as some INT values in CSV might have '.0'
                return int(float(val)) if val else None
            except (ValueError, TypeError):
                return None
        
        # Define a helper function to safely convert values to FLOAT
        def safe_to_float(val):
            try:
                return float(val) if val else None
            except (ValueError, TypeError):
                return None

        # Iterate through each row in the CSV
        for row_num, row in enumerate(reader):
            # Log first few characters of row data to prevent excessively long log messages
            row_preview = {k: str(v)[:50] + ('...' if len(str(v)) > 50 else '') for k, v in row.items()}
            logging.info(f'upload_football_matches_csv::Processing row {row_num + 1}: {row_preview}')
            processed_row = {}
            try:
                # Map CSV columns to SQL table columns based on your schema
                # Handle Date and Time parsing
                date_str = row.get('Date')
                if date_str:
                    # Convert DD/MM/YYYY from CSV to YYYY-MM-DD for SQL DATE type
                    processed_row['MatchDate'] = datetime.datetime.strptime(date_str, '%d/%m/%Y').strftime('%Y-%m-%d')
                else:
                    processed_row['MatchDate'] = None

                # Time needs no special formatting, SQL TIME(0) handles HH:MM
                processed_row['MatchTime'] = row.get('Time')

                # Team Names and Results
                processed_row['Division'] = row.get('Division')
                processed_row['HomeTeam'] = row.get('Home_team')
                processed_row['AwayTeam'] = row.get('Away_team')
                processed_row['FTR'] = row.get('Full_time_result_(H/D/A)')
                processed_row['HTR'] = row.get('Half_time_result_(H/D/A)')

                # Goals and Match Statistics (using safe_to_int for numerical conversions)
                processed_row['FTHG'] = safe_to_int(row.get('Home_goals_(FT)'))
                processed_row['FTAG'] = safe_to_int(row.get('Away_goals_(FT)'))
                processed_row['HTHG'] = safe_to_int(row.get('Home_goals_(HT)'))
                processed_row['HTAG'] = safe_to_int(row.get('Away_goals_(HT)'))
                processed_row['HS'] = safe_to_int(row.get('Home_shots'))
                processed_row['AS'] = safe_to_int(row.get('Away_shots'))
                processed_row['HST'] = safe_to_int(row.get('Home_shots_on_target'))
                processed_row['AST'] = safe_to_int(row.get('Away_shots_on_target'))
                processed_row['HF'] = safe_to_int(row.get('Home_fouls'))
                processed_row['AF'] = safe_to_int(row.get('Away_fouls'))
                processed_row['HC'] = safe_to_int(row.get('Home_corners'))
                processed_row['AC'] = safe_to_int(row.get('Away_corners'))
                processed_row['HY'] = safe_to_int(row.get('Home_yellow_cards'))
                processed_row['AY'] = safe_to_int(row.get('Away_yellow_cards'))
                processed_row['HR'] = safe_to_int(row.get('Home_red_cards'))
                processed_row['AR'] = safe_to_int(row.get('Away_red_cards'))

                # Betting Odds (using safe_to_float for numerical conversions)
                # Pre-match Average Odds
                processed_row['AvgH'] = safe_to_float(row.get('Avg_home_win_odds'))
                processed_row['AvgD'] = safe_to_float(row.get('Avg_draw_odds'))
                processed_row['AvgA'] = safe_to_float(row.get('Avg_away_win_odds'))
                processed_row['Avg_Over_2_5'] = safe_to_float(row.get('Avg_over_2.5_goals'))
                processed_row['Avg_Under_2_5'] = safe_to_float(row.get('Avg_under_2.5_goals'))
                processed_row['AvgAHH'] = safe_to_float(row.get('Avg_AH_home'))
                processed_row['AvgAHA'] = safe_to_float(row.get('Avg_AH_away'))

                # Closing Average Odds (inferred mappings from your initial CSV headers to new SQL names)
                processed_row['AvgCH'] = safe_to_float(row.get('AvgCH'))
                processed_row['AvgCD'] = safe_to_float(row.get('AvgCD'))
                processed_row['AvgCA'] = safe_to_float(row.get('AvgCA'))
                processed_row['AvgC_Over_2_5'] = safe_to_float(row.get('Avg_corners_over_2.5')) # Assuming this maps to AvgC>2.5
                processed_row['AvgC_Under_2_5'] = safe_to_float(row.get('Avg_corners_under_2.5')) # Assuming this maps to AvgC<2.5
                processed_row['AvgCAHH'] = safe_to_float(row.get('Avg_AH_corners_home')) # Assuming this maps to AvgCAHH
                processed_row['AvgCAHA'] = safe_to_float(row.get('Avg_AH_corners_away')) # Assuming this maps to AvgCAHA
                
                matches_to_insert.append(processed_row)

            except Exception as row_e:
                logging.error(f"upload_football_matches_csv::Error processing row {row_num + 1}: {row_e}. Row data: {row_preview}", exc_info=True)
                # If a row causes an error, it will be skipped. You can modify this
                # behavior if you prefer to fail the entire upload on any row error.
                continue

        if not matches_to_insert:
            return func.HttpResponse(
                json.dumps({"status": "error", "message": "No valid data rows found in CSV to insert. Please check CSV format and content."}),
                mimetype="application/json",
                status_code=400
            )

        # Convert the list of dictionaries to a JSON string
        json_data_payload = json.dumps(matches_to_insert)
        total_rows_processed = len(matches_to_insert)

        # Establish database connection and call stored procedure
        try:
            # Connect to SQL Server. autocommit=False allows for transaction management.
            cnxn = pyodbc.connect(sql_connection_string, autocommit=False)
            cursor = cnxn.cursor()

            # Execute the stored procedure. The '?' acts as a placeholder for the @jsonData parameter.
            # {CALL dbo.UpsertFootballMatches(?)} is the ODBC syntax for calling a stored procedure with parameters.
            cursor.execute("{CALL dbo.UpsertFootballMatches(?)}", json_data_payload)
            cnxn.commit() # Commit the transaction if successful

            logging.info(f"upload_football_matches_csv::Successfully executed dbo.UpsertFootballMatches for {total_rows_processed} records via pyodbc.")
            
            # The exact number of inserted rows is printed by the stored procedure to the SQL Server logs.
            # This Python function won't get that specific count back without a SELECT statement from the SP.
            return func.HttpResponse(
                json.dumps({"status": "success", "message": f"Successfully processed and submitted {total_rows_processed} records to SQL for upsertion via stored procedure. Check database logs for exact insert counts."}),
                mimetype="application/json"
            )

        except pyodbc.Error as db_error:
            # Handle database-specific errors
            if cnxn:
                cnxn.rollback() # Rollback the transaction on error
            sqlstate = db_error.args[0]
            logging.error(f"upload_football_matches_csv::Database error executing stored procedure: SQLSTATE={sqlstate}, Error={db_error}", exc_info=True)
            return func.HttpResponse(
                json.dumps({"status": "error", "message": f"Database operation failed: {str(db_error)}"}),
                mimetype="application/json",
                status_code=500
            )
        finally:
            # Ensure cursor and connection are closed
            if cursor:
                cursor.close()
            if cnxn:
                cnxn.close()

    except Exception as e:
        logging.error(f"upload_football_matches_csv::An unexpected error occurred during CSV upload function execution: {e}", exc_info=True)
        return func.HttpResponse(
            json.dumps({"status": "error", "message": f"An unexpected error occurred during CSV processing: {str(e)}"}),
            mimetype="application/json",
            status_code=500
        )
    
@app.route(route="predict", methods=["POST"])
def predict(req: func.HttpRequest) -> func.HttpResponse:
    """ 
    HTTP trigger function to receive data for a match and return a prediction.
    This function expects the match data in the request body as a JSON object.
    """
    logging.info('predict::Python HTTP trigger function processed a prediction request.')
    try:
        # Read the data content from the request body as a UTF-8 string
        post_data = req.get_body().decode('utf-8')
        logging.info('predict::received data successfully.')
        # Parse the JSON data
        post_data = json.loads(post_data)

        if not post_data:
            logging.error('predict::No data provided for prediction.')
            return func.HttpResponse(
                json.dumps({"status": "error", "message": "No data provided for prediction."}),
                mimetype="application/json",
                status_code=400
            )
        if not post_data["HomeTeam"] or not post_data["AwayTeam"] or not post_data["Date"] or not post_data["Time"] :
            logging.error(f'predict::Missing fields.{{"HomeTeam": {post_data["HomeTeam"]}, "AwayTeam": {post_data["AwayTeam"]}, "Date": {post_data["Date"]}, "Time": {post_data["Time"]}}}')
            return func.HttpResponse(
                json.dumps({"status": "error", "message": "Missing parameters. Check post data..."}),
                mimetype="application/json",
                status_code=400
            )

        logging.info(f'predict::Received data for prediction: {post_data}')

        blob_model = ModelBlobStorage()

        model_package = blob_model.load_model("olympiakos_prediction_model.pkl")

        metadata = model_package.get("metadata", {})
        model = model_package.get("model")#LinRegModel(model=model_package.get("model"))
        logging.info(f"predict::Loaded model with metadata: {metadata}")
        logging.info(f'predict::Model loaded successfully: {type(model)}')

        connection_string = get_sql_connection_string()
        data_loader = DataLoader(sql_connection_string=connection_string)
        data = data_loader.load_from_database()
        if data:
            logging.info("Data loaded successfully.")
        
        else:
            logging.error("Failed to load data.")
            return

        processor = DataProcessor()
        #X_train, X_test, y_train, y_test = processor.process_data(data)

        samples = processor.get_samples_to_predict_from_json(data, json.dumps([post_data]))
        logging.info(f'predict::Samples for prediction: {samples}')
        results=[]
        results = model.predict(samples)
        # Convert each NumPy array in the results list to a standard Python list
        serializable_results = [arr.tolist() for arr in results]
        logging.info(f'predict::Prediction results: {json.dumps(serializable_results, indent=2)}')

        return func.HttpResponse(
            json.dumps({"status": "success", "message": "Prediction completed successfully.", "results": serializable_results[0]}),
            mimetype="application/json",
            status_code=200
        )

    except Exception as e:
        logging.error(f"predict::An unexpected error occurred during predict function execution: {e}", exc_info=True)
        return func.HttpResponse(
            json.dumps({"status": "error", "message": f"An unexpected error occurred during predict processing: {str(e)}"}),
            mimetype="application/json",
            status_code=500
        )
    
# ==============================================
# ML Model Training and Saving
# ==============================================
@app.route(route="models/train", methods=["POST"])
def train_and_save_model(req: func.HttpRequest) -> func.HttpResponse:
    """Train a simple model and save it to blob storage"""

    logging.info('Training and saving model.')
    
    try:
    
        blob_name,performance = train_and_save_model()
       

        return func.HttpResponse(
                json.dumps({"status": "success", "message": f"Model Successfully trained for prediction.","performance": performance, "blob_name": blob_name}),
                status_code=201,
                mimetype="application/json"
            )

    except Exception as e:
        logging.error(f"Error in train_and_save_model: {str(e)}")
        return func.HttpResponse(
            json.dumps({"error": str(e)}),
            status_code=500,
            headers={"Content-Type": "application/json"}
        )


@app.function_name(name="data_sync_timer")
@app.timer_trigger(schedule="0 0 1 * * 1",# schedule="0 */1 * * * *", #
              arg_name="data_sync_timer",
              run_on_startup=False) 
def data_sync_timer(data_sync_timer: func.TimerRequest) -> None:
    """
    Syncs the SQL table with the latest data from the CSV file.
    This function is called to ensure the SQL table is up-to-date with the latest match data.
    Run on a schedule  every Monday at 1 AM.
    """
    logging.info('sync_sql_table::Syncing SQL table with latest data from CSV file.')
    try:
       
        logging.info(f'sync_sql_table::Timer trigger function executed at {datetime.datetime.now()}')   

        data_loader = DataLoader()
        # URL for the latest Belgian Jupiler League data (2025/2026 season)
        csv_url = "https://www.football-data.co.uk/mmz4281/2526/B1.csv"

        sql_connection_string = get_sql_connection_string()

        stored_procedure_name = "dbo.UpsertFootballMatches"

        # Call the main function to run the full pipeline
        total_new_row = data_loader.process_and_insert_data(csv_url, sql_connection_string, stored_procedure_name)
        if total_new_row == 0:
            logging.info('sync_sql_table::No new rows were inserted into the SQL table.')
        else:
            logging.info(f'sync_sql_table::Total new rows inserted into the SQL table: {total_new_row}')
            logging.info('sync_sql_table:Trigger training of the model with new data.')
            train_and_save_model()
        
        logging.info(json.dumps({"status": "success", "message": "SQL table synced successfully."}))
   
        
    except Exception as e:
        logging.error(f'sync_sql_table::An error occurred while syncing SQL table: {e}', exc_info=True)
        


#--------------- UTILITY FUNCTIONS ---------------#
def train_and_save_model():
    """ 
    Utility function to train and save the model.
    """
    model,performance,X_train_len = train_model()

    # Create model package with metadata
    logging.info("Saving model to blob storage...")


    blob_name = save_model(model, performance, X_train_len, "olympiakos_prediction_model.pkl")

    return blob_name, performance

def save_model(model, performance,X_train_len, model_name):
    """
    Save the trained model to blob storage with metadata.
    
    Args:
        model: The trained model object to be saved.
        metadata: Metadata associated with the model.
        model_name: Name of the model to be saved in blob storage.
        
    Returns:
        The name of the blob where the model is saved.
    """
    try:
        model_metadata ={
            "performance": performance,
            "training_samples": {X_train_len},
            "content_type": "application/octet-stream"
        }
       
        logging.info(f"save_model-> Model metadata: {model_metadata}")
        # Save to blob storage
        storage_helper = ModelBlobStorage()
        model_name = "olympiakos_prediction_model"
        logging.info(f"Saving model '{model_name}' to blob storage...")
        blob_name = storage_helper.save_model(model,model_metadata, model_name)
        logging.info(f"save_model->Model saved successfully to blob storage with name: {blob_name}")
        
        
        return blob_name
    except Exception as e:
        logging.error(f"ModelBlobStorage::save_model -> Error saving model '{model_name}' to blob storage: {str(e)}", exc_info=True)
        raise e
    
def train_model():
    """
    Utility function to train and save the model.
    This function can be called from the Azure portal or other triggers.

    Returns
        model: The trained model object.
        performance: The performance metrics of the trained model.
    """
    logging.info('train_model-> Training and saving model.')
    try:
        # Initialize DataLoader with SQL connection string
        sql_connection_string = get_sql_connection_string()
        data_loader = DataLoader(sql_connection_string=sql_connection_string)
        data = data_loader.load_from_database()
        if data:
            logging.info("train_model-> Data downloaded successfully.")
        
        else:
            logging.error("train_model-> Failed to download data.")
            return

        processor = DataProcessor()
        X_train, X_test, y_train, y_test = processor.process_data(data) 
        logging.info("train_model->Data processed successfully.")
        # Train the model
        logging.info("train_model->Training the model...")
        model = LinRegModel()
        performance =model.train(X_train, X_test, y_train, y_test)
        logging.info("train_model->Model trained successfully.")
        # Create model package with metadata
        logging.info("train_model->Saving model to blob storage...")

        return model,performance,len(X_train)
    except Exception as e:
        logging.error(f"trai_model->Error in train_model: {str(e)}")
        return func.HttpResponse(
            json.dumps({"error": str(e)}),
            status_code=500,
            headers={"Content-Type": "application/json"}
        )
def map_db_to_csv_format(db_record):
    """
    Maps database column names back to CSV format column names.
    
    Args:
        db_record (dict): Dictionary with database column names as keys
        
    Returns:
        dict: Dictionary with CSV format column names as keys
    """
    # Mapping from database column names to CSV column names
    column_mapping = {
        'MatchDate': 'Date',
        'MatchTime': 'Time',
        'Division': 'Division',
        'HomeTeam': 'Home_team',
        'AwayTeam': 'Away_team',
        'FTR': 'Full_time_result_(H/D/A)',
        'HTR': 'Half_time_result_(H/D/A)',
        'FTHG': 'Home_goals_(FT)',
        'FTAG': 'Away_goals_(FT)',
        'HTHG': 'Home_goals_(HT)',
        'HTAG': 'Away_goals_(HT)',
        'HS': 'Home_shots',
        'AS': 'Away_shots',
        'HST': 'Home_shots_on_target',
        'AST': 'Away_shots_on_target',
        'HF': 'Home_fouls',
        'AF': 'Away_fouls',
        'HC': 'Home_corners',
        'AC': 'Away_corners',
        'HY': 'Home_yellow_cards',
        'AY': 'Away_yellow_cards',
        'HR': 'Home_red_cards',
        'AR': 'Away_red_cards',
        'AvgH': 'Avg_home_win_odds',
        'AvgD': 'Avg_draw_odds',
        'AvgA': 'Avg_away_win_odds',
        'Avg_Over_2_5': 'Avg_over_2.5_goals',
        'Avg_Under_2_5': 'Avg_under_2.5_goals',
        'AvgAHH': 'Avg_AH_home',
        'AvgAHA': 'Avg_AH_away',
        'AvgCH': 'AvgCH',
        'AvgCD': 'AvgCD',
        'AvgCA': 'AvgCA',
        'AvgC_Over_2_5': 'Avg_corners_over_2.5',
        'AvgC_Under_2_5': 'Avg_corners_under_2.5',
        'AvgCAHH': 'Avg_AH_corners_home',
        'AvgCAHA': 'Avg_AH_corners_away'
    }
    
    mapped_record = {}
    for db_col, csv_col in column_mapping.items():
        if db_col in db_record:
            value = db_record[db_col]
            # Convert date format back to DD/MM/YYYY if it's a date string
            if db_col == 'MatchDate' and value:
                try:
                    # Convert YYYY-MM-DD back to DD/MM/YYYY
                    date_obj = datetime.datetime.strptime(value, '%Y-%m-%d')
                    mapped_record[csv_col] = date_obj.strftime('%d/%m/%Y')
                except (ValueError, TypeError):
                    mapped_record[csv_col] = value
            else:
                mapped_record[csv_col] = value
    
    # Include any additional columns that don't have mappings
    for key, value in db_record.items():
        if key not in column_mapping:
            mapped_record[key] = value
    
    return mapped_record    

def get_sql_connection_string():
    """
    Retrieves the SQL connection string from environment variables.
    
    Returns:
        str: The SQL connection string.
    """
    sql_connection_string = os.environ.get("SQL_CONNECTION_STRING_ODBC")
    if not sql_connection_string:
        raise ValueError("SQL_CONNECTION_STRING_ODBC environment variable is not set.")
    return sql_connection_string





