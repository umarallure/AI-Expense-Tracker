import api from '../lib/api';
import { Business, BusinessCreate, Account, AccountCreate, Category, CategoryCreate, Expense, CreateExpenseRequest, ExpenseApprovalRequest, ExpenseApprovalEditRequest, Rule, RuleCreate, RuleUpdate, Document, DocumentUploadRequest, DocumentUpdateRequest, DocumentProcessingStatus } from '../types/index';

export const businessService = {
  async getBusinesses(): Promise<{ businesses: Business[]; total: number }> {
    const response = await api.get('/businesses/');
    return response.data;
  },

  async getBusiness(id: string): Promise<Business> {
    const response = await api.get(`/businesses/${id}`);
    return response.data;
  },

  async createBusiness(data: BusinessCreate): Promise<Business> {
    const response = await api.post('/businesses/', data);
    return response.data;
  },

  async updateBusiness(id: string, data: Partial<BusinessCreate>): Promise<Business> {
    const response = await api.patch(`/businesses/${id}`, data);
    return response.data;
  },

  async deleteBusiness(id: string): Promise<void> {
    await api.delete(`/businesses/${id}`);
  },

  async getBusinessOverview(id: string): Promise<any> {
    const response = await api.get(`/businesses/${id}/overview`);
    return response.data;
  },
};

export const accountService = {
  async getAccounts(businessId: string): Promise<{ accounts: Account[]; total: number }> {
    const response = await api.get(`/accounts/?business_id=${businessId}`);
    return response.data;
  },

  async getAccount(id: string): Promise<Account> {
    const response = await api.get(`/accounts/${id}`);
    return response.data;
  },

  async createAccount(data: AccountCreate): Promise<Account> {
    // business_id must be sent as BOTH query param (for auth dependency) AND in body (for account data)
    const response = await api.post(`/accounts/?business_id=${data.business_id}`, data);
    return response.data;
  },

  async updateAccount(id: string, data: Partial<AccountCreate>): Promise<Account> {
    // business_id must be sent as query param for auth dependency
    const businessId = data.business_id;
    const response = await api.patch(`/accounts/${id}?business_id=${businessId}`, data);
    return response.data;
  },

  async updateBalance(id: string, balance: number): Promise<Account> {
    const response = await api.patch(`/accounts/${id}/balance`, { current_balance: balance });
    return response.data;
  },

  async getAccountsSummary(businessId: string): Promise<any> {
    const response = await api.get(`/accounts/summary/business/${businessId}`);
    return response.data;
  },
};

export const categoryService = {
  async getCategories(businessId: string): Promise<{ categories: Category[]; total: number }> {
    const response = await api.get(`/categories/?business_id=${businessId}`);
    return response.data;
  },

  async getCategory(id: string): Promise<Category> {
    const response = await api.get(`/categories/${id}`);
    return response.data;
  },

  async createCategory(data: CategoryCreate): Promise<Category> {
    // business_id must be sent as BOTH query param (for auth dependency) AND in body (for category data)
    const response = await api.post(`/categories/?business_id=${data.business_id}`, data);
    return response.data;
  },

  async updateCategory(id: string, data: Partial<CategoryCreate>): Promise<Category> {
    // business_id must be sent as query param for auth dependency
    const businessId = data.business_id;
    const response = await api.patch(`/categories/${id}?business_id=${businessId}`, data);
    return response.data;
  },

  async getCategoryHierarchy(businessId: string): Promise<any> {
    const response = await api.get(`/categories/hierarchy/business/${businessId}`);
    return response.data;
  },

  async getCategoriesSummary(businessId: string): Promise<any> {
    const response = await api.get(`/categories/summary/business/${businessId}`);
    return response.data;
  },
};

