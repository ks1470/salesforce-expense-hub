#!/usr/bin/env python3
"""
Deploy Apex Trigger, Handler, and Test Class to Salesforce via Metadata API zip deployment
"""

import io
import zipfile
import base64
import time
import urllib.request
import urllib.error
import os
from salesforce_client import SalesforceClient

def deploy_trigger():
    print("🚀 Connecting to Salesforce Org...")
    sf = SalesforceClient()

    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as z:
        # 1. package.xml
        package_xml = """<?xml version="1.0" encoding="UTF-8"?>
<Package xmlns="http://soap.sforce.com/2006/04/metadata">
    <types>
        <members>DailyTransactionTriggerHandler</members>
        <members>DailyTransactionTriggerTest</members>
        <name>ApexClass</name>
    </types>
    <types>
        <members>DailyTransactionTrigger</members>
        <name>ApexTrigger</name>
    </types>
    <version>60.0</version>
</Package>"""
        z.writestr("package.xml", package_xml)

        base_dir = os.path.dirname(os.path.abspath(__file__))
        meta_dir = os.path.join(base_dir, "salesforce-metadata")

        # Classes
        with open(os.path.join(meta_dir, "classes", "DailyTransactionTriggerHandler.cls"), "r") as f:
            z.writestr("classes/DailyTransactionTriggerHandler.cls", f.read())
        with open(os.path.join(meta_dir, "classes", "DailyTransactionTriggerHandler.cls-meta.xml"), "r") as f:
            z.writestr("classes/DailyTransactionTriggerHandler.cls-meta.xml", f.read())

        with open(os.path.join(meta_dir, "classes", "DailyTransactionTriggerTest.cls"), "r") as f:
            z.writestr("classes/DailyTransactionTriggerTest.cls", f.read())
        with open(os.path.join(meta_dir, "classes", "DailyTransactionTriggerTest.cls-meta.xml"), "r") as f:
            z.writestr("classes/DailyTransactionTriggerTest.cls-meta.xml", f.read())

        # Trigger
        with open(os.path.join(meta_dir, "triggers", "DailyTransactionTrigger.trigger"), "r") as f:
            z.writestr("triggers/DailyTransactionTrigger.trigger", f.read())
        with open(os.path.join(meta_dir, "triggers", "DailyTransactionTrigger.trigger-meta.xml"), "r") as f:
            z.writestr("triggers/DailyTransactionTrigger.trigger-meta.xml", f.read())

    zip_bytes = zip_buffer.getvalue()
    zip_b64 = base64.b64encode(zip_bytes).decode("utf-8")
    print(f"📦 Created deployment package ({len(zip_bytes)} bytes)")

    soap_body = f"""<?xml version="1.0" encoding="utf-8"?>
<soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/"
                  xmlns:met="http://soap.sforce.com/2006/04/metadata">
    <soapenv:Header>
        <met:SessionHeader>
            <met:sessionId>{sf.access_token}</met:sessionId>
        </met:SessionHeader>
    </soapenv:Header>
    <soapenv:Body>
        <met:deploy>
            <met:ZipFile>{zip_b64}</met:ZipFile>
            <met:DeployOptions>
                <met:allowMissingFiles>false</met:allowMissingFiles>
                <met:autoUpdatePackage>false</met:autoUpdatePackage>
                <met:checkOnly>false</met:checkOnly>
                <met:ignoreWarnings>true</met:ignoreWarnings>
                <met:performRetrieve>false</met:performRetrieve>
                <met:purgeOnDelete>false</met:purgeOnDelete>
                <met:rollbackOnError>true</met:rollbackOnError>
                <met:singlePackage>true</met:singlePackage>
                <met:testLevel>RunSpecifiedTests</met:testLevel>
                <met:runTests>DailyTransactionTriggerTest</met:runTests>
            </met:DeployOptions>
        </met:deploy>
    </soapenv:Body>
</soapenv:Envelope>"""

    metadata_url = f"{sf.instance_url}/services/Soap/m/60.0"
    headers = {
        "Content-Type": "text/xml; charset=UTF-8",
        "SOAPAction": '""',
    }

    req = urllib.request.Request(metadata_url, data=soap_body.encode("utf-8"), headers=headers, method="POST")
    print("⏳ Initiating deployment via Salesforce Metadata API...")
    try:
        with urllib.request.urlopen(req) as resp:
            resp_xml = resp.read().decode("utf-8")
    except urllib.error.HTTPError as e:
        print("❌ Deployment request failed:", e.read().decode("utf-8"))
        return

    import re
    match = re.search(r"<id>([^<]+)</id>", resp_xml)
    if not match:
        print("❌ Could not get deploy ID from response:", resp_xml)
        return

    deploy_id = match.group(1)
    print(f"✅ Deployment queued! Async Deploy ID: {deploy_id}")

    # Polling status
    for i in range(20):
        time.sleep(3)
        check_soap = f"""<?xml version="1.0" encoding="utf-8"?>
<soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/"
                  xmlns:met="http://soap.sforce.com/2006/04/metadata">
    <soapenv:Header>
        <met:SessionHeader>
            <met:sessionId>{sf.access_token}</met:sessionId>
        </met:SessionHeader>
    </soapenv:Header>
    <soapenv:Body>
        <met:checkDeployStatus>
            <met:asyncProcessId>{deploy_id}</met:asyncProcessId>
            <met:includeDetails>true</met:includeDetails>
        </met:checkDeployStatus>
    </soapenv:Body>
</soapenv:Envelope>"""

        poll_req = urllib.request.Request(metadata_url, data=check_soap.encode("utf-8"), headers=headers, method="POST")
        with urllib.request.urlopen(poll_req) as p_resp:
            p_xml = p_resp.read().decode("utf-8")

        status_m = re.search(r"<status>([^<]+)</status>", p_xml)
        done_m = re.search(r"<done>([^<]+)</done>", p_xml)
        status = status_m.group(1) if status_m else "Unknown"
        done = done_m.group(1) == "true" if done_m else False

        print(f"   [{i+1}] Status: {status}")
        if done:
            if status == "Succeeded":
                print("\n🎉 SUCCESS! Apex Trigger, Handler, and Test Class deployed successfully!")
            else:
                print(f"\n❌ Deployment finished with status: {status}")
                errors = re.findall(r"<problem>([^<]+)</problem>", p_xml)
                for err in errors:
                    print(f"   • {err}")
            break

if __name__ == "__main__":
    deploy_trigger()
