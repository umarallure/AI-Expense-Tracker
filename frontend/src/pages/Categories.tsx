import React, { useState, useEffect } from 'react';
import { Plus, Edit2, Trash2, Tag, Building2 } from 'lucide-react';
import Button from '../components/ui/Button';
import Card from '../components/ui/Card';
import Modal from '../components/ui/Modal';
import Input from '../components/ui/Input';
import Badge from '../components/ui/Badge';
import { categoryService, businessService } from '../services/business.service';
import type { Category, Business, CategoryCreate } from '../types';

const Categories: React.FC = () => {
  const [categories, setCategories] = useState<Category[]>([]);
  const [businesses, setBusinesses] = useState<Business[]>([]);
  const [selectedBusinessId, setSelectedBusinessId] = useState<string>('');
  const [isLoading, setIsLoading] = useState(true);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [editingCategory, setEditingCategory] = useState<Category | null>(null);
  const [formData, setFormData] = useState<CategoryCreate>({
    business_id: '',
    category_name: '',
    category_type: 'expense',
    description: '',
    parent_category_id: undefined,
    color: '#14B8A6',
    icon: 'tag',
  });

  useEffect(() => {
    fetchBusinesses();
  }, []);

  useEffect(() => {
    if (selectedBusinessId) {
      fetchCategories(selectedBusinessId);
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

  const fetchCategories = async (businessId: string) => {
    try {
      setIsLoading(true);
      const response = await categoryService.getCategories(businessId);
      setCategories(response.categories);
    } catch (error) {
      console.error('Failed to fetch categories:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const handleOpenModal = (category?: Category) => {
    if (category) {
      setEditingCategory(category);
      setFormData({
        business_id: category.business_id,
        category_name: category.category_name,
        category_type: (category.category_type as 'income' | 'expense') || (category.is_income ? 'income' : 'expense'),
        description: category.description || '',
        parent_category_id: category.parent_id,
        color: category.color || '#14B8A6',
        icon: category.icon || 'tag',
        is_income: category.is_income,
      });
    } else {
      setEditingCategory(null);
      setFormData({
        business_id: selectedBusinessId,
        category_name: '',
        category_type: 'expense',
        description: '',
        parent_category_id: undefined,
        color: '#14B8A6',
        icon: 'tag',
        is_income: false,
      });
    }
    setIsModalOpen(true);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      const categoryData = {
        ...formData,
        is_income: formData.category_type === 'income',
      };
      if (editingCategory) {
        await categoryService.updateCategory(editingCategory.id, categoryData);
      } else {
        // Ensure business_id is always set
        const finalData = {
          ...categoryData,
          business_id: formData.business_id || selectedBusinessId,
        };
        await categoryService.createCategory(finalData);
      }
      setIsModalOpen(false);
      if (selectedBusinessId) {
        fetchCategories(selectedBusinessId);
      }
    } catch (error) {
      console.error('Failed to save category:', error);
    }
  };

  const handleDelete = async (id: string) => {
    if (window.confirm('Are you sure you want to delete this category?')) {
      try {
        await categoryService.updateCategory(id, { business_id: selectedBusinessId, is_active: false });
        if (selectedBusinessId) {
          fetchCategories(selectedBusinessId);
        }
      } catch (error) {
        console.error('Failed to delete category:', error);
      }
    }
  };

  const getParentCategories = () => {
    return categories.filter(c => !c.parent_id);
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-center">
          <div className="w-16 h-16 border-4 border-primary-500 border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
          <p className="text-gray-600">Loading categories...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Categories</h1>
          <p className="text-gray-500 mt-1">Manage expense categories</p>
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
          <Button
            variant="primary"
            icon={<Plus className="w-5 h-5" />}
            onClick={() => handleOpenModal()}
            disabled={!selectedBusinessId}
          >
            Add Category
          </Button>
        </div>
      </div>

      {/* Categories Grid */}
      {!selectedBusinessId ? (
        <Card>
          <div className="text-center py-12">
            <Building2 className="w-16 h-16 text-gray-300 mx-auto mb-4" />
            <h3 className="text-lg font-semibold text-gray-900 mb-2">No business selected</h3>
            <p className="text-gray-500">Please create a business first to manage categories</p>
          </div>
        </Card>
      ) : categories.length === 0 ? (
        <Card>
          <div className="text-center py-12">
            <Tag className="w-16 h-16 text-gray-300 mx-auto mb-4" />
            <h3 className="text-lg font-semibold text-gray-900 mb-2">No categories yet</h3>
            <p className="text-gray-500 mb-6">Get started by adding your first expense category</p>
            <Button variant="primary" onClick={() => handleOpenModal()}>
              Create Category
            </Button>
          </div>
        </Card>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {categories.map((category) => (
            <Card key={category.id} className="hover:shadow-md transition-shadow">
              <div className="space-y-4">
                {/* Category Header */}
                <div className="flex items-start justify-between">
                  <div className="flex items-center space-x-3">
                    <div
                      className="w-12 h-12 rounded-xl flex items-center justify-center"
                      style={{ backgroundColor: `${category.color}20` }}
                    >
                      <Tag className="w-6 h-6" style={{ color: category.color }} />
                    </div>
                    <div>
                      <h3 className="font-semibold text-gray-900">{category.category_name}</h3>
                      <div className="flex items-center space-x-2">
                        <Badge variant={category.parent_id ? "default" : "primary"} size="sm">
                          {category.parent_id ? "Subcategory" : "Category"}
                        </Badge>
                        <Badge variant={category.is_income ? "success" : "secondary"} size="sm">
                          {category.is_income ? "Income" : "Expense"}
                        </Badge>
                      </div>
                    </div>
                  </div>
                  <Badge variant={category.is_active ? 'success' : 'default'} size="sm">
                    {category.is_active ? 'Active' : 'Inactive'}
                  </Badge>
                </div>

                {/* Description */}
                {category.description && (
                  <div className="bg-gray-50 rounded-lg p-4">
                    <p className="text-sm text-gray-600 line-clamp-3">
                      {category.description.length > 100
                        ? `${category.description.substring(0, 100)}...`
                        : category.description
                      }
                    </p>
                  </div>
                )}

                {/* Parent Category Info */}
                {category.parent_id && (
                  <div className="text-sm text-gray-500">
                    <span className="font-medium">Parent:</span>{' '}
                    {categories.find(c => c.id === category.parent_id)?.category_name || 'Unknown'}
                  </div>
                )}

                {/* Actions */}
                <div className="flex items-center space-x-2 pt-4 border-t border-gray-200">
                  <Button
                    variant="outline"
                    size="sm"
                    icon={<Edit2 className="w-4 h-4" />}
                    onClick={() => handleOpenModal(category)}
                    className="flex-1"
                  >
                    Edit
                  </Button>
                  <Button
                    variant="ghost"
                    size="sm"
                    icon={<Trash2 className="w-4 h-4" />}
                    onClick={() => handleDelete(category.id)}
                    className="text-red-600 hover:bg-red-50"
                  >
                    Delete
                  </Button>
                </div>
              </div>
            </Card>
          ))}
        </div>
      )}

      {/* Create/Edit Modal */}
      <Modal
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
        title={editingCategory ? 'Edit Category' : 'Create New Category'}
        size="md"
      >
        <form onSubmit={handleSubmit} className="space-y-4">
          <Input
            label="Category Name"
            value={formData.category_name}
            onChange={(e) => setFormData({ ...formData, category_name: e.target.value })}
            required
            placeholder="e.g., Office Supplies"
          />

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1.5">
              Category Type <span className="text-red-500">*</span>
            </label>
            <select
              value={formData.category_type}
              onChange={(e) => setFormData({ ...formData, category_type: e.target.value as 'income' | 'expense' })}
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
              required
            >
              <option value="expense">Expense</option>
              <option value="income">Income</option>
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1.5">Description</label>
            <textarea
              value={formData.description}
              onChange={(e) => setFormData({ ...formData, description: e.target.value })}
              rows={3}
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
              placeholder="Optional description"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1.5">
              Parent Category (Optional)
            </label>
            <select
              value={formData.parent_category_id || ''}
              onChange={(e) =>
                setFormData({
                  ...formData,
                  parent_category_id: e.target.value || undefined,
                })
              }
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
            >
              <option value="">None (Top Level)</option>
              {getParentCategories()
                .filter(c => c.id !== editingCategory?.id)
                .map((category) => (
                  <option key={category.id} value={category.id}>
                    {category.category_name}
                  </option>
                ))}
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1.5">Color</label>
            <div className="flex items-center space-x-3">
              <input
                type="color"
                value={formData.color}
                onChange={(e) => setFormData({ ...formData, color: e.target.value })}
                className="w-12 h-10 rounded border border-gray-300 cursor-pointer"
              />
              <Input
                value={formData.color}
                onChange={(e) => setFormData({ ...formData, color: e.target.value })}
                placeholder="#14B8A6"
                className="flex-1"
              />
            </div>
          </div>

          <div className="flex justify-end space-x-3 pt-4 border-t border-gray-200">
            <Button type="button" variant="ghost" onClick={() => setIsModalOpen(false)}>
              Cancel
            </Button>
            <Button type="submit" variant="primary">
              {editingCategory ? 'Update Category' : 'Create Category'}
            </Button>
          </div>
        </form>
      </Modal>
    </div>
  );
};

export default Categories;
