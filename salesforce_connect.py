#!/usr/bin/env python3
"""
Salesforce OAuth 2.0 Client Credentials Flow Connector
Works with standard Python 3 (zero external dependencies required).
"""

import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request


def load_env(env_path=".env"):
    """Simple .env file loader that does not require python-dotenv."""
    if not os.path.exists(env_path):
        return
    with open(env_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, val = line.split("=", 1)
            key = key.strip()
            val = val.strip().strip('"').strip("'")
            if key not in os.environ:
                os.environ[key] = val


def get_access_token(my_domain_url, client_id, client_secret):
    """
    Requests an OAuth 2.0 access token using the Client Credentials Flow.
    POST https://<MyDomainName>.my.salesforce.com/services/oauth2/token
    """
    token_url = f"{my_domain_url.rstrip('/')}/services/oauth2/token"
    
    payload = {
        "grant_type": "client_credentials",
        "client_id": client_id,
        "client_secret": client_secret,
    }
    
    encoded_data = urllib.parse.urlencode(payload).encode("utf-8")
    req = urllib.request.Request(
        token_url,
        data=encoded_data,
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        method="POST",
    )
    
    try:
        with urllib.request.urlopen(req) as response:
            res_body = response.read().decode("utf-8")
            return json.loads(res_body)
    except urllib.error.HTTPError as e:
        error_body = e.read().decode("utf-8")
        try:
            err_json = json.loads(error_body)
            error_code = err_json.get("error", "Unknown")
            error_desc = err_json.get("error_description", error_body)
        except Exception:
            error_code = f"HTTP {e.code}"
            error_desc = error_body
        
        print("\n❌ Salesforce OAuth Error:")
        print(f"   Code: {error_code}")
        print(f"   Description: {error_desc}\n")
        print("💡 Troubleshooting Tips for Client Credentials Flow:")
        if "invalid_client" in error_code.lower():
            print("   - Verify that your Consumer Key and Consumer Secret are correct.")
        elif "invalid_grant" in error_code.lower():
            print("   - In Salesforce Setup -> App Manager -> Your Connected App:")
            print("     1. Ensure 'Enable Client Credentials Flow' is CHECKED.")
            print("     2. In 'Manage Connected Apps' -> click 'Edit Policies':")
            print("     3. Set 'Client Credentials Flow' -> 'Run As' to an active user/admin.")
        elif "ip" in error_desc.lower():
            print("   - Set IP Relaxation to 'Relax IP restrictions' in Connected App policies.")
        sys.exit(1)
    except urllib.error.URLError as e:
        print(f"\n❌ Network / DNS Error connecting to {my_domain_url}: {e.reason}")
        print("   Make sure the domain URL is reachable and formatted correctly.")
        print("   Example: https://yourcompany.my.salesforce.com")
        sys.exit(1)


def test_salesforce_api(instance_url, access_token):
    """Makes a test REST API call to verify connection."""
    api_url = f"{instance_url.rstrip('/')}/services/data/v60.0/sobjects/"
    req = urllib.request.Request(
        api_url,
        headers={
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
        },
        method="GET",
    )
    
    try:
        with urllib.request.urlopen(req) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            sobjects = data.get("sobjects", [])
            return sobjects
    except Exception as e:
        print(f"⚠️ Warning: Token acquired, but test REST API call failed: {e}")
        return None


def main():
    load_env()

    client_id = os.getenv("SALESFORCE_CLIENT_ID")
    client_secret = os.getenv("SALESFORCE_CLIENT_SECRET")
    my_domain_url = os.getenv("SALESFORCE_MY_DOMAIN_URL")

    if not client_id or not client_secret:
        print("❌ Error: SALESFORCE_CLIENT_ID or SALESFORCE_CLIENT_SECRET missing in .env")
        sys.exit(1)

    if not my_domain_url or not my_domain_url.strip():
        print("=" * 60)
        print("⚠️  SALESFORCE_MY_DOMAIN_URL is not set!")
        print("=" * 60)
        print("To connect via the Client Credentials Flow, Salesforce requires your")
        print("Org's My Domain URL (login.salesforce.com cannot be used for this flow).")
        print("\nExamples:")
        print("  - Developer / Production: https://yourcompany.my.salesforce.com")
        print("  - Sandbox:               https://yourcompany.sandbox.my.salesforce.com")
        print("  - Trailhead Playground:  https://resourceful-badger-xxxxxx-dev-ed.trailblaze.my.salesforce.com\n")
        
        my_domain_url = input("Enter your Salesforce My Domain URL (or press Enter to exit): ").strip()
        if not my_domain_url:
            print("Exiting. Please update SALESFORCE_MY_DOMAIN_URL in .env when ready.")
            sys.exit(0)

    # Ensure protocol is present
    if not my_domain_url.startswith("http://") and not my_domain_url.startswith("https://"):
        my_domain_url = f"https://{my_domain_url}"

    print(f"\n Connecting to Salesforce: {my_domain_url}...")
    token_response = get_access_token(my_domain_url, client_id, client_secret)

    access_token = token_response.get("access_token")
    instance_url = token_response.get("instance_url", my_domain_url)
    token_type = token_response.get("token_type", "Bearer")

    print("\n✅ Successfully connected to Salesforce Org!")
    print("-" * 50)
    print(f" Instance URL : {instance_url}")
    print(f" Token Type   : {token_type}")
    print(f" Access Token : {access_token[:15]}...{access_token[-10:]}")
    print("-" * 50)

    print("\n Running test query on Salesforce REST API (listing objects)...")
    sobjects = test_salesforce_api(instance_url, access_token)
    if sobjects:
        names = [obj.get("name") for obj in sobjects[:5]]
        print(f" Found {len(sobjects)} SObjects in your org.")
        print(f" Sample SObjects: {', '.join(names)}...")
        print("\n Integration ready to use!")


if __name__ == "__main__":
    main()
