import React, { useState, useRef } from 'react';
import { Upload, X, FileText, Image as ImageIcon, File } from 'lucide-react';
import { FileAttachment } from '../../types';

interface FileUploadProps {
  files: FileAttachment[];
  onFilesChange: (files: FileAttachment[]) => void;
  maxFiles?: number;
  maxSizeMB?: number;
  acceptedTypes?: string[];
}

const FileUpload: React.FC<FileUploadProps> = ({
  files,
  onFilesChange,
  maxFiles = 10,
  maxSizeMB = 10,
  acceptedTypes = ['.pdf', '.png', '.jpg', '.jpeg', '.gif', '.xlsx', '.xls', '.csv', '.doc', '.docx']
}) => {
  const [isDragging, setIsDragging] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(true);
  };

  const handleDragLeave = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    
    const droppedFiles = Array.from(e.dataTransfer.files);
    handleFiles(droppedFiles);
  };

  const handleFileInput = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files) {
      const selectedFiles = Array.from(e.target.files);
      handleFiles(selectedFiles);
    }
  };

  const handleFiles = (newFiles: File[]) => {
    // Check max files limit
    if (files.length + newFiles.length > maxFiles) {
      alert(`Maximum ${maxFiles} files allowed`);
      return;
    }

    // Validate and process each file
    const validFiles: FileAttachment[] = [];
    const maxSize = maxSizeMB * 1024 * 1024;

    for (const file of newFiles) {
      // Check file size
      if (file.size > maxSize) {
        alert(`File ${file.name} exceeds ${maxSizeMB}MB limit`);
        continue;
      }

      // Check file type
      const fileExt = '.' + file.name.split('.').pop()?.toLowerCase();
      if (!acceptedTypes.includes(fileExt)) {
        alert(`File type ${fileExt} not allowed for ${file.name}`);
        continue;
      }

      // Create preview for images
      let preview: string | undefined;
      if (file.type.startsWith('image/')) {
        preview = URL.createObjectURL(file);
      }

      // Determine document type based on file extension
      let documentType = 'other';
      if (['.pdf'].includes(fileExt)) documentType = 'receipt';
      else if (['.png', '.jpg', '.jpeg', '.gif'].includes(fileExt)) documentType = 'receipt';
      else if (['.xlsx', '.xls', '.csv'].includes(fileExt)) documentType = 'statement';
      else if (['.doc', '.docx'].includes(fileExt)) documentType = 'invoice';

      validFiles.push({
        file,
        document_type: documentType,
        description: '',
        tags: '',
        preview
      });
    }

    onFilesChange([...files, ...validFiles]);
  };

  const removeFile = (index: number) => {
    const newFiles = [...files];
    // Revoke preview URL if it exists
    if (newFiles[index].preview) {
      URL.revokeObjectURL(newFiles[index].preview!);
    }
    newFiles.splice(index, 1);
    onFilesChange(newFiles);
  };

  const updateFileMetadata = (index: number, field: keyof FileAttachment, value: string) => {
    const newFiles = [...files];
    newFiles[index] = { ...newFiles[index], [field]: value };
    onFilesChange(newFiles);
  };

  const formatFileSize = (bytes: number): string => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i];
  };

  const getFileIcon = (file: File) => {
    if (file.type.startsWith('image/')) return <ImageIcon className="w-8 h-8 text-blue-500" />;
    if (file.type === 'application/pdf') return <FileText className="w-8 h-8 text-red-500" />;
    return <File className="w-8 h-8 text-gray-500" />;
  };

  return (
    <div className="space-y-4">
      {/* Drop Zone */}
      <div
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
        onClick={() => fileInputRef.current?.click()}
        className={`border-2 border-dashed rounded-lg p-8 text-center cursor-pointer transition-colors ${
          isDragging
            ? 'border-primary-500 bg-primary-50'
            : 'border-gray-300 hover:border-primary-400 hover:bg-gray-50'
        }`}
      >
        <Upload className="w-12 h-12 text-gray-400 mx-auto mb-4" />
        <p className="text-gray-700 font-medium mb-1">
          Drop files here or click to browse
        </p>
        <p className="text-sm text-gray-500">
          Supports: {acceptedTypes.join(', ')} • Max {maxSizeMB}MB per file • Up to {maxFiles} files
        </p>
        <input
          ref={fileInputRef}
          type="file"
          multiple
          accept={acceptedTypes.join(',')}
          onChange={handleFileInput}
          className="hidden"
        />
      </div>

      {/* File List */}
      {files.length > 0 && (
        <div className="space-y-3">
          <h4 className="text-sm font-medium text-gray-700">
            Attached Files ({files.length}/{maxFiles})
          </h4>
          {files.map((fileAttachment, index) => (
            <div
              key={index}
              className="border border-gray-200 rounded-lg p-4 bg-white"
            >
              <div className="flex items-start space-x-4">
                {/* File Icon/Preview */}
                <div className="flex-shrink-0">
                  {fileAttachment.preview ? (
                    <img
                      src={fileAttachment.preview}
                      alt={fileAttachment.file.name}
                      className="w-16 h-16 object-cover rounded"
                    />
                  ) : (
                    <div className="w-16 h-16 bg-gray-100 rounded flex items-center justify-center">
                      {getFileIcon(fileAttachment.file)}
                    </div>
                  )}
                </div>

                {/* File Details */}
                <div className="flex-1 min-w-0">
                  <div className="flex items-start justify-between mb-2">
                    <div className="flex-1 min-w-0 mr-2">
                      <p className="text-sm font-medium text-gray-900 truncate">
                        {fileAttachment.file.name}
                      </p>
                      <p className="text-xs text-gray-500">
                        {formatFileSize(fileAttachment.file.size)}
                      </p>
                    </div>
                    <button
                      type="button"
                      onClick={() => removeFile(index)}
                      className="flex-shrink-0 p-1 text-gray-400 hover:text-red-500 transition-colors"
                    >
                      <X className="w-5 h-5" />
                    </button>
                  </div>

                  {/* Metadata Inputs */}
                  <div className="grid grid-cols-2 gap-2">
                    <div>
                      <label className="block text-xs text-gray-600 mb-1">
                        Document Type
                      </label>
                      <select
                        value={fileAttachment.document_type}
                        onChange={(e) => updateFileMetadata(index, 'document_type', e.target.value)}
                        className="w-full px-2 py-1.5 text-sm border border-gray-300 rounded focus:outline-none focus:ring-2 focus:ring-primary-500"
                      >
                        <option value="receipt">Receipt</option>
                        <option value="invoice">Invoice</option>
                        <option value="statement">Statement</option>
                        <option value="contract">Contract</option>
                        <option value="other">Other</option>
                      </select>
                    </div>
                    <div>
                      <label className="block text-xs text-gray-600 mb-1">
                        Tags (comma-separated)
                      </label>
                      <input
                        type="text"
                        value={fileAttachment.tags || ''}
                        onChange={(e) => updateFileMetadata(index, 'tags', e.target.value)}
                        placeholder="e.g., urgent, tax-deductible"
                        className="w-full px-2 py-1.5 text-sm border border-gray-300 rounded focus:outline-none focus:ring-2 focus:ring-primary-500"
                      />
                    </div>
                  </div>
                  <div className="mt-2">
                    <label className="block text-xs text-gray-600 mb-1">
                      Description (optional)
                    </label>
                    <input
                      type="text"
                      value={fileAttachment.description || ''}
                      onChange={(e) => updateFileMetadata(index, 'description', e.target.value)}
                      placeholder="Brief description..."
                      className="w-full px-2 py-1.5 text-sm border border-gray-300 rounded focus:outline-none focus:ring-2 focus:ring-primary-500"
                    />
                  </div>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export default FileUpload;
