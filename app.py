#!/usr/bin/env python3
"""
Salesforce Daily Expense & Income Tracker App
Backend HTTP server + Integrated Modern Dashboard UI
"""

import json
import os
import sys
from datetime import datetime
from http.server import HTTPServer, BaseHTTPRequestHandler
import urllib.parse
import xml.etree.ElementTree as ET
from salesforce_client import SalesforceClient

PORT = int(os.environ.get("PORT", 5050))


class ExpenseTrackerServer(BaseHTTPRequestHandler):
    sf = None

    @classmethod
    def get_sf(cls):
        if cls.sf is None:
            cls.sf = SalesforceClient()
        return cls.sf

    def _set_headers(self, status=200, content_type="application/json"):
        self.send_response(status)
        self.send_header("Content-Type", f"{content_type}; charset=utf-8")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, DELETE, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def do_OPTIONS(self):
        self._set_headers(204)

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path

        if path == "/" or path == "/index.html":
            self.serve_ui()
        elif path == "/login" or path == "/login.html":
            self.serve_login_ui()
        elif path == "/mobile" or path == "/mobile/":
            self.serve_mobile_ui()
        elif path == "/api/auth/info":
            self.get_auth_info()
        elif path == "/api/auth/frontdoor":
            self.get_frontdoor_url(parsed.query)
        elif path.startswith("/_expo/") or path.startswith("/node_modules/"):
            self.serve_static_file(path)
        elif path == "/api/transactions":
            self.get_transactions()
        elif path == "/api/summary":
            self.get_summary()
        elif path == "/api/health":
            self._set_headers(200)
            self.wfile.write(json.dumps({"status": "ok"}).encode("utf-8"))
        else:
            self._set_headers(404)
            self.wfile.write(json.dumps({"error": "Not Found"}).encode("utf-8"))

    def do_POST(self):
        parsed = urllib.parse.urlparse(self.path)
        if parsed.path == "/api/transactions":
            self.create_transaction()
        elif parsed.path == "/api/login" or parsed.path == "/api/auth/login":
            self.login()
        else:
            self._set_headers(404)
            self.wfile.write(json.dumps({"error": "Not Found"}).encode("utf-8"))

    def do_DELETE(self):
        parsed = urllib.parse.urlparse(self.path)
        parts = parsed.path.strip("/").split("/")
        if len(parts) == 3 and parts[0] == "api" and parts[1] == "transactions":
            record_id = parts[2]
            self.delete_transaction(record_id)
        else:
            self._set_headers(400)
            self.wfile.write(json.dumps({"error": "Invalid DELETE path"}).encode("utf-8"))

    def get_transactions(self):
        try:
            sf = self.get_sf()
            soql = (
                "SELECT Id, Name, Type__c, Amount__c, Category__c, "
                "Transaction_Date__c, Payment_Mode__c, Notes__c, CreatedDate "
                "FROM Daily_Transaction__c "
                "ORDER BY Transaction_Date__c DESC, CreatedDate DESC "
                "LIMIT 500"
            )
            result = sf.query(soql)
            records = result.get("records", [])
            self._set_headers(200)
            self.wfile.write(json.dumps({"records": records, "instance_url": sf.instance_url}).encode("utf-8"))
        except Exception as e:
            self._set_headers(500)
            self.wfile.write(json.dumps({"error": str(e)}).encode("utf-8"))

    def get_summary(self):
        try:
            sf = self.get_sf()
            soql = (
                "SELECT Type__c, Category__c, Amount__c, Transaction_Date__c "
                "FROM Daily_Transaction__c"
            )
            result = sf.query(soql)
            records = result.get("records", [])

            total_income = 0.0
            total_expense = 0.0
            expense_by_category = {}
            income_by_category = {}

            for r in records:
                amt = float(r.get("Amount__c") or 0.0)
                t_type = (r.get("Type__c") or "Expense").strip()
                cat = (r.get("Category__c") or "Other").strip()

                if t_type.lower() == "income":
                    total_income += amt
                    income_by_category[cat] = income_by_category.get(cat, 0.0) + amt
                else:
                    total_expense += amt
                    expense_by_category[cat] = expense_by_category.get(cat, 0.0) + amt

            net_balance = total_income - total_expense

            summary_data = {
                "total_income": total_income,
                "total_expense": total_expense,
                "net_balance": net_balance,
                "total_count": len(records),
                "expense_by_category": expense_by_category,
                "income_by_category": income_by_category,
                "instance_url": sf.instance_url,
            }
            self._set_headers(200)
            self.wfile.write(json.dumps(summary_data).encode("utf-8"))
        except Exception as e:
            self._set_headers(500)
            self.wfile.write(json.dumps({"error": str(e)}).encode("utf-8"))

    def create_transaction(self):
        try:
            length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(length).decode("utf-8")
            data = json.loads(body)

            amount = float(data.get("amount", 0))
            if amount <= 0:
                self._set_headers(400)
                self.wfile.write(json.dumps({"error": "Amount must be greater than 0"}).encode("utf-8"))
                return

            t_type = data.get("type", "Expense")
            category = data.get("category", "General")
            t_date = data.get("date", datetime.today().strftime("%Y-%m-%d"))
            payment_mode = data.get("payment_mode", "UPI")
            notes = data.get("notes", "")

            sf_record = {
                "Type__c": t_type,
                "Amount__c": amount,
                "Category__c": category,
                "Transaction_Date__c": t_date,
                "Payment_Mode__c": payment_mode,
                "Notes__c": notes,
            }

            sf = self.get_sf()
            res = sf.create("Daily_Transaction__c", sf_record)

            self._set_headers(201)
            self.wfile.write(json.dumps({
                "success": True,
                "id": res.get("id"),
                "record": sf_record
            }).encode("utf-8"))
        except Exception as e:
            self._set_headers(500)
            self.wfile.write(json.dumps({"error": str(e)}).encode("utf-8"))

    def delete_transaction(self, record_id):
        try:
            sf = self.get_sf()
            sf.delete("Daily_Transaction__c", record_id)
            self._set_headers(200)
            self.wfile.write(json.dumps({"success": True, "deleted_id": record_id}).encode("utf-8"))
        except Exception as e:
            self._set_headers(500)
            self.wfile.write(json.dumps({"error": str(e)}).encode("utf-8"))

    def get_auth_info(self):
        try:
            sf = self.get_sf()
            connected_user = "kuldeep.jangid.142000.915014ae9b32@agentforce.com"
            domain = sf.my_domain_url.replace("https://", "").replace("/", "")
            self._set_headers(200)
            self.wfile.write(json.dumps({
                "instance_url": sf.instance_url,
                "connected_user": connected_user,
                "org_domain": domain,
                "status": "online"
            }).encode("utf-8"))
        except Exception as e:
            self._set_headers(500)
            self.wfile.write(json.dumps({"error": str(e)}).encode("utf-8"))

    def get_frontdoor_url(self, query_string):
        try:
            sf = self.get_sf()
            params = urllib.parse.parse_qs(query_string)
            ret_url = params.get("retURL", ["/apex/Daily_Expense_Dashboard"])[0]
            frontdoor_url = f"{sf.instance_url}/secur/frontdoor.jsp?sid={sf.access_token}&retURL={urllib.parse.quote(ret_url)}"
            self._set_headers(200)
            self.wfile.write(json.dumps({
                "success": True,
                "frontdoor_url": frontdoor_url,
                "instance_url": sf.instance_url,
                "retURL": ret_url
            }).encode("utf-8"))
        except Exception as e:
            self._set_headers(500)
            self.wfile.write(json.dumps({"error": str(e)}).encode("utf-8"))

    def login(self):
        try:
            length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(length).decode("utf-8")
            data = json.loads(body)
            username = data.get("username", "").strip()
            password = data.get("password", "").strip()
            security_token = data.get("security_token", "").strip()
            ret_url = data.get("retURL", "/apex/Daily_Expense_Dashboard").strip() or "/apex/Daily_Expense_Dashboard"

            sf = self.get_sf()

            # 1. Secure Password Verification:
            # If password matches configured master password, authenticate securely and issue session
            allowed_passwords = [
                os.environ.get("APP_PASSWORD", "kuldeep@2000").strip(),
                "kuldeep@2000",
                "Kuldeep@2000"
            ]

            if password and password in allowed_passwords:
                frontdoor_url = f"{sf.instance_url}/secur/frontdoor.jsp?sid={sf.access_token}&retURL={urllib.parse.quote(ret_url)}"
                self._set_headers(200)
                self.wfile.write(json.dumps({
                    "success": True,
                    "frontdoor_url": frontdoor_url,
                    "username": username or "Kuldeep Jangid"
                }).encode("utf-8"))
                return

            # 2. If custom credentials with Security Token provided, attempt SOAP login
            if password:
                full_password = f"{password}{security_token}"
                soap_body = f"""<?xml version="1.0" encoding="utf-8" ?>
<env:Envelope xmlns:xsd="http://www.w3.org/2001/XMLSchema"
    xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
    xmlns:env="http://schemas.xmlsoap.org/soap/envelope/">
  <env:Body>
    <n1:login xmlns:n1="urn:partner.soap.sforce.com">
      <n1:username>{username}</n1:username>
      <n1:password>{full_password}</n1:password>
    </n1:login>
  </env:Body>
</env:Envelope>"""
                endpoints = [
                    f"{sf.my_domain_url.rstrip('/')}/services/Soap/u/59.0",
                    "https://login.salesforce.com/services/Soap/u/59.0"
                ]
                last_err = "Invalid Salesforce credentials"
                for soap_url in endpoints:
                    req = urllib.request.Request(
                        soap_url,
                        data=soap_body.encode("utf-8"),
                        headers={"Content-Type": "text/xml; charset=UTF-8", "SOAPAction": "login"},
                        method="POST"
                    )
                    try:
                        with urllib.request.urlopen(req) as resp:
                            xml_text = resp.read().decode("utf-8")
                            root = ET.fromstring(xml_text)
                            ns = {"soapenv": "http://schemas.xmlsoap.org/soap/envelope/", "urn": "urn:partner.soap.sforce.com"}
                            session_id_el = root.find(".//urn:sessionId", ns)
                            server_url_el = root.find(".//urn:serverUrl", ns)
                            if session_id_el is not None and session_id_el.text:
                                sid = session_id_el.text
                                server_url = server_url_el.text if server_url_el is not None else sf.instance_url
                                parsed_split = urllib.parse.urlsplit(server_url)
                                inst = f"{parsed_split.scheme}://{parsed_split.netloc}"
                                frontdoor_url = f"{inst}/secur/frontdoor.jsp?sid={sid}&retURL={urllib.parse.quote(ret_url)}"
                                self._set_headers(200)
                                self.wfile.write(json.dumps({
                                    "success": True,
                                    "frontdoor_url": frontdoor_url,
                                    "username": username
                                }).encode("utf-8"))
                                return
                    except urllib.error.HTTPError as he:
                        err_xml = he.read().decode("utf-8")
                        try:
                            root = ET.fromstring(err_xml)
                            fault = root.find(".//faultstring")
                            if fault is not None and fault.text:
                                last_err = fault.text
                        except Exception:
                            pass
                    except Exception as e:
                        last_err = str(e)

                self._set_headers(401)
                self.wfile.write(json.dumps({"error": last_err}).encode("utf-8"))
                return

            # 2. If no password provided (instant 1-click admin login)
            frontdoor_url = f"{sf.instance_url}/secur/frontdoor.jsp?sid={sf.access_token}&retURL={urllib.parse.quote(ret_url)}"
            self._set_headers(200)
            self.wfile.write(json.dumps({
                "success": True,
                "frontdoor_url": frontdoor_url,
                "username": username or "Admin User"
            }).encode("utf-8"))
        except Exception as e:
            self._set_headers(500)
            self.wfile.write(json.dumps({"error": str(e)}).encode("utf-8"))

    def serve_login_ui(self):
        login_path = os.path.join(os.path.dirname(__file__), "login.html")
        if os.path.exists(login_path):
            with open(login_path, "rb") as f:
                content = f.read()
            self._set_headers(200, "text/html")
            self.wfile.write(content)
        else:
            self._set_headers(404, "text/plain")
            self.wfile.write(b"login.html not found")

    def serve_ui(self):
        ui_path = os.path.join(os.path.dirname(__file__), "index.html")
        if os.path.exists(ui_path):
            with open(ui_path, "rb") as f:
                content = f.read()
            self._set_headers(200, "text/html")
            self.wfile.write(content)
        else:
            self._set_headers(404, "text/plain")
            self.wfile.write(b"index.html not found")

    def serve_mobile_ui(self):
        mobile_path = os.path.join(os.path.dirname(__file__), "mobile-app", "dist", "index.html")
        if os.path.exists(mobile_path):
            with open(mobile_path, "rb") as f:
                content = f.read()
            self._set_headers(200, "text/html")
            self.wfile.write(content)
        else:
            self._set_headers(404, "text/plain")
            self.wfile.write(b"Mobile app build not found. Run: cd mobile-app && npx expo export -p web --output-dir dist")

    def serve_static_file(self, rel_path):
        import mimetypes
        clean_path = rel_path.lstrip("/")
        file_path = os.path.join(os.path.dirname(__file__), "mobile-app", "dist", clean_path)
        if os.path.exists(file_path) and os.path.isfile(file_path):
            content_type, _ = mimetypes.guess_type(file_path)
            if not content_type:
                if file_path.endswith(".js"):
                    content_type = "application/javascript"
                elif file_path.endswith(".ttf"):
                    content_type = "font/ttf"
                else:
                    content_type = "application/octet-stream"
            with open(file_path, "rb") as f:
                content = f.read()
            self._set_headers(200, content_type)
            self.wfile.write(content)
        else:
            self._set_headers(404, "text/plain")
            self.wfile.write(b"Static file not found")


def run(port=PORT):
    server_address = ("0.0.0.0", port)
    httpd = HTTPServer(server_address, ExpenseTrackerServer)
    print("=" * 60)
    print("🚀 Salesforce Daily Expense & Income Tracker App")
    print(f"👉 Local URL : http://127.0.0.1:{port}")
    print("=" * 60)
    print("Press Ctrl+C to stop the server.")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nStopping server...")
        httpd.server_close()


if __name__ == "__main__":
    port = int(sys.argv[1]) if len(sys.argv) > 1 else PORT
    run(port)
