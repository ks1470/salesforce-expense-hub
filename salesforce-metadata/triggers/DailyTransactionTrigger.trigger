trigger DailyTransactionTrigger on Daily_Transaction__c (before insert, before update, after insert) {
    DailyTransactionTriggerHandler.handle(Trigger.new, Trigger.oldMap, Trigger.operationType);
}
