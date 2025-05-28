// src/components/ContentGenerationForm.tsx
'use client';

import { useState } from 'react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Badge } from '@/components/ui/badge';
import { Textarea } from '@/components/ui/textarea';
import { Loader2, Plus, X } from 'lucide-react';
import { GenerationRequest } from '@/lib/types';

interface ContentGenerationFormProps {
  onSubmit: (request: GenerationRequest) => Promise<void>;
  loading?: boolean;
}

const SUBJECTS = [
  'Mathematics',
  'Science',
  'English Language Arts',
  'Social Studies',
  'Computer Science',
  'Art',
  'Music',
  'Physical Education'
];

const DIFFICULTY_LEVELS = [
  { value: 'beginner', label: 'Beginner' },
  { value: 'intermediate', label: 'Intermediate' },
  { value: 'advanced', label: 'Advanced' }
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

export function ContentGenerationForm({ onSubmit, loading = false }: ContentGenerationFormProps) {
  const [formData, setFormData] = useState<GenerationRequest>({
    subject: '',
    unit: '',
    skill: '',
    subskill: '',
    difficulty_level: 'intermediate',
    prerequisites: []
  });

  const [newPrerequisite, setNewPrerequisite] = useState('');

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!formData.subject || !formData.unit || !formData.skill || !formData.subskill) {
      alert('Please fill in all required fields');
      return;
    }
    await onSubmit(formData);
  };

  const addPrerequisite = (prerequisite: string) => {
    if (prerequisite && !formData.prerequisites?.includes(prerequisite)) {
      setFormData(prev => ({
        ...prev,
        prerequisites: [...(prev.prerequisites || []), prerequisite]
      }));
    }
  };

  const removePrerequisite = (prerequisite: string) => {
    setFormData(prev => ({
      ...prev,
      prerequisites: prev.prerequisites?.filter(p => p !== prerequisite) || []
    }));
  };

  const addCustomPrerequisite = () => {
    if (newPrerequisite.trim()) {
      addPrerequisite(newPrerequisite.trim());
      setNewPrerequisite('');
    }
  };

  return (
    <Card className="w-full max-w-2xl mx-auto">
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Plus className="h-5 w-5" />
          Generate New Content Package
        </CardTitle>
        <CardDescription>
          Create a comprehensive educational content package with reading, visual, audio, and practice components
        </CardDescription>
      </CardHeader>
      <CardContent>
        <form onSubmit={handleSubmit} className="space-y-6">
          {/* Subject Selection */}
          <div className="space-y-2">
            <Label htmlFor="subject">Subject *</Label>
            <Select 
              value={formData.subject} 
              onValueChange={(value) => setFormData(prev => ({ ...prev, subject: value }))}
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

          {/* Unit Input */}
          <div className="space-y-2">
            <Label htmlFor="unit">Unit *</Label>
            <Input
              id="unit"
              placeholder="e.g., Algebra, Biology, Grammar"
              value={formData.unit}
              onChange={(e) => setFormData(prev => ({ ...prev, unit: e.target.value }))}
            />
          </div>

          {/* Skill Input */}
          <div className="space-y-2">
            <Label htmlFor="skill">Skill *</Label>
            <Input
              id="skill"
              placeholder="e.g., Linear Equations, Cell Division, Essay Writing"
              value={formData.skill}
              onChange={(e) => setFormData(prev => ({ ...prev, skill: e.target.value }))}
            />
          </div>

          {/* Subskill Input */}
          <div className="space-y-2">
            <Label htmlFor="subskill">Subskill *</Label>
            <Input
              id="subskill"
              placeholder="e.g., Slope-Intercept Form, Mitosis, Thesis Statements"
              value={formData.subskill}
              onChange={(e) => setFormData(prev => ({ ...prev, subskill: e.target.value }))}
            />
          </div>

          {/* Difficulty Level */}
          <div className="space-y-2">
            <Label htmlFor="difficulty">Difficulty Level</Label>
            <Select 
              value={formData.difficulty_level} 
              onValueChange={(value) => setFormData(prev => ({ ...prev, difficulty_level: value }))}
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

          {/* Prerequisites */}
          <div className="space-y-3">
            <Label>Prerequisites</Label>
            
            {/* Current Prerequisites */}
            {formData.prerequisites && formData.prerequisites.length > 0 && (
              <div className="flex flex-wrap gap-2">
                {formData.prerequisites.map(prerequisite => (
                  <Badge key={prerequisite} variant="secondary" className="pr-1">
                    {prerequisite}
                    <button
                      type="button"
                      onClick={() => removePrerequisite(prerequisite)}
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
                    onClick={() => addPrerequisite(prerequisite)}
                    disabled={formData.prerequisites?.includes(prerequisite)}
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
                onKeyPress={(e) => e.key === 'Enter' && (e.preventDefault(), addCustomPrerequisite())}
                className="flex-1"
              />
              <Button
                type="button"
                variant="outline"
                onClick={addCustomPrerequisite}
                disabled={!newPrerequisite.trim()}
              >
                Add
              </Button>
            </div>
          </div>

          {/* Estimated Generation Time */}
          <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
            <div className="flex items-center gap-2 text-blue-800">
              <div className="w-2 h-2 bg-blue-500 rounded-full"></div>
              <span className="font-medium">Estimated Generation Time: 2-5 minutes</span>
            </div>
            <p className="text-sm text-blue-600 mt-1">
              Your content package will include reading content, interactive visual demo, 
              audio dialogue, and practice problems.
            </p>
          </div>

          {/* Submit Button */}
          <Button 
            type="submit" 
            className="w-full" 
            disabled={loading || !formData.subject || !formData.unit || !formData.skill || !formData.subskill}
          >
            {loading ? (
              <>
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                Generating Content...
              </>
            ) : (
              'Generate Content Package'
            )}
          </Button>
        </form>
      </CardContent>
    </Card>
  );
}