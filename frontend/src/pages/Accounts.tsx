import React, { useState, useEffect } from 'react';
import { Plus, Edit2, Trash2, CreditCard, Building2, DollarSign, TrendingUp } from 'lucide-react';
import Button from '../components/ui/Button';
import Card from '../components/ui/Card';
import Modal from '../components/ui/Modal';
import Input from '../components/ui/Input';
import Badge from '../components/ui/Badge';
import { accountService, businessService } from '../services/business.service';
import type { Account, Business, AccountCreate } from '../types';

const Accounts: React.FC = () => {
  const [accounts, setAccounts] = useState<Account[]>([]);
  const [businesses, setBusinesses] = useState<Business[]>([]);
  const [selectedBusinessId, setSelectedBusinessId] = useState<string>('');
  const [isLoading, setIsLoading] = useState(true);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [editingAccount, setEditingAccount] = useState<Account | null>(null);
  const [formData, setFormData] = useState<AccountCreate>({
    business_id: '',
    account_name: '',
    account_type: 'checking',
    account_number_masked: '',
    institution_name: '',
    current_balance: 0,
    currency: 'USD',
  });

  useEffect(() => {
    fetchBusinesses();
  }, []);

  useEffect(() => {
    if (selectedBusinessId) {
      fetchAccounts(selectedBusinessId);
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

  const fetchAccounts = async (businessId: string) => {
    try {
      setIsLoading(true);
      const response = await accountService.getAccounts(businessId);
      setAccounts(response.accounts);
    } catch (error) {
      console.error('Failed to fetch accounts:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const handleOpenModal = (account?: Account) => {
    if (account) {
      setEditingAccount(account);
      setFormData({
        business_id: account.business_id,
        account_name: account.account_name,
        account_type: account.account_type,
        account_number_masked: account.account_number_masked || '',
        institution_name: account.institution_name || '',
        current_balance: account.current_balance,
        currency: account.currency,
      });
    } else {
      setEditingAccount(null);
      setFormData({
        business_id: selectedBusinessId,
        account_name: '',
        account_type: 'checking',
        account_number_masked: '',
        institution_name: '',
        current_balance: 0,
        currency: 'USD',
      });
    }
    setIsModalOpen(true);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      // Ensure business_id is set for new accounts
      const accountData = {
        ...formData,
        business_id: formData.business_id || selectedBusinessId,
      };

      if (editingAccount) {
        await accountService.updateAccount(editingAccount.id, accountData);
      } else {
        await accountService.createAccount(accountData);
      }
      setIsModalOpen(false);
      if (selectedBusinessId) {
        fetchAccounts(selectedBusinessId);
      }
    } catch (error) {
      console.error('Failed to save account:', error);
    }
  };

  const handleDelete = async (id: string) => {
    if (window.confirm('Are you sure you want to delete this account?')) {
      try {
        await accountService.updateAccount(id, { is_active: false } as any);
        if (selectedBusinessId) {
          fetchAccounts(selectedBusinessId);
        }
      } catch (error) {
        console.error('Failed to delete account:', error);
      }
    }
  };

  const getAccountTypeIcon = (type: string) => {
    switch (type) {
      case 'credit_card':
        return <CreditCard className="w-6 h-6 text-primary-600" />;
      case 'checking':
      case 'savings':
      default:
        return <Building2 className="w-6 h-6 text-primary-600" />;
    }
  };

  const getAccountTypeBadge = (type: string) => {
    const types: Record<string, string> = {
      checking: 'Checking',
      savings: 'Savings',
      credit_card: 'Credit Card',
      investment: 'Investment',
      loan: 'Loan',
      cash: 'Cash',
      other: 'Other',
    };
    return types[type] || type;
  };

  const formatCurrency = (amount: number, currency: string) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: currency,
    }).format(amount);
  };

  const calculateTotals = () => {
    const total = accounts.reduce((sum, acc) => sum + parseFloat(String(acc.current_balance)), 0);
    const activeCount = accounts.filter(acc => acc.is_active).length;
    return { total, activeCount };
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-center">
          <div className="w-16 h-16 border-4 border-primary-500 border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
          <p className="text-gray-600">Loading accounts...</p>
        </div>
      </div>
    );
  }

  const { total: totalBalance, activeCount } = calculateTotals();

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Accounts</h1>
          <p className="text-gray-500 mt-1">Manage your financial accounts</p>
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
          <Button
            variant="primary"
            icon={<Plus className="w-5 h-5" />}
            onClick={() => handleOpenModal()}
            disabled={!selectedBusinessId}
          >
            Add Account
          </Button>
        </div>
      </div>

      {/* Summary Cards */}
      {accounts.length > 0 && (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <Card>
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-500">Total Balance</p>
                <p className="text-2xl font-bold text-gray-900 mt-1">
                  {formatCurrency(totalBalance, 'USD')}
                </p>
              </div>
              <div className="w-12 h-12 bg-green-100 rounded-xl flex items-center justify-center">
                <DollarSign className="w-6 h-6 text-green-600" />
              </div>
            </div>
          </Card>
          <Card>
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-500">Active Accounts</p>
                <p className="text-2xl font-bold text-gray-900 mt-1">{activeCount}</p>
              </div>
              <div className="w-12 h-12 bg-blue-100 rounded-xl flex items-center justify-center">
                <CreditCard className="w-6 h-6 text-blue-600" />
              </div>
            </div>
          </Card>
          <Card>
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-500">Average Balance</p>
                <p className="text-2xl font-bold text-gray-900 mt-1">
                  {formatCurrency(activeCount > 0 ? totalBalance / activeCount : 0, 'USD')}
                </p>
              </div>
              <div className="w-12 h-12 bg-purple-100 rounded-xl flex items-center justify-center">
                <TrendingUp className="w-6 h-6 text-purple-600" />
              </div>
            </div>
          </Card>
        </div>
      )}

      {/* Accounts Grid */}
      {!selectedBusinessId ? (
        <Card>
          <div className="text-center py-12">
            <Building2 className="w-16 h-16 text-gray-300 mx-auto mb-4" />
            <h3 className="text-lg font-semibold text-gray-900 mb-2">No business selected</h3>
            <p className="text-gray-500">Please create a business first to manage accounts</p>
          </div>
        </Card>
      ) : accounts.length === 0 ? (
        <Card>
          <div className="text-center py-12">
            <CreditCard className="w-16 h-16 text-gray-300 mx-auto mb-4" />
            <h3 className="text-lg font-semibold text-gray-900 mb-2">No accounts yet</h3>
            <p className="text-gray-500 mb-6">Get started by adding your first financial account</p>
            <Button variant="primary" onClick={() => handleOpenModal()}>
              Create Account
            </Button>
          </div>
        </Card>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {accounts.map((account) => (
            <Card key={account.id} className="hover:shadow-md transition-shadow">
              <div className="space-y-4">
                {/* Account Header */}
                <div className="flex items-start justify-between">
                  <div className="flex items-center space-x-3">
                    <div className="w-12 h-12 bg-primary-100 rounded-xl flex items-center justify-center">
                      {getAccountTypeIcon(account.account_type)}
                    </div>
                    <div>
                      <h3 className="font-semibold text-gray-900">{account.account_name}</h3>
                      <Badge variant="primary" size="sm">
                        {getAccountTypeBadge(account.account_type)}
                      </Badge>
                    </div>
                  </div>
                  <Badge variant={account.is_active ? 'success' : 'default'} size="sm">
                    {account.is_active ? 'Active' : 'Inactive'}
                  </Badge>
                </div>

                {/* Balance */}
                <div className="bg-gray-50 rounded-lg p-4">
                  <p className="text-sm text-gray-500 mb-1">Current Balance</p>
                  <p className="text-2xl font-bold text-gray-900">
                    {formatCurrency(account.current_balance, account.currency)}
                  </p>
                </div>

                {/* Account Details */}
                <div className="space-y-2 text-sm">
                  {account.institution_name && (
                    <div className="flex items-center text-gray-600">
                      <span className="font-medium mr-2">Bank:</span>
                      <span>{account.institution_name}</span>
                    </div>
                  )}
                  {account.account_number_masked && (
                    <div className="flex items-center text-gray-600">
                      <span className="font-medium mr-2">Account:</span>
                      <span>****{account.account_number_masked.slice(-4)}</span>
                    </div>
                  )}
                </div>

                {/* Actions */}
                <div className="flex items-center space-x-2 pt-4 border-t border-gray-200">
                  <Button
                    variant="outline"
                    size="sm"
                    icon={<Edit2 className="w-4 h-4" />}
                    onClick={() => handleOpenModal(account)}
                    className="flex-1"
                  >
                    Edit
                  </Button>
                  <Button
                    variant="ghost"
                    size="sm"
                    icon={<Trash2 className="w-4 h-4" />}
                    onClick={() => handleDelete(account.id)}
                    className="text-red-600 hover:bg-red-50"
                  >
                    Delete
                  </Button>
                </div>
              </div>
            </Card>
          ))}
        </div>
      )}

      {/* Create/Edit Modal */}
      <Modal
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
        title={editingAccount ? 'Edit Account' : 'Create New Account'}
        size="md"
      >
        <form onSubmit={handleSubmit} className="space-y-4">
          <Input
            label="Account Name"
            value={formData.account_name}
            onChange={(e) => setFormData({ ...formData, account_name: e.target.value })}
            required
            placeholder="e.g., Main Checking"
          />

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1.5">
              Account Type <span className="text-red-500">*</span>
            </label>
            <select
              value={formData.account_type}
              onChange={(e) => setFormData({ ...formData, account_type: e.target.value })}
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
              required
            >
              <option value="checking">Checking</option>
              <option value="savings">Savings</option>
              <option value="credit_card">Credit Card</option>
              <option value="investment">Investment</option>
              <option value="loan">Loan</option>
              <option value="cash">Cash</option>
              <option value="other">Other</option>
            </select>
          </div>

          <Input
            label="Institution Name"
            value={formData.institution_name}
            onChange={(e) => setFormData({ ...formData, institution_name: e.target.value })}
            placeholder="e.g., Chase Bank"
          />

          <Input
            label="Account Number (Masked)"
            value={formData.account_number_masked}
            onChange={(e) => setFormData({ ...formData, account_number_masked: e.target.value })}
            placeholder="Last 4 digits or full number"
          />

          <div className="grid grid-cols-2 gap-4">
            <Input
              label="Current Balance"
              type="number"
              step="0.01"
              value={formData.current_balance}
              onChange={(e) => setFormData({ ...formData, current_balance: parseFloat(e.target.value) || 0 })}
              placeholder="0.00"
            />
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1.5">Currency</label>
              <select
                value={formData.currency}
                onChange={(e) => setFormData({ ...formData, currency: e.target.value })}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
              >
                <option value="USD">USD</option>
                <option value="EUR">EUR</option>
                <option value="GBP">GBP</option>
                <option value="CAD">CAD</option>
              </select>
            </div>
          </div>

          <div className="flex justify-end space-x-3 pt-4 border-t border-gray-200">
            <Button type="button" variant="ghost" onClick={() => setIsModalOpen(false)}>
              Cancel
            </Button>
            <Button type="submit" variant="primary">
              {editingAccount ? 'Update Account' : 'Create Account'}
            </Button>
          </div>
        </form>
      </Modal>
    </div>
  );
};

export default Accounts;
