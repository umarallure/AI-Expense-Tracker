import React, { useState, useEffect } from 'react';
import { Plus, Edit2, Trash2, Settings, Play, Pause, AlertTriangle, Tag } from 'lucide-react';
import Button from '../components/ui/Button';
import Card from '../components/ui/Card';
import Modal from '../components/ui/Modal';
import Input from '../components/ui/Input';
import Badge from '../components/ui/Badge';
import { ruleService, businessService } from '../services/business.service';
import type { Rule, Business, RuleCreate, RuleUpdate, RuleCondition, RuleAction } from '../types';

const Rules: React.FC = () => {
  const [rules, setRules] = useState<Rule[]>([]);
  const [businesses, setBusinesses] = useState<Business[]>([]);
  const [selectedBusinessId, setSelectedBusinessId] = useState<string>('');
  const [isLoading, setIsLoading] = useState(true);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [editingRule, setEditingRule] = useState<Rule | null>(null);
  const [formData, setFormData] = useState<RuleCreate>({
    business_id: '',
    name: '',
    description: '',
    rule_type: 'auto_categorize',
    conditions: [],
    actions: [],
    priority: 0,
    is_active: true,
  });

  useEffect(() => {
    fetchBusinesses();
  }, []);

  useEffect(() => {
    if (selectedBusinessId) {
      fetchRules(selectedBusinessId);
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

  const fetchRules = async (businessId: string) => {
    try {
      setIsLoading(true);
      const response = await ruleService.getRules(businessId);
      setRules(response);
    } catch (error) {
      console.error('Failed to fetch rules:', error);
      setRules([]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleOpenModal = (rule?: Rule) => {
    if (rule) {
      setEditingRule(rule);
      setFormData({
        business_id: rule.business_id,
        name: rule.name,
        description: rule.description || '',
        rule_type: rule.rule_type,
        conditions: rule.conditions,
        actions: rule.actions,
        priority: rule.priority,
        is_active: rule.is_active,
      });
    } else {
      setEditingRule(null);
      setFormData({
        business_id: selectedBusinessId,
        name: '',
        description: '',
        rule_type: 'auto_categorize',
        conditions: [],
        actions: [],
        priority: 0,
        is_active: true,
      });
    }
    setIsModalOpen(true);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      if (editingRule) {
        await ruleService.updateRule(editingRule.id, formData);
      } else {
        await ruleService.createRule(formData);
      }
      setIsModalOpen(false);
      if (selectedBusinessId) {
        fetchRules(selectedBusinessId);
      }
    } catch (error) {
      console.error('Failed to save rule:', error);
    }
  };

  const handleDelete = async (id: string) => {
    if (window.confirm('Are you sure you want to delete this rule? This action cannot be undone.')) {
      try {
        await ruleService.deleteRule(id);
        if (selectedBusinessId) {
          fetchRules(selectedBusinessId);
        }
      } catch (error) {
        console.error('Failed to delete rule:', error);
      }
    }
  };

  const toggleRuleStatus = async (rule: Rule) => {
    try {
      await ruleService.updateRule(rule.id, { is_active: !rule.is_active });
      if (selectedBusinessId) {
        fetchRules(selectedBusinessId);
      }
    } catch (error) {
      console.error('Failed to toggle rule status:', error);
    }
  };

  const getRuleTypeBadge = (ruleType: string) => {
    const variants: Record<string, { variant: any; label: string; icon: any }> = {
      auto_categorize: { variant: 'primary', label: 'Auto Categorize', icon: Tag },
      auto_tag: { variant: 'secondary', label: 'Auto Tag', icon: Settings },
      approval_required: { variant: 'warning', label: 'Approval Required', icon: AlertTriangle },
      flag_suspicious: { variant: 'danger', label: 'Flag Suspicious', icon: AlertTriangle },
    };
    const config = variants[ruleType] || variants.auto_categorize;
    return { ...config, Icon: config.icon };
  };

  const addCondition = () => {
    setFormData({
      ...formData,
      conditions: [...formData.conditions, { field: '', operator: 'equals', value: '' }]
    });
  };

  const updateCondition = (index: number, condition: RuleCondition) => {
    const newConditions = [...formData.conditions];
    newConditions[index] = condition;
    setFormData({ ...formData, conditions: newConditions });
  };

  const removeCondition = (index: number) => {
    setFormData({
      ...formData,
      conditions: formData.conditions.filter((_, i) => i !== index)
    });
  };

  const addAction = () => {
    setFormData({
      ...formData,
      actions: [...formData.actions, { type: '', value: '' }]
    });
  };

  const updateAction = (index: number, action: RuleAction) => {
    const newActions = [...formData.actions];
    newActions[index] = action;
    setFormData({ ...formData, actions: newActions });
  };

  const removeAction = (index: number) => {
    setFormData({
      ...formData,
      actions: formData.actions.filter((_, i) => i !== index)
    });
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-center">
          <div className="w-16 h-16 border-4 border-primary-500 border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
          <p className="text-gray-600">Loading rules...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Automation Rules</h1>
          <p className="text-gray-500 mt-1">Create rules to automatically process transactions</p>
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
            Add Rule
          </Button>
        </div>
      </div>

      {/* Rules List */}
      {!selectedBusinessId ? (
        <Card>
          <div className="text-center py-12">
            <Settings className="w-16 h-16 text-gray-300 mx-auto mb-4" />
            <h3 className="text-lg font-semibold text-gray-900 mb-2">No business selected</h3>
            <p className="text-gray-500">Please create a business first to manage rules</p>
          </div>
        </Card>
      ) : rules.length === 0 ? (
        <Card>
          <div className="text-center py-12">
            <Settings className="w-16 h-16 text-gray-300 mx-auto mb-4" />
            <h3 className="text-lg font-semibold text-gray-900 mb-2">No rules yet</h3>
            <p className="text-gray-500 mb-6">Get started by creating your first automation rule</p>
            <Button variant="primary" onClick={() => handleOpenModal()}>
              Create Rule
            </Button>
          </div>
        </Card>
      ) : (
        <div className="space-y-4">
          {rules.map((rule) => {
            const typeBadge = getRuleTypeBadge(rule.rule_type);
            return (
              <Card key={rule.id} className="hover:shadow-md transition-shadow">
                <div className="space-y-4">
                  {/* Rule Header */}
                  <div className="flex items-start justify-between">
                    <div className="flex items-center space-x-3">
                      <div className="w-12 h-12 rounded-xl flex items-center justify-center bg-primary-100">
                        <typeBadge.Icon className="w-6 h-6 text-primary-600" />
                      </div>
                      <div>
                        <h3 className="font-semibold text-gray-900">{rule.name}</h3>
                        <div className="flex items-center space-x-2 mt-1">
                          <Badge variant={typeBadge.variant} size="sm">
                            {typeBadge.label}
                          </Badge>
                          <Badge variant={rule.is_active ? "success" : "default"} size="sm">
                            {rule.is_active ? "Active" : "Inactive"}
                          </Badge>
                          <span className="text-sm text-gray-500">Priority: {rule.priority}</span>
                        </div>
                      </div>
                    </div>
                    <div className="flex items-center space-x-2">
                      <Button
                        variant="ghost"
                        size="sm"
                        icon={rule.is_active ? <Pause className="w-4 h-4" /> : <Play className="w-4 h-4" />}
                        onClick={() => toggleRuleStatus(rule)}
                        className={rule.is_active ? "text-orange-600 hover:bg-orange-50" : "text-green-600 hover:bg-green-50"}
                      />
                      <Button
                        variant="ghost"
                        size="sm"
                        icon={<Edit2 className="w-4 h-4" />}
                        onClick={() => handleOpenModal(rule)}
                      />
                      <Button
                        variant="ghost"
                        size="sm"
                        icon={<Trash2 className="w-4 h-4" />}
                        onClick={() => handleDelete(rule.id)}
                        className="text-red-600 hover:bg-red-50"
                      />
                    </div>
                  </div>

                  {/* Description */}
                  {rule.description && (
                    <div className="bg-gray-50 rounded-lg p-4">
                      <p className="text-sm text-gray-600">{rule.description}</p>
                    </div>
                  )}

                  {/* Conditions and Actions */}
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div>
                      <h4 className="text-sm font-medium text-gray-700 mb-2">Conditions ({rule.conditions.length})</h4>
                      <div className="space-y-1">
                        {rule.conditions.slice(0, 2).map((condition, index) => (
                          <div key={index} className="text-xs text-gray-500 bg-gray-50 px-2 py-1 rounded">
                            {condition.field} {condition.operator} {String(condition.value)}
                          </div>
                        ))}
                        {rule.conditions.length > 2 && (
                          <div className="text-xs text-gray-400">
                            +{rule.conditions.length - 2} more conditions
                          </div>
                        )}
                      </div>
                    </div>
                    <div>
                      <h4 className="text-sm font-medium text-gray-700 mb-2">Actions ({rule.actions.length})</h4>
                      <div className="space-y-1">
                        {rule.actions.slice(0, 2).map((action, index) => (
                          <div key={index} className="text-xs text-gray-500 bg-gray-50 px-2 py-1 rounded">
                            {action.type}: {String(action.value)}
                          </div>
                        ))}
                        {rule.actions.length > 2 && (
                          <div className="text-xs text-gray-400">
                            +{rule.actions.length - 2} more actions
                          </div>
                        )}
                      </div>
                    </div>
                  </div>
                </div>
              </Card>
            );
          })}
        </div>
      )}

      {/* Create/Edit Modal */}
      <Modal
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
        title={editingRule ? 'Edit Rule' : 'Create New Rule'}
        size="xl"
      >
        <form onSubmit={handleSubmit} className="space-y-6">
          <div className="grid grid-cols-2 gap-4">
            <Input
              label="Rule Name"
              value={formData.name}
              onChange={(e) => setFormData({ ...formData, name: e.target.value })}
              required
              placeholder="e.g., Auto-categorize office supplies"
            />

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1.5">
                Rule Type <span className="text-red-500">*</span>
              </label>
              <select
                value={formData.rule_type}
                onChange={(e) => setFormData({ ...formData, rule_type: e.target.value as any })}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
                required
              >
                <option value="auto_categorize">Auto Categorize</option>
                <option value="auto_tag">Auto Tag</option>
                <option value="approval_required">Approval Required</option>
                <option value="flag_suspicious">Flag Suspicious</option>
              </select>
            </div>
          </div>

          <Input
            label="Description"
            value={formData.description}
            onChange={(e) => setFormData({ ...formData, description: e.target.value })}
            placeholder="Optional description of what this rule does"
          />

          <div className="grid grid-cols-2 gap-4">
            <Input
              label="Priority"
              type="number"
              min="0"
              max="100"
              value={formData.priority}
              onChange={(e) => setFormData({ ...formData, priority: parseInt(e.target.value) || 0 })}
              placeholder="0-100 (higher = higher priority)"
            />

            <div className="flex items-center space-x-3 pt-8">
              <input
                type="checkbox"
                id="is_active"
                checked={formData.is_active}
                onChange={(e) => setFormData({ ...formData, is_active: e.target.checked })}
                className="rounded border-gray-300"
              />
              <label htmlFor="is_active" className="text-sm text-gray-700">Rule is active</label>
            </div>
          </div>

          {/* Conditions */}
          <div>
            <div className="flex items-center justify-between mb-3">
              <h3 className="text-lg font-medium text-gray-900">Conditions</h3>
              <Button type="button" variant="outline" size="sm" onClick={addCondition}>
                Add Condition
              </Button>
            </div>
            <div className="space-y-3">
              {formData.conditions.map((condition, index) => (
                <div key={index} className="flex items-center space-x-3 p-3 bg-gray-50 rounded-lg">
                  <select
                    value={condition.field}
                    onChange={(e) => updateCondition(index, { ...condition, field: e.target.value })}
                    className="flex-1 px-3 py-2 border border-gray-300 rounded focus:outline-none focus:ring-2 focus:ring-primary-500"
                  >
                    <option value="">Select field</option>
                    <option value="description">Description</option>
                    <option value="amount">Amount</option>
                    <option value="category_id">Category ID</option>
                    <option value="account_id">Account ID</option>
                  </select>
                  <select
                    value={condition.operator}
                    onChange={(e) => updateCondition(index, { ...condition, operator: e.target.value as any })}
                    className="px-3 py-2 border border-gray-300 rounded focus:outline-none focus:ring-2 focus:ring-primary-500"
                  >
                    <option value="equals">Equals</option>
                    <option value="not_equals">Not Equals</option>
                    <option value="contains">Contains</option>
                    <option value="greater_than">Greater Than</option>
                    <option value="less_than">Less Than</option>
                    <option value="starts_with">Starts With</option>
                    <option value="ends_with">Ends With</option>
                  </select>
                  <input
                    type="text"
                    value={condition.value}
                    onChange={(e) => updateCondition(index, { ...condition, value: e.target.value })}
                    placeholder="Value"
                    className="flex-1 px-3 py-2 border border-gray-300 rounded focus:outline-none focus:ring-2 focus:ring-primary-500"
                  />
                  <Button
                    type="button"
                    variant="ghost"
                    size="sm"
                    icon={<Trash2 className="w-4 h-4" />}
                    onClick={() => removeCondition(index)}
                    className="text-red-600 hover:bg-red-50"
                  />
                </div>
              ))}
            </div>
          </div>

          {/* Actions */}
          <div>
            <div className="flex items-center justify-between mb-3">
              <h3 className="text-lg font-medium text-gray-900">Actions</h3>
              <Button type="button" variant="outline" size="sm" onClick={addAction}>
                Add Action
              </Button>
            </div>
            <div className="space-y-3">
              {formData.actions.map((action, index) => (
                <div key={index} className="flex items-center space-x-3 p-3 bg-gray-50 rounded-lg">
                  <select
                    value={action.type}
                    onChange={(e) => updateAction(index, { ...action, type: e.target.value })}
                    className="flex-1 px-3 py-2 border border-gray-300 rounded focus:outline-none focus:ring-2 focus:ring-primary-500"
                  >
                    <option value="">Select action</option>
                    <option value="set_category">Set Category</option>
                    <option value="add_tag">Add Tag</option>
                    <option value="require_approval">Require Approval</option>
                    <option value="flag_suspicious">Flag as Suspicious</option>
                  </select>
                  <input
                    type="text"
                    value={action.value}
                    onChange={(e) => updateAction(index, { ...action, value: e.target.value })}
                    placeholder="Value (category ID, tag name, etc.)"
                    className="flex-1 px-3 py-2 border border-gray-300 rounded focus:outline-none focus:ring-2 focus:ring-primary-500"
                  />
                  <Button
                    type="button"
                    variant="ghost"
                    size="sm"
                    icon={<Trash2 className="w-4 h-4" />}
                    onClick={() => removeAction(index)}
                    className="text-red-600 hover:bg-red-50"
                  />
                </div>
              ))}
            </div>
          </div>

          <div className="flex justify-end space-x-3 pt-4 border-t border-gray-200">
            <Button type="button" variant="ghost" onClick={() => setIsModalOpen(false)}>
              Cancel
            </Button>
            <Button type="submit" variant="primary">
              {editingRule ? 'Update Rule' : 'Create Rule'}
            </Button>
          </div>
        </form>
      </Modal>
    </div>
  );
};

export default Rules;