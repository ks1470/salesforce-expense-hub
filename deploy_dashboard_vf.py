import base64
import urllib.request
from salesforce_client import SalesforceClient

sf = SalesforceClient()

vf_content = '''<apex:page standardStylesheets="false" showHeader="false" sidebar="false" docType="html-5.0">
<html>
<head>
    <title>Daily Expense and Income Dashboard</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;600;700;800&amp;display=swap" rel="stylesheet"/>
    <style>body { font-family: 'Plus Jakarta Sans', sans-serif; }</style>
</head>
<body class="bg-slate-50 text-slate-800 p-6">
    <div class="max-w-7xl mx-auto space-y-6">
        <div class="flex items-center justify-between bg-white p-5 rounded-2xl shadow-sm border border-slate-200">
            <div>
                <h1 class="text-xl font-black text-slate-900">Daily Transactions Dashboard</h1>
                <p class="text-xs text-slate-500">Live data directly inside your Salesforce Org</p>
            </div>
            <button onclick="location.reload()" class="px-4 py-2 bg-indigo-600 text-white text-xs font-bold rounded-xl shadow hover:bg-indigo-700">Refresh Data</button>
        </div>

        <div class="grid grid-cols-1 md:grid-cols-3 gap-5">
            <div class="bg-white p-5 rounded-2xl border border-slate-200 shadow-sm">
                <span class="text-xs font-bold text-emerald-600 uppercase">Total Income</span>
                <div id="totIncome" class="text-2xl font-black text-slate-900 mt-2">Loading...</div>
            </div>
            <div class="bg-white p-5 rounded-2xl border border-slate-200 shadow-sm">
                <span class="text-xs font-bold text-rose-600 uppercase">Total Expenses</span>
                <div id="totExpense" class="text-2xl font-black text-slate-900 mt-2">Loading...</div>
            </div>
            <div class="bg-white p-5 rounded-2xl border border-slate-200 shadow-sm">
                <span class="text-xs font-bold text-indigo-600 uppercase">Net Balance</span>
                <div id="netBalance" class="text-2xl font-black text-indigo-600 mt-2">Loading...</div>
            </div>
        </div>

        <div class="grid grid-cols-1 md:grid-cols-2 gap-5">
            <div class="bg-white p-5 rounded-2xl border border-slate-200 shadow-sm">
                <h3 class="text-xs font-bold text-slate-700 uppercase mb-4">Income vs Expense</h3>
                <div style="height: 240px;"><canvas id="barChart"></canvas></div>
            </div>
            <div class="bg-white p-5 rounded-2xl border border-slate-200 shadow-sm">
                <h3 class="text-xs font-bold text-slate-700 uppercase mb-4">Expenses by Category</h3>
                <div style="height: 240px;"><canvas id="donutChart"></canvas></div>
            </div>
        </div>

        <div class="bg-white rounded-2xl border border-slate-200 shadow-sm overflow-hidden">
            <div class="p-5 border-b border-slate-100 flex justify-between items-center">
                <h2 class="text-base font-bold text-slate-900">All Transactions (Live)</h2>
                <a href="/lightning/o/Daily_Transaction__c/list?filterName=All" target="_blank" class="text-xs text-blue-600 font-bold hover:underline">View in List View →</a>
            </div>
            <div class="overflow-x-auto">
                <table class="w-full text-left text-xs">
                    <thead class="bg-slate-50 text-slate-500 uppercase font-semibold border-b">
                        <tr>
                            <th class="px-5 py-3">ID / Date</th>
                            <th class="px-5 py-3">Type</th>
                            <th class="px-5 py-3">Category</th>
                            <th class="px-5 py-3">Payment Mode</th>
                            <th class="px-5 py-3 text-right">Amount (₹)</th>
                        </tr>
                    </thead>
                    <tbody id="recordsBody" class="divide-y font-medium">
                        <tr><td colspan="5" class="p-6 text-center text-slate-400">Loading records...</td></tr>
                    </tbody>
                </table>
            </div>
        </div>
    </div>

    <script>
        const sessionId = '{!$Api.Session_ID}';
        async function fetchRecords() {
            try {
                const query = encodeURIComponent('SELECT Id, Name, Type__c, Amount__c, Category__c, Transaction_Date__c, Payment_Mode__c FROM Daily_Transaction__c ORDER BY Transaction_Date__c DESC, CreatedDate DESC');
                const res = await fetch('/services/data/v60.0/query?q=' + query, {
                    headers: { 'Authorization': 'Bearer ' + sessionId }
                });
                const data = await res.json();
                const records = data.records || [];

                let income = 0, expense = 0;
                const catExpense = {};

                records.forEach(r => {
                    const amt = parseFloat(r.Amount__c || 0);
                    const type = (r.Type__c || '').toLowerCase();
                    const cat = r.Category__c || 'Other';
                    if (type === 'income') {
                        income += amt;
                    } else {
                        expense += amt;
                        catExpense[cat] = (catExpense[cat] || 0) + amt;
                    }
                });

                document.getElementById('totIncome').innerText = '₹' + income.toLocaleString('en-IN', {minimumFractionDigits: 2});
                document.getElementById('totExpense').innerText = '₹' + expense.toLocaleString('en-IN', {minimumFractionDigits: 2});
                const bal = income - expense;
                document.getElementById('netBalance').innerText = '₹' + bal.toLocaleString('en-IN', {minimumFractionDigits: 2});

                // Render Charts
                new Chart(document.getElementById('barChart'), {
                    type: 'bar',
                    data: {
                        labels: ['Income', 'Expense'],
                        datasets: [{ data: [income, expense], backgroundColor: ['#10b981', '#f43f5e'], borderRadius: 8 }]
                    },
                    options: { responsive: true, maintainAspectRatio: false, plugins: { legend: { display: false } } }
                });

                new Chart(document.getElementById('donutChart'), {
                    type: 'doughnut',
                    data: {
                        labels: Object.keys(catExpense),
                        datasets: [{ data: Object.values(catExpense), backgroundColor: ['#f43f5e', '#f59e0b', '#3b82f6', '#8b5cf6', '#10b981'] }]
                    },
                    options: { responsive: true, maintainAspectRatio: false }
                });

                // Render Table
                const tbody = document.getElementById('recordsBody');
                if (!records.length) {
                    tbody.innerHTML = '<tr><td colspan="5" class="p-6 text-center text-slate-400">No records found. Add an entry to get started!</td></tr>';
                    return;
                }
                tbody.innerHTML = records.map(r => {
                    const isInc = (r.Type__c || '').toLowerCase() === 'income';
                    return `<tr>
                        <td class="px-5 py-3 font-bold"><a href="/${r.Id}" target="_blank" class="text-blue-600 hover:underline">${r.Name}</a><div class="text-slate-400 font-normal">${r.Transaction_Date__c}</div></td>
                        <td class="px-5 py-3">${isInc ? '<span class="text-emerald-700 bg-emerald-100 px-2 py-0.5 rounded font-bold">Income</span>' : '<span class="text-rose-700 bg-rose-100 px-2 py-0.5 rounded font-bold">Expense</span>'}</td>
                        <td class="px-5 py-3 font-semibold">${r.Category__c || '-'}</td>
                        <td class="px-5 py-3 text-slate-500">${r.Payment_Mode__c || 'UPI'}</td>
                        <td class="px-5 py-3 text-right font-extrabold ${isInc ? 'text-emerald-600' : 'text-slate-900'}">${isInc ? '+' : '-'}₹${parseFloat(r.Amount__c||0).toLocaleString('en-IN', {minimumFractionDigits: 2})}</td>
                    </tr>`;
                }).join('');
            } catch(e) {
                console.error(e);
            }
        }
        fetchRecords();
    </script>
</body>
</html>
</apex:page>'''

b64 = base64.b64encode(vf_content.encode("utf-8")).decode("utf-8")

soap_body = f"""<?xml version="1.0" encoding="utf-8"?>
<soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/" xmlns:met="http://soap.sforce.com/2006/04/metadata">
  <soapenv:Header>
    <met:SessionHeader>
      <met:sessionId>{sf.access_token}</met:sessionId>
    </met:SessionHeader>
  </soapenv:Header>
  <soapenv:Body>
    <met:createMetadata>
      <met:metadata xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:type="met:ApexPage">
        <met:fullName>Daily_Expense_Dashboard</met:fullName>
        <met:apiVersion>60.0</met:apiVersion>
        <met:label>Daily Expense Dashboard</met:label>
        <met:content>{b64}</met:content>
      </met:metadata>
    </met:createMetadata>
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
        print("ApexPage Deploy Response:", resp.read().decode("utf-8"))
except urllib.error.HTTPError as e:
    print("Error:", e.code, e.read().decode("utf-8"))
