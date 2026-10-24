#!/usr/bin/env python3
"""
Deploy Redesigned Executive Visualforce Dashboard to Salesforce
"""

import base64
import urllib.request
import urllib.error
import os
import re
from salesforce_client import SalesforceClient

def deploy():
    print("🚀 Connecting to Salesforce Org...")
    sf = SalesforceClient()

    vf_path = os.path.join(os.path.dirname(__file__), "salesforce-metadata", "pages", "Daily_Expense_Dashboard.page")
    with open(vf_path, "r", encoding="utf-8") as f:
        vf_content = f.read()

    b64_content = base64.b64encode(vf_content.encode("utf-8")).decode("utf-8")
    print(f"📄 Read Visualforce content ({len(vf_content)} characters)")

    # Try updateMetadata first since the page already exists in the Org
    for action in ["updateMetadata", "createMetadata"]:
        soap_body = f"""<?xml version="1.0" encoding="utf-8"?>
<soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/" xmlns:met="http://soap.sforce.com/2006/04/metadata">
  <soapenv:Header>
    <met:SessionHeader>
      <met:sessionId>{sf.access_token}</met:sessionId>
    </met:SessionHeader>
  </soapenv:Header>
  <soapenv:Body>
    <met:{action}>
      <met:metadata xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:type="met:ApexPage">
        <met:fullName>Daily_Expense_Dashboard</met:fullName>
        <met:apiVersion>60.0</met:apiVersion>
        <met:label>Daily Expense Dashboard</met:label>
        <met:content>{b64_content}</met:content>
      </met:metadata>
    </met:{action}>
  </soapenv:Body>
</soapenv:Envelope>"""

        req = urllib.request.Request(
            f"{sf.instance_url}/services/Soap/m/60.0",
            data=soap_body.encode("utf-8"),
            headers={"Content-Type": "text/xml; charset=utf-8", "SOAPAction": '""'},
            method="POST",
        )

        try:
            with urllib.request.urlopen(req) as resp:
                resp_text = resp.read().decode("utf-8")
                if "<success>true</success>" in resp_text:
                    print(f"🎉 SUCCESS! Daily_Expense_Dashboard updated in Salesforce via {action}!")
                    return True
                elif "<success>false</success>" in resp_text:
                    err_match = re.search(r"<message>([^<]+)</message>", resp_text)
                    msg = err_match.group(1) if err_match else resp_text
                    print(f"Notice from {action}: {msg}")
                    continue
                else:
                    print(f"Response: {resp_text[:300]}")
        except urllib.error.HTTPError as e:
            print(f"HTTP Error on {action}:", e.code, e.read().decode("utf-8"))

    return False

if __name__ == "__main__":
    deploy()
