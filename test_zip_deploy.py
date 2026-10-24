#!/usr/bin/env python3
"""
Deploy Standard Report and Dashboard via Metadata API zip deployment
"""

import io
import zipfile
import base64
import time
import urllib.request
import urllib.error
from salesforce_client import SalesforceClient

sf = SalesforceClient()

# Create in-memory zip
zip_buffer = io.BytesIO()
with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as z:
    # 1. package.xml
    package_xml = """<?xml version="1.0" encoding="UTF-8"?>
<Package xmlns="http://soap.sforce.com/2006/04/metadata">
    <types>
        <members>Finance_Reports</members>
        <members>Finance_Reports/Daily_Expense_and_Income_Report</members>
        <name>Report</name>
    </types>
    <types>
        <members>Finance_Dashboards</members>
        <members>Finance_Dashboards/Daily_Expense_Income_Dashboard</members>
        <name>Dashboard</name>
    </types>
    <version>60.0</version>
</Package>"""
    z.writestr("package.xml", package_xml)

    # 2. Report Folder metadata
    report_folder_meta = """<?xml version="1.0" encoding="UTF-8"?>
<ReportFolder xmlns="http://soap.sforce.com/2006/04/metadata">
    <name>Finance Reports</name>
</ReportFolder>"""
    z.writestr("reports/Finance_Reports-meta.xml", report_folder_meta)

    # 3. Report definition
    report_xml = """<?xml version="1.0" encoding="UTF-8"?>
<Report xmlns="http://soap.sforce.com/2006/04/metadata">
    <chart>
        <backgroundColor1>#FFFFFF</backgroundColor1>
        <backgroundColor2>#FFFFFF</backgroundColor2>
        <backgroundFadeDir>Diagonal</backgroundFadeDir>
        <chartSummaries>
            <aggregate>Sum</aggregate>
            <axisBinding>y</axisBinding>
            <column>Daily_Transaction__c.Amount__c</column>
        </chartSummaries>
        <chartType>Donut</chartType>
        <enableHoverLabels>true</enableHoverLabels>
        <expandOthers>false</expandOthers>
        <groupingColumn>Daily_Transaction__c.Category__c</groupingColumn>
        <legendPosition>Right</legendPosition>
        <location>CHART_BOTTOM</location>
        <showAxisLabels>false</showAxisLabels>
        <showPercentage>true</showPercentage>
        <showTotal>true</showTotal>
        <showValues>true</showValues>
        <size>Medium</size>
        <summaryAxisRange>Auto</summaryAxisRange>
        <textColor>#000000</textColor>
        <textSize>12</textSize>
        <title>Expenses by Category</title>
        <titleColor>#000000</titleColor>
        <titleSize>18</titleSize>
    </chart>
    <columns>
        <field>CUST_NAME</field>
    </columns>
    <columns>
        <field>Daily_Transaction__c.Transaction_Date__c</field>
    </columns>
    <columns>
        <field>Daily_Transaction__c.Payment_Mode__c</field>
    </columns>
    <columns>
        <field>Daily_Transaction__c.Notes__c</field>
    </columns>
    <columns>
        <aggregateTypes>Sum</aggregateTypes>
        <field>Daily_Transaction__c.Amount__c</field>
    </columns>
    <description>Daily Expense and Income Summary by Type and Category</description>
    <format>Summary</format>
    <groupingsDown>
        <dateGranularity>Day</dateGranularity>
        <field>Daily_Transaction__c.Type__c</field>
        <sortOrder>Asc</sortOrder>
    </groupingsDown>
    <groupingsDown>
        <dateGranularity>Day</dateGranularity>
        <field>Daily_Transaction__c.Category__c</field>
        <sortOrder>Asc</sortOrder>
    </groupingsDown>
    <name>Daily Expense and Income Report</name>
    <params>
        <name>co</name>
        <value>1</value>
    </params>
    <reportType>CustomEntity$Daily_Transaction__c</reportType>
    <scope>organization</scope>
    <showDetails>true</showDetails>
    <showSubTotals>true</showSubTotals>
    <timeFrameFilter>
        <dateColumn>Daily_Transaction__c.Transaction_Date__c</dateColumn>
        <interval>INTERVAL_CUSTOM</interval>
    </timeFrameFilter>
</Report>"""
    z.writestr("reports/Finance_Reports/Daily_Expense_and_Income_Report.report", report_xml)

    # 4. Dashboard Folder metadata
    dashboard_folder_meta = """<?xml version="1.0" encoding="UTF-8"?>
<DashboardFolder xmlns="http://soap.sforce.com/2006/04/metadata">
    <name>Finance Dashboards</name>
</DashboardFolder>"""
    z.writestr("dashboards/Finance_Dashboards-meta.xml", dashboard_folder_meta)

    # 5. Dashboard definition
    dashboard_xml = """<?xml version="1.0" encoding="UTF-8"?>
<Dashboard xmlns="http://soap.sforce.com/2006/04/metadata">
    <backgroundEndColor>#FFFFFF</backgroundEndColor>
    <backgroundFadeDirection>Diagonal</backgroundFadeDirection>
    <backgroundStartColor>#FFFFFF</backgroundStartColor>
    <dashboardType>SpecifiedUser</dashboardType>
    <isGridLayout>false</isGridLayout>
    <leftSection>
        <columnSize>Medium</columnSize>
        <components>
            <autoselectColumnsFromReport>true</autoselectColumnsFromReport>
            <chartAxisRange>Auto</chartAxisRange>
            <componentType>Donut</componentType>
            <displayUnits>Auto</displayUnits>
            <header>Expenses by Category</header>
            <report>Finance_Reports/Daily_Expense_and_Income_Report</report>
            <showPercentage>true</showPercentage>
            <showValues>true</showValues>
            <sortBy>RowLabelAscending</sortBy>
        </components>
    </leftSection>
    <middleSection>
        <columnSize>Medium</columnSize>
        <components>
            <autoselectColumnsFromReport>true</autoselectColumnsFromReport>
            <chartAxisRange>Auto</chartAxisRange>
            <componentType>Column</componentType>
            <displayUnits>Auto</displayUnits>
            <header>Income vs Expenses</header>
            <report>Finance_Reports/Daily_Expense_and_Income_Report</report>
            <showValues>true</showValues>
            <sortBy>RowLabelAscending</sortBy>
        </components>
    </middleSection>
    <rightSection>
        <columnSize>Medium</columnSize>
        <components>
            <autoselectColumnsFromReport>true</autoselectColumnsFromReport>
            <chartAxisRange>Auto</chartAxisRange>
            <componentType>Bar</componentType>
            <displayUnits>Auto</displayUnits>
            <header>Transactions Summary</header>
            <report>Finance_Reports/Daily_Expense_and_Income_Report</report>
            <showValues>true</showValues>
            <sortBy>RowLabelAscending</sortBy>
        </components>
    </rightSection>
    <runningUser>kuldeep.jangid.142000.915014ae9b32@agentforce.com</runningUser>
    <textColor>#000000</textColor>
    <title>Daily Expense and Income Dashboard</title>
    <titleColor>#000000</titleColor>
    <titleSize>12</titleSize>
</Dashboard>"""
    z.writestr("dashboards/Finance_Dashboards/Daily_Expense_Income_Dashboard.dashboard", dashboard_xml)

