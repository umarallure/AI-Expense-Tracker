import React, { useState, useEffect } from 'react';
import { Plus, Edit2, Trash2, FolderOpen, Building2, BarChart3 } from 'lucide-react';
import Button from '../components/ui/Button';
import Card from '../components/ui/Card';
import Modal from '../components/ui/Modal';
import Input from '../components/ui/Input';
import Badge from '../components/ui/Badge';
import { projectDivisionService } from '../services/project_division.service';
import { businessService } from '../services/business.service';
import type { ProjectDivision, ProjectDivisionCreate, Business } from '../types';

const ProjectDivisions: React.FC = () => {
  const [divisions, setDivisions] = useState<ProjectDivision[]>([]);
  const [businesses, setBusinesses] = useState<Business[]>([]);
  const [selectedBusinessId, setSelectedBusinessId] = useState<string>('');
  const [isLoading, setIsLoading] = useState(true);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [editingDivision, setEditingDivision] = useState<ProjectDivision | null>(null);
  const [formData, setFormData] = useState<ProjectDivisionCreate>({
    business_id: '',
    name: '',
    description: '',
    color: '#3B82F6',
    is_active: true,
  });

  useEffect(() => {
    fetchBusinesses();
  }, []);

  useEffect(() => {
    if (selectedBusinessId) {
      fetchDivisions(selectedBusinessId);
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

  const fetchDivisions = async (businessId: string) => {
    try {
      setIsLoading(true);
      const response = await projectDivisionService.getDivisions(businessId);
      setDivisions(response.divisions);
    } catch (error) {
      console.error('Failed to fetch divisions:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const handleCreateDivision = async () => {
    try {
      await projectDivisionService.createDivision(selectedBusinessId, {
        name: formData.name,
        description: formData.description,
        color: formData.color,
        is_active: formData.is_active,
      });
      setIsModalOpen(false);
      resetForm();
      fetchDivisions(selectedBusinessId);
    } catch (error) {
      console.error('Failed to create division:', error);
    }
  };

  const handleUpdateDivision = async () => {
    if (!editingDivision) return;

    try {
      await projectDivisionService.updateDivision(
        selectedBusinessId,
        editingDivision.id,
        {
          name: formData.name,
          description: formData.description,
          color: formData.color,
          is_active: formData.is_active,
        }
      );
      setIsModalOpen(false);
      setEditingDivision(null);
      resetForm();
      fetchDivisions(selectedBusinessId);
    } catch (error) {
      console.error('Failed to update division:', error);
    }
  };

  const handleDeleteDivision = async (divisionId: string) => {
    if (!confirm('Are you sure you want to delete this division? This action cannot be undone.')) {
      return;
    }

    try {
      await projectDivisionService.deleteDivision(selectedBusinessId, divisionId);
      fetchDivisions(selectedBusinessId);
    } catch (error) {
      console.error('Failed to delete division:', error);
    }
  };

  const openCreateModal = () => {
    resetForm();
    setFormData(prev => ({ ...prev, business_id: selectedBusinessId }));
    setIsModalOpen(true);
  };

  const openEditModal = (division: ProjectDivision) => {
    setEditingDivision(division);
    setFormData({
      business_id: division.business_id,
      name: division.name,
      description: division.description || '',
      color: division.color || '#3B82F6',
      is_active: division.is_active,
    });
    setIsModalOpen(true);
  };

  const resetForm = () => {
    setFormData({
      business_id: '',
      name: '',
      description: '',
      color: '#3B82F6',
      is_active: true,
    });
    setEditingDivision(null);
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (editingDivision) {
      handleUpdateDivision();
    } else {
      handleCreateDivision();
    }
  };

  if (isLoading && businesses.length === 0) {
    return (
      <div className="flex items-center justify-center min-h-96">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Project Divisions</h1>
          <p className="text-gray-600">Organize your business into sections for better transaction and document management</p>
        </div>
        <Button
          onClick={openCreateModal}
          disabled={!selectedBusinessId}
          className="flex items-center gap-2"
        >
          <Plus className="h-4 w-4" />
          Add Division
        </Button>
      </div>

      {/* Business Selector */}
      <Card className="p-4">
        <div className="flex items-center gap-4">
          <Building2 className="h-5 w-5 text-gray-400" />
          <div className="flex-1">
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Select Business
            </label>
            <select
              value={selectedBusinessId}
              onChange={(e) => setSelectedBusinessId(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="">Select a business...</option>
              {businesses.map((business) => (
                <option key={business.id} value={business.id}>
                  {business.business_name || business.name}
                </option>
              ))}
            </select>
          </div>
        </div>
      </Card>

      {/* Divisions Grid */}
      {selectedBusinessId && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {divisions.map((division) => (
            <Card key={division.id} className="p-6 hover:shadow-md transition-shadow">
              <div className="flex items-start justify-between mb-4">
                <div className="flex items-center gap-3">
                  <div
                    className="w-10 h-10 rounded-lg flex items-center justify-center"
                    style={{ backgroundColor: division.color || '#3B82F6' }}
                  >
                    <FolderOpen className="h-5 w-5 text-white" />
                  </div>
                  <div>
                    <h3 className="font-semibold text-gray-900">{division.name}</h3>
                    <Badge variant={division.is_active ? 'success' : 'secondary'}>
                      {division.is_active ? 'Active' : 'Inactive'}
                    </Badge>
                  </div>
                </div>
                <div className="flex items-center gap-1">
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => openEditModal(division)}
                    className="h-8 w-8 p-0"
                  >
                    <Edit2 className="h-4 w-4" />
                  </Button>
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => handleDeleteDivision(division.id)}
                    className="h-8 w-8 p-0 text-red-600 hover:text-red-700"
                  >
                    <Trash2 className="h-4 w-4" />
                  </Button>
                </div>
              </div>

              {division.description && (
                <p className="text-gray-600 text-sm mb-4">{division.description}</p>
              )}

              <div className="flex items-center justify-between text-sm text-gray-500">
                <span>Created {new Date(division.created_at).toLocaleDateString()}</span>
                <Button variant="ghost" size="sm" className="flex items-center gap-1">
                  <BarChart3 className="h-4 w-4" />
                  View Stats
                </Button>
              </div>
            </Card>
          ))}

          {divisions.length === 0 && !isLoading && (
            <div className="col-span-full text-center py-12">
              <FolderOpen className="h-12 w-12 text-gray-400 mx-auto mb-4" />
              <h3 className="text-lg font-medium text-gray-900 mb-2">No divisions yet</h3>
              <p className="text-gray-600 mb-4">Create your first project division to organize your business sections.</p>
              <Button onClick={openCreateModal} className="flex items-center gap-2 mx-auto">
                <Plus className="h-4 w-4" />
                Add Division
              </Button>
            </div>
          )}
        </div>
      )}

      {/* Create/Edit Modal */}
      <Modal
        isOpen={isModalOpen}
        onClose={() => {
          setIsModalOpen(false);
          resetForm();
        }}
        title={editingDivision ? 'Edit Division' : 'Create Division'}
      >
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Division Name *
            </label>
            <Input
              type="text"
              value={formData.name}
              onChange={(e) => setFormData(prev => ({ ...prev, name: e.target.value }))}
              placeholder="Enter division name"
              required
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Description
            </label>
            <textarea
              value={formData.description}
              onChange={(e) => setFormData(prev => ({ ...prev, description: e.target.value }))}
              placeholder="Enter division description"
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              rows={3}
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Color
            </label>
            <div className="flex items-center gap-2">
              <input
                type="color"
                value={formData.color}
                onChange={(e) => setFormData(prev => ({ ...prev, color: e.target.value }))}
                className="w-10 h-10 border border-gray-300 rounded cursor-pointer"
              />
              <Input
                type="text"
                value={formData.color}
                onChange={(e) => setFormData(prev => ({ ...prev, color: e.target.value }))}
                placeholder="#3B82F6"
                className="flex-1"
              />
            </div>
          </div>

          <div className="flex items-center gap-2">
            <input
              type="checkbox"
              id="is_active"
              checked={formData.is_active}
              onChange={(e) => setFormData(prev => ({ ...prev, is_active: e.target.checked }))}
              className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
            />
            <label htmlFor="is_active" className="text-sm text-gray-700">
              Active division
            </label>
          </div>

          <div className="flex justify-end gap-3 pt-4">
            <Button
              type="button"
              variant="secondary"
              onClick={() => {
                setIsModalOpen(false);
                resetForm();
              }}
            >
              Cancel
            </Button>
            <Button type="submit">
              {editingDivision ? 'Update Division' : 'Create Division'}
            </Button>
          </div>
        </form>
      </Modal>
    </div>
  );
};

export default ProjectDivisions;