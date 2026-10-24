#!/usr/bin/env python3
"""
Salesforce Expense & Income Terminal CLI Tool
Interactive command-line interface to manage Salesforce transactions directly from terminal.
"""

import argparse
import sys
from datetime import datetime
from salesforce_client import SalesforceClient


def print_banner():
    print("\033[1;36m" + "=" * 65 + "\033[0m")
    print("\033[1;32m  ☁️  Salesforce Expense & Income Manager - Terminal CLI\033[0m")
    print("\033[1;36m" + "=" * 65 + "\033[0m")


def show_summary(sf):
    print("\n\033[1;34m📊 Fetching Financial Summary from Salesforce...\033[0m")
    try:
        res = sf.query(
            "SELECT Type__c, Category__c, Amount__c FROM Daily_Transaction__c"
        )
        records = res.get("records", [])

        total_income = 0.0
        total_expense = 0.0
        cat_expense = {}

        for r in records:
            amt = float(r.get("Amount__c") or 0.0)
            t_type = (r.get("Type__c") or "Expense").strip().lower()
            cat = r.get("Category__c") or "Other"

            if t_type == "income":
                total_income += amt
            else:
                total_expense += amt
                cat_expense[cat] = cat_expense.get(cat, 0.0) + amt

        net_balance = total_income - total_expense

        print("\n\033[1;37m" + "-" * 50 + "\033[0m")
        print(f"  🟢 Total Income   : \033[1;32m₹{total_income:,.2f}\033[0m")
        print(f"  🔴 Total Expenses : \033[1;31m₹{total_expense:,.2f}\033[0m")
        bal_color = "\033[1;32m" if net_balance >= 0 else "\033[1;31m"
        print(f"  💰 Net Balance    : {bal_color}₹{net_balance:,.2f}\033[0m")
        print(f"  📝 Total Records  : {len(records)}")
        print("\033[1;37m" + "-" * 50 + "\033[0m")

        if cat_expense:
            print("\n  \033[1;33mTop Expense Categories:\033[0m")
            for cat, amt in sorted(cat_expense.items(), key=lambda x: x[1], reverse=True)[:5]:
                pct = (amt / total_expense * 100) if total_expense else 0
                print(f"    • {cat:<20}: ₹{amt:,.2f} ({pct:.1f}%)")
        print()
    except Exception as e:
        print(f"\033[1;31m❌ Error: {e}\033[0m")


def list_transactions(sf, limit=15):
    print(f"\n\033[1;34m📋 Fetching Latest {limit} Transactions from Salesforce...\033[0m\n")
    try:
        soql = (
            "SELECT Id, Name, Type__c, Amount__c, Category__c, "
            "Transaction_Date__c, Payment_Mode__c, Notes__c "
            "FROM Daily_Transaction__c "
            f"ORDER BY Transaction_Date__c DESC, CreatedDate DESC LIMIT {limit}"
        )
        res = sf.query(soql)
        records = res.get("records", [])

        if not records:
            print("  No transactions found.")
            return

        header = f"  {'ID':<10} {'Date':<12} {'Type':<10} {'Category':<18} {'Mode':<12} {'Amount':>12}"
        print("\033[1;37m" + header + "\033[0m")
        print("  " + "-" * 78)

        for r in records:
            t_id = r.get("Name") or "TRX"
            t_date = r.get("Transaction_Date__c") or ""
            t_type = r.get("Type__c") or "Expense"
            cat = (r.get("Category__c") or "")[:16]
            mode = (r.get("Payment_Mode__c") or "UPI")[:10]
            amt = float(r.get("Amount__c") or 0.0)

            if t_type.lower() == "income":
                type_str = "\033[1;32mIncome\033[0m"
                amt_str = f"\033[1;32m+₹{amt:,.2f}\033[0m"
            else:
                type_str = "\033[1;31mExpense\033[0m"
                amt_str = f"\033[1;31m-₹{amt:,.2f}\033[0m"

            print(f"  {t_id:<10} {t_date:<12} {type_str:<19} {cat:<18} {mode:<12} {amt_str:>21}")

        print("  " + "-" * 78)
        print(f"  Total records shown: {len(records)}\n")
    except Exception as e:
        print(f"\033[1;31m❌ Error: {e}\033[0m")


