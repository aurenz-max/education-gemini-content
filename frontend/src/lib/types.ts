// lib/types.ts - Updated with Grade and Curriculum Support
export interface GenerationRequest {
  subject: string;
  grade?: string; // NEW: Optional grade field
  unit: string;
  skill: string;
  subskill: string;
  difficulty_level?: string;
  prerequisites?: string[];
  custom_instructions?: string; // NEW: For additional context
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
  difficulty: number;
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
  grade?: string; // Add this
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

export interface CurriculumTreeNode {
  id: string;
  title: string;
  type: 'subject' | 'grade' | 'unit' | 'skill' | 'subskill';
  children?: CurriculumTreeNode[];
  metadata?: {
    difficulty_level?: string;
    prerequisites?: string[];
    learning_objectives?: string[];
    concepts?: string[];
  };
}

export interface CurriculumBrowseFilters {
  subject?: string;
  grade?: string;
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

// ==================== REVISION TYPES ====================

export type ComponentType = 'reading' | 'visual' | 'audio' | 'practice';

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

export interface RevisionHistory {
  revision_id: string;
  timestamp: string;
  components_revised: ComponentType[];
  feedback_summary: string;
  status: 'in_progress' | 'completed' | 'failed';
  revised_by: string;
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
  grade?: string; // NEW: Include grade in content package
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
  revision_history?: RevisionHistory[];
  created_at?: string;
  updated_at?: string;
}

export interface PackageFilters {
  subject?: string;
  grade?: string; // NEW: Filter by grade
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
  grade?: string; // NEW: Include grade in review info
  unit: string;
  skill: string;
  subskill: string;
}

export interface ReviewQueueFilters {
  subject?: string;
  grade?: string; // NEW: Filter review queue by grade
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

// ==================== GENERATION MODE TYPES ====================

export type GenerationMode = 'curriculum' | 'manual';

export interface GenerationFormData {
  mode: GenerationMode;
  
  // Curriculum mode data
  selectedSubskillId?: string;
  curriculumContext?: CurriculumContext;
  difficultyOverride?: string;
  prerequisitesOverride?: string[];
  
  // Manual mode data
  subject?: string;
  grade?: string;
  unit?: string;
  skill?: string;
  subskill?: string;
  difficulty_level?: string;
  prerequisites?: string[];
  
  // Common fields
  custom_instructions?: string;
  content_types?: string[];
}

export interface SubskillSelection {
  id: string;
  subject: string;
  grade: string;
  unit: string;
  skill: string;
  subskill: string;
  difficulty_level: string;
  prerequisites: string[];
  learning_objectives: string[];
}

// ==================== COMMON CONSTANTS ====================

export const GRADE_LEVELS = [
  'Kindergarten',
  '1st Grade',
  '2nd Grade',
  '3rd Grade',
  '4th Grade',
  '5th Grade',
  '6th Grade',
  '7th Grade',
  '8th Grade',
  '9th Grade',
  '10th Grade',
  '11th Grade',
  '12th Grade'
] as const;

export const DIFFICULTY_LEVELS = [
  { value: 'beginner', label: 'Beginner' },
  { value: 'intermediate', label: 'Intermediate' },
  { value: 'advanced', label: 'Advanced' }
] as const;

export const CONTENT_TYPES = [
  { value: 'reading', label: 'Reading Content', description: 'Structured explanatory text' },
  { value: 'visual', label: 'Visual Demo', description: 'Interactive p5.js visualization' },
  { value: 'audio', label: 'Audio Content', description: 'Teacher-student dialogue' },
  { value: 'practice', label: 'Practice Problems', description: 'Assessment questions with solutions' }
] as const;

export type ReviewStatus = 'generated' | 'under_review' | 'approved' | 'rejected' | 'needs_revision';

export type PackageStatus = 'draft' | 'generated' | 'approved' | 'rejected' | 'needs_revision' | 'under_review' | 'published';