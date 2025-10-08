import React, { useState, useEffect } from 'react';
import { Search, Filter, Upload, Download, Edit2, Trash2, FileText, Play, Eye, CheckCircle, XCircle, Clock, Loader, AlertCircle } from 'lucide-react';
import Button from '../components/ui/Button';
import Card from '../components/ui/Card';
import Modal from '../components/ui/Modal';
import Input from '../components/ui/Input';
import Badge from '../components/ui/Badge';
import { businessService, documentService } from '../services/business.service';
import type { Business, Document, DocumentProcessingStatus } from '../types';

const Documents: React.FC = () => {
  const [documents, setDocuments] = useState<Document[]>([]);
  const [businesses, setBusinesses] = useState<Business[]>([]);
  const [selectedBusinessId, setSelectedBusinessId] = useState<string>('');
  const [isLoading, setIsLoading] = useState(true);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [editingDocument, setEditingDocument] = useState<Document | null>(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [typeFilter, setTypeFilter] = useState<string>('all');
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [isUploading, setIsUploading] = useState(false);
  const [isViewModalOpen, setIsViewModalOpen] = useState(false);
  const [viewingDocument, setViewingDocument] = useState<DocumentProcessingStatus | null>(null);
  const [isProcessing, setIsProcessing] = useState<Record<string, boolean>>({});
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

  const handleViewExtracted = async (documentId: string) => {
    try {
      const status = await documentService.getProcessingStatus(documentId);
      setViewingDocument(status);
      setIsViewModalOpen(true);
    } catch (error) {
      console.error('Failed to get processing status:', error);
      alert('Failed to load extracted data. Please try again.');
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

  const getExtractionStatusInfo = (status?: string) => {
    const statuses: Record<string, { icon: any; color: string; label: string; variant: any }> = {
      pending: { icon: Clock, color: 'text-gray-500', label: 'Not Processed', variant: 'default' },
      processing: { icon: Loader, color: 'text-blue-500 animate-spin', label: 'Processing...', variant: 'default' },
      completed: { icon: CheckCircle, color: 'text-green-500', label: 'Processed', variant: 'success' },
      failed: { icon: XCircle, color: 'text-red-500', label: 'Failed', variant: 'danger' },
    };
    return statuses[status || 'pending'] || statuses.pending;
  };

  const filteredDocuments = documents.filter((doc) => {
    const matchesSearch =
      doc.document_name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      doc.description?.toLowerCase().includes(searchQuery.toLowerCase());
    const matchesType = typeFilter === 'all' || doc.document_type === typeFilter;
    return matchesSearch && matchesType;
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
          <Button variant="primary" icon={<Upload className="w-5 h-5" />} onClick={() => setIsModalOpen(true)}>
            Upload Document
          </Button>
        </div>
      </div>

      {/* Filters */}
      <Card>
        <div className="flex items-center space-x-4">
          <div className="flex-1 relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-5 h-5" />
            <input
              type="text"
              placeholder="Search documents..."
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
          {filteredDocuments.map((document) => {
            const typeBadge = getDocumentTypeBadge(document.document_type);
            const statusInfo = getExtractionStatusInfo(document.extraction_status);
            const StatusIcon = statusInfo.icon;
            
            return (
              <Card key={document.id}>
                <div className="p-4 space-y-3">
                  <div className="flex items-start justify-between">
                    <div className="flex items-center space-x-3">
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
                  <div className="flex items-center space-x-2">
                    <StatusIcon className={`w-4 h-4 ${statusInfo.color}`} />
                    <span className="text-xs text-gray-600">{statusInfo.label}</span>
                    {document.extraction_status === 'completed' && document.confidence_score && (
                      <span className="text-xs text-gray-500">
                        ({Math.round(document.confidence_score * 100)}% confidence)
                      </span>
                    )}
                  </div>

                  {document.description && (
                    <p className="text-sm text-gray-600 line-clamp-2">{document.description}</p>
                  )}

                  {document.tags && document.tags.length > 0 && (
                    <div className="flex flex-wrap gap-1">
                      {document.tags.map((tag, index) => (
                        <span key={index} className="px-2 py-1 text-xs bg-gray-100 text-gray-600 rounded">
                          {tag}
                        </span>
                      ))}
                    </div>
                  )}

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

      {/* View Extracted Text Modal */}
      <Modal
        isOpen={isViewModalOpen}
        onClose={() => {
          setIsViewModalOpen(false);
          setViewingDocument(null);
        }}
        title="Extracted Document Data"
        size="xl"
      >
        {viewingDocument && (
          <div className="space-y-6">
            {/* Document Info */}
            <div className="grid grid-cols-2 gap-4 p-4 bg-gray-50 rounded-lg">
              <div>
                <p className="text-xs text-gray-500 mb-1">Document Name</p>
                <p className="text-sm font-medium text-gray-900">{viewingDocument.document_name}</p>
              </div>
              <div>
                <p className="text-xs text-gray-500 mb-1">Status</p>
                <Badge variant={getExtractionStatusInfo(viewingDocument.extraction_status).variant} size="sm">
                  {getExtractionStatusInfo(viewingDocument.extraction_status).label}
                </Badge>
              </div>
              {viewingDocument.confidence_score && (
                <div>
                  <p className="text-xs text-gray-500 mb-1">Confidence Score</p>
                  <p className="text-sm font-medium text-gray-900">
                    {Math.round(viewingDocument.confidence_score * 100)}%
                  </p>
                </div>
              )}
              {viewingDocument.word_count && (
                <div>
                  <p className="text-xs text-gray-500 mb-1">Word Count</p>
                  <p className="text-sm font-medium text-gray-900">{viewingDocument.word_count}</p>
                </div>
              )}
              {viewingDocument.processed_at && (
                <div>
                  <p className="text-xs text-gray-500 mb-1">Processed At</p>
                  <p className="text-sm font-medium text-gray-900">{formatDate(viewingDocument.processed_at)}</p>
                </div>
              )}
            </div>

            {/* Extracted Text */}
            {viewingDocument.raw_text_preview && (
              <div>
                <h3 className="text-sm font-semibold text-gray-900 mb-2 flex items-center">
                  <FileText className="w-4 h-4 mr-2" />
                  Extracted Text ({viewingDocument.raw_text_length} characters)
                </h3>
                <div className="p-4 bg-gray-50 rounded-lg border border-gray-200 max-h-96 overflow-y-auto">
                  <pre className="text-xs text-gray-700 whitespace-pre-wrap font-mono">
                    {viewingDocument.raw_text_preview}
                    {viewingDocument.raw_text_length && viewingDocument.raw_text_length > 500 && (
                      <span className="text-gray-500 italic">\n\n... (showing first 500 characters)</span>
                    )}
                  </pre>
                </div>
              </div>
            )}

            {/* Structured Data */}
            {viewingDocument.structured_data && Object.keys(viewingDocument.structured_data).length > 0 && (
              <div>
                <h3 className="text-sm font-semibold text-gray-900 mb-2">Structured Data</h3>
                <div className="p-4 bg-gray-50 rounded-lg border border-gray-200 max-h-96 overflow-y-auto">
                  <pre className="text-xs text-gray-700 whitespace-pre-wrap font-mono">
                    {JSON.stringify(viewingDocument.structured_data, null, 2)}
                  </pre>
                </div>
              </div>
            )}

            {/* Processing Error */}
            {viewingDocument.processing_error && (
              <div className="p-4 bg-red-50 border border-red-200 rounded-lg">
                <div className="flex items-start space-x-2">
                  <AlertCircle className="w-5 h-5 text-red-500 flex-shrink-0 mt-0.5" />
                  <div>
                    <h3 className="text-sm font-semibold text-red-900 mb-1">Processing Error</h3>
                    <p className="text-sm text-red-700">{viewingDocument.processing_error}</p>
                  </div>
                </div>
              </div>
            )}

            {/* Close Button */}
            <div className="flex justify-end pt-4 border-t border-gray-200">
              <Button 
                variant="primary" 
                onClick={() => {
                  setIsViewModalOpen(false);
                  setViewingDocument(null);
                }}
              >
                Close
              </Button>
            </div>
          </div>
        )}
      </Modal>
    </div>
  );
};

export default Documents;
