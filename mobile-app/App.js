import React, { useState, useEffect, useCallback } from 'react';
import {
  StyleSheet,
  Text,
  View,
  ScrollView,
  TouchableOpacity,
  TextInput,
  Modal,
  ActivityIndicator,
  RefreshControl,
  SafeAreaView,
  Platform,
  Alert,
} from 'react-native';
import { StatusBar } from 'expo-status-bar';
import { Ionicons } from '@expo/vector-icons';
import { salesforceApi } from './services/salesforceApi';

const CATEGORIES = {
  Expense: [
    { id: 'Food & Dining', name: 'Food & Dining', icon: 'restaurant', color: '#f43f5e' },
    { id: 'Rent & Housing', name: 'Rent & Housing', icon: 'home', color: '#8b5cf6' },
    { id: 'Groceries', name: 'Groceries', icon: 'cart', color: '#10b981' },
    { id: 'Travel & Fuel', name: 'Travel & Fuel', icon: 'car', color: '#f59e0b' },
    { id: 'Utilities & Bills', name: 'Utilities & Bills', icon: 'flash', color: '#3b82f6' },
    { id: 'Shopping', name: 'Shopping', icon: 'bag-handle', color: '#ec4899' },
    { id: 'Healthcare', name: 'Healthcare', icon: 'medkit', color: '#14b8a6' },
    { id: 'Entertainment', name: 'Entertainment', icon: 'film', color: '#6366f1' },
    { id: 'Other', name: 'Other', icon: 'ellipsis-horizontal', color: '#64748b' },
  ],
  Income: [
    { id: 'Salary', name: 'Salary', icon: 'briefcase', color: '#10b981' },
    { id: 'Freelance / Consulting', name: 'Freelance', icon: 'laptop', color: '#06b6d4' },
    { id: 'Business Revenue', name: 'Business', icon: 'trending-up', color: '#3b82f6' },
    { id: 'Investment Returns', name: 'Investment', icon: 'stats-chart', color: '#8b5cf6' },
    { id: 'Bonus', name: 'Bonus', icon: 'gift', color: '#f59e0b' },
    { id: 'Other', name: 'Other', icon: 'cash', color: '#64748b' },
  ],
};

const PAYMENT_MODES = ['UPI', 'Cash', 'Debit Card', 'Credit Card', 'Net Banking'];

