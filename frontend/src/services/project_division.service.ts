import api from '../lib/api';
import { ProjectDivision, ProjectDivisionCreate, ProjectDivisionUpdate, ProjectDivisionWithStats, ProjectDivisionListResponse } from '../types/index';

export const projectDivisionService = {
  async getDivisions(businessId: string, includeInactive: boolean = false): Promise<ProjectDivisionListResponse> {
    const response = await api.get(`/businesses/${businessId}/divisions/?include_inactive=${includeInactive}`);
    return response.data;
  },

  async getDivision(businessId: string, divisionId: string): Promise<ProjectDivisionWithStats> {
    const response = await api.get(`/businesses/${businessId}/divisions/${divisionId}`);
    return response.data;
  },

  async createDivision(businessId: string, data: Omit<ProjectDivisionCreate, 'business_id'>): Promise<ProjectDivision> {
    const divisionData = { ...data, business_id: businessId };
    const response = await api.post(`/businesses/${businessId}/divisions/`, divisionData);
    return response.data;
  },

  async updateDivision(businessId: string, divisionId: string, data: ProjectDivisionUpdate): Promise<ProjectDivision> {
    const response = await api.patch(`/businesses/${businessId}/divisions/${divisionId}`, data);
    return response.data;
  },

  async deleteDivision(businessId: string, divisionId: string): Promise<void> {
    await api.delete(`/businesses/${businessId}/divisions/${divisionId}`);
  },

  async getDivisionStats(businessId: string, divisionId: string): Promise<any> {
    const response = await api.get(`/businesses/${businessId}/divisions/${divisionId}/stats`);
    return response.data;
  },
};