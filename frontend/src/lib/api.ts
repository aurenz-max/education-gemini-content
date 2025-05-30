// lib/api.ts - Complete API with Curriculum Endpoints and Grade Support
import { ContentPackage, GenerationRequest, PackageFilters, HealthStatus, ComponentType } from './types';

export interface ReviewStatusUpdate {
  status: 'approved' | 'rejected' | 'needs_revision' | 'under_review';
  reviewer_id: string;
  notes: string;
}

export interface ComponentRevision {
  component_type: ComponentType;
  feedback: string;
  priority?: 'low' | 'medium' | 'high';
}

export interface RevisionRequest {
  package_id: string;
  subject: string;
  unit: string;
  revisions: ComponentRevision[];
  reviewer_id?: string;
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

export interface RevisionHistory {
  revision_id: string;
  timestamp: string;
  components_revised: ComponentType[];
  feedback_summary: string;
  status: 'in_progress' | 'completed' | 'failed';
  revised_by: string;
}

// ==================== CURRICULUM TYPES ====================

export interface Subskill {
  subskill_id: string;
  subskill_description: string;
  difficulty_start: number;
  difficulty_end: number;
  target_difficulty: number;
}

export interface Skill {
  skill_id: string;
  skill_description: string;
  subskills: Subskill[];
}

export interface Unit {
  unit_id: string;
  unit_title: string;
  skills: Skill[];
}

export interface CurriculumRecord {
  subject: string;
  grade: string;
  units: Unit[];
}

export interface CurriculumContext {
  subject: string;
  grade: string;
  unit: string;
  skill: string;
  subskill: string;
  subskill_id: string;
  difficulty_level: string;
  target_difficulty: number;
  difficulty_range: {
    start: number;
    end: number;
  };
  prerequisites: string[];
  next_subskill: string | null;
  learning_path: string[];
}

export interface CurriculumReferenceRequest {
  subskill_id: string;
  difficulty_level_override?: string;
  prerequisites_override?: string[];
}

export interface ManualContentRequest {
  subject: string;
  grade?: string;
  unit: string;
  skill: string;
  subskill: string;
  difficulty_level: string;
  prerequisites: string[];
}

export interface EnhancedContentGenerationRequest {
  mode: 'curriculum' | 'manual';
  curriculum_request?: CurriculumReferenceRequest;
  manual_request?: ManualContentRequest;
  custom_instructions?: string;
  content_types?: string[];
}

export interface CurriculumStatus {
  loaded: boolean;
  statistics: {
    subjects_grades: string[];
    total_units: number;
    total_skills: number;
    total_subskills: number;
    learning_paths: number;
    subskill_paths: number;
  };
  sample_subskills: string[];
}

export interface CurriculumBrowseResponse {
  total_curricula: number;
  filters: {
    subject?: string;
    grade?: string;
  };
  curricula: CurriculumRecord[];
}

export class ContentAPI {
  private baseUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

  // ==================== CONTENT GENERATION ====================

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

