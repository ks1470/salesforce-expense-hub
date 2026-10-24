// Salesforce Mobile Service Layer
// Communicates with backend bridge and Salesforce REST API

const API_BASE_URL = 'http://127.0.0.1:5050/api';

export const salesforceApi = {
  // Fetch summary metrics (Total Income, Expenses, Balance, Category breakdown)
  async getSummary() {
    try {
      const response = await fetch(`${API_BASE_URL}/summary`, {
        method: 'GET',
        headers: { 'Content-Type': 'application/json' },
      });
      if (!response.ok) {
        throw new Error(`Server returned ${response.status}`);
      }
      return await response.json();
    } catch (error) {
      console.warn('Backend summary error, using fallback:', error);
      throw error;
    }
  },

  // Fetch all transactions from Salesforce
  async getTransactions() {
    try {
      const response = await fetch(`${API_BASE_URL}/transactions`, {
        method: 'GET',
        headers: { 'Content-Type': 'application/json' },
      });
      if (!response.ok) {
        throw new Error(`Server returned ${response.status}`);
      }
      const data = await response.json();
      return data.records || [];
    } catch (error) {
      console.warn('Backend transactions error:', error);
      throw error;
    }
  },

  // Create a new Income or Expense record in Salesforce
  async createTransaction({ type, amount, category, date, payment_mode, notes }) {
    try {
      const response = await fetch(`${API_BASE_URL}/transactions`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          type,
          amount: parseFloat(amount),
          category,
          date,
          payment_mode,
          notes,
        }),
      });

      const data = await response.json();
      if (!response.ok) {
        throw new Error(data.error || 'Failed to create record in Salesforce');
      }
      return data;
    } catch (error) {
      console.error('Create transaction error:', error);
      throw error;
    }
  },

  // Delete a record from Salesforce
  async deleteTransaction(recordId) {
    try {
      const response = await fetch(`${API_BASE_URL}/transactions/${recordId}`, {
        method: 'DELETE',
        headers: { 'Content-Type': 'application/json' },
      });
      const data = await response.json();
      if (!response.ok) {
        throw new Error(data.error || 'Failed to delete record');
      }
      return data;
    } catch (error) {
      console.error('Delete transaction error:', error);
      throw error;
    }
  },
};
