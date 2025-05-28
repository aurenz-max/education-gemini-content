// lib/types.ts - Updated with Review Types
export interface GenerationRequest {
  subject: string;
  unit: string;
  skill: string;
  subskill: string;
  difficulty_level?: string;
  prerequisites?: string[];
}

export interface MasterContext {
  core_concepts: string[];
  key_terminology: Record<string, string>;
  learning_objectives: string[];
  difficulty_level: string;
  prerequisites: string[];
  real_world_applications: string[];
}

export interface GenerationMetadata {
  generation_time_ms: number;
  coherence_score: number;
}

export interface ReadingContent {
  title: string;
  sections: Array<{
    heading: string;
    content: string;
    key_terms_used: string[];
    concepts_covered: string[];
  }>;
  word_count: number;
  reading_level: string;
}

export interface VisualContent {
  p5_code: string;
  description: string;
  interactive_elements: string[];
  concepts_demonstrated: string[];
  user_instructions: string;
}

export interface AudioContent {
  audio_file_path: string;
  audio_filename: string;
  dialogue_script: string;
  duration_seconds: number;
  voice_config: {
    teacher_voice: string;
    student_voice: string;
  };
  tts_status: string;
}

export interface PracticeProblem {
  id: string;
  problem_data: {
    problem_type: string;
    problem: string;
    answer: string;
    success_criteria: string[];
    teaching_note: string;
    metadata?: {
      subject: string;
      unit: { id: string; title: string };
      skill: { id: string; description: string };
      subskill: { id: string; description: string };
    };
  };
}

export interface PracticeContent {
  problems: PracticeProblem[];
  problem_count: number;
  estimated_time_minutes: number;
}

// ==================== REVIEW TYPES ====================

export interface ReviewNote {
  note: string;
  status: string;
  timestamp: string;
  reviewer_id: string;
}

export interface ContentPackage {
  id: string;
  partition_key?: string;
  subject: string;
  unit: string;
  skill: string;
  subskill: string;
  master_context: MasterContext;
  content: {
    reading: ReadingContent;
    visual: VisualContent;
    audio: AudioContent;
    practice: PracticeContent;
  };
  generation_metadata: GenerationMetadata;
  status?: 'draft' | 'generated' | 'approved' | 'rejected' | 'needs_revision' | 'under_review' | 'published';
  review_status?: string;
  reviewed_by?: string;
  reviewed_at?: string;
  review_notes?: ReviewNote[];
  created_at?: string;
  updated_at?: string;
}

export interface PackageFilters {
  subject?: string;
  unit?: string;
  status?: string;
  limit?: number;
}

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
  review_notes: ReviewNote[];
  created_at: string;
  updated_at: string;
  subject: string;
  unit: string;
  skill: string;
  subskill: string;
}

export interface ReviewQueueFilters {
  subject?: string;
  unit?: string;
  limit?: number;
}

export interface StatusUpdateResponse {
  message: string;
  package_id: string;
  old_status: string;
  new_status: string;
  updated_at: string;
  package: ContentPackage;
}

export interface HealthStatus {
  status: string;
  timestamp: string;
  services: {
    cosmos_db: {
      status: string;
      total_documents: number;
      database: string;
      container: string;
    };
    blob_storage: {
      status: string;
      container: string;
      recent_blobs: number;
    };
    content_generation: {
      status: string;
      service: string;
    };
  };
}

export type ComponentType = 'reading' | 'visual' | 'audio' | 'practice';

export type ReviewStatus = 'generated' | 'under_review' | 'approved' | 'rejected' | 'needs_revision';

export type PackageStatus = 'draft' | 'generated' | 'approved' | 'rejected' | 'needs_revision' | 'under_review' | 'published';