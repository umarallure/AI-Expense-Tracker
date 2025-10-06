import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { ArrowUpRight, Clock, CheckCircle, Plus, AlertTriangle } from 'lucide-react';
import Card from '../components/ui/Card';
import Badge from '../components/ui/Badge';
import Button from '../components/ui/Button';
import { businessService, expenseService, accountService, categoryService } from '../services/business.service';
import type { Business, Expense, Account, Category } from '../types';

const Dashboard: React.FC = () => {
  const navigate = useNavigate();
  const [businesses, setBusinesses] = useState<Business[]>([]);
  const [selectedBusinessId, setSelectedBusinessId] = useState<string>('');
  const [expenses, setExpenses] = useState<Expense[]>([]);
  const [pendingExpenses, setPendingExpenses] = useState<Expense[]>([]);
  const [accounts, setAccounts] = useState<Account[]>([]);
  const [categories, setCategories] = useState<Category[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchInitialData();
  }, []);

  useEffect(() => {
    if (selectedBusinessId) {
      fetchBusinessData(selectedBusinessId);
    }
  }, [selectedBusinessId]);

  const fetchInitialData = async () => {
    try {
      setIsLoading(true);
      const response = await businessService.getBusinesses();
      setBusinesses(response.businesses);
      if (response.businesses.length > 0) {
        setSelectedBusinessId(response.businesses[0].id);
      }
    } catch (err) {
      console.error('Failed to fetch businesses:', err);
      setError('Failed to load dashboard data');
    } finally {
      setIsLoading(false);
    }
  };

  const fetchBusinessData = async (businessId: string) => {
    try {
      setError(null);
      const [expensesResponse, pendingResponse, accountsResponse, categoriesResponse] = await Promise.all([
        expenseService.getExpenses(businessId),
        expenseService.getPendingExpenses(businessId),
        accountService.getAccounts(businessId),
        categoryService.getCategories(businessId)
      ]);

      setExpenses(expensesResponse.transactions);
      setPendingExpenses(pendingResponse.transactions);
      setAccounts(accountsResponse.accounts);
      setCategories(categoriesResponse.categories);
    } catch (err) {
      console.error('Failed to fetch business data:', err);
      setError('Failed to load business data');
    }
  };

  // Calculate dashboard statistics
  const calculateStats = () => {
    // Calculate current month and year
    const currentMonth = new Date().getMonth();
    const currentYear = new Date().getFullYear();

    // Filter approved transactions for current month
    const currentMonthTransactions = expenses.filter(exp => {
      const expDate = new Date(exp.date);
      return expDate.getMonth() === currentMonth && expDate.getFullYear() === currentYear && exp.status === 'approved';
    });

    // Monthly Income: sum of approved income transactions for current month
    const monthlyIncome = currentMonthTransactions
      .filter(exp => exp.is_income)
      .reduce((sum, exp) => sum + exp.amount, 0);

    // Monthly Expense: sum of approved expense transactions for current month
    const monthlyExpenses = currentMonthTransactions
      .filter(exp => !exp.is_income)
      .reduce((sum, exp) => sum + exp.amount, 0);

    // Net Flow: Monthly Income - Monthly Expense
    const netFlow = monthlyIncome - monthlyExpenses;

    // Account Balance: sum of current_balance from all active accounts
    const totalBalance = accounts
      .filter(acc => acc.is_active)
      .reduce((sum, acc) => sum + acc.current_balance, 0);

    const pendingCount = pendingExpenses.length;

    return {
      monthlyIncome,
      monthlyExpenses,
      netFlow,
      totalBalance,
      pendingCount
    };
  };

  const stats = calculateStats();

  const statsData = [
    {
      label: 'Monthly Income',
      value: `$${stats.monthlyIncome.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`,
      change: '+12.5%', // This would need historical data to calculate
      isPositive: true,
      icon: ArrowUpRight,
    },
    {
      label: 'Monthly Expense',
      value: `$${stats.monthlyExpenses.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`,
      change: '-8.2%', // This would need historical data to calculate
      isPositive: false,
      icon: ArrowUpRight,
    },
    {
      label: 'Net Flow',
      value: `$${stats.netFlow.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`,
      change: stats.netFlow >= 0 ? 'Positive' : 'Negative',
      isPositive: stats.netFlow >= 0,
      icon: stats.netFlow >= 0 ? ArrowUpRight : Clock,
    },
    {
      label: 'Account Balance',
      value: `$${stats.totalBalance.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`,
      change: `${accounts.filter(acc => acc.is_active).length} active account${accounts.filter(acc => acc.is_active).length !== 1 ? 's' : ''}`,
      isPositive: true,
      icon: CheckCircle,
    },
  ];

  const pendingTasks = pendingExpenses.slice(0, 5).map(expense => ({
    id: expense.id,
    title: `Review expense: ${expense.description}`,
    type: 'approval' as const,
    dueDate: new Date(expense.date).toLocaleDateString(),
    priority: 'high' as const,
  }));

  const getCategoryName = (categoryId: string) => {
    const category = categories.find(cat => cat.id === categoryId);
    return category ? category.category_name : 'Unknown';
  };

  const getTaskTypeColor = (type: string) => {
    switch (type) {
      case 'approval':
        return 'warning';
      case 'review':
        return 'info';
      case 'urgent':
        return 'danger';
      default:
        return 'default';
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'approved':
        return 'success';
      case 'pending':
        return 'warning';
      case 'rejected':
        return 'danger';
      case 'draft':
        return 'default';
      default:
        return 'default';
    }
  };

  const recentExpenses = expenses
    .sort((a, b) => new Date(b.date).getTime() - new Date(a.date).getTime())
    .slice(0, 5);

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-center">
          <div className="w-16 h-16 border-4 border-primary-500 border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
          <p className="text-gray-600">Loading dashboard...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-center">
          <div className="w-16 h-16 text-red-500 mx-auto mb-4">
            <AlertTriangle className="w-full h-full" />
          </div>
          <p className="text-red-600">{error}</p>
          <Button
            variant="primary"
            className="mt-4"
            onClick={() => {
              setError(null);
              fetchInitialData();
            }}
          >
            Try Again
          </Button>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Dashboard</h1>
          <p className="text-gray-500 mt-1">Welcome back! Here's what's happening today.</p>
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
          <Button variant="primary" icon={<Plus className="w-5 h-5" />} onClick={() => navigate('/expenses')}>
            New Expense
          </Button>
        </div>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {statsData.map((stat, index) => (
          <Card key={index}>
            <div className="flex items-start justify-between">
              <div>
                <p className="text-sm text-gray-500 font-medium">{stat.label}</p>
                <p className="text-2xl font-bold text-gray-900 mt-2">{stat.value}</p>
                <p className={`text-sm mt-2 ${stat.isPositive ? 'text-green-600' : 'text-red-600'}`}>
                  {stat.change}
                </p>
              </div>
              <div className={`p-3 rounded-lg ${stat.isPositive ? 'bg-green-50' : 'bg-red-50'}`}>
                <stat.icon className={`w-6 h-6 ${stat.isPositive ? 'text-green-600' : 'text-red-600'}`} />
              </div>
            </div>
          </Card>
        ))}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Pending Tasks */}
        <Card
          title="Pending Tasks"
          subtitle="Items requiring your attention"
          headerAction={<Button variant="ghost" size="sm" onClick={() => navigate('/approvals')}>View all</Button>}
        >
          <div className="space-y-3">
            {pendingTasks.map((task) => (
              <div
                key={task.id}
                className="flex items-start justify-between p-3 bg-gray-50 rounded-lg hover:bg-gray-100 transition-colors cursor-pointer"
              >
                <div className="flex-1">
                  <p className="text-sm font-medium text-gray-900">{task.title}</p>
                  <p className="text-xs text-gray-500 mt-1">{task.dueDate}</p>
                </div>
                <Badge variant={getTaskTypeColor(task.type) as any} size="sm">
                  {task.type}
                </Badge>
              </div>
            ))}
          </div>
        </Card>

        {/* Quick Actions */}
        <Card title="Quick Actions" subtitle="Common tasks">
          <div className="grid grid-cols-2 gap-3">
            <button className="p-4 bg-primary-50 rounded-lg hover:bg-primary-100 transition-colors" onClick={() => navigate('/expenses')}>
              <Plus className="w-6 h-6 text-primary-600 mx-auto mb-2" />
              <p className="text-sm font-medium text-primary-700">New Expense</p>
            </button>
            <button className="p-4 bg-purple-50 rounded-lg hover:bg-purple-100 transition-colors" onClick={() => navigate('/approvals')}>
              <CheckCircle className="w-6 h-6 text-purple-600 mx-auto mb-2" />
              <p className="text-sm font-medium text-purple-700">Approvals</p>
            </button>
            <button className="p-4 bg-blue-50 rounded-lg hover:bg-blue-100 transition-colors" onClick={() => navigate('/reports')}>
              <ArrowUpRight className="w-6 h-6 text-blue-600 mx-auto mb-2" />
              <p className="text-sm font-medium text-blue-700">Reports</p>
            </button>
            <button className="p-4 bg-orange-50 rounded-lg hover:bg-orange-100 transition-colors" onClick={() => navigate('/expenses')}>
              <Clock className="w-6 h-6 text-orange-600 mx-auto mb-2" />
              <p className="text-sm font-medium text-orange-700">History</p>
            </button>
          </div>
        </Card>

        {/* Monthly Summary */}
        <Card title="Monthly Summary" subtitle={`${new Date().toLocaleDateString('en-US', { month: 'long', year: 'numeric' })}`}>
          <div className="space-y-4">
            <div>
              <div className="flex items-center justify-between mb-2">
                <span className="text-sm text-gray-600">Spent</span>
                <span className="text-sm font-semibold text-gray-900">
                  ${stats.monthlyExpenses.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                </span>
              </div>
              <div className="h-2 bg-gray-200 rounded-full overflow-hidden">
                <div
                  className="h-full bg-primary-500 transition-all duration-300"
                  style={{ width: `${Math.min((stats.monthlyExpenses / 12000) * 100, 100)}%` }}
                />
              </div>
            </div>
            <div>
              <div className="flex items-center justify-between mb-2">
                <span className="text-sm text-gray-600">Budget</span>
                <span className="text-sm font-semibold text-gray-900">$12,000</span>
              </div>
              <div className="h-2 bg-gray-200 rounded-full" />
            </div>
            <div className="pt-3 border-t border-gray-200">
              <div className="flex items-center justify-between text-sm">
                <span className="text-gray-600">Remaining</span>
                <span className={`font-semibold ${Math.max(0, 12000 - stats.monthlyExpenses) >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                  ${Math.max(0, 12000 - stats.monthlyExpenses).toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                </span>
              </div>
            </div>
          </div>
        </Card>
      </div>

      {/* Recent Expenses */}
      <Card
        title="Recent Expenses"
        subtitle="Latest expense submissions"
        headerAction={<Button variant="ghost" size="sm" onClick={() => navigate('/expenses')}>View all</Button>}
      >
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead>
              <tr className="border-b border-gray-200">
                <th className="text-left py-3 px-4 text-sm font-semibold text-gray-700">Date</th>
                <th className="text-left py-3 px-4 text-sm font-semibold text-gray-700">Description</th>
                <th className="text-left py-3 px-4 text-sm font-semibold text-gray-700">Category</th>
                <th className="text-right py-3 px-4 text-sm font-semibold text-gray-700">Amount</th>
                <th className="text-center py-3 px-4 text-sm font-semibold text-gray-700">Status</th>
              </tr>
            </thead>
            <tbody>
              {recentExpenses.map((expense) => (
                <tr key={expense.id} className="border-b border-gray-100 hover:bg-gray-50 transition-colors">
                  <td className="py-3 px-4 text-sm text-gray-600">{expense.date}</td>
                  <td className="py-3 px-4 text-sm font-medium text-gray-900">{expense.description}</td>
                  <td className="py-3 px-4 text-sm text-gray-600">{getCategoryName(expense.category_id)}</td>
                  <td className="py-3 px-4 text-sm font-semibold text-gray-900 text-right">
                    ${expense.amount.toFixed(2)}
                  </td>
                  <td className="py-3 px-4 text-center">
                    <Badge variant={getStatusColor(expense.status) as any} size="sm">
                      {expense.status}
                    </Badge>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </Card>
    </div>
  );
};

export default Dashboard;
