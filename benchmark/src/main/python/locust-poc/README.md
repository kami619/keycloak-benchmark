# Keycloak Load Testing Script

This locust-poc contains a load testing script for Keycloak, built using [Locust](https://locust.io/). The script simulates an authentication workflow, including login, token exchange, token refresh, and logout.

## Features

- **Load Testing**: Simulate concurrent user behavior for Keycloak authentication workflows.
- **Customizable Configuration**: Set up Keycloak server, realm, client details, and headers.
- **Data-Driven Testing**: Read user credentials from a CSV file.
- **Performance Metrics**: Collect and save performance statistics to a JSON summary file.

## Prerequisites

- Python 3.8 or later
- Locust (`pip install locust`)

## Installation

1. Navigate to the locust-poc directory:
    ```bash
    cd benchmark/src/main/python/locust-poc
    ```

2. Install dependencies:
    ```bash
    pip install -r requirements.txt
    ```

3. Prepare test data:
    - Create a CSV file named `test_data.csv` in the same directory.
    - The file should have the following format:
        ```
        username,password
        user-1,user-1-password
        user-2,user-2-password
        ```

## Configuration

Update the following parameters in the script as needed:
- `keycloak_server`: URL of the Keycloak server.
- `realm`: Name of the Keycloak realm.
- `client_id`: Client ID for authentication.
- `client_secret`: Client secret for authentication.
- `scope`: Scopes required for the application.

## Running the Script

1. Start Locust with the GUI:
    ```bash
    locust -f keycloak-load-test.py
    ```

2. Open the Locust web interface:
    - Navigate to [http://localhost:8089](http://localhost:8089).
    - Configure the number of users and spawn rate, and start the test.

Alternatively, we could just run the below command to execute it from CLI.

```bash
locust -f keycloak-load-test.py  --host <KEYCLOAK_URL> --headless -u 1 -t 3s
```
## Example Usage

The script includes a complete example workflow:
- Open the login page.
- Log in using a username and password from the CSV file.
- Exchange the authentication code for tokens.
- Refresh tokens multiple times.
- Log out from the Keycloak server.

## Collecting Results

After the test run completes:
1. Check the `result_summary.json` file for a summary of test results, including:
    - Total requests
    - Total failures
    - Average response time
    - Requests per second
    - Failures per second

## Acknowledgments

- Built with [Locust](https://locust.io/) for performance testing.
- Inspired by Keycloak's authentication workflows.
