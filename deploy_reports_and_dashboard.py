#!/usr/bin/env python3
"""
Deploy Salesforce Standard Report and Dashboard for Daily Expense & Income
"""

import base64
import json
import urllib.request
import urllib.error
from salesforce_client import SalesforceClient

sf = SalesforceClient()

print("Connected to Salesforce Org:", sf.instance_url)

# Step 1: Ensure Daily_Transaction__c has enableReports = true
print("\n1. Enabling Reports on Daily_Transaction__c object...")
enable_reports_soap = f"""<?xml version="1.0" encoding="utf-8"?>
<soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/" xmlns:met="http://soap.sforce.com/2006/04/metadata">
  <soapenv:Header>
    <met:SessionHeader>
      <met:sessionId>{sf.access_token}</met:sessionId>
    </met:SessionHeader>
  </soapenv:Header>
  <soapenv:Body>
    <met:updateMetadata>
      <met:metadata xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:type="met:CustomObject">
        <met:fullName>Daily_Transaction__c</met:fullName>
        <met:label>Daily Transaction</met:label>
        <met:pluralLabel>Daily Transactions</met:pluralLabel>
        <met:nameField>
          <met:displayFormat>TRX-{{0000}}</met:displayFormat>
          <met:label>Transaction ID</met:label>
          <met:type>AutoNumber</met:type>
        </met:nameField>
        <met:deploymentStatus>Deployed</met:deploymentStatus>
        <met:sharingModel>ReadWrite</met:sharingModel>
        <met:enableReports>true</met:enableReports>
      </met:metadata>
    </met:updateMetadata>
  </soapenv:Body>
</soapenv:Envelope>"""

req = urllib.request.Request(
    f"{sf.instance_url}/services/Soap/m/60.0",
    data=enable_reports_soap.encode("utf-8"),
    headers={"Content-Type": "text/xml; charset=utf-8", "SOAPAction": '""'},
    method="POST",
)
try:
    with urllib.request.urlopen(req) as resp:
        res_xml = resp.read().decode("utf-8")
        print("enableReports update response:", "Success" if "true" in res_xml else res_xml)
except urllib.error.HTTPError as e:
    print("HTTPError updating object:", e.code, e.read().decode("utf-8"))

# Step 2: Deploy Standard Report
# We save in unfiled$public/Daily_Expense_Income_Report
print("\n2. Deploying Standard Report: Daily_Expense_Income_Report...")

# Report XML definition
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
    <description>Summary of Daily Income and Expenses categorized and totaled.</description>
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
    <name>Daily Expense &amp; Income Report</name>
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

create_report_soap = f"""<?xml version="1.0" encoding="utf-8"?>
<soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/" xmlns:met="http://soap.sforce.com/2006/04/metadata">
  <soapenv:Header>
    <met:SessionHeader>
      <met:sessionId>{sf.access_token}</met:sessionId>
    </met:SessionHeader>
  </soapenv:Header>
  <soapenv:Body>
    <met:createMetadata>
      <met:metadata xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:type="met:Report">
        <met:fullName>unfiled$public/Daily_Expense_Income_Report</met:fullName>
        <met:name>Daily Expense and Income Report</met:name>
        <met:description>Complete summary and category breakdown of all income and expenses</met:description>
        <met:format>Summary</met:format>
        <met:reportType>CustomEntity$Daily_Transaction__c</met:reportType>
        <met:scope>organization</met:scope>
        <met:showDetails>true</met:showDetails>
        <met:showSubTotals>true</met:showSubTotals>
        <met:columns>
          <met:field>CUST_NAME</met:field>
        </met:columns>
        <met:columns>
          <met:field>Daily_Transaction__c.Transaction_Date__c</met:field>
        </met:columns>
        <met:columns>
          <met:field>Daily_Transaction__c.Payment_Mode__c</met:field>
        </met:columns>
        <met:columns>
          <met:aggregateTypes>Sum</met:aggregateTypes>
          <met:field>Daily_Transaction__c.Amount__c</met:field>
        </met:columns>
        <met:groupingsDown>
          <met:dateGranularity>Day</met:dateGranularity>
          <met:field>Daily_Transaction__c.Type__c</met:field>
          <met:sortOrder>Asc</sortOrder>
        </met:groupingsDown>
        <met:groupingsDown>
          <met:dateGranularity>Day</met:dateGranularity>
          <met:field>Daily_Transaction__c.Category__c</met:field>
          <met:sortOrder>Asc</met:sortOrder>
        </met:groupingsDown>
        <met:timeFrameFilter>
          <met:dateColumn>Daily_Transaction__c.Transaction_Date__c</met:dateColumn>
          <met:interval>INTERVAL_CUSTOM</met:interval>
        </met:timeFrameFilter>
      </met:metadata>
    </met:createMetadata>
  </soapenv:Body>
</soapenv:Envelope>"""

