import React, { useState, useEffect } from 'react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Badge } from '@/components/ui/badge';
import { Textarea } from '@/components/ui/textarea';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Loader2, Plus, X, BookOpen, Edit, ChevronRight, ChevronDown } from 'lucide-react';
import { 
  GenerationRequest, 
  EnhancedContentGenerationRequest,
  CurriculumRecord,
  CurriculumContext,
  GRADE_LEVELS,
  DIFFICULTY_LEVELS,
  GenerationMode
} from '@/lib/types';
import { contentAPI } from '@/lib/api';

interface EnhancedContentGenerationFormProps {
  onSubmit: (request: EnhancedContentGenerationRequest) => Promise<void>;
  loading?: boolean;
}

const SUBJECTS = [
  'Mathematics',
  'Science',
  'Language Arts',
  'Social Studies',
  'Art',
];

const COMMON_PREREQUISITES = [
  'basic_algebra',
  'coordinate_plane',
  'fractions',
  'decimals',
  'geometry_basics',
  'reading_comprehension',
  'writing_basics',
  'scientific_method',
  'data_analysis'
];

export default function EnhancedContentGenerationForm({ onSubmit, loading = false }: EnhancedContentGenerationFormProps) {
  // Mode state
  const [mode, setMode] = useState<GenerationMode>('manual');
  
  // Curriculum state
  const [curriculumLoaded, setCurriculumLoaded] = useState(false);
  const [availableSubjects, setAvailableSubjects] = useState<string[]>([]);
  const [availableGrades, setAvailableGrades] = useState<string[]>([]);
  const [curriculumData, setCurriculumData] = useState<CurriculumRecord[]>([]);
  const [selectedSubject, setSelectedSubject] = useState<string>('');
  const [selectedGrade, setSelectedGrade] = useState<string>('');
  const [selectedSubskill, setSelectedSubskill] = useState<Subskill | null>(null);
  const [curriculumContext, setCurriculumContext] = useState<CurriculumContext | null>(null);
  const [expandedUnits, setExpandedUnits] = useState<Set<string>>(new Set());
  const [expandedSkills, setExpandedSkills] = useState<Set<string>>(new Set());
  
  // Manual form state
  const [manualFormData, setManualFormData] = useState<GenerationRequest>({
    subject: '',
    grade: '',
    unit: '',
    skill: '',
    subskill: '',
    difficulty_level: 'intermediate',
    prerequisites: []
  });
  
  // Override state for curriculum mode
  const [difficultyOverride, setDifficultyOverride] = useState<string>('');
  const [prerequisitesOverride, setPrerequisitesOverride] = useState<string[]>([]);
  const [customInstructions, setCustomInstructions] = useState<string>('');
  const [newPrerequisite, setNewPrerequisite] = useState('');
  
  // Loading states
  const [loadingCurriculum, setLoadingCurriculum] = useState(false);
  const [loadingContext, setLoadingContext] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Check curriculum status on mount
  useEffect(() => {
    checkCurriculumStatus();
  }, []);

  // Load grades when subject changes in curriculum mode
  useEffect(() => {
    if (mode === 'curriculum' && selectedSubject) {
      loadGradesForSubject(selectedSubject);
    }
  }, [selectedSubject, mode]);

  // Load curriculum data when subject and grade are selected
  useEffect(() => {
    if (mode === 'curriculum' && selectedSubject && selectedGrade) {
      loadCurriculumData();
    }
  }, [selectedSubject, selectedGrade, mode]);

  const checkCurriculumStatus = async () => {
    try {
      const status = await contentAPI.getCurriculumStatus();
      setCurriculumLoaded(status.loaded);
      if (status.loaded) {
        // Extract unique subjects from subjects_grades array
        const subjects = [...new Set(status.statistics.subjects_grades.map(sg => sg.split(' - ')[0]))];
        setAvailableSubjects(subjects);
      }
    } catch (err) {
      console.error('Failed to check curriculum status:', err);
      setCurriculumLoaded(false);
    }
  };

  const loadGradesForSubject = async (subject: string) => {
    try {
      const response = await contentAPI.getGrades(subject);
      setAvailableGrades(response.grades);
    } catch (err) {
      console.error('Failed to load grades:', err);
      setError('Failed to load grades for selected subject');
    }
  };

  const loadCurriculumData = async () => {
    setLoadingCurriculum(true);
    setError(null);
    try {
      const response = await contentAPI.browseCurriculum(selectedSubject, selectedGrade);
      setCurriculumData(response.curricula);
    } catch (err) {
      console.error('Failed to load curriculum:', err);
      setError('Failed to load curriculum data');
    } finally {
      setLoadingCurriculum(false);
    }
  };

  const handleSubskillSelect = async (subskill: Subskill) => {
    setLoadingContext(true);
    setError(null);
    try {
      const context = await contentAPI.getCurriculumContext(subskill.subskill_id);
      setSelectedSubskill(subskill);
      setCurriculumContext(context);
      
      // Reset overrides when new subskill is selected
      setDifficultyOverride('');
      setPrerequisitesOverride([]);
    } catch (err) {
      console.error('Failed to load curriculum context:', err);
      setError('Failed to load curriculum context');
    } finally {
      setLoadingContext(false);
    }
  };

  const toggleUnitExpansion = (unitId: string) => {
    const newExpanded = new Set(expandedUnits);
    if (newExpanded.has(unitId)) {
      newExpanded.delete(unitId);
    } else {
      newExpanded.add(unitId);
    }
    setExpandedUnits(newExpanded);
  };

  const toggleSkillExpansion = (skillId: string) => {
    const newExpanded = new Set(expandedSkills);
    if (newExpanded.has(skillId)) {
      newExpanded.delete(skillId);
    } else {
      newExpanded.add(skillId);
    }
    setExpandedSkills(newExpanded);
  };

  const addPrerequisite = (prerequisite: string, isOverride: boolean = false) => {
    if (isOverride) {
      if (prerequisite && !prerequisitesOverride.includes(prerequisite)) {
        setPrerequisitesOverride(prev => [...prev, prerequisite]);
      }
    } else {
      if (prerequisite && !manualFormData.prerequisites?.includes(prerequisite)) {
        setManualFormData(prev => ({
          ...prev,
          prerequisites: [...(prev.prerequisites || []), prerequisite]
        }));
      }
    }
  };

  const removePrerequisite = (prerequisite: string, isOverride: boolean = false) => {
    if (isOverride) {
      setPrerequisitesOverride(prev => prev.filter(p => p !== prerequisite));
    } else {
      setManualFormData(prev => ({
        ...prev,
        prerequisites: prev.prerequisites?.filter(p => p !== prerequisite) || []
      }));
    }
  };

  const addCustomPrerequisite = (isOverride: boolean = false) => {
    if (newPrerequisite.trim()) {
      addPrerequisite(newPrerequisite.trim(), isOverride);
      setNewPrerequisite('');
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);

    try {
      if (mode === 'curriculum') {
        if (!selectedSubskill) {
          setError('Please select a subskill from the curriculum');
          return;
        }

        const request: EnhancedContentGenerationRequest = {
          mode: 'curriculum',
          curriculum_request: {
            subskill_id: selectedSubskill.subskill_id,
            grade: curriculumContext?.grade, // Add this line
            difficulty_level_override: difficultyOverride || undefined,
            prerequisites_override: prerequisitesOverride.length > 0 ? prerequisitesOverride : undefined
          },
          custom_instructions: customInstructions || undefined
        };

        await onSubmit(request);
      } else {
        // Manual mode
        if (!manualFormData.subject || !manualFormData.unit || !manualFormData.skill || !manualFormData.subskill) {
          setError('Please fill in all required fields');
          return;
        }

        const request: EnhancedContentGenerationRequest = {
          mode: 'manual',
          manual_request: {
            subject: manualFormData.subject,
            grade: manualFormData.grade || undefined,
            unit: manualFormData.unit,
            skill: manualFormData.skill,
            subskill: manualFormData.subskill,
            difficulty_level: manualFormData.difficulty_level || 'intermediate',
            prerequisites: manualFormData.prerequisites || []
          },
          custom_instructions: customInstructions || undefined
        };

        await onSubmit(request);
      }
    } catch (err) {
      console.error('Generation request failed:', err);
      setError(err instanceof Error ? err.message : 'Generation request failed');
    }
  };

  // Group curriculum data by unit and skill for the tree structure
  const groupedCurriculum = curriculumData.reduce((acc, curriculum) => {
    curriculum.units.forEach(unit => {
      if (!acc[unit.unit_title]) {
        acc[unit.unit_title] = {};
      }
      unit.skills.forEach(skill => {
        if (!acc[unit.unit_title][skill.skill_description]) {
          acc[unit.unit_title][skill.skill_description] = [];
        }
        acc[unit.unit_title][skill.skill_description].push(...skill.subskills);
      });
    });
    return acc;
  }, {} as Record<string, Record<string, Subskill[]>>);

  return (
    <Card className="w-full max-w-4xl mx-auto">
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Plus className="h-5 w-5" />
          Enhanced Content Generation
        </CardTitle>
        <CardDescription>
          Generate content from curriculum data or manual input with grade-appropriate targeting
        </CardDescription>
      </CardHeader>
      <CardContent>
        {error && (
          <Alert className="mb-6 border-red-200 bg-red-50">
            <AlertDescription className="text-red-800">
              {error}
            </AlertDescription>
          </Alert>
        )}

        <Tabs value={mode} onValueChange={(value) => setMode(value as GenerationMode)}>
          <TabsList className="grid w-full grid-cols-2">
            <TabsTrigger value="curriculum" className="flex items-center gap-2">
              <BookOpen className="h-4 w-4" />
              Browse Curriculum
            </TabsTrigger>
            <TabsTrigger value="manual" className="flex items-center gap-2">
              <Edit className="h-4 w-4" />
              Manual Entry
            </TabsTrigger>
          </TabsList>

          <TabsContent value="curriculum" className="space-y-6">
            {!curriculumLoaded ? (
              <Alert>
                <AlertDescription>
                  Curriculum data is not loaded. Please upload curriculum files to use this feature.
                </AlertDescription>
              </Alert>
            ) : (
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                {/* Curriculum Browser */}
                <div className="space-y-4">
                  <h3 className="text-lg font-medium">Select from Curriculum</h3>
                  
                  {/* Subject Selection */}
                  <div className="space-y-2">
                    <Label>Subject</Label>
                    <Select value={selectedSubject} onValueChange={setSelectedSubject}>
                      <SelectTrigger>
                        <SelectValue placeholder="Select a subject" />
                      </SelectTrigger>
                      <SelectContent>
                        {availableSubjects.map(subject => (
                          <SelectItem key={subject} value={subject}>
                            {subject}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>

                  {/* Grade Selection */}
                  {selectedSubject && (
                    <div className="space-y-2">
                      <Label>Grade</Label>
                      <Select value={selectedGrade} onValueChange={setSelectedGrade}>
                        <SelectTrigger>
                          <SelectValue placeholder="Select a grade" />
                        </SelectTrigger>
                        <SelectContent>
                          {availableGrades.map(grade => (
                            <SelectItem key={grade} value={grade}>
                              {grade}
                            </SelectItem>
                          ))}
                        </SelectContent>
                      </Select>
                    </div>
                  )}

                  {/* Curriculum Tree */}
                  {selectedSubject && selectedGrade && (
                    <div className="space-y-2">
                      <Label>Curriculum Structure</Label>
                      <div className="border rounded-lg p-4 max-h-96 overflow-y-auto">
                        {loadingCurriculum ? (
                          <div className="flex items-center gap-2 text-muted-foreground">
                            <Loader2 className="h-4 w-4 animate-spin" />
                            Loading curriculum...
                          </div>
                        ) : (
                          <div className="space-y-2">
                            {Object.entries(groupedCurriculum).map(([unit, skills]) => (
                              <div key={unit} className="space-y-1">
                                <Button
                                  variant="ghost"
                                  size="sm"
                                  onClick={() => toggleUnitExpansion(unit)}
                                  className="w-full justify-start font-medium"
                                >
                                  {expandedUnits.has(unit) ? (
                                    <ChevronDown className="h-4 w-4 mr-2" />
                                  ) : (
                                    <ChevronRight className="h-4 w-4 mr-2" />
                                  )}
                                  📚 {unit}
                                </Button>
                                
                                {expandedUnits.has(unit) && (
                                  <div className="ml-6 space-y-1">
                                    {Object.entries(skills).map(([skill, subskills]) => (
                                      <div key={skill} className="space-y-1">
                                        <Button
                                          variant="ghost"
                                          size="sm"
                                          onClick={() => toggleSkillExpansion(skill)}
                                          className="w-full justify-start text-sm"
                                        >
                                          {expandedSkills.has(skill) ? (
                                            <ChevronDown className="h-4 w-4 mr-2" />
                                          ) : (
                                            <ChevronRight className="h-4 w-4 mr-2" />
                                          )}
                                          🎯 {skill}
                                        </Button>
                                        
                                        {expandedSkills.has(skill) && (
                                          <div className="ml-6 space-y-1">
                                            {subskills.map((subskill) => (
                                              <Button
                                                key={subskill.subskill_id}
                                                variant={selectedSubskill?.subskill_id === subskill.subskill_id ? "default" : "ghost"}
                                                size="sm"
                                                onClick={() => handleSubskillSelect(subskill)}
                                                className="w-full justify-start text-sm"
                                                disabled={loadingContext}
                                              >
                                                {loadingContext && selectedSubskill?.subskill_id === subskill.subskill_id ? (
                                                  <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                                                ) : (
                                                  <span className="mr-2">📝</span>
                                                )}
                                                {subskill.subskill_description}
                                                <Badge variant="outline" className="ml-auto">
                                                  {subskill.target_difficulty.toFixed(1)}
                                                </Badge>
                                              </Button>
                                            ))}
                                          </div>
                                        )}
                                      </div>
                                    ))}
                                  </div>
                                )}
                              </div>
                            ))}
                          </div>
                        )}
                      </div>
                    </div>
                  )}
                </div>

                {/* Generation Form */}
                <div className="space-y-4">
                  <h3 className="text-lg font-medium">Content Generation</h3>
                  
                  {selectedSubskill && curriculumContext ? (
                    <div className="space-y-4">
                      {/* Selected Context Display */}
                      <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                        <h4 className="font-medium text-blue-900 mb-2">Selected Content</h4>
                        <div className="space-y-1 text-sm text-blue-800">
                          <p><strong>Subject:</strong> {curriculumContext.subject}</p>
                          <p><strong>Grade:</strong> {curriculumContext.grade}</p>
                          <p><strong>Unit:</strong> {curriculumContext.unit}</p>
                          <p><strong>Skill:</strong> {curriculumContext.skill}</p>
                          <p><strong>Subskill:</strong> {curriculumContext.subskill}</p>
                        </div>
                      </div>

                      {/* Difficulty Override */}
                      <div className="space-y-2">
                        <Label>Difficulty Level Override (Optional)</Label>
                        <Select value={difficultyOverride} onValueChange={setDifficultyOverride}>
                          <SelectTrigger>
                            <SelectValue placeholder={`Default: ${curriculumContext.difficulty_level}`} />
                          </SelectTrigger>
                          <SelectContent>
                            {DIFFICULTY_LEVELS.map(level => (
                              <SelectItem key={level.value} value={level.value}>
                                {level.label}
                              </SelectItem>
                            ))}
                          </SelectContent>
                        </Select>
                      </div>

                      {/* Prerequisites Override */}
                      <div className="space-y-3">
                        <Label>Prerequisites Override (Optional)</Label>
                        
                        {/* Current Default Prerequisites */}
                        <div>
                          <Label className="text-sm text-muted-foreground">Default Prerequisites:</Label>
                          <div className="flex flex-wrap gap-2 mt-1">
                            {curriculumContext.prerequisites.map(prerequisite => (
                              <Badge key={prerequisite} variant="outline">
                                {prerequisite}
                              </Badge>
                            ))}
                          </div>
                        </div>

                        {/* Override Prerequisites */}
                        {prerequisitesOverride.length > 0 && (
                          <div>
                            <Label className="text-sm text-muted-foreground">Override Prerequisites:</Label>
                            <div className="flex flex-wrap gap-2 mt-1">
                              {prerequisitesOverride.map(prerequisite => (
                                <Badge key={prerequisite} variant="secondary" className="pr-1">
                                  {prerequisite}
                                  <button
                                    type="button"
                                    onClick={() => removePrerequisite(prerequisite, true)}
                                    className="ml-1 hover:bg-red-500 hover:text-white rounded-full p-0.5"
                                  >
                                    <X className="h-3 w-3" />
                                  </button>
                                </Badge>
                              ))}
                            </div>
                          </div>
                        )}

                        {/* Add Prerequisites */}
                        <div>
                          <Label className="text-sm text-muted-foreground">Add Prerequisites:</Label>
                          <div className="flex flex-wrap gap-2 mt-1">
                            {COMMON_PREREQUISITES.map(prerequisite => (
                              <Button
                                key={prerequisite}
                                type="button"
                                variant="outline"
                                size="sm"
                                className="h-7 text-xs"
                                onClick={() => addPrerequisite(prerequisite, true)}
                                disabled={prerequisitesOverride.includes(prerequisite)}
                              >
                                + {prerequisite.replace('_', ' ')}
                              </Button>
                            ))}
                          </div>
                        </div>

                        {/* Custom Prerequisite */}
                        <div className="flex gap-2">
                          <Input
                            placeholder="Add custom prerequisite"
                            value={newPrerequisite}
                            onChange={(e) => setNewPrerequisite(e.target.value)}
                            onKeyPress={(e) => e.key === 'Enter' && (e.preventDefault(), addCustomPrerequisite(true))}
                            className="flex-1"
                          />
                          <Button
                            type="button"
                            variant="outline"
                            onClick={() => addCustomPrerequisite(true)}
                            disabled={!newPrerequisite.trim()}
                          >
                            Add
                          </Button>
                        </div>
                      </div>
                    </div>
                  ) : (
                    <Alert>
                      <AlertDescription>
                        Select a subskill from the curriculum to configure content generation.
                      </AlertDescription>
                    </Alert>
                  )}
                </div>
              </div>
            )}
          </TabsContent>

          <TabsContent value="manual" className="space-y-6">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              {/* Subject and Grade */}
              <div className="space-y-2">
                <Label htmlFor="subject">Subject *</Label>
                <Select 
                  value={manualFormData.subject} 
                  onValueChange={(value) => setManualFormData(prev => ({ ...prev, subject: value }))}
                >
                  <SelectTrigger>
                    <SelectValue placeholder="Select a subject" />
                  </SelectTrigger>
                  <SelectContent>
                    {SUBJECTS.map(subject => (
                      <SelectItem key={subject} value={subject}>
                        {subject}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>

              <div className="space-y-2">
                <Label htmlFor="grade">Grade (Optional)</Label>
                <Select 
                  value={manualFormData.grade || ''} 
                  onValueChange={(value) => setManualFormData(prev => ({ ...prev, grade: value }))}
                >
                  <SelectTrigger>
                    <SelectValue placeholder="Select a grade" />
                  </SelectTrigger>
                  <SelectContent>
                    {GRADE_LEVELS.map(grade => (
                      <SelectItem key={grade} value={grade}>
                        {grade}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>

              {/* Unit and Skill */}
              <div className="space-y-2">
                <Label htmlFor="unit">Unit *</Label>
                <Input
                  id="unit"
                  placeholder="e.g., Algebra, Biology, Grammar"
                  value={manualFormData.unit}
                  onChange={(e) => setManualFormData(prev => ({ ...prev, unit: e.target.value }))}
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="skill">Skill *</Label>
                <Input
                  id="skill"
                  placeholder="e.g., Linear Equations, Cell Division, Essay Writing"
                  value={manualFormData.skill}
                  onChange={(e) => setManualFormData(prev => ({ ...prev, skill: e.target.value }))}
                />
              </div>

              {/* Subskill and Difficulty */}
              <div className="space-y-2">
                <Label htmlFor="subskill">Subskill *</Label>
                <Input
                  id="subskill"
                  placeholder="e.g., Slope-Intercept Form, Mitosis, Thesis Statements"
                  value={manualFormData.subskill}
                  onChange={(e) => setManualFormData(prev => ({ ...prev, subskill: e.target.value }))}
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="difficulty">Difficulty Level</Label>
                <Select 
                  value={manualFormData.difficulty_level} 
                  onValueChange={(value) => setManualFormData(prev => ({ ...prev, difficulty_level: value }))}
                >
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    {DIFFICULTY_LEVELS.map(level => (
                      <SelectItem key={level.value} value={level.value}>
                        {level.label}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
            </div>

            {/* Prerequisites */}
            <div className="space-y-3">
              <Label>Prerequisites</Label>
              
              {/* Current Prerequisites */}
              {manualFormData.prerequisites && manualFormData.prerequisites.length > 0 && (
                <div className="flex flex-wrap gap-2">
                  {manualFormData.prerequisites.map(prerequisite => (
                    <Badge key={prerequisite} variant="secondary" className="pr-1">
                      {prerequisite}
                      <button
                        type="button"
                        onClick={() => removePrerequisite(prerequisite, false)}
                        className="ml-1 hover:bg-red-500 hover:text-white rounded-full p-0.5"
                      >
                        <X className="h-3 w-3" />
                      </button>
                    </Badge>
                  ))}
                </div>
              )}

              {/* Common Prerequisites */}
              <div>
                <Label className="text-sm text-muted-foreground">Common Prerequisites:</Label>
                <div className="flex flex-wrap gap-2 mt-1">
                  {COMMON_PREREQUISITES.map(prerequisite => (
                    <Button
                      key={prerequisite}
                      type="button"
                      variant="outline"
                      size="sm"
                      className="h-7 text-xs"
                      onClick={() => addPrerequisite(prerequisite, false)}
                      disabled={manualFormData.prerequisites?.includes(prerequisite)}
                    >
                      + {prerequisite.replace('_', ' ')}
                    </Button>
                  ))}
                </div>
              </div>

              {/* Custom Prerequisite */}
              <div className="flex gap-2">
                <Input
                  placeholder="Add custom prerequisite"
                  value={newPrerequisite}
                  onChange={(e) => setNewPrerequisite(e.target.value)}
                  onKeyPress={(e) => e.key === 'Enter' && (e.preventDefault(), addCustomPrerequisite(false))}
                  className="flex-1"
                />
                <Button
                  type="button"
                  variant="outline"
                  onClick={() => addCustomPrerequisite(false)}
                  disabled={!newPrerequisite.trim()}
                >
                  Add
                </Button>
              </div>
            </div>
          </TabsContent>
        </Tabs>

        {/* Custom Instructions */}
        <div className="space-y-2">
          <Label htmlFor="instructions">Custom Instructions (Optional)</Label>
          <Textarea
            id="instructions"
            placeholder="Add any specific requirements or context for content generation..."
            value={customInstructions}
            onChange={(e) => setCustomInstructions(e.target.value)}
            rows={3}
          />
        </div>

        {/* Estimated Generation Time */}
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
          <div className="flex items-center gap-2 text-blue-800">
            <div className="w-2 h-2 bg-blue-500 rounded-full"></div>
            <span className="font-medium">
              Estimated Generation Time: 2-5 minutes
              {mode === 'curriculum' && ' (Grade-optimized content)'}
            </span>
          </div>
          <p className="text-sm text-blue-600 mt-1">
            {mode === 'curriculum' 
              ? 'Content will be generated using curriculum context and optimized for the selected grade level.'
              : 'Your content package will include reading content, interactive visual demo, audio dialogue, and practice problems.'
            }
          </p>
        </div>

        {/* Submit Button */}
        <Button 
          onClick={handleSubmit}
          className="w-full" 
          disabled={loading || (mode === 'curriculum' ? !selectedSubskill : !manualFormData.subject || !manualFormData.unit || !manualFormData.skill || !manualFormData.subskill)}
        >
          {loading ? (
            <>
              <Loader2 className="mr-2 h-4 w-4 animate-spin" />
              Generating Content...
            </>
          ) : (
            <>
              Generate {mode === 'curriculum' ? 'Curriculum-Based' : 'Custom'} Content Package
            </>
          )}
        </Button>
      </CardContent>
    </Card>
  );
}