import React, { useState, useEffect } from 'react';
import { FileText, Image, Eye, Download } from 'lucide-react';
import Button from './ui/Button';
import Modal from './ui/Modal';
import { documentService } from '../services/business.service';
import type { Document } from '../types';

interface DocumentPreviewProps {
  transactionId: string;
  businessId: string;
  compact?: boolean;
}

interface DocumentViewerModalProps {
  isOpen: boolean;
  onClose: () => void;
  document: Document | null;
  documentUrl: string | null;
}

const DocumentViewerModal: React.FC<DocumentViewerModalProps> = ({
  isOpen,
  onClose,
  document,
  documentUrl
}) => {
  const [isLoading, setIsLoading] = useState(false);

  const handleDownload = async () => {
    if (!document) return;

    try {
      setIsLoading(true);
      const response = await documentService.downloadDocument(document.id);
      window.open(response.download_url, '_blank');
    } catch (error) {
      console.error('Failed to download document:', error);
    } finally {
      setIsLoading(false);
    }
  };

  if (!document) return null;

  const isImage = document.mime_type?.startsWith('image/');
  const isPDF = document.mime_type === 'application/pdf';

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title={document.document_name}
      size="xl"
    >
      <div className="space-y-4">
        {/* Document Info */}
        <div className="flex items-center justify-between p-4 bg-gray-50 rounded-lg">
          <div className="flex items-center space-x-3">
            {isImage ? (
              <Image className="w-8 h-8 text-blue-500" />
            ) : (
              <FileText className="w-8 h-8 text-gray-500" />
            )}
            <div>
              <h3 className="font-medium text-gray-900">{document.document_name}</h3>
              <p className="text-sm text-gray-500">
                {document.file_size ? `${(document.file_size / 1024).toFixed(1)} KB` : 'Unknown size'} •
                {document.document_type} •
                {new Date(document.created_at).toLocaleDateString()}
              </p>
            </div>
          </div>
          <Button
            variant="outline"
            icon={isLoading ? undefined : <Download className="w-4 h-4" />}
            onClick={handleDownload}
            disabled={isLoading}
          >
            {isLoading ? 'Downloading...' : 'Download'}
          </Button>
        </div>

        {/* Document Viewer */}
        <div className="bg-gray-100 rounded-lg overflow-hidden">
          {documentUrl ? (
            <div className="h-96 flex items-center justify-center">
              {isImage ? (
                <img
                  src={documentUrl}
                  alt={document.document_name}
                  className="max-w-full max-h-full object-contain"
                  onError={(e) => {
                    console.error('Failed to load image:', e);
                  }}
                />
              ) : isPDF ? (
                <iframe
                  src={documentUrl}
                  className="w-full h-full border-0"
                  title={document.document_name}
                  onError={(e) => {
                    console.error('Failed to load PDF:', e);
                  }}
                />
              ) : (
                <div className="text-center">
                  <FileText className="w-16 h-16 text-gray-400 mx-auto mb-4" />
                  <p className="text-gray-600 mb-4">Document Preview Not Available</p>
                  <Button variant="primary" onClick={handleDownload}>
                    Download to View
                  </Button>
                </div>
              )}
            </div>
          ) : (
            <div className="h-96 flex items-center justify-center">
              <div className="text-center">
                <FileText className="w-16 h-16 text-gray-400 mx-auto mb-4" />
                <p className="text-gray-600 mb-4">Loading document...</p>
              </div>
            </div>
          )}
        </div>

        {/* Document Details */}
        {document.description && (
          <div className="p-4 bg-gray-50 rounded-lg">
            <h4 className="font-medium text-gray-900 mb-2">Description</h4>
            <p className="text-sm text-gray-700">{document.description}</p>
          </div>
        )}

        {/* Labels/Tags */}
        {document.tags && document.tags.length > 0 && (
          <div className="p-4 bg-gray-50 rounded-lg">
            <h4 className="font-medium text-gray-900 mb-2">Labels</h4>
            <div className="flex flex-wrap gap-2">
              {document.tags.map((tag, index) => (
                <span
                  key={index}
                  className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-800"
                >
                  {tag}
                </span>
              ))}
            </div>
          </div>
        )}
      </div>
    </Modal>
  );
};

