#!/usr/bin/env python3
"""
Salesforce REST API Client
Provides simple helpers for SOQL queries and CRUD operations.
"""

import json
import os
import urllib.error
import urllib.parse
import urllib.request
from salesforce_connect import load_env, get_access_token


class SalesforceClient:
    def __init__(self, api_version="v60.0"):
        load_env()
        self.client_id = os.getenv("SALESFORCE_CLIENT_ID")
        self.client_secret = os.getenv("SALESFORCE_CLIENT_SECRET")
        self.my_domain_url = os.getenv("SALESFORCE_MY_DOMAIN_URL")
        self.api_version = api_version

        if not self.client_id or not self.client_secret or not self.my_domain_url:
            raise ValueError("Missing Salesforce credentials or domain in .env")

        token_data = get_access_token(self.my_domain_url, self.client_id, self.client_secret)
        self.access_token = token_data["access_token"]
        self.instance_url = token_data.get("instance_url", self.my_domain_url).rstrip("/")
        self.base_url = f"{self.instance_url}/services/data/{self.api_version}"

    def _request(self, endpoint, method="GET", data=None):
        url = f"{self.base_url}{endpoint}" if endpoint.startswith("/") else f"{self.base_url}/{endpoint}"
        encoded_data = json.dumps(data).encode("utf-8") if data is not None else None

        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json",
        }

        req = urllib.request.Request(url, data=encoded_data, headers=headers, method=method)
        try:
            with urllib.request.urlopen(req) as response:
                if response.status == 204:  # No Content
                    return True
                return json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            err_msg = e.read().decode("utf-8")
            raise RuntimeError(f"Salesforce API Error ({e.code}): {err_msg}")

    def query(self, soql_query):
        """Execute a SOQL query."""
        params = urllib.parse.urlencode({"q": soql_query})
        return self._request(f"/query?{params}")

    def get(self, sobject, record_id, fields=None):
        """Retrieve a single record by ID."""
        endpoint = f"/sobjects/{sobject}/{record_id}"
        if fields:
            params = urllib.parse.urlencode({"fields": ",".join(fields)})
            endpoint = f"{endpoint}?{params}"
        return self._request(endpoint)

    def create(self, sobject, data):
        """Create a new record."""
        return self._request(f"/sobjects/{sobject}", method="POST", data=data)

    def update(self, sobject, record_id, data):
        """Update an existing record."""
        return self._request(f"/sobjects/{sobject}/{record_id}", method="PATCH", data=data)

    def delete(self, sobject, record_id):
        """Delete a record."""
        return self._request(f"/sobjects/{sobject}/{record_id}", method="DELETE")


if __name__ == "__main__":
    # Test query
    sf = SalesforceClient()
    print(" Running sample SOQL query on Account object...")
    try:
        res = sf.query("SELECT Id, Name FROM Account LIMIT 5")
        print(f" Total records found: {res.get('totalSize', 0)}")
        for rec in res.get("records", []):
            print(f"  • {rec.get('Name')} (ID: {rec.get('Id')})")
    except Exception as e:
        print(f"Query error: {e}")
