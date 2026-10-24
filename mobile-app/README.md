# Salesforce Mobile Expense Manager (React Native & Expo)

A modern, high-performance cross-platform mobile app built with **React Native (Expo)** and integrated directly with Salesforce REST API.

---

## Features
- **Hero Financial Dashboard**: Real-time Net Balance, Total Income & Total Expenses.
- **Salesforce Cloud Live Sync**: Direct connection to your custom object `Daily_Transaction__c`.
- **Add Record Sheet**:
  - Segmented toggle: Income vs Expense
  - Quick amount selector chips (+₹100, +₹500, +₹1,000, +₹2,000)
  - Visual category chips with custom icons (Food, Rent, Salary, Travel, Shopping, etc.)
  - Payment mode selector (UPI, Cash, Cards, Net Banking)
  - Remarks / Notes field
- **Category Spending Meters**: Visual breakdown and progress indicators for each category.
- **Recent Activities**: Interactive filter tabs (`All`, `Income`, `Expense`) with delete actions.
- **Pull-to-Refresh**: Seamless live sync from Salesforce.

---

## How to Run

### 1. In Browser (Instant Web View):
The mobile app is pre-built and running at:
👉 **[http://127.0.0.1:5050/mobile](http://127.0.0.1:5050/mobile)**

### 2. On Your Physical iPhone / Android Phone (Expo Go):
1. Install **Expo Go** from Google Play Store or Apple App Store on your phone.
2. In terminal, navigate to the `mobile-app` directory:
   ```bash
   cd mobile-app
   npx expo start
   ```
3. Scan the QR code with your phone camera (iOS) or Expo Go app (Android).
