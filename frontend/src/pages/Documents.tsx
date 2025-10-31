import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Search, Filter, Upload, Download, Edit2, Trash2, FileText, Play, Eye, CheckCircle, XCircle, Clock, Loader, AlertCircle, Link, Tag } from 'lucide-react';
import Button from '../components/ui/Button';
import Card from '../components/ui/Card';
import Modal from '../components/ui/Modal';
import Input from '../components/ui/Input';
import Badge from '../components/ui/Badge';
import DocumentLabelManager from '../components/DocumentLabelManager';
import { businessService, documentService, expenseService } from '../services/business.service';
import type { Business, Document, Expense } from '../types';

const Documents: React.FC = () => {
  const navigate = useNavigate();
  const [documents, setDocuments] = useState<Document[]>([]);
  const [businesses, setBusinesses] = useState<Business[]>([]);
  const [selectedBusinessId, setSelectedBusinessId] = useState<string>('');
  const [isLoading, setIsLoading] = useState(true);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [editingDocument, setEditingDocument] = useState<Document | null>(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [typeFilter, setTypeFilter] = useState<string>('all');
  const [linkFilter, setLinkFilter] = useState<string>('all');
  const [labelFilter, setLabelFilter] = useState<string>('all');
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [isUploading, setIsUploading] = useState(false);
  const [isProcessing, setIsProcessing] = useState<Record<string, boolean>>({});
  const [selectedDocuments, setSelectedDocuments] = useState<Set<string>>(new Set());
  const [isBulkLabelModalOpen, setIsBulkLabelModalOpen] = useState(false);
  const [bulkLabels, setBulkLabels] = useState<string[]>([]);
  const [formData, setFormData] = useState({
    document_type: 'receipt',
    description: '',
    tags: '',
  });

  useEffect(() => {
    fetchBusinesses();
  }, []);

  useEffect(() => {
    if (selectedBusinessId) {
      fetchDocuments(selectedBusinessId);
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

  const fetchDocuments = async (businessId: string) => {
    try {
      const response = await documentService.getDocuments(businessId);
      setDocuments(response.documents);
    } catch (error) {
      console.error('Failed to fetch documents:', error);
      setDocuments([]);
    }
  };

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      setSelectedFile(e.target.files[0]);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!selectedFile && !editingDocument) {
      alert('Please select a file to upload');
      return;
    }

    try {
      setIsUploading(true);

      if (editingDocument) {
        // Update existing document metadata
        await documentService.updateDocument(editingDocument.id, {
          document_type: formData.document_type,
          description: formData.description || undefined,
          tags: formData.tags ? formData.tags.split(',').map(t => t.trim()) : undefined,
        });
        alert('Document updated successfully!');
      } else if (selectedFile) {
        // Upload new document
        const uploadedDoc = await documentService.uploadDocument({
          file: selectedFile,
          business_id: selectedBusinessId,
          document_type: formData.document_type,
          description: formData.description || undefined,
          tags: formData.tags || undefined,
        });
        
        // Auto-trigger processing
        try {
          await documentService.processDocument(uploadedDoc.id);
          alert('Document uploaded and processing started!');
        } catch (processError) {
          console.error('Failed to start processing:', processError);
          alert('Document uploaded successfully, but processing failed to start. You can manually trigger it.');
        }
      }
      
      // Reset form and close modal
      setFormData({
        document_type: 'receipt',
        description: '',
        tags: '',
      });
      setSelectedFile(null);
      setEditingDocument(null);
      setIsModalOpen(false);
      
      // Refresh documents list
      fetchDocuments(selectedBusinessId);
      
    } catch (error) {
      console.error('Failed to save document:', error);
      alert('Failed to save document. Please try again.');
    } finally {
      setIsUploading(false);
    }
  };

  const handleEdit = (document: Document) => {
    setEditingDocument(document);
    setFormData({
      document_type: document.document_type,
      description: document.description || '',
      tags: document.tags?.join(', ') || '',
    });
    setIsModalOpen(true);
  };

  const handleDelete = async (documentId: string) => {
    if (!confirm('Are you sure you want to delete this document? This action cannot be undone.')) {
      return;
    }

    try {
      await documentService.deleteDocument(documentId);
      fetchDocuments(selectedBusinessId);
      alert('Document deleted successfully!');
    } catch (error) {
      console.error('Failed to delete document:', error);
      alert('Failed to delete document. Please try again.');
    }
  };

  const handleDownload = async (documentId: string) => {
    try {
      const response = await documentService.downloadDocument(documentId);
      window.open(response.download_url, '_blank');
    } catch (error) {
      console.error('Failed to download document:', error);
      alert('Failed to download document. Please try again.');
    }
  };

  const handleProcess = async (documentId: string) => {
    try {
      setIsProcessing(prev => ({ ...prev, [documentId]: true }));
      
      await documentService.processDocument(documentId);
      
      // Wait a moment for processing to start
      setTimeout(async () => {
        await fetchDocuments(selectedBusinessId);
        setIsProcessing(prev => ({ ...prev, [documentId]: false }));
      }, 1000);
      
    } catch (error) {
      console.error('Failed to process document:', error);
      alert('Failed to process document. Please try again.');
      setIsProcessing(prev => ({ ...prev, [documentId]: false }));
    }
  };

  const handleBulkLabel = async () => {
    if (selectedDocuments.size === 0 || bulkLabels.length === 0) return;

    try {
      const updatePromises = Array.from(selectedDocuments).map(async (documentId) => {
        const document = documents.find(d => d.id === documentId);
        if (!document) return;

        // Merge existing labels with new bulk labels
        const existingLabels = document.tags || [];
        const newLabels = Array.from(new Set([...existingLabels, ...bulkLabels]));

        return documentService.updateDocument(documentId, {
          tags: newLabels
        });
      });

      await Promise.all(updatePromises);

      // Reset selection and close modal
      setSelectedDocuments(new Set());
      setBulkLabels([]);
      setIsBulkLabelModalOpen(false);

      // Refresh documents
      fetchDocuments(selectedBusinessId);
      alert(`Successfully updated labels for ${selectedDocuments.size} documents!`);

    } catch (error) {
      console.error('Failed to bulk update labels:', error);
      alert('Failed to update labels. Please try again.');
    }
  };

  const handleSelectDocument = (documentId: string, selected: boolean) => {
    const newSelection = new Set(selectedDocuments);
    if (selected) {
      newSelection.add(documentId);
    } else {
      newSelection.delete(documentId);
    }
    setSelectedDocuments(newSelection);
  };

  const handleSelectAll = (selected: boolean) => {
    if (selected) {
      const allIds = new Set(filteredDocuments.map(doc => doc.id));
      setSelectedDocuments(allIds);
    } else {
      setSelectedDocuments(new Set());
    }
  };

  const handleViewExtracted = async (documentId: string) => {
    navigate(`/documents/${documentId}`);
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

  const getExtractionStatusInfo = (status?: string, confidenceScore?: number, lowConfidenceFields?: string[]) => {
    const statuses: Record<string, { icon: any; color: string; label: string; variant: any; helpText?: string }> = {
      pending: {
        icon: Clock,
        color: 'text-gray-500',
        label: 'Not Processed',
        variant: 'default',
        helpText: 'Document uploaded but not yet processed by AI'
      },
      processing: {
        icon: Loader,
        color: 'text-blue-500 animate-spin',
        label: 'Processing...',
        variant: 'default',
        helpText: 'AI is currently analyzing the document'
      },
      completed: {
        icon: CheckCircle,
        color: 'text-green-500',
        label: 'Verified',
        variant: 'success',
        helpText: 'Document processed successfully with high confidence'
      },
      needs_review: {
        icon: AlertCircle,
        color: 'text-amber-500',
        label: 'Needs Review',
        variant: 'warning',
        helpText: 'Document processed but some fields need manual verification'
      },
      failed: {
        icon: XCircle,
        color: 'text-red-500',
        label: 'Failed',
        variant: 'danger',
        helpText: 'Document processing failed. Please try reprocessing or contact support.'
      },
    };

    // Determine status based on confidence score for completed documents
    if (status === 'completed' && confidenceScore !== undefined) {
      if (confidenceScore >= 0.9) {
        return statuses.completed;
      } else if (confidenceScore >= 0.7) {
        return statuses.needs_review;
      } else {
        return statuses.needs_review;
      }
    }

    return statuses[status || 'pending'] || statuses.pending;
  };

  const formatLowConfidenceFields = (fields?: string[]) => {
    if (!fields || fields.length === 0) return null;

    const fieldLabels: Record<string, string> = {
      payment_method: 'Payment method',
      due_date: 'Due date',
      amount: 'Amount',
      vendor: 'Vendor',
      date: 'Date',
      description: 'Description',
      tax_amount: 'Tax amount',
      total: 'Total',
    };

    const formattedFields = fields.map(field => fieldLabels[field] || field.replace(/_/g, ' ')).join(', ');
    return `Please verify: ${formattedFields}`;
  };

  // Component to display transaction linking info for a document
  const TransactionLinkInfo: React.FC<{
    document: Document;
    onLinkToTransaction?: (documentId: string) => void;
  }> = ({
    document,
    onLinkToTransaction
  }) => {
    const [transactionInfo, setTransactionInfo] = useState<Expense | null>(null);
    const [isLoading, setIsLoading] = useState(false);

    useEffect(() => {
      if (document.transaction_id) {
        fetchTransactionInfo(document.transaction_id);
      }
    }, [document.transaction_id]);

    const fetchTransactionInfo = async (transactionId: string) => {
      try {
        setIsLoading(true);
        const response = await expenseService.getExpense(transactionId);
        setTransactionInfo(response);
      } catch (error) {
        console.error('Failed to fetch transaction info:', error);
        // Keep transactionInfo as null to show error state
      } finally {
        setIsLoading(false);
      }
    };

    if (!document.transaction_id) {
      return (
        <div className="space-y-2">
          <div className="flex items-center space-x-2 text-xs text-gray-500">
            <div className="w-2 h-2 bg-gray-300 rounded-full"></div>
            <span>Not linked</span>
          </div>
          {onLinkToTransaction && (
            <Button
              variant="ghost"
              size="sm"
              icon={<Link className="w-3 h-3" />}
              onClick={() => onLinkToTransaction(document.id)}
              className="text-xs h-6 px-2 text-blue-600 hover:bg-blue-50"
            >
              Link to Transaction
            </Button>
          )}
        </div>
      );
    }

    return (
      <div className="space-y-1">
        
        {isLoading ? (
          <div className="text-xs text-gray-500">Loading transaction details...</div>
        ) : transactionInfo ? (
          <div className="text-xs text-gray-600 bg-gray-50 p-2 rounded">
            <div className="font-medium truncate">{transactionInfo.description}</div>
            <div className="text-gray-500">
              ${transactionInfo.amount.toFixed(2)} • {new Date(transactionInfo.date).toLocaleDateString('en-US', {
                month: 'short',
                day: 'numeric',
                year: 'numeric'
              })}
            </div>
          </div>
        ) : (
          <div className="text-xs text-red-500">Failed to load transaction details</div>
        )}
      </div>
    );
  };

  const filteredDocuments = documents.filter((doc) => {
    const matchesSearch =
      doc.document_name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      doc.description?.toLowerCase().includes(searchQuery.toLowerCase()) ||
      doc.tags?.some(tag => tag.toLowerCase().includes(searchQuery.toLowerCase()));
    const matchesType = typeFilter === 'all' || doc.document_type === typeFilter;
    const matchesLink = linkFilter === 'all' ||
      (linkFilter === 'linked' && doc.transaction_id) ||
      (linkFilter === 'unlinked' && !doc.transaction_id);
    const matchesLabel = labelFilter === 'all' ||
      (doc.tags && doc.tags.includes(labelFilter));
    return matchesSearch && matchesType && matchesLink && matchesLabel;
  });

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-center">
          <div className="w-16 h-16 border-4 border-primary-500 border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
          <p className="text-gray-600">Loading documents...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Documents</h1>
          <p className="text-gray-500 mt-1">Manage receipts, invoices, and other business documents</p>
          {documents.length > 0 && (
            <div className="flex items-center space-x-4 mt-2 text-sm text-gray-600">
              <span>Total: {documents.length}</span>
              <span className="flex items-center space-x-1">
                <div className="w-2 h-2 bg-green-500 rounded-full"></div>
                <span>Linked: {documents.filter(d => d.transaction_id).length}</span>
              </span>
              <span className="flex items-center space-x-1">
                <div className="w-2 h-2 bg-gray-300 rounded-full"></div>
                <span>Unlinked: {documents.filter(d => !d.transaction_id).length}</span>
              </span>
            </div>
          )}
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

          {/* Bulk Actions */}
          {selectedDocuments.size > 0 && (
            <div className="flex items-center space-x-2 px-3 py-2 bg-blue-50 border border-blue-200 rounded-lg">
              <span className="text-sm text-blue-700 font-medium">
                {selectedDocuments.size} selected
              </span>
              <Button
                variant="outline"
                size="sm"
                icon={<Tag className="w-4 h-4" />}
                onClick={() => setIsBulkLabelModalOpen(true)}
                className="text-blue-600 border-blue-300 hover:bg-blue-100"
              >
                Add Labels
              </Button>
              <Button
                variant="ghost"
                size="sm"
                onClick={() => setSelectedDocuments(new Set())}
                className="text-gray-500 hover:text-gray-700"
              >
                Clear
              </Button>
            </div>
          )}

          <Button variant="primary" icon={<Upload className="w-5 h-5" />} onClick={() => setIsModalOpen(true)}>
            Upload Document
          </Button>
        </div>
      </div>

      {/* Status Help */}
      <Card className="bg-blue-50 border-blue-200">
        <div className="flex items-start space-x-3">
          <AlertCircle className="w-5 h-5 text-blue-500 flex-shrink-0 mt-0.5" />
          <div className="text-sm">
            <p className="font-medium text-blue-900 mb-1">Document Processing Status</p>
            <div className="text-blue-800 space-y-1">
              <p><strong>Verified:</strong> Document processed successfully with high confidence</p>
              <p><strong>Needs Review:</strong> Document processed but some fields may need manual verification</p>
              <p><strong>Processing:</strong> AI is currently analyzing the document</p>
            </div>
          </div>
        </div>
      </Card>

      {/* Filters */}
      <Card>
        <div className="flex items-center space-x-4">
          <div className="flex-1 relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-5 h-5" />
            <input
              type="text"
              placeholder="Search documents, descriptions, or labels..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
            />
          </div>
          <div className="flex items-center space-x-2">
            <Filter className="w-5 h-5 text-gray-400" />
            <select
              value={typeFilter}
              onChange={(e) => setTypeFilter(e.target.value)}
              className="px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
            >
              <option value="all">All Types</option>
              <option value="receipt">Receipt</option>
              <option value="invoice">Invoice</option>
              <option value="statement">Statement</option>
              <option value="contract">Contract</option>
              <option value="other">Other</option>
            </select>
          </div>
          <div className="flex items-center space-x-2">
            <Link className="w-5 h-5 text-gray-400" />
            <select
              value={linkFilter}
              onChange={(e) => setLinkFilter(e.target.value)}
              className="px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
            >
              <option value="all">All Documents</option>
              <option value="linked">Linked to Transactions</option>
              <option value="unlinked">Not Linked</option>
            </select>
          </div>
          <div className="flex items-center space-x-2">
            <Tag className="w-5 h-5 text-gray-400" />
            <select
              value={labelFilter}
              onChange={(e) => setLabelFilter(e.target.value)}
              className="px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
            >
              <option value="all">All Labels</option>
              {Array.from(new Set(documents.flatMap(doc => doc.tags || []))).sort().map((label) => (
                <option key={label} value={label}>{label}</option>
              ))}
            </select>
          </div>
        </div>
      </Card>

      {/* Documents Grid */}
      {filteredDocuments.length === 0 ? (
        <Card>
          <div className="text-center py-12">
            <FileText className="w-16 h-16 text-gray-300 mx-auto mb-4" />
            <h3 className="text-lg font-semibold text-gray-900 mb-2">No documents found</h3>
            <p className="text-gray-500 mb-6">
              {documents.length === 0
                ? 'Get started by uploading your first document'
                : 'No documents match your search criteria'}
            </p>
            {documents.length === 0 && (
              <Button variant="primary" onClick={() => setIsModalOpen(true)}>
                Upload Document
              </Button>
            )}
          </div>
        </Card>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {/* Select All Checkbox */}
          {filteredDocuments.length > 0 && (
            <div className="col-span-full mb-2 flex items-center space-x-2">
              <input
                type="checkbox"
                checked={selectedDocuments.size === filteredDocuments.length && filteredDocuments.length > 0}
                onChange={(e) => handleSelectAll(e.target.checked)}
                className="w-4 h-4 text-primary-600 border-gray-300 rounded focus:ring-primary-500"
              />
              <label className="text-sm text-gray-700">
                Select All ({filteredDocuments.length} documents)
              </label>
            </div>
          )}

          {filteredDocuments.map((document) => {
            const typeBadge = getDocumentTypeBadge(document.document_type);
            const statusInfo = getExtractionStatusInfo(document.extraction_status, document.confidence_score, document.low_confidence_fields);
            const StatusIcon = statusInfo.icon;
            
            return (
              <Card key={document.id}>
                <div className="p-4 space-y-3">
                  {/* Selection Checkbox */}
                  <div className="flex items-center space-x-2">
                    <input
                      type="checkbox"
                      checked={selectedDocuments.has(document.id)}
                      onChange={(e) => handleSelectDocument(document.id, e.target.checked)}
                      className="w-4 h-4 text-primary-600 border-gray-300 rounded focus:ring-primary-500"
                    />
                    <div className="flex items-center space-x-3 flex-1">
                      <div className="p-2 bg-primary-50 rounded-lg">
                        <FileText className="w-6 h-6 text-primary-600" />
                      </div>
                      <div className="flex-1 min-w-0">
                        <h3 className="text-sm font-medium text-gray-900 truncate">{document.document_name}</h3>
                        <p className="text-xs text-gray-500">{formatFileSize(document.file_size)}</p>
                      </div>
                    </div>
                    <Badge variant={typeBadge.variant} size="sm">
                      {typeBadge.label}
                    </Badge>
                  </div>

                  {/* Processing Status */}
                  <div className="space-y-2">
                    <div className="flex items-center space-x-2">
                      <StatusIcon className={`w-4 h-4 ${statusInfo.color}`} />
                      <span className="text-xs text-gray-600">{statusInfo.label}</span>
                      <button
                        className="text-gray-400 hover:text-gray-600 transition-colors"
                        title={statusInfo.helpText}
                      >
                        <AlertCircle className="w-3 h-3" />
                      </button>
                    </div>

                    {/* Low confidence fields warning */}
                    {document.extraction_status === 'completed' &&
                     document.confidence_score &&
                     document.confidence_score < 0.9 &&
                     document.low_confidence_fields &&
                     document.low_confidence_fields.length > 0 && (
                      <div className="flex items-start space-x-2 p-2 bg-amber-50 border border-amber-200 rounded">
                        <AlertCircle className="w-3 h-3 text-amber-500 flex-shrink-0 mt-0.5" />
                        <p className="text-xs text-amber-700">
                          {formatLowConfidenceFields(document.low_confidence_fields)}
                        </p>
                      </div>
                    )}
                  </div>

                  {/* Transaction Linking Info */}
                  <TransactionLinkInfo
                    document={document}
                    onLinkToTransaction={(documentId) => {
                      // For now, just show an alert - in a real implementation, this would open a transaction selector
                      alert(`Link document ${documentId} to transaction`);
                    }}
                  />

                  {document.description && (
                    <p className="text-sm text-gray-600 line-clamp-2">{document.description}</p>
                  )}

                  {/* Labels */}
                  <DocumentLabelManager
                    currentLabels={document.tags || []}
                    onLabelsChange={async (newLabels) => {
                      try {
                        await documentService.updateDocument(document.id, {
                          tags: newLabels
                        });
                        // Refresh documents to show updated labels
                        fetchDocuments(selectedBusinessId);
                      } catch (error) {
                        console.error('Failed to update document labels:', error);
                        alert('Failed to update labels. Please try again.');
                      }
                    }}
                    className="mt-2"
                  />

                  {/* Processing Error */}
                  {document.extraction_status === 'failed' && document.processing_error && (
                    <div className="flex items-start space-x-2 p-2 bg-red-50 border border-red-200 rounded">
                      <AlertCircle className="w-4 h-4 text-red-500 flex-shrink-0 mt-0.5" />
                      <p className="text-xs text-red-700 line-clamp-2">{document.processing_error}</p>
                    </div>
                  )}

                  <div className="flex items-center justify-between pt-3 border-t border-gray-100">
                    <span className="text-xs text-gray-500">{formatDate(document.created_at)}</span>
                    <div className="flex items-center space-x-1">
                      {/* Process Button - show if pending or failed */}
                      {(document.extraction_status === 'pending' || document.extraction_status === 'failed') && (
                        <Button 
                          variant="ghost" 
                          size="sm" 
                          icon={<Play className="w-4 h-4" />}
                          onClick={() => handleProcess(document.id)}
                          disabled={isProcessing[document.id]}
                          title="Process document"
                        />
                      )}
                      
                      {/* View Extracted Text - show if completed */}
                      {document.extraction_status === 'completed' && (
                        <Button 
                          variant="ghost" 
                          size="sm" 
                          icon={<Eye className="w-4 h-4" />}
                          onClick={() => handleViewExtracted(document.id)}
                          title="View extracted text"
                        />
                      )}
                      
                      <Button 
                        variant="ghost" 
                        size="sm" 
                        icon={<Download className="w-4 h-4" />}
                        onClick={() => handleDownload(document.id)}
                        title="Download"
                      />
                      <Button 
                        variant="ghost" 
                        size="sm" 
                        icon={<Edit2 className="w-4 h-4" />}
                        onClick={() => handleEdit(document)}
                        title="Edit"
                      />
                      <Button
                        variant="ghost"
                        size="sm"
                        icon={<Trash2 className="w-4 h-4" />}
                        className="text-red-600 hover:bg-red-50"
                        onClick={() => handleDelete(document.id)}
                        title="Delete"
                      />
                    </div>
                  </div>
                </div>
              </Card>
            );
          })}
        </div>
      )}

      {/* Upload/Edit Modal */}
      <Modal
        isOpen={isModalOpen}
        onClose={() => {
          setIsModalOpen(false);
          setEditingDocument(null);
          setSelectedFile(null);
          setFormData({
            document_type: 'receipt',
            description: '',
            tags: '',
          });
        }}
        title={editingDocument ? "Edit Document" : "Upload Document"}
        size="lg"
      >
        <form onSubmit={handleSubmit} className="space-y-4">
          {!editingDocument && (
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1.5">
                File <span className="text-red-500">*</span>
              </label>
              <div className="border-2 border-dashed border-gray-300 rounded-lg p-6 text-center hover:border-primary-500 transition-colors">
                <input
                  type="file"
                  onChange={handleFileSelect}
                  accept=".pdf,.png,.jpg,.jpeg,.gif,.xlsx,.xls,.csv,.doc,.docx"
                  className="hidden"
                  id="file-upload"
                  required={!editingDocument}
                />
                <label htmlFor="file-upload" className="cursor-pointer">
                  <Upload className="w-8 h-8 text-gray-400 mx-auto mb-2" />
                  {selectedFile ? (
                    <div>
                      <p className="text-sm font-medium text-gray-900">{selectedFile.name}</p>
                      <p className="text-xs text-gray-500 mt-1">{formatFileSize(selectedFile.size)}</p>
                    </div>
                  ) : (
                    <div>
                      <p className="text-sm text-gray-600">Click to upload or drag and drop</p>
                      <p className="text-xs text-gray-500 mt-1">PDF, PNG, JPG, Excel, CSV up to 10MB</p>
                    </div>
                  )}
                </label>
              </div>
            </div>
          )}

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1.5">
              Document Type <span className="text-red-500">*</span>
            </label>
            <select 
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
              value={formData.document_type}
              onChange={(e) => setFormData({ ...formData, document_type: e.target.value })}
              required
            >
              <option value="receipt">Receipt</option>
              <option value="invoice">Invoice</option>
              <option value="statement">Statement</option>
              <option value="contract">Contract</option>
              <option value="other">Other</option>
            </select>
          </div>

          <Input 
            label="Description" 
            placeholder="Brief description of the document"
            value={formData.description}
            onChange={(e) => setFormData({ ...formData, description: e.target.value })}
          />

          <Input 
            label="Tags" 
            placeholder="e.g., office, travel, equipment (comma-separated)"
            value={formData.tags}
            onChange={(e) => setFormData({ ...formData, tags: e.target.value })}
          />

          <div className="flex justify-end space-x-3 pt-4 border-t border-gray-200">
            <Button type="button" variant="ghost" onClick={() => setIsModalOpen(false)} disabled={isUploading}>
              Cancel
            </Button>
            <Button type="submit" variant="primary" disabled={isUploading}>
              {isUploading ? 'Uploading...' : (editingDocument ? 'Update Document' : 'Upload Document')}
            </Button>
          </div>
        </form>
      </Modal>

      {/* Bulk Label Modal */}
      <Modal
        isOpen={isBulkLabelModalOpen}
        onClose={() => {
          setIsBulkLabelModalOpen(false);
          setBulkLabels([]);
        }}
        title={`Add Labels to ${selectedDocuments.size} Documents`}
        size="md"
      >
        <div className="space-y-4">
          <p className="text-sm text-gray-600">
            Add labels to all selected documents. Existing labels will be preserved.
          </p>

          <DocumentLabelManager
            currentLabels={bulkLabels}
            onLabelsChange={setBulkLabels}
            className="border border-gray-200 rounded-lg"
          />

          <div className="flex justify-end space-x-3 pt-4 border-t border-gray-200">
            <Button
              variant="ghost"
              onClick={() => {
                setIsBulkLabelModalOpen(false);
                setBulkLabels([]);
              }}
            >
              Cancel
            </Button>
            <Button
              variant="primary"
              onClick={handleBulkLabel}
              disabled={bulkLabels.length === 0}
            >
              Add Labels to {selectedDocuments.size} Documents
            </Button>
          </div>
        </div>
      </Modal>

    </div>
  );
};

export default Documents;