req2 = urllib.request.Request(
    f"{sf.instance_url}/services/Soap/m/60.0",
    data=create_report_soap.encode("utf-8"),
    headers={"Content-Type": "text/xml; charset=utf-8", "SOAPAction": '""'},
    method="POST",
)
try:
    with urllib.request.urlopen(req2) as resp:
        res2 = resp.read().decode("utf-8")
        print("Report Create Response:", "Success" if "success>true" in res2 else res2)
except urllib.error.HTTPError as e:
    print("HTTPError creating report:", e.code, e.read().decode("utf-8"))

# Step 3: Deploy Standard Lightning Dashboard
print("\n3. Deploying Standard Dashboard: Daily_Expense_Income_Dashboard...")
create_dashboard_soap = f"""<?xml version="1.0" encoding="utf-8"?>
<soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/" xmlns:met="http://soap.sforce.com/2006/04/metadata">
  <soapenv:Header>
    <met:SessionHeader>
      <met:sessionId>{sf.access_token}</met:sessionId>
    </met:SessionHeader>
  </soapenv:Header>
  <soapenv:Body>
    <met:createMetadata>
      <met:metadata xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:type="met:Dashboard">
        <met:fullName>unfiled$public/Daily_Expense_Income_Dashboard</met:fullName>
        <met:title>Daily Expense &amp; Income Dashboard</met:title>
        <met:description>Executive dashboard tracking daily income, expenses, and category trends</met:description>
        <met:isGridLayout>true</met:isGridLayout>
        <met:leftSection>
          <met:columnSize>Medium</met:columnSize>
          <met:components>
            <met:autoselectColumnsFromReport>true</met:autoselectColumnsFromReport>
            <met:chartAxisRange>Auto</met:chartAxisRange>
            <met:componentType>Donut</met:componentType>
            <met:displayUnits>Auto</met:displayUnits>
            <met:header>Expenses by Category</met:header>
            <met:report>unfiled$public/Daily_Expense_Income_Report</met:report>
            <met:showPercentage>true</met:showPercentage>
            <met:showValues>true</met:showValues>
          </met:components>
        </met:leftSection>
        <met:middleSection>
          <met:columnSize>Medium</met:columnSize>
          <met:components>
            <met:autoselectColumnsFromReport>true</met:autoselectColumnsFromReport>
            <met:chartAxisRange>Auto</met:chartAxisRange>
            <met:componentType>Column</met:componentType>
            <met:displayUnits>Auto</met:displayUnits>
            <met:header>Income vs Expenses</met:header>
            <met:report>unfiled$public/Daily_Expense_Income_Report</met:report>
            <met:showValues>true</met:showValues>
          </met:components>
        </met:middleSection>
        <met:rightSection>
          <met:columnSize>Medium</met:columnSize>
          <met:components>
            <met:autoselectColumnsFromReport>true</met:autoselectColumnsFromReport>
            <met:componentType>Metric</met:componentType>
            <met:displayUnits>Auto</met:displayUnits>
            <met:header>Total Transactions</met:header>
            <met:metricLabel>Total Records</met:metricLabel>
            <met:report>unfiled$public/Daily_Expense_Income_Report</met:report>
          </met:components>
        </met:rightSection>
      </met:metadata>
    </met:createMetadata>
  </soapenv:Body>
</soapenv:Envelope>"""

req3 = urllib.request.Request(
    f"{sf.instance_url}/services/Soap/m/60.0",
    data=create_dashboard_soap.encode("utf-8"),
    headers={"Content-Type": "text/xml; charset=utf-8", "SOAPAction": '""'},
    method="POST",
)
try:
    with urllib.request.urlopen(req3) as resp:
        res3 = resp.read().decode("utf-8")
        print("Dashboard Create Response:", "Success" if "success>true" in res3 else res3)
except urllib.error.HTTPError as e:
    print("HTTPError creating dashboard:", e.code, e.read().decode("utf-8"))

print("\nDeployment complete.")
