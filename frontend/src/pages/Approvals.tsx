import React, { useState, useEffect } from 'react';
import { CheckCircle, XCircle, Edit3, Eye, Clock, DollarSign, Calendar, FileText, User } from 'lucide-react';
import Button from '../components/ui/Button';
import Card from '../components/ui/Card';
import Modal from '../components/ui/Modal';
import Input from '../components/ui/Input';
import Badge from '../components/ui/Badge';
import { businessService, categoryService, accountService, expenseService } from '../services/business.service';
import type { Business, Expense, Category, Account, ExpenseApprovalRequest, ExpenseApprovalEditRequest } from '../types';

const Approvals: React.FC = () => {
  const [pendingExpenses, setPendingExpenses] = useState<Expense[]>([]);
  const [businesses, setBusinesses] = useState<Business[]>([]);
  const [categories, setCategories] = useState<Category[]>([]);
  const [accounts, setAccounts] = useState<Account[]>([]);
  const [selectedBusinessId, setSelectedBusinessId] = useState<string>('');
  const [isLoading, setIsLoading] = useState(true);
  const [selectedExpense, setSelectedExpense] = useState<Expense | null>(null);
  const [isApprovalModalOpen, setIsApprovalModalOpen] = useState(false);
  const [isEditModalOpen, setIsEditModalOpen] = useState(false);
  const [approvalAction, setApprovalAction] = useState<'approve' | 'reject'>('approve');
  const [approvalNotes, setApprovalNotes] = useState('');
  const [editFormData, setEditFormData] = useState({
    amount: '',
    description: '',
    category_id: '',
    account_id: '',
    date: '',
    notes: '',
  });

  useEffect(() => {
    fetchBusinesses();
  }, []);

  useEffect(() => {
    if (selectedBusinessId) {
      fetchCategoriesAndAccounts(selectedBusinessId);
      fetchPendingExpenses(selectedBusinessId);
    }
  }, [selectedBusinessId]);

  const fetchBusinesses = async () => {
    try {
      const response = await businessService.getBusinesses();
      setBusinesses(response.businesses);
      if (response.businesses.length > 0) {
        setSelectedBusinessId(response.businesses[0].id);
      }
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

  const fetchPendingExpenses = async (businessId: string) => {
    try {
      const response = await expenseService.getPendingExpenses(businessId);
      setPendingExpenses(response.transactions);
    } catch (error) {
      console.error('Failed to fetch pending expenses:', error);
      setPendingExpenses([]);
    }
  };

  const handleApproval = (expense: Expense, action: 'approve' | 'reject') => {
    setSelectedExpense(expense);
    setApprovalAction(action);
    setApprovalNotes('');
    setIsApprovalModalOpen(true);
  };

  const handleEditApproval = (expense: Expense) => {
    setSelectedExpense(expense);
    setEditFormData({
      amount: expense.amount.toString(),
      description: expense.description,
      category_id: expense.category_id || '',
      account_id: expense.account_id,
      date: new Date(expense.date).toISOString().split('T')[0],
      notes: expense.notes || '',
    });
    setApprovalNotes('');
    setIsEditModalOpen(true);
  };

  const submitApproval = async () => {
    if (!selectedExpense) return;

    try {
      const approvalData: ExpenseApprovalRequest = {
        status: approvalAction === 'approve' ? 'approved' : 'rejected',
        approval_notes: approvalNotes || undefined,
      };

      await expenseService.approveExpense(selectedExpense.id, approvalData);

      // Refresh the list
      fetchPendingExpenses(selectedBusinessId);
      setIsApprovalModalOpen(false);
      setSelectedExpense(null);
    } catch (error) {
      console.error('Failed to approve expense:', error);
    }
  };

  const submitEditApproval = async () => {
    if (!selectedExpense) return;

    try {
      const approvalData: ExpenseApprovalEditRequest = {
        ...editFormData,
        amount: parseFloat(editFormData.amount),
        date: new Date(editFormData.date).toISOString(),
        category_id: editFormData.category_id || undefined,
        notes: editFormData.notes || undefined,
        status: 'approved',
        approval_notes: approvalNotes || undefined,
      };

      await expenseService.approveAndEditExpense(selectedExpense.id, approvalData);

      // Refresh the list
      fetchPendingExpenses(selectedBusinessId);
      setIsEditModalOpen(false);
      setSelectedExpense(null);
    } catch (error) {
      console.error('Failed to approve and edit expense:', error);
    }
  };

  const formatCurrency = (amount: number, currency: string = 'USD') => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: currency,
    }).format(amount);
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
    });
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-center">
          <div className="w-16 h-16 border-4 border-primary-500 border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
          <p className="text-gray-600">Loading approvals...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Expense Approvals</h1>
          <p className="text-gray-500 mt-1">Review and approve pending expense requests</p>
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
        </div>
      </div>

      {/* Pending Expenses */}
      {pendingExpenses.length === 0 ? (
        <Card>
          <div className="text-center py-12">
            <CheckCircle className="w-16 h-16 text-green-300 mx-auto mb-4" />
            <h3 className="text-lg font-semibold text-gray-900 mb-2">All caught up!</h3>
            <p className="text-gray-500">No pending expenses require approval</p>
          </div>
        </Card>
      ) : (
        <div className="space-y-4">
          {pendingExpenses.map((expense) => (
            <Card key={expense.id} className="p-6">
              <div className="flex items-start justify-between">
                <div className="flex-1">
                  <div className="flex items-center space-x-4 mb-3">
                    <h3 className="text-lg font-semibold text-gray-900">{expense.description}</h3>
                    <Badge variant="warning" size="sm">
                      <Clock className="w-3 h-3 mr-1" />
                      Pending
                    </Badge>
                  </div>

                  <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-4">
                    <div className="flex items-center text-sm text-gray-600">
                      <DollarSign className="w-4 h-4 mr-2" />
                      {formatCurrency(expense.amount, expense.currency)}
                    </div>
                    <div className="flex items-center text-sm text-gray-600">
                      <Calendar className="w-4 h-4 mr-2" />
                      {formatDate(expense.date)}
                    </div>
                    <div className="flex items-center text-sm text-gray-600">
                      <FileText className="w-4 h-4 mr-2" />
                      {categories.find(cat => cat.id === expense.category_id)?.category_name || 'No Category'}
                    </div>
                    <div className="flex items-center text-sm text-gray-600">
                      <User className="w-4 h-4 mr-2" />
                      {accounts.find(acc => acc.id === expense.account_id)?.account_name || 'Unknown Account'}
                    </div>
                  </div>

                  {expense.notes && (
                    <div className="bg-gray-50 p-3 rounded-lg mb-4">
                      <p className="text-sm text-gray-700">{expense.notes}</p>
                    </div>
                  )}

                  {expense.receipt_url && (
                    <div className="mb-4">
                      <a
                        href={expense.receipt_url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="text-primary-600 hover:text-primary-700 text-sm flex items-center"
                      >
                        <FileText className="w-4 h-4 mr-1" />
                        View Receipt
                      </a>
                    </div>
                  )}
                </div>

                <div className="flex items-center space-x-2 ml-4">
                  <Button
                    variant="ghost"
                    size="sm"
                    icon={<Eye className="w-4 h-4" />}
                    onClick={() => setSelectedExpense(expense)}
                  />
                  <Button
                    variant="ghost"
                    size="sm"
                    icon={<Edit3 className="w-4 h-4" />}
                    onClick={() => handleEditApproval(expense)}
                    className="text-blue-600 hover:bg-blue-50"
                  />
                  <Button
                    variant="ghost"
                    size="sm"
                    icon={<XCircle className="w-4 h-4" />}
                    onClick={() => handleApproval(expense, 'reject')}
                    className="text-red-600 hover:bg-red-50"
                  />
                  <Button
                    variant="primary"
                    size="sm"
                    icon={<CheckCircle className="w-4 h-4" />}
                    onClick={() => handleApproval(expense, 'approve')}
                  />
                </div>
              </div>
            </Card>
          ))}
        </div>
      )}

      {/* Approval Modal */}
      <Modal
        isOpen={isApprovalModalOpen}
        onClose={() => setIsApprovalModalOpen(false)}
        title={`${approvalAction === 'approve' ? 'Approve' : 'Reject'} Expense`}
        size="md"
      >
        <div className="space-y-4">
          {selectedExpense && (
            <div className="bg-gray-50 p-4 rounded-lg">
              <h4 className="font-semibold text-gray-900 mb-2">{selectedExpense.description}</h4>
              <p className="text-sm text-gray-600">
                {formatCurrency(selectedExpense.amount, selectedExpense.currency)} • {formatDate(selectedExpense.date)}
              </p>
            </div>
          )}

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Approval Notes <span className="text-gray-500">(optional)</span>
            </label>
            <textarea
              rows={3}
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
              placeholder={`Add notes for ${approvalAction === 'approve' ? 'approval' : 'rejection'}...`}
              value={approvalNotes}
              onChange={(e) => setApprovalNotes(e.target.value)}
            />
          </div>

          <div className="flex justify-end space-x-3 pt-4 border-t border-gray-200">
            <Button type="button" variant="ghost" onClick={() => setIsApprovalModalOpen(false)}>
              Cancel
            </Button>
            <Button
              type="button"
              variant={approvalAction === 'approve' ? 'primary' : 'danger'}
              onClick={submitApproval}
            >
              {approvalAction === 'approve' ? 'Approve' : 'Reject'} Expense
            </Button>
          </div>
        </div>
      </Modal>

      {/* Edit and Approve Modal */}
      <Modal
        isOpen={isEditModalOpen}
        onClose={() => setIsEditModalOpen(false)}
        title="Edit & Approve Expense"
        size="lg"
      >
        <form onSubmit={(e) => { e.preventDefault(); submitEditApproval(); }} className="space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <Input
              label="Amount"
              type="number"
              step="0.01"
              required
              placeholder="0.00"
              value={editFormData.amount}
              onChange={(e) => setEditFormData({ ...editFormData, amount: e.target.value })}
            />
            <Input
              label="Date"
              type="date"
              required
              value={editFormData.date}
              onChange={(e) => setEditFormData({ ...editFormData, date: e.target.value })}
            />
          </div>

          <Input
            label="Description"
            required
            placeholder="e.g., Office supplies"
            value={editFormData.description}
            onChange={(e) => setEditFormData({ ...editFormData, description: e.target.value })}
          />

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1.5">
                Category
              </label>
              <select
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
                value={editFormData.category_id}
                onChange={(e) => setEditFormData({ ...editFormData, category_id: e.target.value })}
              >
                <option value="">No Category</option>
                {categories.map((category) => (
                  <option key={category.id} value={category.id}>
                    {category.category_name}
                  </option>
                ))}
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1.5">
                Account
              </label>
              <select
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
                value={editFormData.account_id}
                onChange={(e) => setEditFormData({ ...editFormData, account_id: e.target.value })}
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
            <label className="block text-sm font-medium text-gray-700 mb-1.5">Notes</label>
            <textarea
              rows={3}
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
              placeholder="Additional notes..."
              value={editFormData.notes}
              onChange={(e) => setEditFormData({ ...editFormData, notes: e.target.value })}
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Approval Notes <span className="text-gray-500">(optional)</span>
            </label>
            <textarea
              rows={2}
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
              placeholder="Notes about the changes made..."
              value={approvalNotes}
              onChange={(e) => setApprovalNotes(e.target.value)}
            />
          </div>

          <div className="flex justify-end space-x-3 pt-4 border-t border-gray-200">
            <Button type="button" variant="ghost" onClick={() => setIsEditModalOpen(false)}>
              Cancel
            </Button>
            <Button type="submit" variant="primary">
              Save Changes & Approve
            </Button>
          </div>
        </form>
      </Modal>
    </div>
  );
};

export default Approvals;
