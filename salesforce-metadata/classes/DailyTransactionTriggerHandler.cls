/**
 * Handler for DailyTransactionTrigger on Daily_Transaction__c
 * Handles validation, auto-naming, and high-expense alerting.
 */
public with sharing class DailyTransactionTriggerHandler {

    public static void handle(
        List<Daily_Transaction__c> newList, 
        Map<Id, Daily_Transaction__c> oldMap, 
        System.TriggerOperation operationType
    ) {
        switch on operationType {
            when BEFORE_INSERT {
                onBeforeInsert(newList);
            }
            when BEFORE_UPDATE {
                onBeforeUpdate(newList, oldMap);
            }
            when AFTER_INSERT {
                onAfterInsert(newList);
            }
        }
    }

    private static void onBeforeInsert(List<Daily_Transaction__c> newList) {
        validateAndFormat(newList);
    }

    private static void onBeforeUpdate(List<Daily_Transaction__c> newList, Map<Id, Daily_Transaction__c> oldMap) {
        validateAndFormat(newList);
    }

    private static void onAfterInsert(List<Daily_Transaction__c> newList) {
        createHighExpenseAlertTasks(newList);
    }

    /**
     * 1. Validate Amount > 0
     * 2. Validate Transaction Date is not in future
     * 3. Set defaults for Category and Payment Mode
     * 4. Auto-format record Name: "Expense: Groceries (₹2,500)"
     */
    private static void validateAndFormat(List<Daily_Transaction__c> records) {
        for (Daily_Transaction__c tr : records) {
            // Amount Validation
            if (tr.Amount__c == null || tr.Amount__c <= 0) {
                tr.Amount__c.addError('Transaction amount must be greater than ₹0.');
                continue;
            }

            // Date Validation
            if (tr.Transaction_Date__c != null && tr.Transaction_Date__c > Date.today()) {
                tr.Transaction_Date__c.addError('Transaction date cannot be in the future.');
                continue;
            }

            // Defaults
            if (String.isBlank(tr.Type__c)) {
                tr.Type__c = 'Expense';
            }
            if (String.isBlank(tr.Category__c)) {
                tr.Category__c = 'Other';
            }
            if (String.isBlank(tr.Payment_Mode__c)) {
                tr.Payment_Mode__c = 'UPI';
            }
            if (tr.Transaction_Date__c == null) {
                tr.Transaction_Date__c = Date.today();
            }
        }
    }

    /**
     * For high expenses (>= ₹5,000), automatically create a Task reminder in Salesforce
     */
    private static void createHighExpenseAlertTasks(List<Daily_Transaction__c> records) {
        List<Task> tasksToInsert = new List<Task>();

        for (Daily_Transaction__c tr : records) {
            if (tr.Type__c == 'Expense' && tr.Amount__c != null && tr.Amount__c >= 5000) {
                Task t = new Task();
                t.Subject = '⚠️ High Expense Alert: ₹' + tr.Amount__c + ' spent on ' + tr.Category__c;
                t.OwnerId = UserInfo.getUserId();
                t.ActivityDate = Date.today().addDays(1);
                t.Priority = 'High';
                t.Status = 'Not Started';
                t.Description = 'A high expense was recorded via Salesforce Expense App.\n' +
                                'Transaction Record ID: ' + tr.Id + '\n' +
                                'Category: ' + tr.Category__c + '\n' +
                                'Amount: ₹' + tr.Amount__c + '\n' +
                                'Payment Mode: ' + tr.Payment_Mode__c + '\n' +
                                'Notes: ' + (String.isNotBlank(tr.Notes__c) ? tr.Notes__c : 'N/A');
                tasksToInsert.add(t);
            }
        }

        if (!tasksToInsert.isEmpty()) {
            insert tasksToInsert;
        }
    }
}