export const expenseService = {
  async getExpenses(businessId: string): Promise<{ transactions: Expense[]; total: number }> {
    const response = await api.get(`/transactions/?business_id=${businessId}`);
    return response.data;
  },

  async getExpense(id: string): Promise<Expense> {
    const response = await api.get(`/transactions/${id}`);
    return response.data;
  },

  async createExpense(data: CreateExpenseRequest): Promise<Expense> {
    // business_id must be sent as BOTH query param (for auth dependency) AND in body (for expense data)
    const response = await api.post(`/transactions/?business_id=${data.business_id}`, data);
    return response.data;
  },

  async updateExpense(id: string, data: Partial<CreateExpenseRequest>): Promise<Expense> {
    // business_id must be sent as query param for auth dependency
    const businessId = data.business_id;
    const response = await api.patch(`/transactions/${id}?business_id=${businessId}`, data);
    return response.data;
  },

  async deleteExpense(id: string, businessId: string): Promise<void> {
    await api.delete(`/transactions/${id}?business_id=${businessId}`);
  },

  async approveExpense(id: string, approvalData: ExpenseApprovalRequest): Promise<Expense> {
    const response = await api.post(`/transactions/${id}/approve`, approvalData);
    return response.data;
  },

  async approveAndEditExpense(id: string, approvalData: ExpenseApprovalEditRequest): Promise<Expense> {
    const response = await api.put(`/transactions/${id}/approve-edit`, approvalData);
    return response.data;
  },

  async getPendingExpenses(businessId: string): Promise<{ transactions: Expense[]; total: number }> {
    const response = await api.get(`/transactions/pending/${businessId}`);
    return response.data;
  },
};

export const ruleService = {
  async getRules(businessId?: string): Promise<Rule[]> {
    const url = businessId ? `/rules/?business_id=${businessId}` : '/rules/';
    const response = await api.get(url);
    return response.data;
  },

  async getRule(id: string): Promise<Rule> {
    const response = await api.get(`/rules/${id}`);
    return response.data;
  },

  async createRule(data: RuleCreate): Promise<Rule> {
    const response = await api.post('/rules/', data);
    return response.data;
  },

  async updateRule(id: string, data: RuleUpdate): Promise<Rule> {
    const response = await api.put(`/rules/${id}`, data);
    return response.data;
  },

  async deleteRule(id: string): Promise<void> {
    await api.delete(`/rules/${id}`);
  },
};

export const documentService = {
  async uploadDocument(data: DocumentUploadRequest): Promise<Document> {
    const formData = new FormData();
    formData.append('file', data.file);
    formData.append('business_id', data.business_id);
    formData.append('document_type', data.document_type);
    if (data.description) formData.append('description', data.description);
    if (data.tags) formData.append('tags', data.tags);
    if (data.transaction_id) formData.append('transaction_id', data.transaction_id);

    const response = await api.post('/documents/upload', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    return response.data;
  },

  async getDocuments(businessId: string, transactionId?: string, documentType?: string): Promise<{ documents: Document[]; total: number }> {
    let url = `/documents/?business_id=${businessId}`;
    if (transactionId) url += `&transaction_id=${transactionId}`;
    if (documentType) url += `&document_type=${documentType}`;
    
    const response = await api.get(url);
    return response.data;
  },

  async getDocument(id: string): Promise<Document> {
    const response = await api.get(`/documents/${id}`);
    return response.data;
  },

  async downloadDocument(id: string): Promise<{ download_url: string; expires_in: number; document_name: string }> {
    const response = await api.get(`/documents/${id}/download`);
    return response.data;
  },

  async updateDocument(id: string, data: DocumentUpdateRequest): Promise<Document> {
    const response = await api.put(`/documents/${id}`, data);
    return response.data;
  },

  async deleteDocument(id: string): Promise<void> {
    await api.delete(`/documents/${id}`);
  },

  async processDocument(id: string): Promise<{ message: string; document_id: string; status: string }> {
    const response = await api.post(`/document-processing/${id}/process`);
    return response.data;
  },

  async getProcessingStatus(id: string): Promise<DocumentProcessingStatus> {
    const response = await api.get(`/document-processing/${id}/status`);
    return response.data;
  },

  async getSupportedTypes(): Promise<{ supported_extensions: string[]; supported_mimetypes: string[]; extractors: any[] }> {
    const response = await api.get('/document-processing/supported-types');
    return response.data;
  },
};