const DocumentPreview: React.FC<DocumentPreviewProps> = ({
  transactionId,
  businessId,
  compact = false
}) => {
  const [documents, setDocuments] = useState<Document[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [selectedDocument, setSelectedDocument] = useState<Document | null>(null);
  const [documentUrl, setDocumentUrl] = useState<string | null>(null);
  const [isViewerOpen, setIsViewerOpen] = useState(false);

  useEffect(() => {
    fetchDocuments();
  }, [transactionId, businessId]);

  const fetchDocuments = async () => {
    try {
      setIsLoading(true);
      const response = await documentService.getDocuments(businessId, transactionId);
      setDocuments(response.documents);
    } catch (error) {
      console.error('Failed to fetch documents:', error);
      setDocuments([]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleViewDocument = async (document: Document) => {
    setSelectedDocument(document);
    setIsViewerOpen(true);

    try {
      const response = await documentService.downloadDocument(document.id);
      setDocumentUrl(response.download_url);
    } catch (error) {
      console.error('Failed to get document URL:', error);
      setDocumentUrl(null);
    }
  };

  const handleCloseViewer = () => {
    setIsViewerOpen(false);
    setSelectedDocument(null);
    setDocumentUrl(null);
  };

  if (isLoading) {
    return (
      <div className="flex items-center space-x-2 text-gray-400">
        <div className="w-4 h-4 border-2 border-gray-300 border-t-gray-600 rounded-full animate-spin"></div>
        <span className="text-sm">Loading...</span>
      </div>
    );
  }

  if (documents.length === 0) {
    return (
      <div className="text-gray-400 text-sm">
        No documents attached
      </div>
    );
  }

  if (compact) {
    // Compact view: show thumbnails in a row
    return (
      <>
        <div className="flex items-center space-x-2">
          <div className="flex -space-x-2">
            {documents.slice(0, 3).map((document) => (
              <div
                key={document.id}
                className="relative w-8 h-8 border-2 border-white rounded-lg overflow-hidden cursor-pointer hover:border-blue-300 transition-colors"
                onClick={() => handleViewDocument(document)}
                title={document.document_name}
              >
                {document.mime_type?.startsWith('image/') ? (
                  <div className="w-full h-full">
                    <img
                      src={`/api/documents/${document.id}/thumbnail`}
                      alt={document.document_name}
                      className="w-full h-full object-cover"
                      onError={(e) => {
                        // Fallback to icon if thumbnail fails
                        const target = e.target as HTMLImageElement;
                        const parent = target.parentElement;
                        if (parent) {
                          target.style.display = 'none';
                          const fallback = parent.querySelector('.fallback-icon') as HTMLElement;
                          if (fallback) fallback.style.display = 'flex';
                        }
                      }}
                    />
                    <div className="fallback-icon w-full h-full bg-gray-100 flex items-center justify-center" style={{ display: 'none' }}>
                      <FileText className="w-4 h-4 text-gray-400" />
                    </div>
                  </div>
                ) : (
                  <div className="w-full h-full bg-gray-100 flex items-center justify-center">
                    <FileText className="w-4 h-4 text-gray-400" />
                  </div>
                )}
              </div>
            ))}
            {documents.length > 3 && (
              <div className="w-8 h-8 bg-gray-100 border-2 border-white rounded-lg flex items-center justify-center">
                <span className="text-xs text-gray-600 font-medium">+{documents.length - 3}</span>
              </div>
            )}
          </div>
          <Button
            variant="ghost"
            size="sm"
            icon={<Eye className="w-4 h-4" />}
            onClick={() => documents.length > 0 && handleViewDocument(documents[0])}
            className="text-blue-600 hover:bg-blue-50"
          >
            View
          </Button>
        </div>

        <DocumentViewerModal
          isOpen={isViewerOpen}
          onClose={handleCloseViewer}
          document={selectedDocument}
          documentUrl={documentUrl}
        />
      </>
    );
  }

  // Full view: show document cards
  return (
    <>
      <div className="space-y-3">
        <div className="flex items-center justify-between">
          <h4 className="text-sm font-medium text-gray-900">
            Documents ({documents.length})
          </h4>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
          {documents.map((document) => (
            <div
              key={document.id}
              className="p-3 border border-gray-200 rounded-lg hover:shadow-md transition-shadow cursor-pointer bg-white"
              onClick={() => handleViewDocument(document)}
            >
              <div className="flex items-start space-x-3">
                <div className="flex-shrink-0">
                  {document.mime_type?.startsWith('image/') ? (
                    <div className="w-12 h-12 bg-gray-100 rounded-lg overflow-hidden">
                      <img
                        src={`/api/documents/${document.id}/thumbnail`}
                        alt={document.document_name}
                        className="w-full h-full object-cover"
                        onError={(e) => {
                          // Fallback to icon if thumbnail fails
                          const target = e.target as HTMLImageElement;
                          const parent = target.parentElement;
                          if (parent) {
                            target.style.display = 'none';
                            const fallback = parent.querySelector('.fallback-icon') as HTMLElement;
                            if (fallback) fallback.style.display = 'flex';
                          }
                        }}
                      />
                      <div className="fallback-icon w-full h-full flex items-center justify-center" style={{ display: 'none' }}>
                        <Image className="w-6 h-6 text-gray-400" />
                      </div>
                    </div>
                  ) : (
                    <div className="w-12 h-12 bg-gray-100 rounded-lg flex items-center justify-center">
                      <FileText className="w-6 h-6 text-gray-400" />
                    </div>
                  )}
                </div>

                <div className="flex-1 min-w-0">
                  <h5 className="text-sm font-medium text-gray-900 truncate">
                    {document.document_name}
                  </h5>
                  <p className="text-xs text-gray-500">
                    {document.file_size ? `${(document.file_size / 1024).toFixed(1)} KB` : 'Unknown size'} •
                    {document.document_type}
                  </p>
                  {document.description && (
                    <p className="text-xs text-gray-600 mt-1 line-clamp-2">
                      {document.description}
                    </p>
                  )}
                  {document.tags && document.tags.length > 0 && (
                    <div className="flex flex-wrap gap-1 mt-2">
                      {document.tags.slice(0, 2).map((tag) => (
                        <span
                          key={tag}
                          className="inline-flex items-center px-1.5 py-0.5 rounded text-xs font-medium bg-blue-100 text-blue-800"
                        >
                          {tag}
                        </span>
                      ))}
                      {document.tags.length > 2 && (
                        <span className="text-xs text-gray-500">
                          +{document.tags.length - 2} more
                        </span>
                      )}
                    </div>
                  )}
                </div>

                <div className="flex-shrink-0">
                  <Eye className="w-4 h-4 text-gray-400" />
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>

      <DocumentViewerModal
        isOpen={isViewerOpen}
        onClose={handleCloseViewer}
        document={selectedDocument}
        documentUrl={documentUrl}
      />
    </>
  );
};

export default DocumentPreview;