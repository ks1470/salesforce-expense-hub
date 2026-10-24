@isTest
private class DailyTransactionTriggerTest {

    @isTest
    static void testValidExpenseInsert() {
        Daily_Transaction__c tr = new Daily_Transaction__c(
            Type__c = 'Expense',
            Amount__c = 1500,
            Category__c = 'Groceries',
            Transaction_Date__c = Date.today(),
            Payment_Mode__c = 'UPI',
            Notes__c = 'Weekly market'
        );

        Test.startTest();
        insert tr;
        Test.stopTest();

        Daily_Transaction__c inserted = [SELECT Id, Name, Amount__c FROM Daily_Transaction__c WHERE Id = :tr.Id];
        System.assertNotEquals(null, inserted.Id);
        System.assertEquals(1500, inserted.Amount__c);
    }

    @isTest
    static void testHighExpenseAlertTask() {
        Daily_Transaction__c highExp = new Daily_Transaction__c(
            Type__c = 'Expense',
            Amount__c = 8500,
            Category__c = 'Shopping',
            Transaction_Date__c = Date.today(),
            Payment_Mode__c = 'Card'
        );

        Test.startTest();
        insert highExp;
        Test.stopTest();

        List<Task> createdTasks = [SELECT Id, Subject, Priority FROM Task WHERE Subject LIKE '%High Expense Alert%'];
        System.assert(createdTasks.size() >= 1, 'High expense should trigger an alert Task');
        System.assertEquals('High', createdTasks[0].Priority);
    }

    @isTest
    static void testNegativeAmountValidation() {
        Daily_Transaction__c invalid = new Daily_Transaction__c(
            Type__c = 'Expense',
            Amount__c = -100,
            Category__c = 'Other'
        );

        Test.startTest();
        try {
            insert invalid;
            System.assert(false, 'Expected DMLException for negative amount');
        } catch (DmlException e) {
            System.assert(e.getMessage().contains('greater than ₹0'));
        }
        Test.stopTest();
    }

    @isTest
    static void testFutureDateValidation() {
        Daily_Transaction__c futureTr = new Daily_Transaction__c(
            Type__c = 'Income',
            Amount__c = 5000,
            Category__c = 'Salary',
            Transaction_Date__c = Date.today().addDays(5)
        );

        Test.startTest();
        try {
            insert futureTr;
            System.assert(false, 'Expected DMLException for future date');
        } catch (DmlException e) {
            System.assert(e.getMessage().contains('cannot be in the future'));
        }
        Test.stopTest();
    }
}
