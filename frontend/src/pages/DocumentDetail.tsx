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
  Link as LinkIcon,
  ExternalLink,
  BarChart3,
  Code,
  Database
} from 'lucide-react';
import Button from '../components/ui/Button';
import Card from '../components/ui/Card';
import Badge from '../components/ui/Badge';
import { documentService, expenseService } from '../services/business.service';
import DocumentLabelManager from '../components/DocumentLabelManager';
import type { Document, DocumentProcessingStatus, Expense } from '../types';

const DocumentDetail: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();

  const [document, setDocument] = useState<Document | null>(null);
  const [processingStatus, setProcessingStatus] = useState<DocumentProcessingStatus | null>(null);
  const [linkedTransaction, setLinkedTransaction] = useState<Expense | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isProcessing, setIsProcessing] = useState(false);
  const [documentUrl, setDocumentUrl] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<'viewer' | 'extracted' | 'structured' | 'confidence' | 'transaction'>('extracted');

  useEffect(() => {
    if (id) {
      fetchDocumentData(id);
    }
  }, [id]);

  const fetchDocumentData = async (documentId: string) => {
    try {
      setIsLoading(true);

      // Fetch document details
      const docResponse = await documentService.getDocument(documentId);
      setDocument(docResponse);
      console.log('Document data:', docResponse);

      // Get document download URL for viewing
      try {
        const downloadResponse = await documentService.downloadDocument(documentId);
        setDocumentUrl(downloadResponse.download_url);
      } catch (downloadError) {
        console.error('Failed to get document download URL:', downloadError);
      }

      // Always try to fetch processing status (not just if is_processed is true)
      let fetchedProcessingStatus: DocumentProcessingStatus | null = null;
      try {
        const statusResponse = await documentService.getProcessingStatus(documentId);
        fetchedProcessingStatus = statusResponse;
        setProcessingStatus(statusResponse);
        console.log('Processing status:', statusResponse);
      } catch (statusError) {
        console.error('Failed to fetch processing status:', statusError);
        // Don't set processing status to null, keep it as is
      }

      // Fetch linked transaction if exists (check both document and processing status)
      const transactionId = docResponse.transaction_id || fetchedProcessingStatus?.transaction_id;
      if (transactionId) {
        try {
          const transactionResponse = await expenseService.getExpense(transactionId);
          setLinkedTransaction(transactionResponse);
        } catch (transactionError) {
          console.error('Failed to fetch linked transaction:', transactionError);
          setLinkedTransaction(null);
        }
      } else {
        setLinkedTransaction(null);
      }

    } catch (error) {
      console.error('Failed to fetch document data:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const handleProcessDocument = async () => {
    if (!document) return;

    try {
      setIsProcessing(true);
      await documentService.processDocument(document.id);

      // Wait a moment then refresh data
      setTimeout(() => {
        fetchDocumentData(document.id);
        setIsProcessing(false);
      }, 2000);

    } catch (error) {
      console.error('Failed to process document:', error);
      setIsProcessing(false);
    }
  };

  const handleDownload = async () => {
    if (!document) return;

    try {
      const response = await documentService.downloadDocument(document.id);
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

    // Determine status based on confidence score for completed documents
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

  const DocumentViewer: React.FC<{ document: Document; documentUrl: string | null }> = ({ document, documentUrl }) => {
    const isImage = document.mime_type?.startsWith('image/');
    const isPDF = document.mime_type === 'application/pdf';

    if (isImage && documentUrl) {
      return (
        <div className="flex items-center justify-center h-full bg-gray-100 rounded-lg">
          <img
            src={documentUrl}
            alt={document.document_name}
            className="max-w-full max-h-full object-contain rounded-lg shadow-lg"
            onError={(e) => {
              console.error('Failed to load image:', e);
            }}
          />
        </div>
      );
    }

    if (isPDF && documentUrl) {
      return (
        <div className="h-full bg-gray-100 rounded-lg overflow-hidden">
          <iframe
            src={documentUrl}
            className="w-full h-full border-0"
            title={document.document_name}
            onError={(e) => {
              console.error('Failed to load PDF:', e);
            }}
          />
        </div>
      );
    }

    return (
      <div className="flex items-center justify-center h-full bg-gray-100 rounded-lg">
        <div className="text-center">
          <FileText className="w-16 h-16 text-gray-400 mx-auto mb-4" />
          <p className="text-gray-600 mb-4">Document Preview Not Available</p>
          <Button variant="primary" icon={<Download className="w-4 h-4" />} onClick={handleDownload}>
            Download Document
          </Button>
        </div>
      </div>
    );
  };

  const ExtractedTextSection: React.FC<{ status: DocumentProcessingStatus }> = ({ status }) => (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h3 className="text-lg font-semibold text-gray-900 flex items-center">
          <FileText className="w-5 h-5 mr-2" />
          Extracted Text
        </h3>
        {status.word_count && (
          <Badge variant="default">{status.word_count} words</Badge>
        )}
      </div>

      {status.raw_text_preview ? (
        <div className="bg-gray-50 border border-gray-200 rounded-lg p-4 max-h-96 overflow-y-auto">
          <pre className="text-sm text-gray-700 whitespace-pre-wrap font-mono leading-relaxed">
            {status.raw_text_preview}
            {status.raw_text_length && status.raw_text_length > 500 && (
              <span className="text-gray-500 italic">
                {'\n\n'}... (showing first 500 characters of {status.raw_text_length} total)
              </span>
            )}
          </pre>
        </div>
      ) : (
        <div className="text-center py-8 text-gray-500">
          <FileText className="w-12 h-12 mx-auto mb-2 text-gray-300" />
          <p>No extracted text available</p>
        </div>
      )}
    </div>
  );

  const StructuredDataSection: React.FC<{ status: DocumentProcessingStatus }> = ({ status }) => (
    <div className="space-y-4">
      <h3 className="text-lg font-semibold text-gray-900 flex items-center">
        <Database className="w-5 h-5 mr-2" />
        Structured Data
      </h3>

      {status.structured_data && Object.keys(status.structured_data).length > 0 ? (
        <div className="bg-gray-50 border border-gray-200 rounded-lg p-4 max-h-96 overflow-y-auto">
          <pre className="text-sm text-gray-700 whitespace-pre-wrap font-mono">
            {JSON.stringify(status.structured_data, null, 2)}
          </pre>
        </div>
      ) : (
        <div className="text-center py-8 text-gray-500">
          <Database className="w-12 h-12 mx-auto mb-2 text-gray-300" />
          <p>No structured data available</p>
        </div>
      )}
    </div>
  );

  const ConfidenceSection: React.FC<{ status: DocumentProcessingStatus }> = ({ status }) => (
    <div className="space-y-4">
      <h3 className="text-lg font-semibold text-gray-900 flex items-center">
        <BarChart3 className="w-5 h-5 mr-2" />
        AI Confidence Analysis
      </h3>

      <div className="space-y-4">
        {/* Overall Confidence */}
        {status.confidence_score !== undefined && (
          <Card className="p-4">
            <div className="flex items-center justify-between mb-2">
              <span className="text-sm font-medium text-gray-700">Overall Confidence</span>
              <span className="text-sm font-bold text-gray-900">
                {Math.round(status.confidence_score * 100)}%
              </span>
            </div>
            <div className="w-full bg-gray-200 rounded-full h-2">
              <div
                className={`h-2 rounded-full ${
                  status.confidence_score >= 0.9 ? 'bg-green-500' :
                  status.confidence_score >= 0.7 ? 'bg-yellow-500' : 'bg-red-500'
                }`}
                style={{ width: `${status.confidence_score * 100}%` }}
              />
            </div>
            <p className="text-xs text-gray-500 mt-2">
              {status.confidence_score >= 0.9 ? 'High confidence - data is reliable' :
               status.confidence_score >= 0.7 ? 'Medium confidence - review recommended' :
               'Low confidence - manual verification required'}
            </p>
          </Card>
        )}

        {/* Low Confidence Fields */}
        {status.low_confidence_fields && status.low_confidence_fields.length > 0 && (
          <Card className="p-4 border-amber-200 bg-amber-50">
            <div className="flex items-start space-x-2">
              <AlertCircle className="w-5 h-5 text-amber-500 flex-shrink-0 mt-0.5" />
              <div>
                <h4 className="text-sm font-medium text-amber-900 mb-2">Fields Needing Review</h4>
                <div className="space-y-1">
                  {status.low_confidence_fields.map((field, index) => (
                    <div key={index} className="text-sm text-amber-800">
                      • {field.replace(/_/g, ' ')}
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </Card>
        )}

        {/* Processing Details */}
        <Card className="p-4">
          <h4 className="text-sm font-medium text-gray-700 mb-3">Processing Details</h4>
          <div className="grid grid-cols-2 gap-4 text-sm">
            <div>
              <span className="text-gray-500">Status:</span>
              <div className="flex items-center mt-1">
                {React.createElement(getExtractionStatusInfo(status.extraction_status, status.confidence_score).icon, {
                  className: `w-4 h-4 mr-2 ${getExtractionStatusInfo(status.extraction_status, status.confidence_score).color}`
                })}
                <span className="font-medium">
                  {getExtractionStatusInfo(status.extraction_status, status.confidence_score).label}
                </span>
              </div>
            </div>
            {status.processed_at && (
              <div>
                <span className="text-gray-500">Processed:</span>
                <div className="font-medium mt-1">{formatDate(status.processed_at)}</div>
              </div>
            )}
          </div>
        </Card>
      </div>
    </div>
  );

  const TransactionSection: React.FC<{ transaction: Expense | null }> = ({ transaction }) => (
    <div className="space-y-4">
      <h3 className="text-lg font-semibold text-gray-900 flex items-center">
        <LinkIcon className="w-5 h-5 mr-2" />
        Linked Transaction
      </h3>

      {transaction ? (
        <Card className="p-4">
          <div className="flex items-start justify-between mb-4">
            <div className="flex-1">
              <h4 className="text-lg font-semibold text-gray-900 mb-1">
                {transaction.description}
              </h4>
              <div className="flex items-center space-x-4 text-sm text-gray-600">
                <span>${transaction.amount.toFixed(2)}</span>
                <span>{new Date(transaction.date).toLocaleDateString()}</span>
                <Badge variant={
                  transaction.status === 'approved' ? 'success' :
                  transaction.status === 'pending' ? 'warning' :
                  transaction.status === 'rejected' ? 'danger' : 'default'
                }>
                  {transaction.status}
                </Badge>
              </div>
            </div>
            <Button
              variant="ghost"
              size="sm"
              icon={<ExternalLink className="w-4 h-4" />}
              onClick={() => navigate(`/expenses`)}
              className="text-blue-600 hover:bg-blue-50"
            >
              View Transaction
            </Button>
          </div>

          <div className="grid grid-cols-2 gap-4 text-sm">
            {transaction.vendor && (
              <div>
                <span className="text-gray-500">Vendor:</span>
                <div className="font-medium">{transaction.vendor}</div>
              </div>
            )}
            {transaction.payment_method && (
              <div>
                <span className="text-gray-500">Payment Method:</span>
                <div className="font-medium">{transaction.payment_method}</div>
              </div>
            )}
            {transaction.notes && (
              <div className="col-span-2">
                <span className="text-gray-500">Notes:</span>
                <div className="font-medium mt-1">{transaction.notes}</div>
              </div>
            )}
          </div>
        </Card>
      ) : (
        <Card className="p-8 text-center">
          <LinkIcon className="w-12 h-12 text-gray-300 mx-auto mb-4" />
          <h4 className="text-lg font-medium text-gray-900 mb-2">No Linked Transaction</h4>
          <p className="text-gray-600 mb-4">
            This document is not currently linked to any transaction.
          </p>
          <Button
            variant="outline"
            icon={<LinkIcon className="w-4 h-4" />}
            onClick={() => navigate('/expenses')}
          >
            Link to Transaction
          </Button>
        </Card>
      )}
    </div>
  );

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-center">
          <div className="w-16 h-16 border-4 border-primary-500 border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
          <p className="text-gray-600">Loading document...</p>
        </div>
      </div>
    );
  }

  if (!document) {
    return (
      <div className="text-center py-12">
        <h1 className="text-2xl font-bold text-gray-900 mb-4">Document Not Found</h1>
        <p className="text-gray-600 mb-6">The document you're looking for doesn't exist or has been deleted.</p>
        <Button variant="primary" onClick={() => navigate('/documents')}>
          Back to Documents
        </Button>
      </div>
    );
  }

  const typeBadge = getDocumentTypeBadge(document.document_type);
  const statusInfo = getExtractionStatusInfo(document.extraction_status, document.confidence_score);

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-4">
          <Button
            variant="ghost"
            icon={<ArrowLeft className="w-5 h-5" />}
            onClick={() => navigate('/documents')}
          >
            Back to Documents
          </Button>
          <div>
            <h1 className="text-2xl font-bold text-gray-900">{document.document_name}</h1>
            <p className="text-gray-500 mt-1">
              {formatFileSize(document.file_size)} • Uploaded {formatDate(document.created_at)}
            </p>
          </div>
        </div>
        <div className="flex items-center space-x-3">
          <Badge variant={typeBadge.variant}>{typeBadge.label}</Badge>
          <div className="flex items-center space-x-2">
            {React.createElement(statusInfo.icon, {
              className: `w-4 h-4 ${statusInfo.color}`
            })}
            <span className="text-sm text-gray-600">{statusInfo.label}</span>
          </div>
          <DocumentLabelManager
            currentLabels={document.tags || []}
            onLabelsChange={async (newLabels) => {
              try {
                await documentService.updateDocument(document.id, {
                  tags: newLabels
                });
                // Refresh document data to show updated labels
                fetchDocumentData(document.id);
              } catch (error) {
                console.error('Failed to update document labels:', error);
                alert('Failed to update labels. Please try again.');
              }
            }}
            className="mr-2"
          />
          <Button variant="outline" icon={<Download className="w-4 h-4" />} onClick={handleDownload}>
            Download
          </Button>
          {document.extraction_status === 'pending' || document.extraction_status === 'failed' ? (
            <Button
              variant="primary"
              icon={<Loader className={`w-4 h-4 ${isProcessing ? 'animate-spin' : ''}`} />}
              onClick={handleProcessDocument}
              disabled={isProcessing}
            >
              {isProcessing ? 'Processing...' : 'Process Document'}
            </Button>
          ) : null}
        </div>
      </div>

      {/* Main Content */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Left Side - Document Viewer */}
        <div className="space-y-4">
          <Card className="p-0">
            <div className="p-4 border-b border-gray-200">
              <h2 className="text-lg font-semibold text-gray-900 flex items-center">
                <Eye className="w-5 h-5 mr-2" />
                Document Viewer
              </h2>
            </div>
            <div className="p-4">
              <div className="h-96">
                <DocumentViewer document={document} documentUrl={documentUrl} />
              </div>
            </div>
          </Card>
        </div>

        {/* Right Side - Data Sections */}
        <div className="space-y-4">
          {/* Tab Navigation */}
          <Card className="p-4">
            <div className="flex space-x-1 mb-4">
              {[
                { id: 'extracted', label: 'Extracted Text', icon: FileText },
                { id: 'structured', label: 'Structured Data', icon: Code },
                { id: 'confidence', label: 'AI Confidence', icon: BarChart3 },
                { id: 'transaction', label: 'Transaction', icon: LinkIcon },
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

              {activeTab === 'extracted' && processingStatus && (
                <ExtractedTextSection status={processingStatus} />
              )}
              {activeTab === 'structured' && processingStatus && (
                <StructuredDataSection status={processingStatus} />
              )}
              {activeTab === 'confidence' && processingStatus && (
                <ConfidenceSection status={processingStatus} />
              )}
              {activeTab === 'transaction' && (
                <TransactionSection transaction={linkedTransaction} />
              )}

              {/* Empty State */}
              {((activeTab === 'extracted' || activeTab === 'structured' || activeTab === 'confidence') && !processingStatus) && (
                <div className="text-center py-12">
                  <AlertCircle className="w-12 h-12 text-gray-300 mx-auto mb-4" />
                  <h3 className="text-lg font-medium text-gray-900 mb-2">Document Not Processed</h3>
                  <p className="text-gray-600 mb-4">
                    This document hasn't been processed yet. Process it to see extracted data.
                  </p>
                  <Button
                    variant="primary"
                    icon={<Loader className={`w-4 h-4 ${isProcessing ? 'animate-spin' : ''}`} />}
                    onClick={handleProcessDocument}
                    disabled={isProcessing}
                  >
                    {isProcessing ? 'Processing...' : 'Process Document'}
                  </Button>
                </div>
              )}
            </div>
          </Card>
        </div>
      </div>
    </div>
  );
};

export default DocumentDetail;