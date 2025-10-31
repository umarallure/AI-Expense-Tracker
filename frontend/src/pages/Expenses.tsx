import React, { useState, useEffect } from 'react';
import { Search, Filter, FileText, ChevronRight, AlertCircle, AlertTriangle } from 'lucide-react';
import Button from '../components/ui/Button';
import Card from '../components/ui/Card';
import Modal from '../components/ui/Modal';
import Input from '../components/ui/Input';
import FileUpload from '../components/ui/FileUpload';
import DuplicateWarning from '../components/ui/DuplicateWarning';
import { CategorySuggestion } from '../components/ui/CategorySuggestion';
import DocumentPreview from '../components/DocumentPreview';
import { businessService, categoryService, accountService, expenseService, documentService, categorySuggestionService } from '../services/business.service';
import { detectDuplicates, findExactDuplicates, DuplicateMatch } from '../utils/duplicateDetection';
import type { Business, Expense, ExpenseStatus, Category, Account, CreateExpenseRequest, FileAttachment, CategorySuggestion as CategorySuggestionType } from '../types';

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
  const [expandedId, setExpandedId] = useState<string | null>(null);
  const [statusFilter, setStatusFilter] = useState<ExpenseStatus | 'all'>('all');
  const [missingFieldsFilter, setMissingFieldsFilter] = useState<boolean>(false);
  const [attachedFiles, setAttachedFiles] = useState<FileAttachment[]>([]);
  const [isUploading, setIsUploading] = useState(false);
  const [potentialDuplicates, setPotentialDuplicates] = useState<DuplicateMatch[]>([]);
  const [showDuplicateWarning, setShowDuplicateWarning] = useState(false);
  const [duplicateGroups, setDuplicateGroups] = useState<Map<string, Expense[]>>(new Map());
  const [categorySuggestions, setCategorySuggestions] = useState<CategorySuggestionType[]>([]);
  const [currentPage, setCurrentPage] = useState(1);
  const [pageSize, setPageSize] = useState(10);
  const [totalCount, setTotalCount] = useState(0);
  const [formData, setFormData] = useState({
    date: '',
    amount: '',
    description: '',
    category_id: '',
    account_id: '',
    status: 'pending',
    is_income: false,
    notes: '',
    vendor: '',
    taxes_fees: '',
    payment_method: '',
    recipient_id: '',
  });

  useEffect(() => {
    fetchBusinesses();
  }, []);

  useEffect(() => {
    if (selectedBusinessId) {
      // Fetch categories and accounts first, then expenses
      fetchCategoriesAndAccounts(selectedBusinessId).then(() => {
        setCurrentPage(1); // Reset to first page when business changes
        fetchExpenses(selectedBusinessId, 1);
      });
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
      console.log('Fetching categories for business ID:', businessId);
      const [categoriesResponse, accountsResponse] = await Promise.all([
        categoryService.getCategories(businessId),
        accountService.getAccounts(businessId)
      ]);
      console.log('Fetched categories count:', categoriesResponse.categories?.length || 0);
      setCategories(categoriesResponse.categories);
      setAccounts(accountsResponse.accounts);
    } catch (error) {
      console.error('Failed to fetch categories and accounts:', error);
    }
  };

  const fetchExpenses = async (businessId: string, page: number = currentPage, size: number = pageSize) => {
    try {
      const skip = (page - 1) * size;
      const response = await expenseService.getExpenses(businessId, { skip, limit: size });
      setExpenses(response.transactions);
      setTotalCount(response.total);
      
      // Detect existing duplicate groups
      const duplicates = findExactDuplicates(response.transactions);
      setDuplicateGroups(duplicates);

      // Fetch category suggestions for uncategorized transactions
      fetchCategorySuggestions(businessId, response.transactions);
    } catch (error) {
      console.error('Failed to fetch expenses:', error);
      setExpenses([]);
      setTotalCount(0);
    }
  };

  const fetchCategorySuggestions = async (businessId: string, transactions: Expense[]) => {
    // Only fetch suggestions for transactions without categories
    const uncategorizedTransactions = transactions.filter(t => !t.category_id);
    
    if (uncategorizedTransactions.length === 0) {
      setCategorySuggestions([]);
      return;
    }

    try {
      const response = await categorySuggestionService.getBulkSuggestions(businessId, {
        transactionIds: uncategorizedTransactions.map(t => t.id),
        maxSuggestions: 50
      });
      
      setCategorySuggestions(response.suggestions);
    } catch (error) {
      console.error('Failed to fetch category suggestions:', error);
      setCategorySuggestions([]);
    }
  };

  // Check for duplicates when form data changes
  useEffect(() => {
    if (
      !isModalOpen ||
      !formData.date ||
      !formData.amount ||
      !formData.description ||
      expenses.length === 0
    ) {
      setPotentialDuplicates([]);
      setShowDuplicateWarning(false);
      return;
    }

    // Don't check for duplicates when editing (unless we want to warn about other duplicates)
    if (editingExpense) {
      return;
    }

    const result = detectDuplicates(
      {
        date: formData.date,
        amount: parseFloat(formData.amount),
        vendor: formData.vendor,
        description: formData.description,
      },
      expenses,
      {
        fuzzyMatchThreshold: 0.85,
        dateTolerance: 2, // Check within 2 days
      }
    );

    if (result.isDuplicate) {
      setPotentialDuplicates(result.duplicates);
      setShowDuplicateWarning(true);
    } else {
      setPotentialDuplicates([]);
      setShowDuplicateWarning(false);
    }
  }, [
    formData.date,
    formData.amount,
    formData.description,
    formData.vendor,
    expenses,
    isModalOpen,
    editingExpense,
  ]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsUploading(true);
    
    try {
      // Check for missing required fields when approving
      if (formData.status === 'approved') {
        const testExpense: Expense = {
          ...formData,
          id: editingExpense?.id || '',
          business_id: selectedBusinessId,
          user_id: '',
          currency: 'USD',
          date: formData.date,
          amount: parseFloat(formData.amount),
          is_income: formData.is_income,
          status: formData.status as ExpenseStatus,
          created_at: editingExpense?.created_at || '',
          updated_at: editingExpense?.updated_at || '',
          description: formData.description,
          vendor: formData.vendor || undefined,
          taxes_fees: formData.taxes_fees ? parseFloat(formData.taxes_fees) : undefined,
          payment_method: formData.payment_method || undefined,
          recipient_id: formData.recipient_id || undefined,
        };
        
        const missingFieldsCheck = getMissingFields(testExpense);
        if (missingFieldsCheck.length > 0) {
          alert(`Cannot approve transaction with missing required fields: ${missingFieldsCheck.join(', ')}. Please complete all required information first.`);
          setIsUploading(false);
          return;
        }
      }
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
        vendor: formData.vendor || undefined,
        taxes_fees: formData.taxes_fees ? parseFloat(formData.taxes_fees) : undefined,
        payment_method: formData.payment_method || undefined,
        recipient_id: formData.recipient_id || undefined,
      };

      let transactionId: string;
      
      if (editingExpense) {
        const updatedExpense = await expenseService.updateExpense(editingExpense.id, expenseData);
        transactionId = updatedExpense.id;
      } else {
        const createdExpense = await expenseService.createExpense(expenseData);
        transactionId = createdExpense.id;
      }
      
      // Upload attached documents if any
      if (attachedFiles.length > 0) {
        const uploadPromises = attachedFiles.map(fileAttachment =>
          documentService.uploadDocument({
            file: fileAttachment.file,
            business_id: selectedBusinessId,
            transaction_id: transactionId,
            document_type: fileAttachment.document_type,
            description: fileAttachment.description,
            tags: fileAttachment.tags
          })
        );
        
        await Promise.all(uploadPromises);
      }
      
      alert(
        editingExpense
          ? `Expense updated successfully!${attachedFiles.length > 0 ? ` ${attachedFiles.length} document(s) attached.` : ''}`
          : `Expense submitted for approval successfully!${attachedFiles.length > 0 ? ` ${attachedFiles.length} document(s) attached.` : ''}`
      );
      
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
        vendor: '',
        taxes_fees: '',
        payment_method: '',
        recipient_id: '',
      });
      setAttachedFiles([]);
      setEditingExpense(null);
      setIsModalOpen(false);
      
      // Refresh expenses list (reset to page 1 to show new transaction)
      setCurrentPage(1);
      fetchExpenses(selectedBusinessId, 1);
      
    } catch (error) {
      console.error('Failed to save expense:', error);
      alert('Failed to save expense. Please try again.');
    } finally {
      setIsUploading(false);
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
      vendor: expense.vendor || '',
      taxes_fees: expense.taxes_fees?.toString() || '',
      payment_method: expense.payment_method || '',
      recipient_id: expense.recipient_id || '',
    });
    setIsModalOpen(true);
  };

  const handleDelete = async (expenseId: string) => {
    if (!confirm('Are you sure you want to delete this expense? This action cannot be undone.')) {
      return;
    }

    try {
      await expenseService.deleteExpense(expenseId, selectedBusinessId);
      
      // Check if we need to go back a page (if this was the last item on the current page)
      const remainingItems = expenses.length - 1;
      if (remainingItems === 0 && currentPage > 1) {
        setCurrentPage(currentPage - 1);
        fetchExpenses(selectedBusinessId, currentPage - 1);
      } else {
        fetchExpenses(selectedBusinessId, currentPage);
      }
      
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
    const matchesMissingFields = !missingFieldsFilter || hasMissingFields(expense);
    return matchesSearch && matchesStatus && matchesMissingFields;
  });

  const toggleRow = (expenseId: string) => {
    setExpandedId(expandedId === expenseId ? null : expenseId);
  };

  // Check if a transaction is part of a duplicate group
  const isDuplicateTransaction = (transactionId: string): boolean => {
    for (const group of duplicateGroups.values()) {
      if (group.some(t => t.id === transactionId)) {
        return true;
      }
    }
    return false;
  };

  // Get duplicate group for a transaction
  const getDuplicateGroup = (transactionId: string): Expense[] | null => {
    for (const group of duplicateGroups.values()) {
      if (group.some(t => t.id === transactionId)) {
        return group;
      }
    }
    return null;
  };

  // Handle viewing a specific transaction (scroll to it and expand)
  const handleViewTransaction = (transactionId: string) => {
    setExpandedId(transactionId);
    // Close the modal if open
    setIsModalOpen(false);
    // Scroll to the transaction
    setTimeout(() => {
      const element = document.getElementById(`transaction-${transactionId}`);
      if (element) {
        element.scrollIntoView({ behavior: 'smooth', block: 'center' });
      }
    }, 100);
  };

  // Handle category suggestion application
  const handleCategorySuggestionApplied = (transactionId: string, categoryId: string) => {
    // Update the transaction in the local state
    setExpenses(prevExpenses => 
      prevExpenses.map(expense => 
        expense.id === transactionId 
          ? { ...expense, category_id: categoryId }
          : expense
      )
    );
    
    // Remove the suggestion from the list
    setCategorySuggestions(prevSuggestions => 
      prevSuggestions.filter(suggestion => suggestion.transaction_id !== transactionId)
    );
  };

  // Handle category suggestion dismissal
  const handleCategorySuggestionDismissed = (transactionId: string) => {
    // Remove the suggestion from the list
    setCategorySuggestions(prevSuggestions => 
      prevSuggestions.filter(suggestion => suggestion.transaction_id !== transactionId)
    );
  };

  // Get category suggestion for a transaction
  const getCategorySuggestionForTransaction = (transactionId: string): CategorySuggestionType | undefined => {
    return categorySuggestions.find(suggestion => suggestion.transaction_id === transactionId);
  };

  // Check for missing required fields in a transaction
  const getMissingFields = (expense: Expense): string[] => {
    const missing: string[] = [];

    if (!expense.category_id) {
      missing.push('Category');
    }

    if (!expense.account_id) {
      missing.push('Account');
    }

    if (!expense.payment_method) {
      missing.push('Payment Method');
    }

    if (!expense.vendor && !expense.description.includes('Transfer') && !expense.description.includes('Deposit')) {
      missing.push('Vendor');
    }

    if (!expense.amount || expense.amount <= 0) {
      missing.push('Amount');
    }

    return missing;
  };

  // Check if transaction has missing required fields
  const hasMissingFields = (expense: Expense): boolean => {
    return getMissingFields(expense).length > 0;
  };

  // Component to display document count for a transaction
  const DocumentCount: React.FC<{ transactionId: string }> = ({ transactionId }) => {
    const [count, setCount] = useState<number>(0);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
      const fetchDocumentCount = async () => {
        try {
          const response = await documentService.getDocuments(selectedBusinessId, transactionId);
          setCount(response.total);
        } catch (error) {
          console.error('Failed to fetch document count:', error);
          setCount(0);
        } finally {
          setLoading(false);
        }
      };
      fetchDocumentCount();
    }, [transactionId]);

    if (loading) {
      return <span className="text-gray-400 text-xs">...</span>;
    }

    if (count === 0) {
      return <span className="text-gray-400 text-xs">-</span>;
    }

    return (
      <div className="flex items-center space-x-1 text-primary-600">
        <FileText className="w-4 h-4" />
        <span className="text-sm font-medium">{count}</span>
      </div>
    );
  };

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
    <div className="min-h-screen bg-white p-8">
      <div className="max-w-7xl mx-auto space-y-6">
        {/* Header */}
        <div className="flex items-center justify-between mb-8">
          <h1 className="text-4xl font-bold tracking-tight">TRANSACTIONS</h1>
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
            <button className="px-6 py-2 border border-gray-300 rounded-lg text-base font-medium hover:bg-gray-50 transition-colors">
              Export
            </button>
            <button 
              onClick={() => setIsModalOpen(true)}
              className="px-6 py-2 bg-teal-700 text-white rounded-lg text-base font-medium hover:bg-teal-800 transition-colors"
            >
              Add Transaction
            </button>
          </div>
        </div>

        {/* Filters */}
        <Card>
          <div className="flex items-center space-x-4">
            <div className="flex-1 relative">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-5 h-5" />
              <input
                type="text"
                placeholder="Search transactions..."
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
            <div className="flex items-center space-x-2">
              <label className="flex items-center space-x-2 text-sm text-gray-700">
                <input
                  type="checkbox"
                  checked={missingFieldsFilter}
                  onChange={(e) => setMissingFieldsFilter(e.target.checked)}
                  className="rounded border-gray-300 text-primary-600 focus:ring-primary-500"
                />
                <span>Show only transactions needing review</span>
              </label>
            </div>
          </div>
        </Card>

      {/* Duplicate Detection Banner */}
      {duplicateGroups.size > 0 && (
        <Card>
          <div className="flex items-start gap-3 bg-yellow-50 border border-yellow-200 rounded-lg p-4">
            <AlertTriangle className="w-5 h-5 text-yellow-600 flex-shrink-0 mt-0.5" />
            <div className="flex-1">
              <h3 className="font-semibold text-yellow-900 mb-1">
                {duplicateGroups.size} Duplicate Group{duplicateGroups.size > 1 ? 's' : ''} Detected
              </h3>
              <p className="text-sm text-yellow-800">
                We've detected {duplicateGroups.size} group{duplicateGroups.size > 1 ? 's' : ''} of potential duplicate transactions in your records.
                Duplicate transactions are marked with <AlertTriangle className="w-4 h-4 inline text-yellow-600" /> in the list below.
                Click on a transaction to see details and identify duplicates.
              </p>
            </div>
          </div>
        </Card>
      )}

      {/* Category Suggestions Banner */}
      {categorySuggestions.length > 0 && (
        <Card>
          <div className="flex items-start gap-3 bg-blue-50 border border-blue-200 rounded-lg p-4">
            <AlertCircle className="w-5 h-5 text-blue-600 flex-shrink-0 mt-0.5" />
            <div className="flex-1">
              <h3 className="font-semibold text-blue-900 mb-1">
                Smart Category Suggestions Available
              </h3>
              <p className="text-sm text-blue-800">
                We've analyzed {categorySuggestions.length} uncategorized transaction{categorySuggestions.length > 1 ? 's' : ''} and found intelligent category suggestions.
                Transactions with suggestions are highlighted in the list below. Click on a transaction to see and apply suggestions.
              </p>
            </div>
          </div>
        </Card>
      )}

      {/* Missing Fields Banner */}
      {(() => {
        const transactionsWithMissingFields = expenses.filter(expense => hasMissingFields(expense)).length;
        return transactionsWithMissingFields > 0 && (
          <Card>
            <div className="flex items-start gap-3 bg-red-50 border border-red-200 rounded-lg p-4">
              <AlertTriangle className="w-5 h-5 text-red-600 flex-shrink-0 mt-0.5" />
              <div className="flex-1">
                <h3 className="font-semibold text-red-900 mb-1">
                  {transactionsWithMissingFields} Transaction{transactionsWithMissingFields > 1 ? 's' : ''} Need{transactionsWithMissingFields === 1 ? 's' : ''} Review
                </h3>
                <p className="text-sm text-red-800">
                  {transactionsWithMissingFields} transaction{transactionsWithMissingFields > 1 ? 's have' : ' has'} missing required information and cannot be approved.
                  Transactions with missing fields are highlighted in red in the list below. Click on a transaction to review and complete the missing information.
                </p>
              </div>
            </div>
          </Card>
        );
      })()}

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
        <div className="border-t border-gray-200">
          {/* Table Header */}
          <div className={`grid gap-4 px-6 py-4 bg-white border-b border-gray-200 ${
            categorySuggestions.length > 0 ? 'grid-cols-13' : 'grid-cols-12'
          }`}>
            <div className="col-span-1"></div>
            <div className="text-sm font-medium text-gray-700">Date</div>
            <div className="text-sm font-medium text-gray-700">Description</div>
            <div className="text-sm font-medium text-gray-700">Category</div>
            <div className="text-sm font-medium text-gray-700">Account</div>
            <div className="text-sm font-medium text-gray-700">Amount</div>
            <div className="text-sm font-medium text-gray-700">Status</div>
            {categorySuggestions.length > 0 && (
              <div className="text-sm font-medium text-gray-700">Quick Assign</div>
            )}
          </div>

          {/* Table Rows */}
          {filteredExpenses.map((expense) => {
            const statusBadge = getStatusBadge(expense.status);
            const isExpanded = expandedId === expense.id;
            const isDuplicate = isDuplicateTransaction(expense.id);
            const duplicateGroup = getDuplicateGroup(expense.id);
            const categorySuggestion = getCategorySuggestionForTransaction(expense.id);
            const hasCategorySuggestion = !!categorySuggestion;
            const missingFields = getMissingFields(expense);
            const hasMissingRequiredFields = missingFields.length > 0;
            
            return (
              <div key={expense.id} id={`transaction-${expense.id}`}>
                <div
                  onClick={() => toggleRow(expense.id)}
                  className={`grid gap-4 px-6 py-6 border-b border-gray-100 hover:bg-gray-50 transition-colors items-center cursor-pointer ${
                    categorySuggestions.length > 0 ? 'grid-cols-13' : 'grid-cols-12'
                  } ${
                    isDuplicate ? 'bg-yellow-50' : hasCategorySuggestion ? 'bg-blue-50' : hasMissingRequiredFields ? 'bg-red-50 border-red-200' : ''
                  }`}
                >
                  <div className="col-span-1 flex justify-center">
                    {isDuplicate && (
                      <div className="relative">
                        <AlertTriangle className="w-5 h-5 text-yellow-600 mr-2" />
                        <span className="absolute -top-1 -right-1 flex h-3 w-3">
                          <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-yellow-400 opacity-75"></span>
                          <span className="relative inline-flex rounded-full h-3 w-3 bg-yellow-500"></span>
                        </span>
                      </div>
                    )}
                    {hasCategorySuggestion && !isDuplicate && (
                      <div className="relative">
                        <AlertCircle className="w-5 h-5 text-blue-600 mr-2" />
                        <span className="absolute -top-1 -right-1 flex h-3 w-3">
                          <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-blue-400 opacity-75"></span>
                          <span className="relative inline-flex rounded-full h-3 w-3 bg-blue-500"></span>
                        </span>
                      </div>
                    )}
                    {hasMissingRequiredFields && !isDuplicate && !hasCategorySuggestion && (
                      <div className="relative">
                        <AlertTriangle className="w-5 h-5 text-red-600 mr-2" />
                        <span className="absolute -top-1 -right-1 flex h-3 w-3">
                          <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-red-400 opacity-75"></span>
                          <span className="relative inline-flex rounded-full h-3 w-3 bg-red-500"></span>
                        </span>
                      </div>
                    )}
                    <ChevronRight
                      size={20}
                      className={`transition-transform text-gray-400 ${isExpanded ? 'rotate-90' : ''}`}
                    />
                  </div>
                  <div className="text-base text-gray-900">{formatDate(expense.date)}</div>
                  <div className="text-base text-gray-900 font-medium">{expense.description}</div>
                  <div className="text-base text-gray-900">
                    {(() => {
                      if (!categories || categories.length === 0) {
                        return 'Loading...';
                      }
                      const foundCategory = categories.find(cat => cat.id === expense.category_id);
                      return foundCategory?.category_name || 'Unknown';
                    })()}
                  </div>
                  <div className="text-base text-gray-900">
                    {accounts.find(acc => acc.id === expense.account_id)?.account_name || 'Unknown'}
                  </div>
                  <div className="text-base text-gray-900 font-medium">
                    {formatCurrency(expense.amount, expense.currency)}
                  </div>
                  <div className="">
                    <span className={`inline-block px-3 py-1 rounded-full text-sm font-medium ${
                      statusBadge.variant === 'success' ? 'bg-green-100 text-green-700' :
                      statusBadge.variant === 'warning' ? 'bg-yellow-100 text-yellow-700' :
                      statusBadge.variant === 'danger' ? 'bg-red-100 text-red-700' :
                      'bg-gray-100 text-gray-700'
                    }`}>
                      {statusBadge.label}
                    </span>
                  </div>
                  {categorySuggestions.length > 0 && (
                    <div className="">
                      {categorySuggestion ? (
                        <CategorySuggestion
                          suggestion={categorySuggestion}
                          businessId={selectedBusinessId}
                          onApplied={handleCategorySuggestionApplied}
                          onDismissed={handleCategorySuggestionDismissed}
                          compact={true}
                        />
                      ) : (
                        <span className="text-gray-400 text-sm">-</span>
                      )}
                    </div>
                  )}
                </div>

                {isExpanded && (
                  <div className="border-b border-gray-100 bg-gray-50 p-6">
                    <div className="max-w-5xl mx-auto space-y-6">
                      {/* Missing Fields Alert */}
                      {hasMissingRequiredFields && (
                        <div className="bg-red-50 border border-red-200 rounded-lg p-4">
                          <div className="flex items-start gap-3">
                            <AlertTriangle className="w-5 h-5 text-red-600 flex-shrink-0 mt-0.5" />
                            <div className="flex-1">
                              <h4 className="font-semibold text-red-900 mb-2">
                                Missing Required Information
                              </h4>
                              <p className="text-sm text-red-800 mb-3">
                                This transaction is missing required fields and cannot be approved until they are completed.
                              </p>
                              <div className="bg-white border border-red-300 rounded p-3">
                                <p className="text-sm font-medium text-red-900 mb-2">
                                  Please verify and complete:
                                </p>
                                <ul className="text-sm text-red-800 space-y-1">
                                  {missingFields.map((field, index) => (
                                    <li key={index} className="flex items-center justify-between">
                                      <span className="flex items-center">
                                        <span className="w-2 h-2 bg-red-500 rounded-full mr-2 flex-shrink-0"></span>
                                        {field}
                                      </span>
                                      <button
                                        onClick={(e) => {
                                          e.stopPropagation();
                                          handleEdit(expense);
                                        }}
                                        className="text-red-600 hover:text-red-700 font-medium text-sm underline"
                                      >
                                        Edit
                                      </button>
                                    </li>
                                  ))}
                                </ul>
                              </div>
                            </div>
                          </div>
                        </div>
                      )}

                      {/* Duplicate Alert */}
                      {isDuplicate && duplicateGroup && duplicateGroup.length > 1 && (
                        <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
                          <div className="flex items-start gap-3">
                            <AlertTriangle className="w-5 h-5 text-yellow-600 flex-shrink-0 mt-0.5" />
                            <div className="flex-1">
                              <h4 className="font-semibold text-yellow-900 mb-2">
                                Duplicate Transaction Detected
                              </h4>
                              <p className="text-sm text-yellow-800 mb-3">
                                This transaction appears to be a duplicate of {duplicateGroup.length - 1} other transaction(s) with identical date, amount, vendor, and description.
                              </p>
                              <div className="space-y-2">
                                {duplicateGroup
                                  .filter(t => t.id !== expense.id)
                                  .map(duplicate => (
                                    <div
                                      key={duplicate.id}
                                      className="bg-white border border-yellow-300 rounded p-3 text-sm"
                                    >
                                      <div className="flex items-center justify-between">
                                        <div>
                                          <p className="font-medium text-gray-900">
                                            {duplicate.description}
                                          </p>
                                          <p className="text-gray-600 text-xs mt-1">
                                            {formatDate(duplicate.date)} • {formatCurrency(duplicate.amount, duplicate.currency)}
                                            {duplicate.vendor && ` • ${duplicate.vendor}`}
                                          </p>
                                        </div>
                                        <button
                                          onClick={(e) => {
                                            e.stopPropagation();
                                            handleViewTransaction(duplicate.id);
                                          }}
                                          className="text-primary-600 hover:text-primary-700 font-medium text-sm"
                                        >
                                          View
                                        </button>
                                      </div>
                                    </div>
                                  ))}
                              </div>
                              <p className="text-xs text-yellow-700 mt-3">
                                <strong>Recommendation:</strong> Review these transactions and consider deleting duplicates to maintain accurate records.
                              </p>
                            </div>
                          </div>
                        </div>
                      )}

                      {/* Category Suggestion */}
                      {categorySuggestion && (
                        <CategorySuggestion
                          suggestion={categorySuggestion}
                          businessId={selectedBusinessId}
                          onApplied={handleCategorySuggestionApplied}
                          onDismissed={handleCategorySuggestionDismissed}
                        />
                      )}

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
                              {categories.find(cat => cat.id === expense.category_id)?.category_name || 'Unknown'}
                            </p>
                          </div>
                          <div>
                            <p className="text-base text-gray-900">
                              {accounts.find(acc => acc.id === expense.account_id)?.account_name || 'Unknown'}
                            </p>
                          </div>
                        </div>
                        <span className={`inline-block px-3 py-1 rounded-full text-sm font-medium ${
                          statusBadge.variant === 'success' ? 'bg-green-100 text-green-700' :
                          statusBadge.variant === 'warning' ? 'bg-yellow-100 text-yellow-700' :
                          statusBadge.variant === 'danger' ? 'bg-red-100 text-red-700' :
                          'bg-gray-100 text-gray-700'
                        }`}>
                          {statusBadge.label}
                        </span>
                      </div>

                      {/* Transaction Details Section */}
                      <div className="bg-white rounded-lg border border-gray-200 p-6 space-y-4">
                        <h3 className="text-xl font-bold text-gray-900">Transaction Details</h3>
                        <div className="border-t border-gray-200 pt-4 grid grid-cols-2 gap-4">
                          <div>
                            <p className="text-sm text-gray-500 mb-1">Type</p>
                            <p className="text-base text-gray-900 font-medium">
                              {expense.is_income ? 'Income' : 'Expense'}
                            </p>
                          </div>
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
                          <div>
                            <p className="text-sm text-gray-500 mb-1">Documents</p>
                            <DocumentCount transactionId={expense.id} />
                          </div>
                        </div>
                        {expense.notes && (
                          <div className="border-t border-gray-200 pt-4">
                            <p className="text-sm text-gray-500 mb-1">Notes</p>
                            <p className="text-base text-gray-900">{expense.notes}</p>
                          </div>
                        )}
                      </div>

                      {/* Review Needed Section (if applicable) */}
                      {expense.approval_notes && (
                        <div className="bg-white rounded-lg border border-gray-200 p-6 space-y-4">
                          <h3 className="text-xl font-bold text-gray-900">Review Notes</h3>
                          <div className="flex gap-4">
                            <AlertCircle size={24} className="text-yellow-500 flex-shrink-0 mt-1" />
                            <div>
                              <p className="text-base text-gray-700">{expense.approval_notes}</p>
                            </div>
                          </div>
                        </div>
                      )}

                      {/* Documents Section */}
                      <div className="bg-white rounded-lg border border-gray-200 p-6 space-y-4">
                        <DocumentPreview
                          transactionId={expense.id}
                          businessId={selectedBusinessId}
                          compact={false}
                        />
                      </div>

                      {/* Review Needed Section (if applicable) */}
                      {expense.approval_notes && (
                        <div className="bg-white rounded-lg border border-gray-200 p-6 space-y-4">
                          <h3 className="text-xl font-bold text-gray-900">Review Notes</h3>
                          <div className="flex gap-4">
                            <AlertCircle size={24} className="text-yellow-500 flex-shrink-0 mt-1" />
                            <div>
                              <p className="text-base text-gray-700">{expense.approval_notes}</p>
                            </div>
                          </div>
                        </div>
                      )}

                      {/* Action Buttons */}
                      <div className="flex gap-4 justify-end">
                        <Button
                          variant="primary"
                          onClick={(e) => {
                            e.stopPropagation();
                            handleEdit(expense);
                          }}
                        >
                          Edit Transaction
                        </Button>
                        {(expense.status === 'pending' || expense.status === 'draft') && (
                          <Button
                            variant="ghost"
                            className="text-red-600 hover:bg-red-50"
                            onClick={(e) => {
                              e.stopPropagation();
                              handleDelete(expense.id);
                            }}
                          >
                            Delete
                          </Button>
                        )}
                      </div>
                    </div>
                  </div>
                )}
              </div>
            );
          })}
        </div>
      )}

      {/* Pagination Controls */}
      {totalCount > 0 && (
        <div className="flex items-center justify-between bg-white px-6 py-4 border-t border-gray-200">
          <div className="flex items-center space-x-4">
            <div className="text-sm text-gray-700">
              Showing {Math.min((currentPage - 1) * pageSize + 1, totalCount)} to {Math.min(currentPage * pageSize, totalCount)} of {totalCount} transactions
            </div>
            <div className="flex items-center space-x-2">
              <label className="text-sm text-gray-700">Show:</label>
              <select
                value={pageSize}
                onChange={(e) => {
                  const newSize = parseInt(e.target.value);
                  setPageSize(newSize);
                  setCurrentPage(1); // Reset to first page when changing page size
                  fetchExpenses(selectedBusinessId, 1, newSize);
                }}
                className="px-2 py-1 border border-gray-300 rounded text-sm focus:outline-none focus:ring-2 focus:ring-primary-500"
              >
                <option value={10}>10</option>
                <option value={25}>25</option>
                <option value={50}>50</option>
                <option value={100}>100</option>
              </select>
              <span className="text-sm text-gray-700">per page</span>
            </div>
          </div>
          
          <div className="flex items-center space-x-2">
            <button
              onClick={() => {
                const newPage = currentPage - 1;
                setCurrentPage(newPage);
                fetchExpenses(selectedBusinessId, newPage);
              }}
              disabled={currentPage === 1}
              className="px-3 py-1 border border-gray-300 rounded text-sm hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              Previous
            </button>
            
            <div className="flex items-center space-x-1">
              {Array.from({ length: Math.min(5, Math.ceil(totalCount / pageSize)) }, (_, i) => {
                const startPage = Math.max(1, currentPage - 2);
                const endPage = Math.min(Math.ceil(totalCount / pageSize), startPage + 4);
                const adjustedPageNum = startPage + i;
                
                if (adjustedPageNum > endPage) return null;
                
                return (
                  <button
                    key={adjustedPageNum}
                    onClick={() => {
                      setCurrentPage(adjustedPageNum);
                      fetchExpenses(selectedBusinessId, adjustedPageNum);
                    }}
                    className={`px-3 py-1 border rounded text-sm ${
                      adjustedPageNum === currentPage
                        ? 'bg-primary-600 text-white border-primary-600'
                        : 'border-gray-300 hover:bg-gray-50'
                    }`}
                  >
                    {adjustedPageNum}
                  </button>
                );
              })}
            </div>
            
            <button
              onClick={() => {
                const newPage = currentPage + 1;
                setCurrentPage(newPage);
                fetchExpenses(selectedBusinessId, newPage);
              }}
              disabled={currentPage === Math.ceil(totalCount / pageSize)}
              className="px-3 py-1 border border-gray-300 rounded text-sm hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              Next
            </button>
          </div>
        </div>
      )}

      {/* Create/Edit Modal */}
      <Modal
        isOpen={isModalOpen}
        onClose={() => {
          setIsModalOpen(false);
          setEditingExpense(null);
          setAttachedFiles([]);
          setFormData({
            date: '',
            amount: '',
            description: '',
            category_id: '',
            account_id: '',
            status: 'pending',
            is_income: false,
            notes: '',
            vendor: '',
            taxes_fees: '',
            payment_method: '',
            recipient_id: '',
          });
        }}
        title={editingExpense ? "Edit Expense" : "Add New Expense"}
        size="lg"
      >
        <form onSubmit={handleSubmit} className="space-y-4">
          {/* Duplicate Warning */}
          {showDuplicateWarning && potentialDuplicates.length > 0 && (
            <DuplicateWarning
              duplicates={potentialDuplicates}
              categories={categories}
              accounts={accounts}
              onDismiss={() => setShowDuplicateWarning(false)}
              onViewDuplicate={handleViewTransaction}
            />
          )}

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

          <div className="grid grid-cols-2 gap-4">
            <Input 
              label="Vendor" 
              placeholder="e.g., Amazon, Walmart"
              value={formData.vendor}
              onChange={(e) => setFormData({ ...formData, vendor: e.target.value })}
            />
            <Input 
              label="Taxes & Fees" 
              type="number" 
              step="0.01" 
              placeholder="0.00"
              value={formData.taxes_fees}
              onChange={(e) => setFormData({ ...formData, taxes_fees: e.target.value })}
            />
          </div>

          <div className="grid grid-cols-2 gap-4">
            <Input 
              label="Payment Method" 
              placeholder="e.g., Credit Card, Cash, Bank Transfer"
              value={formData.payment_method}
              onChange={(e) => setFormData({ ...formData, payment_method: e.target.value })}
            />
            <Input 
              label="Recipient ID" 
              placeholder="e.g., Employee ID, Vendor ID"
              value={formData.recipient_id}
              onChange={(e) => setFormData({ ...formData, recipient_id: e.target.value })}
            />
          </div>

          {/* Document Attachments */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Attach Documents (Receipts, Invoices, etc.)
            </label>
            <FileUpload
              files={attachedFiles}
              onFilesChange={setAttachedFiles}
              maxFiles={5}
              maxSizeMB={10}
            />
          </div>

          <div className="flex justify-end space-x-3 pt-4 border-t border-gray-200">
            <Button type="button" variant="ghost" onClick={() => {
              setIsModalOpen(false);
              setAttachedFiles([]);
            }}>
              Cancel
            </Button>
            <Button 
              type="submit" 
              variant="primary"
              disabled={isUploading}
            >
              {isUploading ? (
                <>
                  <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin mr-2"></div>
                  Uploading...
                </>
              ) : (
                editingExpense ? "Update Expense" : (formData.status === 'approved' ? "Add Transaction" : "Submit for Approval")
              )}
            </Button>
          </div>
        </form>
      </Modal>
      </div>
    </div>
  );
};

export default Expenses;
