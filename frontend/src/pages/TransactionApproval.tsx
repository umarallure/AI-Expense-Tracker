import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import {
  ArrowLeft,
  FileText,
  Eye,
  Download,
  CheckCircle,
  XCircle,
  Clock,
  AlertCircle,
  Loader,
  BarChart3,
  Code,
  Edit3,
  ZoomIn,
  ZoomOut,
  RotateCw,
  ChevronLeft,
  ChevronRight
} from 'lucide-react';
import Button from '../components/ui/Button';
import Card from '../components/ui/Card';
import Badge from '../components/ui/Badge';
import Input from '../components/ui/Input';
import { documentService, expenseService, categoryService, accountService } from '../services/business.service';
import type { Document, DocumentProcessingStatus, Expense, Category, Account, ExpenseApprovalEditRequest } from '../types';

const TransactionApproval: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();

  // Main data states
  const [transaction, setTransaction] = useState<Expense | null>(null);
  const [linkedDocuments, setLinkedDocuments] = useState<Document[]>([]);
  const [processingStatuses, setProcessingStatuses] = useState<DocumentProcessingStatus[]>([]);
  const [categories, setCategories] = useState<Category[]>([]);
  const [accounts, setAccounts] = useState<Account[]>([]);

  // UI states
  const [isLoading, setIsLoading] = useState(true);
  const [isSaving, setIsSaving] = useState(false);
  const [activeDocumentIndex, setActiveDocumentIndex] = useState(0);
  const [activeTab, setActiveTab] = useState<'viewer' | 'extracted' | 'structured' | 'confidence'>('viewer');
  const [documentUrls, setDocumentUrls] = useState<Map<string, string>>(new Map());
  const [zoomLevel, setZoomLevel] = useState(100);

  // Form states
  const [formData, setFormData] = useState({
    date: '',
    amount: '',
    description: '',
    category_id: '',
    account_id: '',
    vendor: '',
    payment_method: '',
    taxes_fees: '',
    recipient_id: '',
    notes: '',
    approval_notes: '',
  });

  // Validation states
  const [missingFields, setMissingFields] = useState<string[]>([]);
  const [isFormValid, setIsFormValid] = useState(false);

  useEffect(() => {
    if (id) {
      fetchTransactionData(id);
    }
  }, [id]);

  useEffect(() => {
    validateForm();
  }, [formData]);

  const fetchTransactionData = async (id: string) => {
    try {
      setIsLoading(true);

      // Fetch transaction details
      const transactionResponse = await expenseService.getExpense(id);
      setTransaction(transactionResponse);

      // Fetch categories and accounts for the business
      await fetchCategoriesAndAccounts(transactionResponse.business_id);

      // Initialize form data
      setFormData({
        date: new Date(transactionResponse.date).toISOString().split('T')[0],
        amount: transactionResponse.amount.toString(),
        description: transactionResponse.description,
        category_id: transactionResponse.category_id || '',
        account_id: transactionResponse.account_id,
        vendor: transactionResponse.vendor || '',
        payment_method: transactionResponse.payment_method || '',
        taxes_fees: transactionResponse.taxes_fees?.toString() || '',
        recipient_id: transactionResponse.recipient_id || '',
        notes: transactionResponse.notes || '',
        approval_notes: '',
      });

      // Fetch linked documents
      try {
        const documentsResponse = await documentService.getDocuments(transactionResponse.business_id, id);
        setLinkedDocuments(documentsResponse.documents);

        // Fetch processing status for each document
        const statusPromises = documentsResponse.documents.map(doc =>
          documentService.getProcessingStatus(doc.id).catch(() => null)
        );
        const statuses = await Promise.all(statusPromises);
        setProcessingStatuses(statuses.filter(status => status !== null));

        // Fetch document URLs
        const urlPromises = documentsResponse.documents.map(async (doc) => {
          try {
            const downloadResponse = await documentService.downloadDocument(doc.id);
            return [doc.id, downloadResponse.download_url] as [string, string];
          } catch {
            return [doc.id, ''] as [string, string];
          }
        });
        const urls = await Promise.all(urlPromises);
        setDocumentUrls(new Map(urls));
      } catch (error) {
        console.error('Failed to fetch linked documents:', error);
      }

    } catch (error) {
      console.error('Failed to fetch transaction data:', error);
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

  const validateForm = () => {
    const missing: string[] = [];

    if (!formData.category_id) missing.push('Category');
    if (!formData.account_id) missing.push('Account');
    if (!formData.payment_method) missing.push('Payment Method');
    if (!formData.vendor && !formData.description.includes('Transfer') && !formData.description.includes('Deposit')) {
      missing.push('Vendor');
    }
    if (!formData.amount || parseFloat(formData.amount) <= 0) missing.push('Amount');

    setMissingFields(missing);
    setIsFormValid(missing.length === 0);
  };

  const handleSaveAndApprove = async () => {
    if (!transaction || !isFormValid) return;

    try {
      setIsSaving(true);

      const approvalData: ExpenseApprovalEditRequest = {
        business_id: transaction.business_id,
        account_id: formData.account_id,
        category_id: formData.category_id || undefined,
        amount: parseFloat(formData.amount),
        currency: transaction.currency,
        description: formData.description,
        date: new Date(formData.date).toISOString(),
        is_income: transaction.is_income,
        notes: formData.notes || undefined,
        vendor: formData.vendor || undefined,
        taxes_fees: formData.taxes_fees ? parseFloat(formData.taxes_fees) : undefined,
        payment_method: formData.payment_method || undefined,
        recipient_id: formData.recipient_id || undefined,
        status: 'approved',
        approval_notes: formData.approval_notes || undefined,
      };

      await expenseService.approveAndEditExpense(transaction.id, approvalData);

      alert('Transaction approved successfully!');
      navigate('/approvals');

    } catch (error) {
      console.error('Failed to approve transaction:', error);
      alert('Failed to approve transaction. Please try again.');
    } finally {
      setIsSaving(false);
    }
  };

  const handleReject = async () => {
    if (!transaction) return;

    const reason = prompt('Please provide a reason for rejection:');
    if (!reason) return;

    try {
      setIsSaving(true);

      const approvalData = {
        status: 'rejected' as const,
        approval_notes: reason,
      };

      await expenseService.approveExpense(transaction.id, approvalData);

      alert('Transaction rejected.');
      navigate('/approvals');

    } catch (error) {
      console.error('Failed to reject transaction:', error);
      alert('Failed to reject transaction. Please try again.');
    } finally {
      setIsSaving(false);
    }
  };

  const handleDownloadDocument = async (documentId: string) => {
    try {
      const response = await documentService.downloadDocument(documentId);
      window.open(response.download_url, '_blank');
    } catch (error) {
      console.error('Failed to download document:', error);
    }
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  const formatFileSize = (bytes: number) => {
    if (bytes < 1024) return bytes + ' B';
    if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(2) + ' KB';
    return (bytes / (1024 * 1024)).toFixed(2) + ' MB';
  };

  const getDocumentTypeBadge = (type: string) => {
    const types: Record<string, { variant: any; label: string }> = {
      receipt: { variant: 'success', label: 'Receipt' },
      invoice: { variant: 'warning', label: 'Invoice' },
      statement: { variant: 'default', label: 'Statement' },
      contract: { variant: 'default', label: 'Contract' },
      other: { variant: 'default', label: 'Other' },
    };
    return types[type] || types.other;
  };

  const getExtractionStatusInfo = (status?: string, confidenceScore?: number) => {
    const statuses: Record<string, { icon: any; color: string; label: string; variant: any }> = {
      pending: {
        icon: Clock,
        color: 'text-gray-500',
        label: 'Not Processed',
        variant: 'default',
      },
      processing: {
        icon: Loader,
        color: 'text-blue-500 animate-spin',
        label: 'Processing...',
        variant: 'default',
      },
      completed: {
        icon: CheckCircle,
        color: 'text-green-500',
        label: 'Verified',
        variant: 'success',
      },
      failed: {
        icon: XCircle,
        color: 'text-red-500',
        label: 'Failed',
        variant: 'danger',
      },
    };

    if (status === 'completed' && confidenceScore !== undefined) {
      if (confidenceScore >= 0.9) {
        return statuses.completed;
      } else if (confidenceScore >= 0.7) {
        return { ...statuses.completed, label: 'Needs Review' };
      } else {
        return { ...statuses.completed, label: 'Needs Review' };
      }
    }

    return statuses[status || 'pending'] || statuses.pending;
  };

  const DocumentViewer: React.FC<{ document: Document; documentUrl: string | undefined }> = ({ document, documentUrl }) => {
    const isImage = document.mime_type?.startsWith('image/');
    const isPDF = document.mime_type === 'application/pdf';

    const handleZoomIn = () => setZoomLevel(prev => Math.min(prev + 25, 300));
    const handleZoomOut = () => setZoomLevel(prev => Math.max(prev - 25, 25));
    const handleResetZoom = () => setZoomLevel(100);

    if (isImage && documentUrl) {
      return (
        <div className="flex flex-col h-full bg-gray-100 rounded-lg">
          {/* Zoom Controls */}
          <div className="flex items-center justify-between p-3 border-b border-gray-200 bg-white rounded-t-lg">
            <div className="flex items-center space-x-2">
              <Button variant="ghost" size="sm" icon={<ZoomOut className="w-4 h-4" />} onClick={handleZoomOut} />
              <span className="text-sm font-medium">{zoomLevel}%</span>
              <Button variant="ghost" size="sm" icon={<ZoomIn className="w-4 h-4" />} onClick={handleZoomIn} />
              <Button variant="ghost" size="sm" icon={<RotateCw className="w-4 h-4" />} onClick={handleResetZoom} />
            </div>
            <Button variant="ghost" size="sm" icon={<Download className="w-4 h-4" />} onClick={() => handleDownloadDocument(document.id)} />
          </div>

          {/* Image Viewer */}
          <div className="flex items-center justify-center flex-1 p-4 overflow-auto">
            <img
              src={documentUrl}
              alt={document.document_name}
              className="max-w-full max-h-full object-contain rounded-lg shadow-lg transition-transform"
              style={{ transform: `scale(${zoomLevel / 100})` }}
              onError={(e) => {
                console.error('Failed to load image:', e);
              }}
            />
          </div>
        </div>
      );
    }

    if (isPDF && documentUrl) {
      return (
        <div className="flex flex-col h-full bg-gray-100 rounded-lg">
          {/* PDF Controls */}
          <div className="flex items-center justify-between p-3 border-b border-gray-200 bg-white rounded-t-lg">
            <div className="flex items-center space-x-2">
              <Button variant="ghost" size="sm" icon={<ZoomOut className="w-4 h-4" />} onClick={handleZoomOut} />
              <span className="text-sm font-medium">{zoomLevel}%</span>
              <Button variant="ghost" size="sm" icon={<ZoomIn className="w-4 h-4" />} onClick={handleZoomIn} />
              <Button variant="ghost" size="sm" icon={<RotateCw className="w-4 h-4" />} onClick={handleResetZoom} />
            </div>
            <Button variant="ghost" size="sm" icon={<Download className="w-4 h-4" />} onClick={() => handleDownloadDocument(document.id)} />
          </div>

          {/* PDF Viewer */}
          <div className="flex-1 overflow-hidden rounded-b-lg">
            <iframe
              src={documentUrl}
              className="w-full h-full border-0"
              title={document.document_name}
              onError={(e) => {
                console.error('Failed to load PDF:', e);
              }}
            />
          </div>
        </div>
      );
    }

    return (
      <div className="flex items-center justify-center h-full bg-gray-100 rounded-lg">
        <div className="text-center">
          <FileText className="w-16 h-16 text-gray-400 mx-auto mb-4" />
          <p className="text-gray-600 mb-4">Document Preview Not Available</p>
          <Button variant="primary" icon={<Download className="w-4 h-4" />} onClick={() => handleDownloadDocument(document.id)}>
            Download Document
          </Button>
        </div>
      </div>
    );
  };

  const TransactionForm: React.FC = () => (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h3 className="text-lg font-semibold text-gray-900 flex items-center">
          <Edit3 className="w-5 h-5 mr-2" />
          Edit Transaction Details
        </h3>
        {missingFields.length > 0 && (
          <Badge variant="danger">{missingFields.length} missing fields</Badge>
        )}
      </div>

      {/* Missing Fields Warning */}
      {missingFields.length > 0 && (
        <Card className="p-4 border-amber-200 bg-amber-50">
          <div className="flex items-start space-x-2">
            <AlertCircle className="w-5 h-5 text-amber-500 flex-shrink-0 mt-0.5" />
            <div>
              <h4 className="text-sm font-medium text-amber-900 mb-2">Required Fields Missing</h4>
              <div className="space-y-1">
                {missingFields.map((field, index) => (
                  <div key={index} className="text-sm text-amber-800">
                    • {field}
                  </div>
                ))}
              </div>
              <p className="text-sm text-amber-700 mt-2">
                Please complete all required fields before approving this transaction.
              </p>
            </div>
          </div>
        </Card>
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

      <div className="grid grid-cols-2 gap-4">
        <Input
          label="Vendor"
          placeholder="e.g., Amazon, Walmart"
          value={formData.vendor}
          onChange={(e) => setFormData({ ...formData, vendor: e.target.value })}
        />
        <Input
          label="Payment Method"
          placeholder="e.g., Credit Card, Cash, Bank Transfer"
          value={formData.payment_method}
          onChange={(e) => setFormData({ ...formData, payment_method: e.target.value })}
        />
      </div>

      <div className="grid grid-cols-2 gap-4">
        <Input
          label="Taxes & Fees"
          type="number"
          step="0.01"
          placeholder="0.00"
          value={formData.taxes_fees}
          onChange={(e) => setFormData({ ...formData, taxes_fees: e.target.value })}
        />
        <Input
          label="Recipient ID"
          placeholder="e.g., Employee ID, Vendor ID"
          value={formData.recipient_id}
          onChange={(e) => setFormData({ ...formData, recipient_id: e.target.value })}
        />
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
        <label className="block text-sm font-medium text-gray-700 mb-1.5">
          Approval Notes <span className="text-gray-500">(optional)</span>
        </label>
        <textarea
          rows={2}
          className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
          placeholder="Notes about changes made during approval..."
          value={formData.approval_notes}
          onChange={(e) => setFormData({ ...formData, approval_notes: e.target.value })}
        />
      </div>
    </div>
  );

  const DocumentTabs: React.FC = () => {
    const activeDocument = linkedDocuments[activeDocumentIndex];
    const activeStatus = processingStatuses.find(s => s.document_id === activeDocument?.id);

    return (
      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <h3 className="text-lg font-semibold text-gray-900 flex items-center">
            <FileText className="w-5 h-5 mr-2" />
            Supporting Documents ({linkedDocuments.length})
          </h3>
          {linkedDocuments.length > 1 && (
            <div className="flex items-center space-x-2">
              <Button
                variant="ghost"
                size="sm"
                icon={<ChevronLeft className="w-4 h-4" />}
                onClick={() => setActiveDocumentIndex(prev => Math.max(0, prev - 1))}
                disabled={activeDocumentIndex === 0}
              />
              <span className="text-sm text-gray-600">
                {activeDocumentIndex + 1} of {linkedDocuments.length}
              </span>
              <Button
                variant="ghost"
                size="sm"
                icon={<ChevronRight className="w-4 h-4" />}
                onClick={() => setActiveDocumentIndex(prev => Math.min(linkedDocuments.length - 1, prev + 1))}
                disabled={activeDocumentIndex === linkedDocuments.length - 1}
              />
            </div>
          )}
        </div>

        {activeDocument && (
          <div className="space-y-4">
            {/* Document Info */}
            <Card className="p-4">
              <div className="flex items-center justify-between mb-2">
                <h4 className="font-medium text-gray-900">{activeDocument.document_name}</h4>
                <Badge variant={getDocumentTypeBadge(activeDocument.document_type).variant}>
                  {getDocumentTypeBadge(activeDocument.document_type).label}
                </Badge>
              </div>
              <div className="flex items-center space-x-4 text-sm text-gray-600">
                <span>{formatFileSize(activeDocument.file_size)}</span>
                <span>Uploaded {formatDate(activeDocument.created_at)}</span>
                {activeStatus && (
                  <div className="flex items-center space-x-1">
                    {React.createElement(getExtractionStatusInfo(activeStatus.extraction_status, activeStatus.confidence_score).icon, {
                      className: `w-4 h-4 ${getExtractionStatusInfo(activeStatus.extraction_status, activeStatus.confidence_score).color}`
                    })}
                    <span>{getExtractionStatusInfo(activeStatus.extraction_status, activeStatus.confidence_score).label}</span>
                  </div>
                )}
              </div>
            </Card>

            {/* Tab Navigation */}
            <Card className="p-4">
              <div className="flex space-x-1 mb-4">
                {[
                  { id: 'viewer', label: 'Document', icon: Eye },
                  { id: 'extracted', label: 'Extracted Text', icon: FileText },
                  { id: 'structured', label: 'Data', icon: Code },
                  { id: 'confidence', label: 'AI Analysis', icon: BarChart3 },
                ].map((tab) => (
                  <button
                    key={tab.id}
                    onClick={() => setActiveTab(tab.id as any)}
                    className={`flex items-center space-x-2 px-3 py-2 rounded-lg text-sm font-medium transition-colors ${
                      activeTab === tab.id
                        ? 'bg-primary-100 text-primary-700'
                        : 'text-gray-600 hover:bg-gray-100'
                    }`}
                  >
                    <tab.icon className="w-4 h-4" />
                    <span>{tab.label}</span>
                  </button>
                ))}
              </div>

              {/* Tab Content */}
              <div className="min-h-96">
                {activeTab === 'viewer' && (
                  <DocumentViewer
                    document={activeDocument}
                    documentUrl={documentUrls.get(activeDocument.id)}
                  />
                )}
                {activeTab === 'extracted' && activeStatus && (
                  <div className="bg-gray-50 border border-gray-200 rounded-lg p-4 max-h-96 overflow-y-auto">
                    <pre className="text-sm text-gray-700 whitespace-pre-wrap font-mono leading-relaxed">
                      {activeStatus.raw_text_preview || 'No extracted text available'}
                    </pre>
                  </div>
                )}
                {activeTab === 'structured' && activeStatus && (
                  <div className="bg-gray-50 border border-gray-200 rounded-lg p-4 max-h-96 overflow-y-auto">
                    <pre className="text-sm text-gray-700 whitespace-pre-wrap font-mono">
                      {activeStatus.structured_data ? JSON.stringify(activeStatus.structured_data, null, 2) : 'No structured data available'}
                    </pre>
                  </div>
                )}
                {activeTab === 'confidence' && activeStatus && (
                  <div className="space-y-4">
                    {activeStatus.confidence_score !== undefined && (
                      <Card className="p-4">
                        <div className="flex items-center justify-between mb-2">
                          <span className="text-sm font-medium text-gray-700">Overall Confidence</span>
                          <span className="text-sm font-bold text-gray-900">
                            {Math.round(activeStatus.confidence_score * 100)}%
                          </span>
                        </div>
                        <div className="w-full bg-gray-200 rounded-full h-2">
                          <div
                            className={`h-2 rounded-full ${
                              activeStatus.confidence_score >= 0.9 ? 'bg-green-500' :
                              activeStatus.confidence_score >= 0.7 ? 'bg-yellow-500' : 'bg-red-500'
                            }`}
                            style={{ width: `${activeStatus.confidence_score * 100}%` }}
                          />
                        </div>
                      </Card>
                    )}
                  </div>
                )}
              </div>
            </Card>
          </div>
        )}
      </div>
    );
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-center">
          <div className="w-16 h-16 border-4 border-primary-500 border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
          <p className="text-gray-600">Loading transaction...</p>
        </div>
      </div>
    );
  }

  if (!transaction) {
    return (
      <div className="text-center py-12">
        <h1 className="text-2xl font-bold text-gray-900 mb-4">Transaction Not Found</h1>
        <p className="text-gray-600 mb-6">The transaction you're looking for doesn't exist or has been deleted.</p>
        <Button variant="primary" onClick={() => navigate('/approvals')}>
          Back to Approvals
        </Button>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-white p-8">
      <div className="max-w-7xl mx-auto space-y-6">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-4">
            <Button
              variant="ghost"
              icon={<ArrowLeft className="w-5 h-5" />}
              onClick={() => navigate('/approvals')}
            >
              Back to Approvals
            </Button>
            <div>
              <h1 className="text-2xl font-bold text-gray-900">Review Transaction</h1>
              <p className="text-gray-500 mt-1">
                ${transaction.amount.toFixed(2)} • {transaction.description}
              </p>
            </div>
          </div>
          <div className="flex items-center space-x-3">
            <Badge variant="warning">Pending Approval</Badge>
            <Button
              variant="danger"
              icon={<XCircle className="w-4 h-4" />}
              onClick={handleReject}
              disabled={isSaving}
            >
              Reject
            </Button>
            <Button
              variant="primary"
              icon={<CheckCircle className="w-4 h-4" />}
              onClick={handleSaveAndApprove}
              disabled={isSaving || !isFormValid}
            >
              {isSaving ? 'Saving...' : 'Approve Transaction'}
            </Button>
          </div>
        </div>

        {/* Main Content */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Left Side - Document Viewer */}
          <div className="space-y-4">
            {linkedDocuments.length > 0 ? (
              <DocumentTabs />
            ) : (
              <Card className="p-8 text-center">
                <FileText className="w-12 h-12 text-gray-300 mx-auto mb-4" />
                <h3 className="text-lg font-medium text-gray-900 mb-2">No Documents Attached</h3>
                <p className="text-gray-600">
                  This transaction doesn't have any supporting documents.
                </p>
              </Card>
            )}
          </div>

          {/* Right Side - Transaction Form */}
          <div className="space-y-4">
            <Card className="p-6">
              <TransactionForm />
            </Card>
          </div>
        </div>
      </div>
    </div>
  );
}

export default TransactionApproval;