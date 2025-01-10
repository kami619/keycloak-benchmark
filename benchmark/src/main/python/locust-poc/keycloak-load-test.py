from locust import HttpUser, task, between, events
import random
import re
import urllib3
import warnings
import csv
import json
import os

# Suppress InsecureRequestWarning globally
warnings.filterwarnings("ignore", category=urllib3.exceptions.InsecureRequestWarning)


class KeycloakScenarioBuilder(HttpUser):
    wait_time = between(1, 2)

    # Configuration
    keycloak_server = "https://a185621011ac277a7.dualstack.awsglobalaccelerator.com"
    realm = "realm-0"
    client_id = "client-0"
    client_secret = "client-0-secret"
    scope = "openid profile"
    ui_headers = {
        "Accept" : "text/html,application/xhtml+xml,application/xml",
        "Accept-Encoding" : "gzip, deflate",
        "Accept-Language" : "en-US,en;q=0.5",
        "User-Agent" : "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.8; rv:16.0) Gecko/20100101 Firefox/16.0"
    }
    results_summary = {}

    def on_start(self):
        self.session_data = {}

    @task
    def authentication_workflow(self):
        csvfile = open(os.path.join(os.path.dirname(__file__), "test_data.csv"))
        iter = csv.reader(csvfile)

        try:
            username, password = next(iter)
        except StopIteration:
            csvfile.seek(0, 0)
            username, password = next(iter)
        self.open_login_page()
        self.login_username_password(username, password)
        self.exchange_code()
        self.repeat_refresh()
        self.logout()

    def open_login_page(self):
        login_endpoint = f"{self.keycloak_server}/realms/{self.realm}/protocol/openid-connect/auth"
        params = {
            "response_type": "code",
            "client_id": self.client_id,
            "scope": self.scope,
            "redirect_uri": f"{self.keycloak_server}/realms/{self.realm}/account",
            "state": str(random.randint(1, 100000))
        }
        self.client.request_name="OPEN_LOGIN_PAGE"
        with self.client.get(login_endpoint,verify=False, params=params, headers=self.ui_headers, catch_response=True) as response:
            if response.status_code == 200:
                match = re.search(r'action="([^"]*)"', response.text)
                if match:
                    self.session_data["login_form_uri"] = match.group(1).replace("&amp;", "&")
                else:
                    response.failure("Login form URI not found in the response")
            else:
                response.failure("Failed to open login page")

    def login_username_password(self, username, password):
        login_form_uri = self.session_data.get("login_form_uri")
        if not login_form_uri:
            return
        payload = {
            "username": username,
            "password": password,
            "login": "Log in"
        }
        self.client.request_name="LOGIN_WITH_PASSWORD"
        with self.client.post(login_form_uri, verify=False, data=payload, headers=self.ui_headers, catch_response=True, allow_redirects=False) as response:
            #for key, value in response.headers.items():
            #    print(f"{key}: {value}")
            if response.status_code == 302:
                self.session_data["code"] = response.headers.get("Location", "").split("code=")[-1]
            else:
                response.failure("Failed to log in with username and password")

    def exchange_code(self):
        code = self.session_data.get("code")
        if not code:
            return

        token_endpoint = f"{self.keycloak_server}/realms/{self.realm}/protocol/openid-connect/token"
        payload = {
            "grant_type": "authorization_code",
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "redirect_uri": f"{self.keycloak_server}/realms/{self.realm}/account",
            "code": code
        }
        self.client.request_name="EXCHANGE_CODE"
        with self.client.post(token_endpoint, verify=False, data=payload, headers=self.ui_headers, catch_response=True) as response:
            #print(f"Exchange code request response is : {response.status_code}")
            if response.status_code == 200:
                tokens = response.json()
                #print(f"Token response is : {tokens}")
                self.session_data.update(tokens)
            else:
                response.failure("Failed to exchange code for tokens")

    def repeat_refresh(self):
        refresh_token = self.session_data.get("refresh_token")
        if not refresh_token:
            return

        token_endpoint = f"{self.keycloak_server}/realms/{self.realm}/protocol/openid-connect/token"
        for _ in range(3):  # Example: repeat refresh 3 times
            payload = {
                "grant_type": "refresh_token",
                "refresh_token": refresh_token,
                "client_id": self.client_id,
                "client_secret": self.client_secret
            }
            self.client.request_name="REFRESH_TOKEN"
            with self.client.post(token_endpoint, verify=False, data=payload, headers=self.ui_headers, catch_response=True) as response:
                if response.status_code == 200:
                    tokens = response.json()
                    self.session_data.update(tokens)
                else:
                    response.failure("Failed to refresh token")

    def logout(self):
        id_token = self.session_data.get("id_token")
        if not id_token:
            return

        logout_endpoint = f"{self.keycloak_server}/realms/{self.realm}/protocol/openid-connect/logout"
        params = {
            "id_token_hint": id_token,
            "post_logout_redirect_uri": f"{self.keycloak_server}/realms/{self.realm}/account"
        }
        self.client.request_name="LOGOUT"
        with self.client.get(logout_endpoint, verify=False, params=params, catch_response=True) as response:
            if response.status_code != 200:
                response.failure("Failed to log out")

    #This is an example implementation,
    # on how we can use event listeners to capture the run data.
    results_summary = {}

    @events.test_stop.add_listener
    def on_test_stop(environment, **kwargs):
        # Use the global results_summary variable
        global results_summary

        # Collect results into the dictionary
        results_summary = {
            "total_requests": environment.stats.total.num_requests,
            "total_failures": environment.stats.total.num_failures,
            "average_response_time": environment.stats.total.avg_response_time,
            "requests_per_second": environment.stats.total.total_rps,
            "failures_per_second": environment.stats.total.fail_ratio,
        }

        # Save the summary to a JSON file
        with open("result_summary.json", "w") as f:
            json.dump(results_summary, f, indent=4)

        print("JSON summary saved: result_summary.json")
