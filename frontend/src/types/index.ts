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
