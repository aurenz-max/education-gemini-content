// lib/api.ts - Extended with Review Workflow Methods
import { ContentPackage, GenerationRequest, PackageFilters, HealthStatus } from './types';

export interface ReviewStatusUpdate {
  status: 'approved' | 'rejected' | 'needs_revision' | 'under_review';
  reviewer_id: string;
  notes: string;
}

export interface ReviewInfo {
  package_id: string;
  current_status: string;
  review_status: string;
  reviewed_by?: string;
  reviewed_at?: string;
  review_notes: Array<{
    note: string;
    status: string;
    timestamp: string;
    reviewer_id: string;
  }>;
  created_at: string;
  updated_at: string;
  subject: string;
  unit: string;
  skill: string;
  subskill: string;
}

export class ContentAPI {
  private baseUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

  // Content Generation
  async generateContent(request: GenerationRequest): Promise<ContentPackage> {
    const response = await fetch(`${this.baseUrl}/api/v1/generate-content`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(request)
    });
    
    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: 'Generation failed' }));
      throw new Error(error.detail || 'Failed to generate content');
    }
    
    return response.json();
  }

  // Content Management
  async getContentPackage(packageId: string, subject: string, unit: string): Promise<ContentPackage> {
    const params = new URLSearchParams({ subject, unit });
    const response = await fetch(
      `${this.baseUrl}/api/v1/content/${packageId}?${params}`
    );
    
    if (!response.ok) {
      if (response.status === 404) {
        throw new Error('Content package not found');
      }
      throw new Error('Failed to retrieve content package');
    }
    
    return response.json();
  }

  async listContentPackages(filters?: PackageFilters): Promise<ContentPackage[]> {
    const params = new URLSearchParams();
    if (filters?.subject) params.append('subject', filters.subject);
    if (filters?.unit) params.append('unit', filters.unit);
    if (filters?.status) params.append('status', filters.status);
    if (filters?.limit) params.append('limit', filters.limit.toString());
    
    const response = await fetch(`${this.baseUrl}/api/v1/content?${params}`);
    
    if (!response.ok) {
      throw new Error('Failed to list content packages');
    }
    
    return response.json();
  }

  async deleteContentPackage(packageId: string, subject: string, unit: string): Promise<boolean> {
    const params = new URLSearchParams({ subject, unit });
    const response = await fetch(
      `${this.baseUrl}/api/v1/content/${packageId}?${params}`,
      { method: 'DELETE' }
    );
    
    return response.ok;
  }

  // ==================== NEW REVIEW WORKFLOW METHODS ====================

  // Get packages awaiting review
  async getReviewQueue(filters?: {
    subject?: string;
    unit?: string;
    limit?: number;
  }): Promise<ContentPackage[]> {
    const params = new URLSearchParams();
    if (filters?.subject) params.append('subject', filters.subject);
    if (filters?.unit) params.append('unit', filters.unit);
    if (filters?.limit) params.append('limit', filters.limit.toString());
    
    const response = await fetch(
      `${this.baseUrl}/api/v1/packages/review-queue?${params}`
    );
    
    if (!response.ok) {
      throw new Error('Failed to get packages for review');
    }
    
    return response.json();
  }

  // Update package status (approve, reject, etc.)
  async updatePackageStatus(
    packageId: string,
    subject: string,
    unit: string,
    statusUpdate: ReviewStatusUpdate
  ): Promise<{
    message: string;
    package_id: string;
    old_status: string;
    new_status: string;
    updated_at: string;
    package: ContentPackage;
  }> {
    const params = new URLSearchParams({ subject, unit });
    const response = await fetch(
      `${this.baseUrl}/api/v1/packages/${packageId}/status?${params}`,
      {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(statusUpdate)
      }
    );
    
    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: 'Status update failed' }));
      throw new Error(error.detail || 'Failed to update package status');
    }
    
    return response.json();
  }

  // Get package review information
  async getPackageReviewInfo(packageId: string, subject: string, unit: string): Promise<ReviewInfo> {
    const params = new URLSearchParams({ subject, unit });
    const response = await fetch(
      `${this.baseUrl}/api/v1/packages/${packageId}/review-info?${params}`
    );
    
    if (!response.ok) {
      if (response.status === 404) {
        throw new Error('Package not found');
      }
      throw new Error('Failed to get package review info');
    }
    
    return response.json();
  }

  // Convenience methods for specific actions
  async approvePackage(packageId: string, subject: string, unit: string, reviewerId: string, notes?: string) {
    return this.updatePackageStatus(packageId, subject, unit, {
      status: 'approved',
      reviewer_id: reviewerId,
      notes: notes || 'Package approved for publication'
    });
  }

  async rejectPackage(packageId: string, subject: string, unit: string, reviewerId: string, notes: string) {
    return this.updatePackageStatus(packageId, subject, unit, {
      status: 'rejected',
      reviewer_id: reviewerId,
      notes
    });
  }

  async requestChanges(packageId: string, subject: string, unit: string, reviewerId: string, notes: string) {
    return this.updatePackageStatus(packageId, subject, unit, {
      status: 'needs_revision',
      reviewer_id: reviewerId,
      notes
    });
  }

  // Subject-specific packages
  async getPackagesBySubject(subject: string, unit?: string): Promise<{
    subject: string;
    unit?: string;
    total_packages: number;
    packages: ContentPackage[];
  }> {
    const params = new URLSearchParams();
    if (unit) params.append('unit', unit);
    
    const response = await fetch(
      `${this.baseUrl}/api/v1/packages/${subject}?${params}`
    );
    
    if (!response.ok) {
      throw new Error(`Failed to get packages for ${subject}`);
    }
    
    return response.json();
  }

  // Audio file URL
  async getAudioFileUrl(packageId: string, filename: string): Promise<string> {
    const response = await fetch(
      `${this.baseUrl}/api/v1/audio/${packageId}/${filename}`,
      { redirect: 'manual' }
    );
    
    if (response.status === 302) {
      return response.headers.get('location') || '';
    }
    
    throw new Error('Audio file not found');
  }

  // Health Check
  async healthCheck(): Promise<HealthStatus> {
    const response = await fetch(`${this.baseUrl}/api/v1/health`);
    return response.json();
  }

  // Storage Statistics
  async getStorageStats(): Promise<{
    blob_storage: any;
    cosmos_db: {
      total_packages: number;
      database: string;
      container: string;
    };
  }> {
    const response = await fetch(`${this.baseUrl}/api/v1/storage/stats`);
    
    if (!response.ok) {
      throw new Error('Failed to get storage statistics');
    }
    
    return response.json();
  }
}

export const contentAPI = new ContentAPI();