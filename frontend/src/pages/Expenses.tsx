import React, { useState, useEffect } from 'react';
import { Plus, Search, Filter, Download, Upload, Edit2, Trash2, FileText } from 'lucide-react';
import Button from '../components/ui/Button';
import Card from '../components/ui/Card';
import Modal from '../components/ui/Modal';
import Input from '../components/ui/Input';
import Badge from '../components/ui/Badge';
import { businessService, categoryService, accountService, expenseService } from '../services/business.service';
import type { Business, Expense, ExpenseStatus, Category, Account, CreateExpenseRequest } from '../types';

const Expenses: React.FC = () => {
  const [expenses, setExpenses] = useState<Expense[]>([]);
  const [businesses, setBusinesses] = useState<Business[]>([]);
  const [categories, setCategories] = useState<Category[]>([]);
  const [accounts, setAccounts] = useState<Account[]>([]);
  const [selectedBusinessId, setSelectedBusinessId] = useState<string>('');
  const [isLoading, setIsLoading] = useState(true);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [editingExpense, setEditingExpense] = useState<Expense | null>(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [statusFilter, setStatusFilter] = useState<ExpenseStatus | 'all'>('all');
  const [formData, setFormData] = useState({
    date: '',
    amount: '',
    description: '',
    category_id: '',
    account_id: '',
    status: 'pending',
    is_income: false,
    notes: '',
  });

  useEffect(() => {
    fetchBusinesses();
  }, []);

  useEffect(() => {
    if (selectedBusinessId) {
      fetchCategoriesAndAccounts(selectedBusinessId);
      fetchExpenses(selectedBusinessId);
    }
  }, [selectedBusinessId]);

  const fetchBusinesses = async () => {
    try {
      const response = await businessService.getBusinesses();
      setBusinesses(response.businesses);
      if (response.businesses.length > 0) {
        setSelectedBusinessId(response.businesses[0].id);
      }
      // TODO: Fetch expenses when API is ready
      setExpenses([]);
    } catch (error) {
      console.error('Failed to fetch businesses:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const fetchCategoriesAndAccounts = async (businessId: string) => {
    try {
      const [categoriesResponse, accountsResponse] = await Promise.all([
        categoryService.getCategories(businessId),
        accountService.getAccounts(businessId)
      ]);
      setCategories(categoriesResponse.categories);
      setAccounts(accountsResponse.accounts);
    } catch (error) {
      console.error('Failed to fetch categories and accounts:', error);
    }
  };

  const fetchExpenses = async (businessId: string) => {
    try {
      const response = await expenseService.getExpenses(businessId);
      setExpenses(response.transactions);
    } catch (error) {
      console.error('Failed to fetch expenses:', error);
      setExpenses([]);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      const expenseData: CreateExpenseRequest = {
        business_id: selectedBusinessId,
        account_id: formData.account_id,
        category_id: formData.category_id || undefined,
        amount: parseFloat(formData.amount),
        currency: 'USD',
        description: formData.description,
        date: new Date(formData.date).toISOString(),
        is_income: formData.is_income,
        status: formData.status as ExpenseStatus,
        notes: formData.notes || undefined,
      };

      if (editingExpense) {
        await expenseService.updateExpense(editingExpense.id, expenseData);
        alert('Expense updated successfully!');
      } else {
        await expenseService.createExpense(expenseData);
        alert('Expense submitted for approval successfully!');
      }
      
      // Reset form and close modal
      setFormData({
        date: '',
        amount: '',
        description: '',
        category_id: '',
        account_id: '',
        status: 'pending',
        is_income: false,
        notes: '',
      });
      setEditingExpense(null);
      setIsModalOpen(false);
      
      // Refresh expenses list
      fetchExpenses(selectedBusinessId);
      
    } catch (error) {
      console.error('Failed to save expense:', error);
      // TODO: Show error message to user
    }
  };

  const getStatusBadge = (status: ExpenseStatus) => {
    const variants: Record<ExpenseStatus, { variant: any; label: string }> = {
      draft: { variant: 'default', label: 'Draft' },
      pending: { variant: 'warning', label: 'Pending' },
      approved: { variant: 'success', label: 'Approved' },
      rejected: { variant: 'danger', label: 'Rejected' },
    };
    return variants[status] || variants.draft;
  };

  const handleEdit = (expense: Expense) => {
    setEditingExpense(expense);
    setFormData({
      date: new Date(expense.date).toISOString().split('T')[0],
      amount: expense.amount.toString(),
      description: expense.description,
      category_id: expense.category_id || '',
      account_id: expense.account_id,
      status: expense.status,
      is_income: expense.is_income || false,
      notes: expense.notes || '',
    });
    setIsModalOpen(true);
  };

  const handleDelete = async (expenseId: string) => {
    if (!confirm('Are you sure you want to delete this expense? This action cannot be undone.')) {
      return;
    }

    try {
      await expenseService.deleteExpense(expenseId, selectedBusinessId);
      fetchExpenses(selectedBusinessId);
      alert('Expense deleted successfully!');
    } catch (error) {
      console.error('Failed to delete expense:', error);
      alert('Failed to delete expense. Please try again.');
    }
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
    });
  };

  const formatCurrency = (amount: number, currency: string = 'USD') => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: currency,
    }).format(amount);
  };

  const filteredExpenses = expenses.filter((expense) => {
    const matchesSearch =
      expense.description.toLowerCase().includes(searchQuery.toLowerCase()) ||
      expense.amount.toString().includes(searchQuery);
    const matchesStatus = statusFilter === 'all' || expense.status === statusFilter;
    return matchesSearch && matchesStatus;
  });

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-center">
          <div className="w-16 h-16 border-4 border-primary-500 border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
          <p className="text-gray-600">Loading expenses...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Income & Expenses Transactions </h1>
          <p className="text-gray-500 mt-1">Track and manage your income and expenses</p>
        </div>
        <div className="flex items-center space-x-4">
          <select
            value={selectedBusinessId}
            onChange={(e) => setSelectedBusinessId(e.target.value)}
            className="px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
            disabled={businesses.length === 0}
          >
            {businesses.map((business) => (
              <option key={business.id} value={business.id}>
                {business.business_name || business.name}
              </option>
            ))}
          </select>
          <Button variant="outline" icon={<Download className="w-5 h-5" />}>
            Export
          </Button>
          <Button variant="primary" icon={<Plus className="w-5 h-5" />} onClick={() => setIsModalOpen(true)}>
            Add Transaction
          </Button>
        </div>
      </div>

      {/* Filters */}
      <Card>
        <div className="flex items-center space-x-4">
          <div className="flex-1 relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-5 h-5" />
            <input
              type="text"
              placeholder="Search expenses..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
            />
          </div>
          <div className="flex items-center space-x-2">
            <Filter className="w-5 h-5 text-gray-400" />
            <select
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value as ExpenseStatus | 'all')}
              className="px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
            >
              <option value="all">All Status</option>
              <option value="draft">Draft</option>
              <option value="pending">Pending</option>
              <option value="approved">Approved</option>
              <option value="rejected">Rejected</option>
            </select>
          </div>
        </div>
      </Card>

      {/* Expenses Table */}
      {filteredExpenses.length === 0 ? (
        <Card>
          <div className="text-center py-12">
            <FileText className="w-16 h-16 text-gray-300 mx-auto mb-4" />
            <h3 className="text-lg font-semibold text-gray-900 mb-2">No expenses found</h3>
            <p className="text-gray-500 mb-6">
              {expenses.length === 0
                ? 'Get started by adding your first expense'
                : 'No expenses match your search criteria'}
            </p>
            {expenses.length === 0 && (
              <Button variant="primary" onClick={() => setIsModalOpen(true)}>
                Add Transaction
              </Button>
            )}
          </div>
        </Card>
      ) : (
        <Card>
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="border-b border-gray-200">
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Date
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Description
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Type
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Category
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Account
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Amount
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Status
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Receipt
                  </th>
                  <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Actions
                  </th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-200">
                {filteredExpenses.map((expense) => {
                  const statusBadge = getStatusBadge(expense.status);
                  return (
                    <tr key={expense.id} className="hover:bg-gray-50">
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                        {formatDate(expense.date)}
                      </td>
                      <td className="px-6 py-4 text-sm text-gray-900">
                        <div>
                          <div className="font-medium">{expense.description}</div>
                          {expense.notes && (
                            <div className="text-gray-500 text-xs mt-1">{expense.notes}</div>
                          )}
                        </div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm">
                        <Badge variant={expense.is_income ? "success" : "default"} size="sm">
                          {expense.is_income ? "Income" : "Expense"}
                        </Badge>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                        {categories.find(cat => cat.id === expense.category_id)?.category_name || 'Unknown Category'}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                        {accounts.find(acc => acc.id === expense.account_id)?.account_name || 'Unknown Account'}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                        {formatCurrency(expense.amount, expense.currency)}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <Badge variant={statusBadge.variant} size="sm">
                          {statusBadge.label}
                        </Badge>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm">
                        {expense.receipt_url ? (
                          <a
                            href={expense.receipt_url}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="text-primary-600 hover:text-primary-700 flex items-center"
                          >
                            <FileText className="w-4 h-4 mr-1" />
                            View
                          </a>
                        ) : (
                          <span className="text-gray-400">-</span>
                        )}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-right text-sm">
                        <div className="flex items-center justify-end space-x-2">
                          <Button 
                            variant="ghost" 
                            size="sm" 
                            icon={<Edit2 className="w-4 h-4" />}
                            onClick={() => handleEdit(expense)}
                          />
                          {(expense.status === 'pending' || expense.status === 'draft') && (
                            <Button
                              variant="ghost"
                              size="sm"
                              icon={<Trash2 className="w-4 h-4" />}
                              className="text-red-600 hover:bg-red-50"
                              onClick={() => handleDelete(expense.id)}
                            />
                          )}
                        </div>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </Card>
      )}

      {/* Create/Edit Modal */}
      <Modal
        isOpen={isModalOpen}
        onClose={() => {
          setIsModalOpen(false);
          setEditingExpense(null);
          setFormData({
            date: '',
            amount: '',
            description: '',
            category_id: '',
            account_id: '',
            status: 'pending',
            is_income: false,
            notes: '',
          });
        }}
        title={editingExpense ? "Edit Expense" : "Add New Expense"}
        size="lg"
      >
        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <Input 
              label="Date" 
              type="date" 
              required 
              value={formData.date}
              onChange={(e) => setFormData({ ...formData, date: e.target.value })}
            />
            <Input 
              label="Amount" 
              type="number" 
              step="0.01" 
              required 
              placeholder="0.00"
              value={formData.amount}
              onChange={(e) => setFormData({ ...formData, amount: e.target.value })}
            />
          </div>

          <Input 
            label="Description" 
            required 
            placeholder="e.g., Office supplies"
            value={formData.description}
            onChange={(e) => setFormData({ ...formData, description: e.target.value })}
          />

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1.5">
              Type <span className="text-red-500">*</span>
            </label>
            <div className="flex space-x-6">
              <label className="flex items-center">
                <input
                  type="radio"
                  name="is_income"
                  checked={!formData.is_income}
                  onChange={() => setFormData({ ...formData, is_income: false, category_id: '' })}
                  className="mr-2"
                />
                <span className="text-sm text-gray-700">Expense</span>
              </label>
              <label className="flex items-center">
                <input
                  type="radio"
                  name="is_income"
                  checked={formData.is_income}
                  onChange={() => setFormData({ ...formData, is_income: true, category_id: '' })}
                  className="mr-2"
                />
                <span className="text-sm text-gray-700">Income</span>
              </label>
            </div>
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1.5">
                Category <span className="text-red-500">*</span>
              </label>
              <select 
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
                value={formData.category_id}
                onChange={(e) => setFormData({ ...formData, category_id: e.target.value })}
                required
              >
                <option value="">Select category</option>
                {categories.filter(category => category.is_income === formData.is_income).map((category) => (
                  <option key={category.id} value={category.id}>
                    {category.category_name}
                  </option>
                ))}
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1.5">
                Account <span className="text-red-500">*</span>
              </label>
              <select 
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
                value={formData.account_id}
                onChange={(e) => setFormData({ ...formData, account_id: e.target.value })}
                required
              >
                <option value="">Select account</option>
                {accounts.map((account) => (
                  <option key={account.id} value={account.id}>
                    {account.account_name}
                  </option>
                ))}
              </select>
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1.5">
              Status
            </label>
            <select 
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
              value={formData.status}
              onChange={(e) => setFormData({ ...formData, status: e.target.value as ExpenseStatus })}
            >
              <option value="pending">Pending (Requires Approval)</option>
              <option value="approved">Approved (Bypass Approval)</option>
            </select>
            <p className="text-xs text-gray-500 mt-1">
              Select 'Approved' to bypass the approval workflow
            </p>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1.5">Notes</label>
            <textarea
              rows={3}
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
              placeholder="Additional notes..."
              value={formData.notes}
              onChange={(e) => setFormData({ ...formData, notes: e.target.value })}
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1.5">Receipt</label>
            <div className="border-2 border-dashed border-gray-300 rounded-lg p-6 text-center hover:border-primary-500 transition-colors cursor-pointer">
              <Upload className="w-8 h-8 text-gray-400 mx-auto mb-2" />
              <p className="text-sm text-gray-600">Click to upload or drag and drop</p>
              <p className="text-xs text-gray-500 mt-1">PDF, PNG, JPG up to 10MB</p>
            </div>
          </div>

          <div className="flex justify-end space-x-3 pt-4 border-t border-gray-200">
            <Button type="button" variant="ghost" onClick={() => setIsModalOpen(false)}>
              Cancel
            </Button>
            <Button type="button" variant="outline">
              Save as Draft
            </Button>
            <Button type="submit" variant="primary">
              {editingExpense ? "Update Expense" : (formData.status === 'approved' ? "Add Transaction" : "Submit for Approval")}
            </Button>
          </div>
        </form>
      </Modal>
    </div>
  );
};

export default Expenses;
