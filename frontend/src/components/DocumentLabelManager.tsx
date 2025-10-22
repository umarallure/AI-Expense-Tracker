import React, { useState, useEffect } from 'react';
import { X, Plus, Tag, Check } from 'lucide-react';
import Button from '../components/ui/Button';
import Badge from '../components/ui/Badge';

interface DocumentLabelManagerProps {
  currentLabels: string[];
  onLabelsChange: (labels: string[]) => void;
  predefinedLabels?: string[];
  className?: string;
}

const DocumentLabelManager: React.FC<DocumentLabelManagerProps> = ({
  currentLabels = [],
  onLabelsChange,
  predefinedLabels = [],
  className = ''
}) => {
  const [isEditing, setIsEditing] = useState(false);
  const [newLabel, setNewLabel] = useState('');
  const [selectedLabels, setSelectedLabels] = useState<string[]>(currentLabels);

  // Common predefined labels
  const defaultPredefinedLabels = [
    'Q1 Fuel', 'Q2 Fuel', 'Q3 Fuel', 'Q4 Fuel',
    'Travel Receipts', 'Office Supplies', 'Rental Agreements',
    'Insurance', 'Taxes', 'Utilities', 'Marketing',
    'Equipment', 'Software', 'Training', 'Meals',
    'Client Expenses', 'Personal', 'Business'
  ];

  const allPredefinedLabels = [...new Set([...defaultPredefinedLabels, ...predefinedLabels])];

  useEffect(() => {
    setSelectedLabels(currentLabels);
  }, [currentLabels]);

  const handleAddLabel = (label: string) => {
    if (label.trim() && !selectedLabels.includes(label.trim())) {
      const updatedLabels = [...selectedLabels, label.trim()];
      setSelectedLabels(updatedLabels);
      onLabelsChange(updatedLabels);
    }
    setNewLabel('');
  };

  const handleRemoveLabel = (labelToRemove: string) => {
    const updatedLabels = selectedLabels.filter(label => label !== labelToRemove);
    setSelectedLabels(updatedLabels);
    onLabelsChange(updatedLabels);
  };

  const handleSave = () => {
    onLabelsChange(selectedLabels);
    setIsEditing(false);
  };

  const handleCancel = () => {
    setSelectedLabels(currentLabels);
    setIsEditing(false);
    setNewLabel('');
  };

  const getLabelColor = (label: string) => {
    // Generate consistent colors based on label text
    const colors = [
      'bg-blue-100 text-blue-800',
      'bg-green-100 text-green-800',
      'bg-yellow-100 text-yellow-800',
      'bg-red-100 text-red-800',
      'bg-purple-100 text-purple-800',
      'bg-pink-100 text-pink-800',
      'bg-indigo-100 text-indigo-800',
      'bg-gray-100 text-gray-800'
    ];
    const index = label.split('').reduce((acc, char) => acc + char.charCodeAt(0), 0) % colors.length;
    return colors[index];
  };

  if (!isEditing) {
    return (
      <div className={`flex items-center space-x-2 ${className}`}>
        <div className="flex flex-wrap gap-1">
          {selectedLabels.length > 0 ? (
            selectedLabels.slice(0, 3).map((label) => (
              <Badge
                key={label}
                variant="default"
                className={`${getLabelColor(label)} text-xs`}
              >
                {label}
              </Badge>
            ))
          ) : (
            <span className="text-gray-400 text-sm">No labels</span>
          )}
          {selectedLabels.length > 3 && (
            <Badge variant="default" className="text-xs">
              +{selectedLabels.length - 3} more
            </Badge>
          )}
        </div>
        <Button
          variant="ghost"
          size="sm"
          icon={<Tag className="w-4 h-4" />}
          onClick={() => setIsEditing(true)}
          className="text-gray-500 hover:text-gray-700"
        >
          Edit
        </Button>
      </div>
    );
  }

  return (
    <div className={`border border-gray-200 rounded-lg p-4 bg-white ${className}`}>
      <div className="flex items-center justify-between mb-3">
        <h4 className="text-sm font-medium text-gray-900">Manage Labels</h4>
        <div className="flex space-x-2">
          <Button
            variant="ghost"
            size="sm"
            onClick={handleCancel}
            className="text-gray-500"
          >
            Cancel
          </Button>
          <Button
            variant="primary"
            size="sm"
            onClick={handleSave}
            icon={<Check className="w-4 h-4" />}
          >
            Save
          </Button>
        </div>
      </div>

      {/* Current Labels */}
      {selectedLabels.length > 0 && (
        <div className="mb-4">
          <h5 className="text-xs font-medium text-gray-700 mb-2">Current Labels</h5>
          <div className="flex flex-wrap gap-2">
            {selectedLabels.map((label) => (
              <Badge
                key={label}
                variant="default"
                className={`${getLabelColor(label)} flex items-center space-x-1`}
              >
                <span>{label}</span>
                <button
                  onClick={() => handleRemoveLabel(label)}
                  className="ml-1 hover:bg-black hover:bg-opacity-20 rounded-full p-0.5"
                >
                  <X className="w-3 h-3" />
                </button>
              </Badge>
            ))}
          </div>
        </div>
      )}

      {/* Add New Label */}
      <div className="mb-4">
        <h5 className="text-xs font-medium text-gray-700 mb-2">Add New Label</h5>
        <div className="flex space-x-2">
          <input
            type="text"
            value={newLabel}
            onChange={(e) => setNewLabel(e.target.value)}
            onKeyPress={(e) => e.key === 'Enter' && handleAddLabel(newLabel)}
            placeholder="Enter label name..."
            className="flex-1 px-3 py-2 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent"
          />
          <Button
            variant="outline"
            size="sm"
            onClick={() => handleAddLabel(newLabel)}
            disabled={!newLabel.trim()}
            icon={<Plus className="w-4 h-4" />}
          >
            Add
          </Button>
        </div>
      </div>

      {/* Predefined Labels */}
      <div>
        <h5 className="text-xs font-medium text-gray-700 mb-2">Quick Add</h5>
        <div className="flex flex-wrap gap-2">
          {allPredefinedLabels
            .filter(label => !selectedLabels.includes(label))
            .slice(0, 12)
            .map((label) => (
            <button
              key={label}
              onClick={() => handleAddLabel(label)}
              className="px-3 py-1 text-xs bg-gray-100 text-gray-700 rounded-full hover:bg-gray-200 transition-colors"
            >
              + {label}
            </button>
          ))}
        </div>
      </div>
    </div>
  );
};

export default DocumentLabelManager;