// src/components/review/AudioContentPanel.tsx - Updated with Revision Support
'use client';

import { useState, useRef, useEffect } from 'react';
import { Card, CardContent, CardFooter, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { 
  Volume2, 
  RotateCcw, 
  Check, 
  MessageSquare, 
  Download, 
  Play, 
  Pause,
  Volume1,
  VolumeX,
  SkipBack,
  SkipForward,
  Mic,
  FileAudio
} from 'lucide-react';
import { RevisionDialog } from '../RevisionDialog';
import { AudioContent } from '@/lib/types';

interface AudioContentPanelProps {
  content: AudioContent;
  packageId: string;
  subject: string;
  unit: string;
  onRevisionRequest?: (feedback: string, priority: 'low' | 'medium' | 'high') => void;
  isSubmittingRevision?: boolean;
}

export function AudioContentPanel({ 
  content, 
  packageId, 
  subject, 
  unit, 
  onRevisionRequest,
  isSubmittingRevision = false 
}: AudioContentPanelProps) {
  const [approved, setApproved] = useState(false);
  const [isPlaying, setIsPlaying] = useState(false);
  const [currentTime, setCurrentTime] = useState(0);
  const [duration, setDuration] = useState(0);
  const [volume, setVolume] = useState(1);
  const [isMuted, setIsMuted] = useState(false);
  const [isLoaded, setIsLoaded] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [showRevisionDialog, setShowRevisionDialog] = useState(false);
  
  const audioRef = useRef<HTMLAudioElement>(null);

  const handleRevisionRequest = (feedback: string, priority: 'low' | 'medium' | 'high') => {
    if (onRevisionRequest) {
      onRevisionRequest(feedback, priority);
    }
  };

  const formatDuration = (seconds: number) => {
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  const getAudioUrl = () => {
    // Use the backend API endpoint which handles authentication and redirects to blob storage
    if (content.audio_filename) {
      // Extract package ID from filename or use a more reliable method
      const packageIdMatch = content.audio_filename.match(/pkg_(\d+)/);
      const pkgId = packageIdMatch ? packageIdMatch[0] : packageId;
      
      // Use your backend API endpoint
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
      return `${apiUrl}/api/v1/audio/${pkgId}/${content.audio_filename}`;
    }
    
    // Fallback to file path if filename not available
    if (content.audio_file_path) {
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
      const filename = content.audio_file_path.split('/').pop();
      const packageIdMatch = filename?.match(/pkg_(\d+)/);
      const pkgId = packageIdMatch ? packageIdMatch[0] : packageId;
      return `${apiUrl}/api/v1/audio/${pkgId}/${filename}`;
    }
    
    return '#';
  };

  // Audio event handlers
  useEffect(() => {
    const audio = audioRef.current;
    if (!audio) return;

    const handleLoadedData = () => {
      setIsLoaded(true);
      setDuration(audio.duration);
      setError(null);
    };

    const handleTimeUpdate = () => {
      setCurrentTime(audio.currentTime);
    };

    const handleEnded = () => {
      setIsPlaying(false);
      setCurrentTime(0);
    };

    const handleError = () => {
      setError('Failed to load audio file');
      setIsLoaded(false);
    };

    audio.addEventListener('loadeddata', handleLoadedData);
    audio.addEventListener('timeupdate', handleTimeUpdate);
    audio.addEventListener('ended', handleEnded);
    audio.addEventListener('error', handleError);

    return () => {
      audio.removeEventListener('loadeddata', handleLoadedData);
      audio.removeEventListener('timeupdate', handleTimeUpdate);
      audio.removeEventListener('ended', handleEnded);
      audio.removeEventListener('error', handleError);
    };
  }, []);

  const togglePlayPause = () => {
    const audio = audioRef.current;
    if (!audio) return;

    if (isPlaying) {
      audio.pause();
      setIsPlaying(false);
    } else {
      audio.play();
      setIsPlaying(true);
    }
  };

  const handleSeek = (percentage: number) => {
    const audio = audioRef.current;
    if (!audio) return;

    const newTime = (percentage / 100) * duration;
    audio.currentTime = newTime;
    setCurrentTime(newTime);
  };

  const handleVolumeChange = (value: number) => {
    const newVolume = value / 100;
    setVolume(newVolume);
    setIsMuted(newVolume === 0);
    
    const audio = audioRef.current;
    if (audio) {
      audio.volume = newVolume;
    }
  };

  const toggleMute = () => {
    const audio = audioRef.current;
    if (!audio) return;

    if (isMuted) {
      audio.volume = volume;
      setIsMuted(false);
    } else {
      audio.volume = 0;
      setIsMuted(true);
    }
  };

  const skip = (seconds: number) => {
    const audio = audioRef.current;
    if (!audio) return;

    const newTime = Math.max(0, Math.min(duration, currentTime + seconds));
    audio.currentTime = newTime;
    setCurrentTime(newTime);
  };

  const parseDialogueScript = (script: string) => {
    if (!script) return [];
    
    return script.split('\n').map((line, index) => {
      const trimmedLine = line.trim();
      if (!trimmedLine) return null;
      
      if (trimmedLine.startsWith('Teacher:')) {
        return {
          id: index,
          speaker: 'Teacher',
          text: trimmedLine.replace('Teacher:', '').trim(),
          type: 'teacher'
        };
      } else if (trimmedLine.startsWith('Student:')) {
        return {
          id: index,
          speaker: 'Student', 
          text: trimmedLine.replace('Student:', '').trim(),
          type: 'student'
        };
      } else if (trimmedLine.startsWith('[') && trimmedLine.endsWith(']')) {
        return {
          id: index,
          speaker: 'Direction',
          text: trimmedLine,
          type: 'direction'
        };
      } else {
        return {
          id: index,
          speaker: 'Narrator',
          text: trimmedLine,
          type: 'narrator'
        };
      }
    }).filter(Boolean);
  };

  const dialogueLines = parseDialogueScript(content.dialogue_script || '');

  return (
    <>
      <Card className="h-full flex flex-col">
        <CardHeader>
          <div className="flex items-center justify-between">
            <CardTitle className="flex items-center gap-2">
              <Volume2 className="h-5 w-5" />
              Audio Dialogue
            </CardTitle>
            <div className="flex items-center gap-2">
              <Badge variant="outline" className="flex items-center gap-1">
                <FileAudio className="h-3 w-3" />
                {formatDuration(content.duration_seconds || duration)}
              </Badge>
              <Badge variant={content.tts_status === 'success' ? 'default' : 'destructive'}>
                {content.tts_status || 'unknown'}
              </Badge>
            </div>
          </div>
        </CardHeader>

        <CardContent className="flex-1 overflow-y-auto">
          <div className="space-y-6">
            {/* Audio Player */}
            <div className="bg-gradient-to-r from-purple-50 to-blue-50 border border-purple-200 rounded-xl p-6">
              <div className="flex items-center justify-between mb-4">
                <h4 className="font-semibold text-purple-900">Audio Player</h4>
                <Button variant="outline" size="sm" disabled={!isLoaded || !!error}>
                  <Download className="mr-2 h-4 w-4" />
                  Download
                </Button>
              </div>

              {/* Hidden HTML5 Audio Element */}
              <audio
                ref={audioRef}
                src={getAudioUrl()}
                preload="metadata"
                className="hidden"
              />

              {error ? (
                <div className="text-center py-8">
                  <VolumeX className="h-12 w-12 mx-auto text-red-400 mb-3" />
                  <p className="text-red-600 text-sm">{error}</p>
                  <p className="text-xs text-red-500 mt-1">
                    File: {content.audio_filename || 'Unknown'}
                  </p>
                </div>
              ) : (
                <div className="space-y-4">
                  {/* Progress Bar */}
                  <div className="space-y-2">
                    <div 
                      className="w-full h-2 bg-gray-200 rounded-full cursor-pointer"
                      onClick={(e) => {
                        const rect = e.currentTarget.getBoundingClientRect();
                        const percent = ((e.clientX - rect.left) / rect.width) * 100;
                        handleSeek(percent);
                      }}
                    >
                      <div 
                        className="h-2 bg-purple-600 rounded-full transition-all"
                        style={{ width: `${duration > 0 ? (currentTime / duration) * 100 : 0}%` }}
                      />
                    </div>
                    <div className="flex justify-between text-xs text-purple-700">
                      <span>{formatDuration(currentTime)}</span>
                      <span>{formatDuration(duration || content.duration_seconds || 0)}</span>
                    </div>
                  </div>

                  {/* Player Controls */}
                  <div className="flex items-center justify-center space-x-4">
                    <Button 
                      variant="outline" 
                      size="sm"
                      onClick={() => skip(-10)}
                      disabled={!isLoaded}
                    >
                      <SkipBack className="h-4 w-4" />
                    </Button>

                    <Button
                      variant="default"
                      size="lg"
                      onClick={togglePlayPause}
                      disabled={!isLoaded}
                      className="rounded-full w-12 h-12"
                    >
                      {isPlaying ? (
                        <Pause className="h-6 w-6" />
                      ) : (
                        <Play className="h-6 w-6 ml-0.5" />
                      )}
                    </Button>

                    <Button 
                      variant="outline" 
                      size="sm"
                      onClick={() => skip(10)}
                      disabled={!isLoaded}
                    >
                      <SkipForward className="h-4 w-4" />
                    </Button>
                  </div>

                  {/* Volume Controls */}
                  <div className="flex items-center space-x-3">
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={toggleMute}
                    >
                      {isMuted || volume === 0 ? (
                        <VolumeX className="h-4 w-4" />
                      ) : volume < 0.5 ? (
                        <Volume1 className="h-4 w-4" />
                      ) : (
                        <Volume2 className="h-4 w-4" />
                      )}
                    </Button>
                    <div 
                      className="flex-1 h-2 bg-gray-200 rounded-full cursor-pointer"
                      onClick={(e) => {
                        const rect = e.currentTarget.getBoundingClientRect();
                        const percent = ((e.clientX - rect.left) / rect.width) * 100;
                        handleVolumeChange(percent);
                      }}
                    >
                      <div 
                        className="h-2 bg-purple-600 rounded-full transition-all"
                        style={{ width: `${isMuted ? 0 : volume * 100}%` }}
                      />
                    </div>
                    <span className="text-xs text-purple-700 w-8">
                      {Math.round((isMuted ? 0 : volume) * 100)}%
                    </span>
                  </div>
                </div>
              )}

              {/* Voice Configuration */}
              <div className="mt-6 pt-4 border-t border-purple-200">
                <div className="grid grid-cols-2 gap-4">
                  <div className="flex items-center gap-2">
                    <div className="w-3 h-3 bg-blue-500 rounded-full"></div>
                    <div>
                      <div className="text-sm font-medium">Teacher Voice</div>
                      <div className="text-xs text-purple-600">
                        {content.voice_config?.teacher_voice || 'Default'}
                      </div>
                    </div>
                  </div>
                  <div className="flex items-center gap-2">
                    <div className="w-3 h-3 bg-green-500 rounded-full"></div>
                    <div>
                      <div className="text-sm font-medium">Student Voice</div>
                      <div className="text-xs text-purple-600">
                        {content.voice_config?.student_voice || 'Default'}
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>

            {/* Dialogue Script */}
            <div>
              <h4 className="font-semibold text-lg mb-3 flex items-center gap-2">
                <Mic className="h-5 w-5" />
                Dialogue Script
              </h4>
              
              <div className="bg-white border rounded-lg max-h-80 overflow-y-auto">
                {dialogueLines.length > 0 ? (
                  <div className="p-4 space-y-3">
                    {dialogueLines.map((line) => (
                      <div key={line.id} className={`flex gap-3 ${
                        line.type === 'teacher' ? 'items-start' : 
                        line.type === 'student' ? 'items-start' : 'items-center'
                      }`}>
                        {line.type === 'teacher' && (
                          <>
                            <Badge variant="default" className="bg-blue-600 text-white text-xs mt-0.5">
                              Teacher
                            </Badge>
                            <p className="text-sm leading-relaxed flex-1 font-medium">
                              {line.text}
                            </p>
                          </>
                        )}
                        {line.type === 'student' && (
                          <>
                            <Badge variant="outline" className="text-xs mt-0.5 border-green-500 text-green-700">
                              Student
                            </Badge>
                            <p className="text-sm leading-relaxed flex-1 text-gray-700">
                              {line.text}
                            </p>
                          </>
                        )}
                        {line.type === 'direction' && (
                          <p className="text-sm text-gray-500 italic text-center w-full">
                            {line.text}
                          </p>
                        )}
                        {line.type === 'narrator' && (
                          <p className="text-sm text-gray-600 w-full">
                            {line.text}
                          </p>
                        )}
                      </div>
                    ))}
                  </div>
                ) : (
                  <div className="p-8 text-center text-muted-foreground">
                    <Mic className="h-8 w-8 mx-auto mb-2 opacity-50" />
                    <p>No dialogue script available</p>
                  </div>
                )}
              </div>
            </div>

            {/* Audio Quality Analysis */}
            <div className="bg-gray-50 rounded-lg p-4">
              <h5 className="font-medium text-sm mb-3">Audio Analysis</h5>
              <div className="grid grid-cols-2 gap-4 text-sm">
                <div className="space-y-2">
                  <div className="flex justify-between">
                    <span className="text-muted-foreground">Duration:</span>
                    <span className="font-medium">{formatDuration(content.duration_seconds || 0)}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-muted-foreground">Status:</span>
                    <Badge variant={content.tts_status === 'success' ? 'default' : 'destructive'} className="text-xs">
                      {content.tts_status || 'Unknown'}
                    </Badge>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-muted-foreground">File Size:</span>
                    <span className="font-medium">~{Math.round((content.duration_seconds || 0) * 32)}KB</span>
                  </div>
                </div>
                <div className="space-y-2">
                  <div className="flex justify-between">
                    <span className="text-muted-foreground">Script Length:</span>
                    <span className="font-medium">
                      {content.dialogue_script ? content.dialogue_script.split(' ').length : 0} words
                    </span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-muted-foreground">Speaking Rate:</span>
                    <span className="font-medium">
                      {content.dialogue_script && content.duration_seconds ? 
                        Math.round((content.dialogue_script.split(' ').length / content.duration_seconds) * 60) : 0
                      } wpm
                    </span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-muted-foreground">Dialogue Lines:</span>
                    <span className="font-medium">{dialogueLines.length}</span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </CardContent>

        <CardFooter className="flex justify-between border-t">
          <div className="flex gap-2">
            <Button variant="outline" size="sm">
              <MessageSquare className="mr-2 h-4 w-4" />
              Add Note
            </Button>
            <Button 
              variant="outline" 
              size="sm" 
              onClick={() => setShowRevisionDialog(true)}
              disabled={isSubmittingRevision}
            >
              <RotateCcw className="mr-2 h-4 w-4" />
              Request Changes
            </Button>
          </div>
          <Button 
            size="sm" 
            variant={approved ? "default" : "outline"}
            onClick={() => setApproved(!approved)}
          >
            <Check className="mr-2 h-4 w-4" />
            {approved ? 'Approved' : 'Approve'}
          </Button>
        </CardFooter>
      </Card>

      {/* Revision Dialog */}
      <RevisionDialog
        isOpen={showRevisionDialog}
        onClose={() => setShowRevisionDialog(false)}
        componentType="audio"
        onSubmit={handleRevisionRequest}
        isSubmitting={isSubmittingRevision}
      />
    </>
  );
}