  // Enhanced content generation with curriculum support
  async generateContentEnhanced(request: EnhancedContentGenerationRequest): Promise<ContentPackage> {
    const response = await fetch(`${this.baseUrl}/api/v1/generate-content-enhanced`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(request)
    });
    
    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: 'Enhanced generation failed' }));
      throw new Error(error.detail || 'Failed to generate enhanced content');
    }
    
    return response.json();
  }

  // ==================== CURRICULUM ENDPOINTS ====================

  // Load curriculum data
  async loadCurriculumData(
    curriculumFile: File,
    learningPathsFile?: File,
    subskillPathsFile?: File
  ): Promise<{
    status: string;
    curriculum_records: number;
    learning_paths: number;
    subskill_paths: number;
    subjects: string[];
  }> {
    const formData = new FormData();
    formData.append('curriculum_file', curriculumFile);
    
    if (learningPathsFile) {
      formData.append('learning_paths_file', learningPathsFile);
    }
    
    if (subskillPathsFile) {
      formData.append('subskill_paths_file', subskillPathsFile);
    }

    const response = await fetch(`${this.baseUrl}/api/v1/curriculum/load`, {
      method: 'POST',
      body: formData
    });
    
    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: 'Curriculum load failed' }));
      throw new Error(error.detail || 'Failed to load curriculum');
    }
    
    return response.json();
  }

  // Get curriculum status
  async getCurriculumStatus(): Promise<CurriculumStatus> {
    const response = await fetch(`${this.baseUrl}/api/v1/curriculum/status`);
    
    if (!response.ok) {
      throw new Error('Failed to get curriculum status');
    }
    
    return response.json();
  }

  // Get available subjects
  async getSubjects(): Promise<{ subjects: string[]; total: number }> {
    const response = await fetch(`${this.baseUrl}/api/v1/curriculum/subjects`);
    
    if (!response.ok) {
      throw new Error('Failed to get subjects');
    }
    
    return response.json();
  }

  // Get available grades (optionally filtered by subject)
  async getGrades(subject?: string): Promise<{ grades: string[]; subject_filter?: string; total: number }> {
    const params = new URLSearchParams();
    if (subject) params.append('subject', subject);
    
    const response = await fetch(`${this.baseUrl}/api/v1/curriculum/grades?${params}`);
    
    if (!response.ok) {
      throw new Error('Failed to get grades');
    }
    
    return response.json();
  }

  // Browse curriculum structure
  async browseCurriculum(subject?: string, grade?: string): Promise<CurriculumBrowseResponse> {
    const params = new URLSearchParams();
    if (subject) params.append('subject', subject);
    if (grade) params.append('grade', grade);
    
    const response = await fetch(`${this.baseUrl}/api/v1/curriculum/browse?${params}`);
    
    if (!response.ok) {
      throw new Error('Failed to browse curriculum');
    }
    
    return response.json();
  }

  // Get detailed context for a subskill
  async getCurriculumContext(subskillId: string): Promise<CurriculumContext> {
    const response = await fetch(`${this.baseUrl}/api/v1/curriculum/context/${subskillId}`);
    
    if (!response.ok) {
      if (response.status === 404) {
        throw new Error('Subskill not found in curriculum');
      }
      throw new Error('Failed to get curriculum context');
    }
    
    return response.json();
  }

  // Get learning path for a skill
  async getLearningPath(skillId: string): Promise<{
    skill_id: string;
    next_skills: string[];
    path_length: number;
  }> {
    const response = await fetch(`${this.baseUrl}/api/v1/curriculum/learning-path/${skillId}`);
    
    if (!response.ok) {
      throw new Error('Failed to get learning path');
    }
    
    return response.json();
  }

  // Get next subskill in progression
  async getSubskillPath(subskillId: string): Promise<{
    current_subskill: string;
    next_subskill: string | null;
    has_next: boolean;
  }> {
    const response = await fetch(`${this.baseUrl}/api/v1/curriculum/subskill-path/${subskillId}`);
    
    if (!response.ok) {
      throw new Error('Failed to get subskill path');
    }
    
    return response.json();
  }

  // ==================== CONTENT MANAGEMENT ====================

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

  // ==================== REVISION METHODS ====================

  async reviseContentPackage(
    packageId: string,
    subject: string,
    unit: string,
    revisions: ComponentRevision[],
    reviewerId?: string
  ): Promise<ContentPackage> {
    const response = await fetch(`${this.baseUrl}/api/v1/content/${packageId}/revise`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        package_id: packageId,
        subject,
        unit,
        revisions,
        reviewer_id: reviewerId
      })
    });
    
    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: 'Revision failed' }));
      throw new Error(error.detail || 'Failed to revise content package');
    }
    
    return response.json();
  }

  async getRevisionHistory(packageId: string, subject: string, unit: string): Promise<RevisionHistory[]> {
    const params = new URLSearchParams({ subject, unit });
    const response = await fetch(`${this.baseUrl}/api/v1/content/${packageId}/revisions?${params}`);
    
    if (!response.ok) {
      if (response.status === 404) {
        return [];
      }
      throw new Error('Failed to get revision history');
    }
    
    return response.json();
  }

  async reviseComponent(
    packageId: string,
    subject: string,
    unit: string,
    componentType: ComponentType,
    feedback: string,
    priority: 'low' | 'medium' | 'high' = 'medium',
    reviewerId?: string
  ): Promise<ContentPackage> {
    return this.reviseContentPackage(packageId, subject, unit, [{
      component_type: componentType,
      feedback,
      priority
    }], reviewerId);
  }

  // ==================== REVIEW WORKFLOW METHODS ====================

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

  // ==================== UTILITY METHODS ====================

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

  async getAudioFileUrl(packageId: string, filename: string): Promise<string> {
    return `${this.baseUrl}/api/v1/audio/${packageId}/${filename}`;
  }

  async healthCheck(): Promise<HealthStatus> {
    const response = await fetch(`${this.baseUrl}/api/v1/health`);
    return response.json();
  }

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