export default function App() {
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [summary, setSummary] = useState({
    total_income: 0,
    total_expense: 0,
    net_balance: 0,
    total_count: 0,
    expense_by_category: {},
  });
  const [transactions, setTransactions] = useState([]);
  const [activeTab, setActiveTab] = useState('All'); // All, Income, Expense

  // Modal State
  const [modalVisible, setModalVisible] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [entryType, setEntryType] = useState('Expense');
  const [amount, setAmount] = useState('');
  const [selectedCategory, setSelectedCategory] = useState(CATEGORIES.Expense[0].id);
  const [paymentMode, setPaymentMode] = useState('UPI');
  const [notes, setNotes] = useState('');

  const loadData = useCallback(async () => {
    try {
      const [sumData, trxData] = await Promise.all([
        salesforceApi.getSummary(),
        salesforceApi.getTransactions(),
      ]);
      setSummary(sumData);
      setTransactions(trxData);
    } catch (err) {
      console.error('Error fetching data:', err);
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, []);

  useEffect(() => {
    loadData();
  }, [loadData]);

  const onRefresh = () => {
    setRefreshing(true);
    loadData();
  };

  const openAddModal = (type) => {
    setEntryType(type);
    setSelectedCategory(CATEGORIES[type][0].id);
    setAmount('');
    setNotes('');
    setPaymentMode('UPI');
    setModalVisible(true);
  };

  const handleSaveTransaction = async () => {
    if (!amount || parseFloat(amount) <= 0) {
      alert('Please enter a valid amount');
      return;
    }

    setSubmitting(true);
    try {
      await salesforceApi.createTransaction({
        type: entryType,
        amount: parseFloat(amount),
        category: selectedCategory,
        date: new Date().toISOString().split('T')[0],
        payment_mode: paymentMode,
        notes: notes.trim(),
      });
      setModalVisible(false);
      await loadData();
    } catch (err) {
      alert(`Error saving to Salesforce: ${err.message}`);
    } finally {
      setSubmitting(false);
    }
  };

  const handleDelete = (id) => {
    const doDelete = async () => {
      try {
        await salesforceApi.deleteTransaction(id);
        loadData();
      } catch (err) {
        alert(`Delete failed: ${err.message}`);
      }
    };

    if (Platform.OS === 'web') {
      if (confirm('Delete this record from Salesforce?')) {
        doDelete();
      }
    } else {
      Alert.alert('Confirm Delete', 'Delete this record from Salesforce Org?', [
        { text: 'Cancel', style: 'cancel' },
        { text: 'Delete', style: 'destructive', onPress: doDelete },
      ]);
    }
  };

  const filteredTransactions = transactions.filter((t) => {
    if (activeTab === 'All') return true;
    return (t.Type__c || '').toLowerCase() === activeTab.toLowerCase();
  });

  const formatCurrency = (val) => {
    return '₹' + parseFloat(val || 0).toLocaleString('en-IN', { minimumFractionDigits: 2 });
  };

  const getCategoryDetails = (catName, type) => {
    const list = CATEGORIES[type] || CATEGORIES.Expense;
    return list.find((c) => c.id === catName) || { icon: 'wallet', color: '#64748b' };
  };

  return (
    <SafeAreaView style={styles.safeArea}>
      <StatusBar style="light" />

      {/* Top Header */}
      <View style={styles.header}>
        <View style={styles.headerLeft}>
          <View style={styles.avatar}>
            <Text style={styles.avatarText}>KJ</Text>
          </View>
          <View>
            <Text style={styles.greeting}>Kuldeep Jangid</Text>
            <View style={styles.orgBadge}>
              <View style={styles.onlineDot} />
              <Text style={styles.orgText}>Salesforce Org Connected</Text>
            </View>
          </View>
        </View>

        <TouchableOpacity style={styles.refreshButton} onPress={onRefresh}>
          <Ionicons name="sync" size={18} color="#fff" />
        </TouchableOpacity>
      </View>

      <ScrollView
        contentContainerStyle={styles.scrollContent}
        refreshControl={<RefreshControl refreshing={refreshing} onRefresh={onRefresh} tintColor="#6366f1" />}
      >
        {/* Hero Financial Balance Card */}
        <View style={styles.heroCard}>
          <View style={styles.heroTop}>
            <Text style={styles.heroLabel}>NET SAVINGS / BALANCE</Text>
            <View style={styles.salesforcePill}>
              <Ionicons name="cloud-done" size={13} color="#a5b4fc" style={{ marginRight: 4 }} />
              <Text style={styles.salesforcePillText}>Salesforce Cloud</Text>
            </View>
          </View>

          <Text style={styles.heroAmount}>{formatCurrency(summary.net_balance)}</Text>

          {/* Income vs Expense Split */}
          <View style={styles.splitRow}>
            {/* Income Pill */}
            <View style={styles.splitBox}>
              <View style={styles.splitIconIncome}>
                <Ionicons name="arrow-up" size={14} color="#10b981" />
              </View>
              <View>
                <Text style={styles.splitLabel}>Income</Text>
                <Text style={styles.incomeAmount}>{formatCurrency(summary.total_income)}</Text>
              </View>
            </View>

            <View style={styles.splitDivider} />

            {/* Expense Pill */}
            <View style={styles.splitBox}>
              <View style={styles.splitIconExpense}>
                <Ionicons name="arrow-down" size={14} color="#f43f5e" />
              </View>
              <View>
                <Text style={styles.splitLabel}>Expenses</Text>
                <Text style={styles.expenseAmount}>{formatCurrency(summary.total_expense)}</Text>
              </View>
            </View>
          </View>
        </View>

        {/* Quick Action Buttons */}
        <View style={styles.quickActions}>
          <TouchableOpacity
            style={[styles.actionBtn, styles.actionBtnExpense]}
            onPress={() => openAddModal('Expense')}
            activeOpacity={0.8}
          >
            <View style={styles.actionIconWrapExpense}>
              <Ionicons name="remove-circle" size={20} color="#f43f5e" />
            </View>
            <Text style={styles.actionBtnText}>Add Expense</Text>
          </TouchableOpacity>

          <TouchableOpacity
            style={[styles.actionBtn, styles.actionBtnIncome]}
            onPress={() => openAddModal('Income')}
            activeOpacity={0.8}
          >
            <View style={styles.actionIconWrapIncome}>
              <Ionicons name="add-circle" size={20} color="#10b981" />
            </View>
            <Text style={styles.actionBtnText}>Add Income</Text>
          </TouchableOpacity>
        </View>

        {/* Expense Category Breakdown Section */}
        {summary.total_expense > 0 && (
          <View style={styles.sectionContainer}>
            <Text style={styles.sectionTitle}>Spending by Category</Text>
            <View style={styles.categoryCard}>
              {Object.entries(summary.expense_by_category || {}).map(([cat, amt]) => {
                const percent = Math.round((amt / summary.total_expense) * 100);
                const details = getCategoryDetails(cat, 'Expense');
                return (
                  <View key={cat} style={styles.catItem}>
                    <View style={styles.catItemHeader}>
                      <View style={styles.catNameRow}>
                        <View style={[styles.catIconMini, { backgroundColor: details.color + '20' }]}>
                          <Ionicons name={details.icon} size={13} color={details.color} />
                        </View>
                        <Text style={styles.catNameText}>{cat}</Text>
                      </View>
                      <Text style={styles.catAmountText}>{formatCurrency(amt)} ({percent}%)</Text>
                    </View>
                    <View style={styles.progressBarBg}>
                      <View style={[styles.progressBarFill, { width: `${percent}%`, backgroundColor: details.color }]} />
                    </View>
                  </View>
                );
              })}
            </View>
          </View>
        )}

        {/* Recent Transactions List */}
        <View style={styles.sectionContainer}>
          <View style={styles.trxHeaderRow}>
            <Text style={styles.sectionTitle}>Recent Activity</Text>
            <Text style={styles.trxCountBadge}>{summary.total_count} records</Text>
          </View>

          {/* Filter Segmented Tabs */}
          <View style={styles.segmentedContainer}>
            {['All', 'Income', 'Expense'].map((tab) => (
              <TouchableOpacity
                key={tab}
                style={[styles.segmentTab, activeTab === tab && styles.segmentTabActive]}
                onPress={() => setActiveTab(tab)}
              >
                <Text style={[styles.segmentText, activeTab === tab && styles.segmentTextActive]}>
                  {tab}
                </Text>
              </TouchableOpacity>
            ))}
          </View>

          {/* Transactions Cards */}
          {loading ? (
            <ActivityIndicator size="large" color="#6366f1" style={{ marginTop: 24 }} />
          ) : filteredTransactions.length === 0 ? (
            <View style={styles.emptyCard}>
              <Ionicons name="receipt-outline" size={40} color="#94a3b8" />
              <Text style={styles.emptyText}>No transactions found</Text>
              <Text style={styles.emptySubText}>Add an income or expense to sync with Salesforce</Text>
            </View>
          ) : (
            filteredTransactions.map((item) => {
              const isIncome = (item.Type__c || '').toLowerCase() === 'income';
              const catDetails = getCategoryDetails(item.Category__c, isIncome ? 'Income' : 'Expense');

              return (
                <View key={item.Id} style={styles.trxCard}>
                  <View style={[styles.trxIconWrap, { backgroundColor: isIncome ? '#10b98115' : '#f43f5e15' }]}>
                    <Ionicons
                      name={catDetails.icon}
                      size={20}
                      color={isIncome ? '#10b981' : '#f43f5e'}
                    />
                  </View>

                  <View style={styles.trxDetails}>
                    <Text style={styles.trxTitle}>{item.Category__c || 'General'}</Text>
                    <Text style={styles.trxSub}>
                      {item.Transaction_Date__c} • {item.Payment_Mode__c || 'UPI'}
                      {item.Notes__c ? ` • ${item.Notes__c}` : ''}
                    </Text>
                  </View>

                  <View style={styles.trxRight}>
                    <Text style={[styles.trxAmount, isIncome ? styles.incomeText : styles.expenseText]}>
                      {isIncome ? '+' : '-'}{formatCurrency(item.Amount__c)}
                    </Text>
                    <TouchableOpacity
                      onPress={() => handleDelete(item.Id)}
                      hitSlop={{ top: 10, bottom: 10, left: 10, right: 10 }}
                      style={styles.deleteBtn}
                    >
                      <Ionicons name="trash-outline" size={14} color="#94a3b8" />
                    </TouchableOpacity>
                  </View>
                </View>
              );
            })
          )}
        </View>
      </ScrollView>

      {/* Add Transaction Modal */}
      <Modal visible={modalVisible} animationType="slide" transparent={true}>
        <View style={styles.modalOverlay}>
          <View style={styles.modalSheet}>
            {/* Modal Header */}
            <View style={styles.modalHeader}>
              <Text style={styles.modalTitle}>
                {entryType === 'Expense' ? '🔴 Add New Expense' : '🟢 Add New Income'}
              </Text>
              <TouchableOpacity onPress={() => setModalVisible(false)} style={styles.modalClose}>
                <Ionicons name="close" size={22} color="#64748b" />
              </TouchableOpacity>
            </View>

            {/* Type Switcher */}
            <View style={styles.modalTypeToggle}>
              <TouchableOpacity
                style={[styles.toggleBtn, entryType === 'Expense' && styles.toggleBtnExpense]}
                onPress={() => {
                  setEntryType('Expense');
                  setSelectedCategory(CATEGORIES.Expense[0].id);
                }}
              >
                <Text style={[styles.toggleText, entryType === 'Expense' && styles.toggleTextActive]}>
                  Expense
                </Text>
              </TouchableOpacity>
              <TouchableOpacity
                style={[styles.toggleBtn, entryType === 'Income' && styles.toggleBtnIncome]}
                onPress={() => {
                  setEntryType('Income');
                  setSelectedCategory(CATEGORIES.Income[0].id);
                }}
              >
                <Text style={[styles.toggleText, entryType === 'Income' && styles.toggleTextActive]}>
                  Income
                </Text>
              </TouchableOpacity>
            </View>

            {/* Amount Input */}
            <View style={styles.amountInputWrap}>
              <Text style={styles.currencySymbol}>₹</Text>
              <TextInput
                style={styles.amountInput}
                placeholder="0.00"
                placeholderTextColor="#94a3b8"
                keyboardType="numeric"
                value={amount}
                onChangeText={setAmount}
                autoFocus
              />
            </View>

            {/* Quick Amount Chips */}
            <ScrollView horizontal showsHorizontalScrollIndicator={false} style={styles.quickChipScroll}>
              {[100, 250, 500, 1000, 2000, 5000].map((quick) => (
                <TouchableOpacity
                  key={quick}
                  style={styles.quickChip}
                  onPress={() => setAmount(String(quick))}
                >
                  <Text style={styles.quickChipText}>+₹{quick}</Text>
                </TouchableOpacity>
              ))}
            </ScrollView>

            {/* Category Selector */}
            <Text style={styles.inputLabel}>Category</Text>
            <ScrollView horizontal showsHorizontalScrollIndicator={false} style={styles.catChipScroll}>
              {CATEGORIES[entryType].map((c) => {
                const isSelected = selectedCategory === c.id;
                return (
                  <TouchableOpacity
                    key={c.id}
                    style={[styles.catChip, isSelected && { backgroundColor: c.color, borderColor: c.color }]}
                    onPress={() => setSelectedCategory(c.id)}
                  >
                    <Ionicons name={c.icon} size={15} color={isSelected ? '#fff' : c.color} style={{ marginRight: 6 }} />
                    <Text style={[styles.catChipText, isSelected && { color: '#fff' }]}>{c.name}</Text>
                  </TouchableOpacity>
                );
              })}
            </ScrollView>

            {/* Payment Mode Selector */}
            <Text style={styles.inputLabel}>Payment Mode</Text>
            <View style={styles.payModeRow}>
              {PAYMENT_MODES.slice(0, 4).map((mode) => (
                <TouchableOpacity
                  key={mode}
                  style={[styles.payChip, paymentMode === mode && styles.payChipActive]}
                  onPress={() => setPaymentMode(mode)}
                >
                  <Text style={[styles.payChipText, paymentMode === mode && styles.payChipTextActive]}>{mode}</Text>
                </TouchableOpacity>
              ))}
            </View>

            {/* Notes Input */}
            <Text style={styles.inputLabel}>Notes / Remarks (Optional)</Text>
            <TextInput
              style={styles.notesInput}
              placeholder="e.g. Dinner with friends, Client payout..."
              placeholderTextColor="#94a3b8"
              value={notes}
              onChangeText={setNotes}
            />

            {/* Submit Button */}
            <TouchableOpacity
              style={[styles.saveBtn, submitting && { opacity: 0.7 }]}
              onPress={handleSaveTransaction}
              disabled={submitting}
              activeOpacity={0.8}
            >
              {submitting ? (
                <ActivityIndicator color="#fff" />
              ) : (
                <View style={styles.saveBtnInner}>
                  <Ionicons name="cloud-upload" size={18} color="#fff" style={{ marginRight: 8 }} />
                  <Text style={styles.saveBtnText}>Save & Sync to Salesforce</Text>
                </View>
              )}
            </TouchableOpacity>
          </View>
        </View>
      </Modal>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  safeArea: {
    flex: 1,
    backgroundColor: '#0f172a', // Premium dark slate background
  },
  header: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingHorizontal: 20,
    paddingTop: Platform.OS === 'android' ? 40 : 12,
    paddingBottom: 16,
    backgroundColor: '#0f172a',
  },
  headerLeft: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  avatar: {
    width: 42,
    height: 42,
    borderRadius: 21,
    backgroundColor: '#6366f1',
    alignItems: 'center',
    justifyContent: 'center',
    marginRight: 12,
    borderWidth: 2,
    borderColor: '#818cf8',
  },
  avatarText: {
    color: '#fff',
    fontWeight: '800',
    fontSize: 16,
  },
  greeting: {
    color: '#f8fafc',
    fontSize: 17,
    fontWeight: '700',
  },
  orgBadge: {
    flexDirection: 'row',
    alignItems: 'center',
    marginTop: 2,
  },
  onlineDot: {
    width: 7,
    height: 7,
    borderRadius: 3.5,
    backgroundColor: '#10b981',
    marginRight: 5,
  },
  orgText: {
    color: '#94a3b8',
    fontSize: 11,
    fontWeight: '500',
  },
  refreshButton: {
    width: 38,
    height: 38,
    borderRadius: 19,
    backgroundColor: '#1e293b',
    alignItems: 'center',
    justifyContent: 'center',
    borderWidth: 1,
    borderColor: '#334155',
  },
  scrollContent: {
    paddingHorizontal: 18,
    paddingBottom: 40,
  },
  heroCard: {
    backgroundColor: '#1e1b4b',
    borderRadius: 24,
    padding: 22,
    marginTop: 8,
    borderWidth: 1,
    borderColor: '#4338ca',
    shadowColor: '#4f46e5',
    shadowOffset: { width: 0, height: 8 },
    shadowOpacity: 0.3,
    shadowRadius: 16,
    elevation: 8,
  },
  heroTop: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  heroLabel: {
    color: '#c7d2fe',
    fontSize: 11,
    fontWeight: '700',
    letterSpacing: 1.2,
  },
  salesforcePill: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: 'rgba(255,255,255,0.08)',
    paddingHorizontal: 8,
    paddingVertical: 3,
    borderRadius: 12,
  },
  salesforcePillText: {
    color: '#e0e7ff',
    fontSize: 10,
    fontWeight: '600',
  },
  heroAmount: {
    color: '#ffffff',
    fontSize: 32,
    fontWeight: '900',
    marginTop: 8,
    letterSpacing: -0.5,
  },
  splitRow: {
    flexDirection: 'row',
    marginTop: 20,
    paddingTop: 16,
    borderTopWidth: 1,
    borderTopColor: 'rgba(255,255,255,0.1)',
  },
  splitBox: {
    flex: 1,
    flexDirection: 'row',
    alignItems: 'center',
  },
  splitDivider: {
    width: 1,
    backgroundColor: 'rgba(255,255,255,0.1)',
    marginHorizontal: 12,
  },
  splitIconIncome: {
    width: 28,
    height: 28,
    borderRadius: 14,
    backgroundColor: 'rgba(16, 185, 129, 0.2)',
    alignItems: 'center',
    justifyContent: 'center',
    marginRight: 8,
  },
  splitIconExpense: {
    width: 28,
    height: 28,
    borderRadius: 14,
    backgroundColor: 'rgba(244, 63, 94, 0.2)',
    alignItems: 'center',
    justifyContent: 'center',
    marginRight: 8,
  },
  splitLabel: {
    color: '#94a3b8',
    fontSize: 10,
    fontWeight: '600',
  },
  incomeAmount: {
    color: '#34d399',
    fontSize: 14,
    fontWeight: '800',
  },
  expenseAmount: {
    color: '#fb7185',
    fontSize: 14,
    fontWeight: '800',
  },
  quickActions: {
    flexDirection: 'row',
    gap: 12,
    marginTop: 16,
  },
  actionBtn: {
    flex: 1,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    paddingVertical: 14,
    borderRadius: 16,
    borderWidth: 1,
  },
  actionBtnExpense: {
    backgroundColor: '#1e293b',
    borderColor: '#334155',
  },
  actionBtnIncome: {
    backgroundColor: '#1e293b',
    borderColor: '#334155',
  },
  actionIconWrapExpense: {
    marginRight: 8,
  },
  actionIconWrapIncome: {
    marginRight: 8,
  },
  actionBtnText: {
    color: '#f8fafc',
    fontSize: 14,
    fontWeight: '700',
  },
  sectionContainer: {
    marginTop: 24,
  },
  sectionTitle: {
    color: '#f8fafc',
    fontSize: 17,
    fontWeight: '700',
    marginBottom: 12,
  },
  categoryCard: {
    backgroundColor: '#1e293b',
    borderRadius: 20,
    padding: 16,
    borderWidth: 1,
    borderColor: '#334155',
  },
  catItem: {
    marginBottom: 14,
  },
  catItemHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 6,
  },
  catNameRow: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  catIconMini: {
    width: 22,
    height: 22,
    borderRadius: 6,
    alignItems: 'center',
    justifyContent: 'center',
    marginRight: 8,
  },
  catNameText: {
    color: '#e2e8f0',
    fontSize: 13,
    fontWeight: '600',
  },
  catAmountText: {
    color: '#94a3b8',
    fontSize: 12,
    fontWeight: '700',
  },
  progressBarBg: {
    height: 6,
    backgroundColor: '#334155',
    borderRadius: 3,
    overflow: 'hidden',
  },
  progressBarFill: {
    height: '100%',
    borderRadius: 3,
  },
  trxHeaderRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  trxCountBadge: {
    color: '#818cf8',
    fontSize: 11,
    fontWeight: '700',
    backgroundColor: '#1e1b4b',
    paddingHorizontal: 8,
    paddingVertical: 3,
    borderRadius: 10,
  },
  segmentedContainer: {
    flexDirection: 'row',
    backgroundColor: '#1e293b',
    borderRadius: 14,
    padding: 4,
    marginBottom: 12,
  },
  segmentTab: {
    flex: 1,
    paddingVertical: 8,
    alignItems: 'center',
    borderRadius: 10,
  },
  segmentTabActive: {
    backgroundColor: '#6366f1',
  },
  segmentText: {
    color: '#94a3b8',
    fontSize: 12,
    fontWeight: '700',
  },
  segmentTextActive: {
    color: '#ffffff',
  },
  trxCard: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#1e293b',
    borderRadius: 18,
    padding: 14,
    marginBottom: 10,
    borderWidth: 1,
    borderColor: '#334155',
  },
  trxIconWrap: {
    width: 42,
    height: 42,
    borderRadius: 21,
    alignItems: 'center',
    justifyContent: 'center',
    marginRight: 12,
  },
  trxDetails: {
    flex: 1,
  },
  trxTitle: {
    color: '#f8fafc',
    fontSize: 14,
    fontWeight: '700',
  },
  trxSub: {
    color: '#94a3b8',
    fontSize: 11,
    marginTop: 2,
  },
  trxRight: {
    alignItems: 'flex-end',
    marginLeft: 8,
  },
  trxAmount: {
    fontSize: 14,
    fontWeight: '800',
  },
  incomeText: {
    color: '#34d399',
  },
  expenseText: {
    color: '#f87171',
  },
  deleteBtn: {
    marginTop: 4,
    padding: 2,
  },
  emptyCard: {
    backgroundColor: '#1e293b',
    borderRadius: 20,
    padding: 32,
    alignItems: 'center',
    justifyContent: 'center',
    borderWidth: 1,
    borderColor: '#334155',
  },
  emptyText: {
    color: '#e2e8f0',
    fontSize: 15,
    fontWeight: '700',
    marginTop: 10,
  },
  emptySubText: {
    color: '#64748b',
    fontSize: 12,
    marginTop: 4,
    textAlign: 'center',
  },
  // Modal Styles
  modalOverlay: {
    flex: 1,
    backgroundColor: 'rgba(0,0,0,0.7)',
    justifyContent: 'flex-end',
  },
  modalSheet: {
    backgroundColor: '#0f172a',
    borderTopLeftRadius: 30,
    borderTopRightRadius: 30,
    padding: 24,
    paddingBottom: 36,
    borderWidth: 1,
    borderColor: '#334155',
  },
  modalHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 16,
  },
  modalTitle: {
    color: '#ffffff',
    fontSize: 18,
    fontWeight: '800',
  },
  modalClose: {
    width: 32,
    height: 32,
    borderRadius: 16,
    backgroundColor: '#1e293b',
    alignItems: 'center',
    justifyContent: 'center',
  },
  modalTypeToggle: {
    flexDirection: 'row',
    backgroundColor: '#1e293b',
    borderRadius: 14,
    padding: 4,
    marginBottom: 18,
  },
  toggleBtn: {
    flex: 1,
    paddingVertical: 9,
    alignItems: 'center',
    borderRadius: 10,
  },
  toggleBtnExpense: {
    backgroundColor: '#f43f5e',
  },
  toggleBtnIncome: {
    backgroundColor: '#10b981',
  },
  toggleText: {
    color: '#94a3b8',
    fontSize: 13,
    fontWeight: '700',
  },
  toggleTextActive: {
    color: '#ffffff',
  },
  amountInputWrap: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#1e293b',
    borderRadius: 18,
    paddingHorizontal: 16,
    paddingVertical: 8,
    borderWidth: 1,
    borderColor: '#475569',
  },
  currencySymbol: {
    color: '#6366f1',
    fontSize: 26,
    fontWeight: '800',
    marginRight: 6,
  },
  amountInput: {
    flex: 1,
    color: '#ffffff',
    fontSize: 26,
    fontWeight: '800',
  },
  quickChipScroll: {
    marginTop: 10,
    marginBottom: 14,
  },
  quickChip: {
    backgroundColor: '#1e293b',
    borderWidth: 1,
    borderColor: '#334155',
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 12,
    marginRight: 8,
  },
  quickChipText: {
    color: '#cbd5e1',
    fontSize: 12,
    fontWeight: '600',
  },
  inputLabel: {
    color: '#94a3b8',
    fontSize: 11,
    fontWeight: '700',
    textTransform: 'uppercase',
    letterSpacing: 0.8,
    marginTop: 8,
    marginBottom: 8,
  },
  catChipScroll: {
    marginBottom: 12,
  },
  catChip: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#1e293b',
    borderWidth: 1,
    borderColor: '#334155',
    paddingHorizontal: 12,
    paddingVertical: 8,
    borderRadius: 14,
    marginRight: 8,
  },
  catChipText: {
    color: '#e2e8f0',
    fontSize: 12,
    fontWeight: '600',
  },
  payModeRow: {
    flexDirection: 'row',
    gap: 8,
    marginBottom: 12,
  },
  payChip: {
    flex: 1,
    backgroundColor: '#1e293b',
    paddingVertical: 8,
    borderRadius: 12,
    alignItems: 'center',
    borderWidth: 1,
    borderColor: '#334155',
  },
  payChipActive: {
    backgroundColor: '#6366f1',
    borderColor: '#6366f1',
  },
  payChipText: {
    color: '#94a3b8',
    fontSize: 11,
    fontWeight: '700',
  },
  payChipTextActive: {
    color: '#ffffff',
  },
  notesInput: {
    backgroundColor: '#1e293b',
    borderRadius: 14,
    paddingHorizontal: 14,
    paddingVertical: 10,
    color: '#ffffff',
    fontSize: 13,
    borderWidth: 1,
    borderColor: '#334155',
    marginBottom: 20,
  },
  saveBtn: {
    backgroundColor: '#6366f1',
    paddingVertical: 15,
    borderRadius: 16,
    alignItems: 'center',
    justifyContent: 'center',
    shadowColor: '#6366f1',
    shadowOffset: { width: 0, height: 6 },
    shadowOpacity: 0.4,
    shadowRadius: 10,
    elevation: 6,
  },
  saveBtnInner: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  saveBtnText: {
    color: '#ffffff',
    fontSize: 15,
    fontWeight: '800',
  },
});
