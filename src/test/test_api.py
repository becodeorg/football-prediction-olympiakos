import requests
import json

def fetch_data_from_api():
    """
    Fetches JSON data from a specified API endpoint.
    """
    # Define the API endpoint URL
    api_url = "https://olympiakos.azurewebsites.net/api/get_datas"

    # Define any necessary headers (e.g., for Content-Type or Authorization)
    headers = {
        # "Authorization": "Bearer YOUR_API_TOKEN",
        "Content-Type": "application/json"
    }

    # Define any query parameters (not needed here, but included for completeness)
    params = {
        # "api_param_1": "example",
        # "api_param_2": 10
    }
    
    try:
        # Make the GET request to the API
        print(f"Making a GET request to: {api_url}")
        # Set a timeout for the request to avoid hanging indefinitely but put 60 seconds 
        # to be sure it has enough time to respond and load docker image
        response = requests.get(api_url, headers=headers, params=params, timeout=60)

        # Raise an exception for bad status codes (4xx or 5xx)
        response.raise_for_status()

        # Parse the JSON response
        data = response.json()
        print("Successfully fetched and parsed data!")
        
        # You can now work with the 'data' dictionary
        return data

    except requests.exceptions.HTTPError as http_err:
        print(f"HTTP error occurred: {http_err}")
    except requests.exceptions.ConnectionError as conn_err:
        print(f"Connection error occurred: {conn_err}")
    except requests.exceptions.Timeout as timeout_err:
        print(f"Timeout error occurred: {timeout_err}")
    except requests.exceptions.RequestException as req_err:
        print(f"An unexpected error occurred: {req_err}")
    except json.JSONDecodeError:
        print("Error: Could not decode JSON from response.")
        print("Response content was:", response.text)

    return None

if __name__ == "__main__":
    api_data = fetch_data_from_api()
    # If data is successfully fetched, print it
    if api_data:
        print("Data received:")
        print(json.dumps(api_data, indent=2))
        # uncomment the following lines if you want to see the data in a specific format
        # convert in a list of dictionaries if neede
        # if isinstance(api_data, list):
        #     list_of_data = [dict(data) for data in api_data]
        #     print("List of data:")
        #     print(list_of_data)