def add_transaction(sf, t_type, amount, category, date, payment_mode, notes):
    try:
        record = {
            "Type__c": t_type,
            "Amount__c": float(amount),
            "Category__c": category,
            "Transaction_Date__c": date or datetime.today().strftime("%Y-%m-%d"),
            "Payment_Mode__c": payment_mode or "UPI",
            "Notes__c": notes or "",
        }
        print(f"\n  ⏳ Syncing {t_type} of ₹{float(amount):,.2f} to Salesforce...")
        res = sf.create("Daily_Transaction__c", record)
        print(f"  \033[1;32m✅ Successfully created in Salesforce! (ID: {res.get('id')})\033[0m\n")
    except Exception as e:
        print(f"  \033[1;31m❌ Error adding record: {e}\033[0m\n")


def interactive_add(sf):
    print("\n\033[1;35m➕ Add New Transaction to Salesforce (Interactive)\033[0m")
    print("--------------------------------------------------")
    
    print("Select Type:")
    print("  1) 🔴 Expense")
    print("  2) 🟢 Income")
    choice = input("Enter choice (1/2) [default: 1]: ").strip()
    t_type = "Income" if choice == "2" else "Expense"

    while True:
        try:
            amt_input = input("Enter Amount (₹): ").strip()
            amount = float(amt_input)
            if amount > 0:
                break
            print("Amount must be greater than 0.")
        except ValueError:
            print("Please enter a valid numeric amount.")

    if t_type == "Income":
        print("Popular Categories: Salary, Freelance, Business, Investment, Bonus, Other")
        category = input("Enter Category [default: Salary]: ").strip() or "Salary"
    else:
        print("Popular Categories: Food & Dining, Rent, Groceries, Travel, Shopping, Bills, Other")
        category = input("Enter Category [default: Food & Dining]: ").strip() or "Food & Dining"

    today_str = datetime.today().strftime("%Y-%m-%d")
    t_date = input(f"Enter Date (YYYY-MM-DD) [default: {today_str}]: ").strip() or today_str

    print("Payment Modes: UPI, Cash, Debit Card, Credit Card, Net Banking")
    payment_mode = input("Enter Payment Mode [default: UPI]: ").strip() or "UPI"

    notes = input("Enter Notes / Description (optional): ").strip()

    add_transaction(sf, t_type, amount, category, t_date, payment_mode, notes)


def main():
    print_banner()
    parser = argparse.ArgumentParser(description="Salesforce Expense & Income CLI Tool")
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # summary
    subparsers.add_parser("summary", help="Show financial balance and totals")

    # list
    list_parser = subparsers.add_parser("list", help="List recent transactions")
    list_parser.add_argument("--limit", type=int, default=15, help="Number of records to show")

    # add
    add_parser = subparsers.add_parser("add", help="Add a transaction")
    add_parser.add_argument("--type", choices=["Income", "Expense"], required=True, help="Income or Expense")
    add_parser.add_argument("--amount", type=float, required=True, help="Amount in INR")
    add_parser.add_argument("--category", type=str, default="General", help="Category name")
    add_parser.add_argument("--date", type=str, default=None, help="Date (YYYY-MM-DD)")
    add_parser.add_argument("--mode", type=str, default="UPI", help="Payment mode (UPI/Cash/Card)")
    add_parser.add_argument("--notes", type=str, default="", help="Remarks")

    # interactive
    subparsers.add_parser("interactive", help="Interactive step-by-step entry")

    args = parser.parse_args()

    try:
        sf = SalesforceClient()
    except Exception as e:
        print(f"\033[1;31m❌ Could not connect to Salesforce: {e}\033[0m")
        sys.exit(1)

    if args.command == "summary":
        show_summary(sf)
    elif args.command == "list":
        list_transactions(sf, args.limit)
    elif args.command == "add":
        add_transaction(sf, args.type, args.amount, args.category, args.date, args.mode, args.notes)
    elif args.command == "interactive" or args.command is None:
        if args.command is None:
            # Default to interactive
            show_summary(sf)
            interactive_add(sf)
        else:
            interactive_add(sf)


if __name__ == "__main__":
    main()
