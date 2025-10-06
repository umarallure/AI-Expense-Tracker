import React, { useState, useEffect } from 'react';
import { Plus, Edit2, Trash2, Building2, Calendar } from 'lucide-react';
import Button from '../components/ui/Button';
import Card from '../components/ui/Card';
import Modal from '../components/ui/Modal';
import Input from '../components/ui/Input';
import Badge from '../components/ui/Badge';
import { businessService } from '../services/business.service';
import type { Business } from '../types';

const Businesses: React.FC = () => {
  const [businesses, setBusinesses] = useState<Business[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [editingBusiness, setEditingBusiness] = useState<Business | null>(null);
  const [formData, setFormData] = useState({
    business_name: '',
    business_type: 'llc',
    currency: 'USD',
    industry: '',
    fiscal_year_start: 1,
    address: '',
    city: '',
    state: '',
    country: 'USA',
    postal_code: '',
    phone: '',
    email: '',
    website: '',
  });

  useEffect(() => {
    fetchBusinesses();
  }, []);

  const fetchBusinesses = async () => {
    try {
      setIsLoading(true);
      const response = await businessService.getBusinesses();
      setBusinesses(response.businesses);
    } catch (error) {
      console.error('Failed to fetch businesses:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const handleOpenModal = (business?: Business) => {
    if (business) {
      setEditingBusiness(business);
      setFormData({
        business_name: business.business_name || business.name,
        business_type: business.business_type || 'llc',
        currency: business.currency || 'USD',
        industry: business.industry || '',
        fiscal_year_start: business.fiscal_year_start || 1,
        address: business.address || '',
        city: business.city || '',
        state: business.state || '',
        country: business.country || 'USA',
        postal_code: business.postal_code || '',
        phone: business.phone || '',
        email: business.email || '',
        website: business.website || '',
      });
    } else {
      setEditingBusiness(null);
      setFormData({
        business_name: '',
        business_type: 'llc',
        currency: 'USD',
        industry: '',
        fiscal_year_start: 1,
        address: '',
        city: '',
        state: '',
        country: 'USA',
        postal_code: '',
        phone: '',
        email: '',
        website: '',
      });
    }
    setIsModalOpen(true);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      if (editingBusiness) {
        await businessService.updateBusiness(editingBusiness.id, formData);
      } else {
        await businessService.createBusiness(formData);
      }
      setIsModalOpen(false);
      fetchBusinesses();
    } catch (error) {
      console.error('Failed to save business:', error);
    }
  };

  const handleDelete = async (id: string) => {
    if (window.confirm('Are you sure you want to delete this business?')) {
      try {
        await businessService.deleteBusiness(id);
        fetchBusinesses();
      } catch (error) {
        console.error('Failed to delete business:', error);
      }
    }
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
    });
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-center">
          <div className="w-16 h-16 border-4 border-primary-500 border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
          <p className="text-gray-600">Loading businesses...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Businesses</h1>
          <p className="text-gray-500 mt-1">Manage your business entities</p>
        </div>
        <Button variant="primary" icon={<Plus className="w-5 h-5" />} onClick={() => handleOpenModal()}>
          Add Business
        </Button>
      </div>

      {/* Businesses Grid */}
      {businesses.length === 0 ? (
        <Card>
          <div className="text-center py-12">
            <Building2 className="w-16 h-16 text-gray-300 mx-auto mb-4" />
            <h3 className="text-lg font-semibold text-gray-900 mb-2">No businesses yet</h3>
            <p className="text-gray-500 mb-6">Get started by creating your first business entity</p>
            <Button variant="primary" onClick={() => handleOpenModal()}>
              Create Business
            </Button>
          </div>
        </Card>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {businesses.map((business) => (
            <Card key={business.id} className="hover:shadow-md transition-shadow">
              <div className="space-y-4">
                {/* Business Header */}
                <div className="flex items-start justify-between">
                  <div className="flex items-center space-x-3">
                    <div className="w-12 h-12 bg-primary-100 rounded-xl flex items-center justify-center">
                      <Building2 className="w-6 h-6 text-primary-600" />
                    </div>
                    <div>
                      <h3 className="font-semibold text-gray-900">{business.business_name || business.name}</h3>
                      <Badge variant="primary" size="sm">
                        {business.business_type?.toUpperCase() || 'LLC'}
                      </Badge>
                    </div>
                  </div>
                  <Badge variant={business.is_active ? 'success' : 'default'} size="sm">
                    {business.is_active ? 'Active' : 'Inactive'}
                  </Badge>
                </div>

                {/* Business Details */}
                <div className="space-y-2 text-sm">
                  {business.industry && (
                    <div className="flex items-center text-gray-600">
                      <span className="font-medium mr-2">Industry:</span>
                      <span>{business.industry}</span>
                    </div>
                  )}
                  {business.city && business.state && (
                    <div className="flex items-center text-gray-600">
                      <span className="font-medium mr-2">Location:</span>
                      <span>{business.city}, {business.state}</span>
                    </div>
                  )}
                  <div className="flex items-center text-gray-600">
                    <Calendar className="w-4 h-4 mr-2" />
                    <span>Created {formatDate(business.created_at)}</span>
                  </div>
                </div>

                {/* Actions */}
                <div className="flex items-center space-x-2 pt-4 border-t border-gray-200">
                  <Button
                    variant="outline"
                    size="sm"
                    icon={<Edit2 className="w-4 h-4" />}
                    onClick={() => handleOpenModal(business)}
                    className="flex-1"
                  >
                    Edit
                  </Button>
                  <Button
                    variant="ghost"
                    size="sm"
                    icon={<Trash2 className="w-4 h-4" />}
                    onClick={() => handleDelete(business.id)}
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
        title={editingBusiness ? 'Edit Business' : 'Create New Business'}
        size="lg"
      >
        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <Input
              label="Business Name"
              value={formData.business_name}
              onChange={(e) => setFormData({ ...formData, business_name: e.target.value })}
              required
              placeholder="Enter business name"
            />
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1.5">
                Business Type <span className="text-red-500">*</span>
              </label>
              <select
                value={formData.business_type}
                onChange={(e) => setFormData({ ...formData, business_type: e.target.value })}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
                required
              >
                <option value="sole_proprietor">Sole Proprietor</option>
                <option value="llc">LLC</option>
                <option value="corporation">Corporation</option>
                <option value="partnership">Partnership</option>
                <option value="non_profit">Non-Profit</option>
              </select>
            </div>
          </div>

          <div className="grid grid-cols-2 gap-4">
            <Input
              label="Industry"
              value={formData.industry}
              onChange={(e) => setFormData({ ...formData, industry: e.target.value })}
              placeholder="e.g., Technology, Retail"
            />
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1.5">Currency</label>
              <select
                value={formData.currency}
                onChange={(e) => setFormData({ ...formData, currency: e.target.value })}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
              >
                <option value="USD">USD</option>
                <option value="EUR">EUR</option>
                <option value="GBP">GBP</option>
                <option value="CAD">CAD</option>
              </select>
            </div>
          </div>

          <Input
            label="Address"
            value={formData.address}
            onChange={(e) => setFormData({ ...formData, address: e.target.value })}
            placeholder="Street address"
          />

          <div className="grid grid-cols-3 gap-4">
            <Input
              label="City"
              value={formData.city}
              onChange={(e) => setFormData({ ...formData, city: e.target.value })}
              placeholder="City"
            />
            <Input
              label="State"
              value={formData.state}
              onChange={(e) => setFormData({ ...formData, state: e.target.value })}
              placeholder="State"
            />
            <Input
              label="Postal Code"
              value={formData.postal_code}
              onChange={(e) => setFormData({ ...formData, postal_code: e.target.value })}
              placeholder="Postal code"
            />
          </div>

          <div className="grid grid-cols-2 gap-4">
            <Input
              label="Phone"
              value={formData.phone}
              onChange={(e) => setFormData({ ...formData, phone: e.target.value })}
              placeholder="+1 (555) 123-4567"
            />
            <Input
              label="Email"
              type="email"
              value={formData.email}
              onChange={(e) => setFormData({ ...formData, email: e.target.value })}
              placeholder="business@example.com"
            />
          </div>

          <Input
            label="Website"
            value={formData.website}
            onChange={(e) => setFormData({ ...formData, website: e.target.value })}
            placeholder="https://www.example.com"
          />

          <div className="flex justify-end space-x-3 pt-4 border-t border-gray-200">
            <Button type="button" variant="ghost" onClick={() => setIsModalOpen(false)}>
              Cancel
            </Button>
            <Button type="submit" variant="primary">
              {editingBusiness ? 'Update Business' : 'Create Business'}
            </Button>
          </div>
        </form>
      </Modal>
    </div>
  );
};

export default Businesses;
