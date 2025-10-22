import React, { useState, useEffect } from 'react';
import { CheckCircle, XCircle, Edit3, Eye, Clock, DollarSign, Calendar, FileText, User, AlertCircle, Building, ChevronRight } from 'lucide-react';
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
  const [expandedId, setExpandedId] = useState<string | null>(null);
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

  const toggleRow = (expenseId: string) => {
    setExpandedId(expandedId === expenseId ? null : expenseId);
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
    <div className="min-h-screen bg-white p-8">
      <div className="max-w-7xl mx-auto space-y-6">
        {/* Header */}
        <div className="flex items-center justify-between mb-8">
          <div>
            <h1 className="text-4xl font-bold tracking-tight">APPROVALS</h1>
            <p className="text-gray-500 mt-2">Review and approve pending expense requests</p>
          </div>
          <div className="flex gap-4">
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

        {/* Pending Expenses List */}
        {pendingExpenses.length === 0 ? (
          <div className="bg-white rounded-lg border border-gray-200 p-12 text-center">
            <CheckCircle className="w-16 h-16 text-green-300 mx-auto mb-4" />
            <h3 className="text-xl font-bold text-gray-900 mb-2">All caught up!</h3>
            <p className="text-gray-500">No pending expenses require approval</p>
          </div>
        ) : (
          <div className="border-t border-gray-200">
            {/* Table Header */}
            <div className="grid grid-cols-12 gap-4 px-6 py-4 bg-white border-b border-gray-200">
              <div className="col-span-1"></div>
              <div className="col-span-2 text-sm font-medium text-gray-700">Date</div>
              <div className="col-span-2 text-sm font-medium text-gray-700">Description</div>
              <div className="col-span-2 text-sm font-medium text-gray-700">Category</div>
              <div className="col-span-2 text-sm font-medium text-gray-700">Account</div>
              <div className="col-span-2 text-sm font-medium text-gray-700">Amount</div>
              <div className="col-span-1 text-sm font-medium text-gray-700">Status</div>
            </div>

            {/* Table Rows */}
            {pendingExpenses.map((expense) => {
              const hasCategory = expense.category_id && categories.find(cat => cat.id === expense.category_id);
              const isExpanded = expandedId === expense.id;
              
              return (
                <div key={expense.id}>
                  <div
                    onClick={() => toggleRow(expense.id)}
                    className="grid grid-cols-12 gap-4 px-6 py-6 border-b border-gray-100 hover:bg-gray-50 transition-colors items-center cursor-pointer"
                  >
                    <div className="col-span-1 flex justify-center text-gray-400">
                      <ChevronRight
                        size={20}
                        className={`transition-transform ${isExpanded ? 'rotate-90' : ''}`}
                      />
                    </div>
                    <div className="col-span-2 text-base text-gray-900">{formatDate(expense.date)}</div>
                    <div className="col-span-2">
                      <p className="text-base text-gray-900 font-medium">{expense.description}</p>
                      {expense.notes && !isExpanded && (
                        <p className="text-sm text-gray-500 mt-1">{expense.notes.substring(0, 50)}{expense.notes.length > 50 ? '...' : ''}</p>
                      )}
                    </div>
                    <div className="col-span-2 text-base">
                      {hasCategory ? (
                        <span className="text-gray-900">{categories.find(cat => cat.id === expense.category_id)?.category_name}</span>
                      ) : (
                        <span className="text-orange-600 font-medium">⚠ No Category</span>
                      )}
                    </div>
                    <div className="col-span-2 text-base text-gray-900">
                      {accounts.find(acc => acc.id === expense.account_id)?.account_name || 'Unknown'}
                    </div>
                    <div className="col-span-2 text-base text-gray-900 font-medium">
                      {formatCurrency(expense.amount, expense.currency)}
                    </div>
                    <div className="col-span-1">
                      <span className="inline-block px-3 py-1 bg-yellow-100 text-yellow-700 rounded-full text-sm font-medium">
                        Pending
                      </span>
                    </div>
                  </div>

                  {isExpanded && (
                    <div className="border-b border-gray-100 bg-gray-50 p-6">
                      <div className="max-w-5xl mx-auto space-y-6">
                        {/* Summary Row */}
                        <div className="bg-white rounded-lg border border-gray-200 p-6 flex items-center justify-between">
                          <div className="flex gap-8">
                            <div>
                              <p className="text-base text-gray-900">{formatDate(expense.date)}</p>
                            </div>
                            <div>
                              <p className="text-base text-gray-900">{expense.description}</p>
                            </div>
                            <div>
                              <p className="text-base text-gray-900">
                                {hasCategory ? categories.find(cat => cat.id === expense.category_id)?.category_name : 'No Category'}
                              </p>
                            </div>
                            <div>
                              <p className="text-base text-gray-900">
                                {accounts.find(acc => acc.id === expense.account_id)?.account_name || 'Unknown'}
                              </p>
                            </div>
                          </div>
                          <span className="inline-block px-3 py-1 bg-yellow-100 text-yellow-700 rounded-full text-sm font-medium">
                            Pending
                          </span>
                        </div>

                        {/* Transaction Details Section */}
                        <div className="bg-white rounded-lg border border-gray-200 p-6 space-y-4">
                          <h3 className="text-xl font-bold text-gray-900">Transaction Details</h3>
                          <div className="border-t border-gray-200 pt-4 grid grid-cols-2 gap-4">
                            {expense.vendor && (
                              <div>
                                <p className="text-sm text-gray-500 mb-1">Vendor</p>
                                <p className="text-base text-gray-900">{expense.vendor}</p>
                              </div>
                            )}
                            {expense.payment_method && (
                              <div>
                                <p className="text-sm text-gray-500 mb-1">Payment Method</p>
                                <p className="text-base text-gray-900">{expense.payment_method}</p>
                              </div>
                            )}
                            {expense.taxes_fees && expense.taxes_fees > 0 && (
                              <div>
                                <p className="text-sm text-gray-500 mb-1">Taxes & Fees</p>
                                <p className="text-base text-gray-900">
                                  {formatCurrency(expense.taxes_fees, expense.currency)}
                                </p>
                              </div>
                            )}
                            {expense.recipient_id && (
                              <div>
                                <p className="text-sm text-gray-500 mb-1">Recipient ID</p>
                                <p className="text-base text-gray-900">{expense.recipient_id}</p>
                              </div>
                            )}
                          </div>
                          {expense.notes && (
                            <div className="border-t border-gray-200 pt-4">
                              <p className="text-sm text-gray-500 mb-1">Notes</p>
                              <p className="text-base text-gray-900">{expense.notes}</p>
                            </div>
                          )}
                        </div>

                        {/* Missing Category Warning */}
                        {!hasCategory && (
                          <div className="bg-white rounded-lg border border-gray-200 p-6 space-y-4">
                            <h3 className="text-xl font-bold text-gray-900">Review Needed</h3>
                            <div className="flex gap-4">
                              <AlertCircle size={24} className="text-yellow-500 flex-shrink-0 mt-1" />
                              <div>
                                <p className="text-base font-medium text-gray-900 mb-2">Please verify:</p>
                                <ul className="space-y-1">
                                  <li className="text-base text-gray-700 flex items-center gap-2">
                                    <span className="w-1.5 h-1.5 bg-gray-400 rounded-full"></span>
                                    Category
                                  </li>
                                </ul>
                              </div>
                            </div>
                          </div>
                        )}

                        {/* Action Buttons */}
                        <div className="flex gap-4 justify-end pt-4">
                          <button
                            onClick={(e) => {
                              e.stopPropagation();
                              setSelectedExpense(expense);
                              handleApproval(expense, 'reject');
                            }}
                            className="px-6 py-2 border border-gray-300 text-gray-700 rounded-lg text-base font-medium hover:bg-gray-50 transition-colors"
                          >
                            Reject
                          </button>
                          <button
                            onClick={(e) => {
                              e.stopPropagation();
                              setSelectedExpense(expense);
                              handleEditApproval(expense);
                            }}
                            className="px-6 py-2 border-2 border-yellow-600 text-yellow-700 rounded-lg text-base font-medium hover:bg-yellow-50 transition-colors"
                          >
                            Request Changes
                          </button>
                          <button
                            onClick={(e) => {
                              e.stopPropagation();
                              setSelectedExpense(expense);
                              handleApproval(expense, 'approve');
                            }}
                            className="px-6 py-2 bg-teal-700 text-white rounded-lg text-base font-medium hover:bg-teal-800 transition-colors"
                          >
                            Approve
                          </button>
                        </div>
                      </div>
                    </div>
                  )}
                </div>
              );
            })}
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
          title="Request Changes & Edit"
          size="lg"
        >
          <form onSubmit={(e) => { e.preventDefault(); submitEditApproval(); }} className="space-y-4">
            <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4 mb-4">
              <div className="flex items-start gap-3">
                <AlertCircle className="w-5 h-5 text-yellow-600 flex-shrink-0 mt-0.5" />
                <div>
                  <p className="text-sm font-medium text-yellow-800">Review and Edit Required Fields</p>
                  <p className="text-sm text-yellow-700 mt-1">Make necessary changes before approving this transaction</p>
                </div>
              </div>
            </div>

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
                  Category <span className="text-red-500">*</span>
                </label>
                <select
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
                  value={editFormData.category_id}
                  onChange={(e) => setEditFormData({ ...editFormData, category_id: e.target.value })}
                  required
                >
                  <option value="">Select Category</option>
                  {categories.map((category) => (
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
    </div>
  );
};

export default Approvals;
