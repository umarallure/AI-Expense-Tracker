// User Types
export interface User {
  id: string;
  email: string;
  full_name: string;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

// Auth Types
export interface LoginCredentials {
  email: string;
  password: string;
}

export interface SignupData {
  email: string;
  password: string;
  full_name: string;
}

export interface AuthResponse {
  access_token: string;
  token_type: string;
  user: User;
}

// Business Types
export interface Business {
  id: string;
  name: string; // Keep for backwards compatibility
  business_name?: string; // API uses this field
  description?: string;
  industry?: string;
  tax_id?: string;
  owner_id: string;
  is_active: boolean;
  business_type?: string;
  currency?: string;
  fiscal_year_start?: number;
  address?: string;
  city?: string;
  state?: string;
  country?: string;
  postal_code?: string;
  phone?: string;
  email?: string;
  website?: string;
  created_at: string;
  updated_at: string;
}

export interface CreateBusinessRequest {
  name: string;
  description?: string;
  industry?: string;
  tax_id?: string;
}

export interface BusinessCreate {
  business_name: string;
  business_type?: string;
  currency?: string;
  industry?: string;
  fiscal_year_start?: number;
  address?: string;
  city?: string;
  state?: string;
  country?: string;
  postal_code?: string;
  phone?: string;
  email?: string;
  website?: string;
}

export interface AccountCreate {
  business_id: string;
  account_name: string;
  account_type: string;
  account_number_masked?: string;
  institution_name?: string;
  current_balance?: number;
  currency?: string;
}

export interface CategoryCreate {
  business_id: string;
  category_name: string;
  category_type: 'income' | 'expense';
  is_income?: boolean;
  description?: string;
  parent_category_id?: string;
  color?: string;
  icon?: string;
  is_active?: boolean;
}

// Account Types
export type AccountType = 'bank' | 'credit_card' | 'cash' | 'other';

export interface Account {
  id: string;
  business_id: string;
  account_name: string;
  account_type: AccountType | string;
  account_number_masked?: string;
  institution_name?: string;
  current_balance: number;
  currency: string;
  is_active: boolean;
  created_at: string;
  updated_at: string;
  description?: string;
  routing_number?: string;
  available_balance?: number;
  credit_limit?: number;
  interest_rate?: number;
  minimum_payment?: number;
  due_date?: number;
  is_primary?: boolean;
  color?: string;
  icon?: string;
  settings?: Record<string, any>;
}

export interface CreateAccountRequest {
  business_id: string;
  account_name: string;
  account_type: AccountType;
  account_number_masked?: string;
  institution_name?: string;
  current_balance?: number;
  currency?: string;
}

// Category Types
export interface Category {
  id: string;
  business_id: string;
  category_name: string;
  category_type?: string;
  is_income?: boolean;
  description?: string;
  parent_id?: string;
  display_order?: number;
  color?: string;
  icon?: string;
  settings?: Record<string, any>;
  is_system?: boolean;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface CreateCategoryRequest {
  business_id: string;
  category_name: string;
  category_type?: string;
  description?: string;
  parent_id?: string;
  color?: string;
  icon?: string;
}

// Expense Types
export type ExpenseStatus = 'draft' | 'pending' | 'approved' | 'rejected';

export interface Expense {
  id: string;
  business_id: string;
  account_id: string;
  category_id: string;
  user_id: string;
  amount: number;
  currency: string;
  description: string;
  date: string;
  is_income?: boolean;
  receipt_url?: string;
  status: ExpenseStatus;
  notes?: string;
  approved_by?: string;
  approved_at?: string;
  approval_notes?: string;
  vendor?: string;
  taxes_fees?: number;
  payment_method?: string;
  recipient_id?: string;
  created_at: string;
  updated_at: string;
}

export interface CreateExpenseRequest {
  business_id: string;
  account_id: string;
  category_id?: string;
  amount: number;
  currency: string;
  description: string;
  date: string;
  is_income?: boolean;
  receipt_url?: string;
  status?: ExpenseStatus;
  notes?: string;
  vendor?: string;
  taxes_fees?: number;
  payment_method?: string;
  recipient_id?: string;
}

export interface ExpenseApprovalRequest {
  status: ExpenseStatus;
  approval_notes?: string;
}

export interface ExpenseApprovalEditRequest extends ExpenseApprovalRequest {
  business_id?: string;
  account_id?: string;
  category_id?: string;
  amount?: number;
  currency?: string;
  description?: string;
  date?: string;
  is_income?: boolean;
  receipt_url?: string;
  notes?: string;
}

// Rule Types
export interface RuleCondition {
  field: string;
  operator: 'equals' | 'not_equals' | 'contains' | 'greater_than' | 'less_than' | 'starts_with' | 'ends_with';
  value: any;
}

export interface RuleAction {
  type: string;
  value: any;
}

export interface Rule {
  id: string;
  business_id: string;
  name: string;
  description?: string;
  rule_type: 'auto_categorize' | 'auto_tag' | 'approval_required' | 'flag_suspicious';
  conditions: RuleCondition[];
  actions: RuleAction[];
  priority: number;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface RuleCreate {
  business_id: string;
  name: string;
  description?: string;
  rule_type: 'auto_categorize' | 'auto_tag' | 'approval_required' | 'flag_suspicious';
  conditions: RuleCondition[];
  actions: RuleAction[];
  priority?: number;
  is_active?: boolean;
}

export interface RuleUpdate {
  name?: string;
  description?: string;
  rule_type?: 'auto_categorize' | 'auto_tag' | 'approval_required' | 'flag_suspicious';
  conditions?: RuleCondition[];
  actions?: RuleAction[];
  priority?: number;
  is_active?: boolean;
}

// Document Types
export type ExtractionStatus = 'pending' | 'processing' | 'completed' | 'failed';

export interface Document {
  id: string;
  business_id: string;
  transaction_id?: string;
  user_id: string;
  document_name: string;
  document_type: string;
  file_path: string;
  file_size: number;
  mime_type: string;
  storage_bucket: string;
  description?: string;
  tags?: string[];
  metadata?: Record<string, any>;
  is_processed: boolean;
  processed_at?: string;
  created_at: string;
  updated_at: string;
  // Phase 3.2: Document Processing fields
  extraction_status?: ExtractionStatus;
  raw_text?: string;
  structured_data?: Record<string, any>;
  confidence_score?: number;
  processing_error?: string;
}

export interface DocumentProcessingStatus {
  document_id: string;
  document_name: string;
  extraction_status: ExtractionStatus;
  document_type?: string;
  confidence_score?: number;
  processing_error?: string;
  processed_at?: string;
  created_at: string;
  raw_text_preview?: string;
  raw_text_length?: number;
  word_count?: number;
  structured_data?: Record<string, any>;
}

export interface DocumentUploadRequest {
  file: File;
  business_id: string;
  document_type: string;
  description?: string;
  tags?: string;
  transaction_id?: string;
}

export interface DocumentUpdateRequest {
  document_name?: string;
  document_type?: string;
  description?: string;
  tags?: string[];
  transaction_id?: string;
}

// File attachment for transaction creation
export interface FileAttachment {
  file: File;
  document_type: string;
  description?: string;
  tags?: string;
  preview?: string; // For image previews
}
