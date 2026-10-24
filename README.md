# Salesforce Daily Expense & Income Tracker

Integrated application to track daily Income & Expenses and sync them directly to your Salesforce Org via REST API.

---

## What was built:

1. **Salesforce Custom Object (`Daily_Transaction__c`)**:
   - `Type__c`: Income / Expense
   - `Amount__c`: Currency
   - `Category__c`: Text (Food, Rent, Salary, Shopping, Bills, etc.)
   - `Transaction_Date__c`: Date
   - `Payment_Mode__c`: UPI, Cash, Card, Net Banking
   - `Notes__c`: Description / Remarks
   - Permission set & Field-Level Security configured automatically.

2. **Web Application & Dashboard (`app.py` & `index.html`)**:
   - Clean, modern responsive interface.
   - Real-time KPI metrics: Total Income, Total Expenses, Net Savings, Transaction Count.
   - Interactive Charts (Income vs Expense comparison, Category-wise breakdown).
   - Form to add Income / Expense entries with single-click sync to Salesforce.
   - Live transaction history table with delete and direct links to Salesforce records.

---

## How to Run:

Start the application server:
```bash
python3 app.py
```

Then open your browser at:
👉 **http://127.0.0.1:5050**