zip_bytes = zip_buffer.getvalue()
b64_zip = base64.b64encode(zip_bytes).decode("utf-8")

deploy_soap = f"""<?xml version="1.0" encoding="utf-8"?>
<soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/" xmlns:met="http://soap.sforce.com/2006/04/metadata">
  <soapenv:Header>
    <met:SessionHeader>
      <met:sessionId>{sf.access_token}</met:sessionId>
    </met:SessionHeader>
  </soapenv:Header>
  <soapenv:Body>
    <met:deploy>
      <met:ZipFile>{b64_zip}</met:ZipFile>
      <met:DeployOptions>
        <met:allowMissingFiles>false</met:allowMissingFiles>
        <met:autoUpdatePackage>false</met:autoUpdatePackage>
        <met:checkOnly>false</met:checkOnly>
        <met:ignoreWarnings>true</met:ignoreWarnings>
        <met:performRetrieve>false</met:performRetrieve>
        <met:purgeOnDelete>false</met:purgeOnDelete>
        <met:rollbackOnError>true</met:rollbackOnError>
        <met:singlePackage>true</met:singlePackage>
        <met:testLevel>NoTestRun</met:testLevel>
      </met:DeployOptions>
    </met:deploy>
  </soapenv:Body>
</soapenv:Envelope>"""

req = urllib.request.Request(
    f"{sf.instance_url}/services/Soap/m/60.0",
    data=deploy_soap.encode("utf-8"),
    headers={"Content-Type": "text/xml; charset=utf-8", "SOAPAction": '""'},
    method="POST",
)

try:
    with urllib.request.urlopen(req) as resp:
        res = resp.read().decode("utf-8")
        print("Deploy Response:", res)
        # Extract AsyncProcessId
        import re
        match = re.search(r"<id>([a-zA-Z0-9]{18})</id>", res)
        if match:
            async_id = match.group(1)
            print("Deploy Async ID:", async_id)
            
            # Check deploy status
            for _ in range(15):
                time.sleep(2)
                check_soap = f"""<?xml version="1.0" encoding="utf-8"?>
<soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/" xmlns:met="http://soap.sforce.com/2006/04/metadata">
  <soapenv:Header>
    <met:SessionHeader>
      <met:sessionId>{sf.access_token}</met:sessionId>
    </met:SessionHeader>
  </soapenv:Header>
  <soapenv:Body>
    <met:checkDeployStatus>
      <met:asyncProcessId>{async_id}</met:asyncProcessId>
      <met:includeDetails>true</met:includeDetails>
    </met:checkDeployStatus>
  </soapenv:Body>
</soapenv:Envelope>"""
                req_check = urllib.request.Request(
                    f"{sf.instance_url}/services/Soap/m/60.0",
                    data=check_soap.encode("utf-8"),
                    headers={"Content-Type": "text/xml; charset=utf-8", "SOAPAction": '""'},
                    method="POST",
                )
                with urllib.request.urlopen(req_check) as c_resp:
                    c_res = c_resp.read().decode("utf-8")
                    if "<done>true</done>" in c_res:
                        print("Check Status Result:")
                        if "<success>true</success>" in c_res:
                            print("🎉 DEPLOYMENT SUCCEEDED!")
                        else:
                            print("❌ Deployment Failed Details:")
                            # Print failure messages
                            for m in re.findall(r"<problem>(.*?)</problem>", c_res):
                                print(" -", m)
                        break
                    else:
                        print("Deploy in progress...")
except urllib.error.HTTPError as e:
    print("HTTPError:", e.code, e.read().decode("utf-8"))
