
'use client';

import React, { useState, useRef, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import Image from 'next/image';
import { Button } from '@/components/ui/button';
import {
  Sidebar,
  SidebarProvider,
  SidebarInset,
  SidebarHeader,
  SidebarContent,
  SidebarFooter,
  SidebarTrigger,
} from '@/components/ui/sidebar';
import { Card, CardContent } from '@/components/ui/card';
import { Separator } from '@/components/ui/separator';
import { StoryList } from '@/components/story-list';
import type { Story } from '@/lib/types';
import { Mic, Play, Send, Square, RefreshCcw, Pause, LogOut, Loader2 } from 'lucide-react';
import { useAuth } from '@/hooks/use-auth.tsx';
import { useToast } from '@/hooks/use-toast';
import { getApiEndpoint } from '@/lib/api-config';

export default function HomePage() {
  const [isRecording, setIsRecording] = useState(false);
  const [audioBlob, setAudioBlob] = useState<Blob | null>(null);
  const [selectedStory, setSelectedStory] = useState<Story | null>(null);
  const [isPlayingAudio, setIsPlayingAudio] = useState(false);
  const [isSending, setIsSending] = useState(false);
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const audioRef = useRef<HTMLAudioElement>(null);
  const router = useRouter();
  const { logout, user, firebaseToken } = useAuth();
  const { toast } = useToast();

  const handleRecord = async () => {
    if (isRecording) {
      mediaRecorderRef.current?.stop();
      setIsRecording(false);
    } else {
      try {
        const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
        mediaRecorderRef.current = new MediaRecorder(stream);
        mediaRecorderRef.current.ondataavailable = (event) => {
          setAudioBlob(event.data);
        };
        mediaRecorderRef.current.start();
        setIsRecording(true);
        setAudioBlob(null);
      } catch (err) {
        toast({
            variant: 'destructive',
            title: 'Recording Error',
            description: 'Could not start recording. Please make sure you have a microphone and have granted permission to use it.',
        })
      }
    }
  };
  
  const handleRecordAgain = () => {
    setAudioBlob(null);
    handleRecord();
  }

  const handlePreview = () => {
    if (audioBlob && audioRef.current) {
        if (isPlayingAudio) {
            audioRef.current.pause();
        } else {
            const url = URL.createObjectURL(audioBlob);
            audioRef.current.src = url;
            audioRef.current.play();
        }
    }
  };

  const handleSend = async () => {
    if (!audioBlob || !firebaseToken) return;

    setIsSending(true);
    try {
      const formData = new FormData();
      formData.append('voice_audio', audioBlob, 'story.wav');

      const response = await fetch(getApiEndpoint('CHATS'), {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${firebaseToken}`,
        },
        body: formData,
      });

      if (!response.ok) {
        throw new Error('Failed to create a new story.');
      }
      
      const newStory = await response.json();
      sessionStorage.setItem('selectedStoryId', newStory.chat_id);
      router.push('/draw');

    } catch (error: any) {
      toast({
        variant: 'destructive',
        title: 'Upload Failed',
        description: error.message || 'Could not create the story. Please try again.',
      });
    } finally {
      setIsSending(false);
    }
  };

  const handleSelectStory = (story: Story) => {
    sessionStorage.setItem('selectedStoryId', story.chat_id);
    router.push('/draw');
  };
  
  useEffect(() => {
    const audioElement = audioRef.current;
    if (!audioElement) return;
    
    const onPlay = () => setIsPlayingAudio(true);
    const onPause = () => setIsPlayingAudio(false);
    
    audioElement.addEventListener('play', onPlay);
    audioElement.addEventListener('pause', onPause);
    audioElement.addEventListener('ended', onPause);
    
    return () => {
        audioElement.removeEventListener('play', onPlay);
        audioElement.removeEventListener('pause', onPause);
        audioElement.removeEventListener('ended', onPause);
    }
  }, []);

  return (
    <SidebarProvider>
      <Sidebar>
        <SidebarHeader>
          <div className="flex items-center gap-2 p-2">
            <svg
              xmlns="http://www.w3.org/2000/svg"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth="2"
              strokeLinecap="round"
              strokeLinejoin="round"
              className="w-8 h-8 text-primary"
            >
              <path d="M12 12a5 5 0 1 0-5-5 5 5 0 0 0 5 5z" />
              <path d="M12 12a5 5 0 1 0 5-5 5 5 0 0 0-5 5z" />
              <path d="M12 12a5 5 0 1 0-5 5 5 5 0 0 0 5 5z" />
              <path d="M12 12a5 5 0 1 0 5 5 5 5 0 0 0-5 5z" />
              <path d="M22 12c0 5.523-4.477 10-10 10S2 17.523 2 12 6.477 2 12 2s10 4.477 10 10z" />
            </svg>
            <h1 className="text-2xl font-bold font-headline">Story Canvas</h1>
          </div>
        </SidebarHeader>
        <Separator />
        <SidebarContent>
          <StoryList onSelectStory={handleSelectStory} selectedStoryId={selectedStory?.chat_id} />
        </SidebarContent>
        <SidebarFooter>
          <div className="flex flex-col gap-2 p-2">
            {user && (
              <div className='p-2 text-sm'>
                Welcome, {user.displayName || user.email}
              </div>
            )}
            <Button onClick={logout} variant="outline" className="w-full justify-start gap-2">
              <LogOut size={16} />
              Sign Out
            </Button>
            <div className="p-2 text-xs text-muted-foreground">
              &copy; 2024 Story Canvas
            </div>
          </div>
        </SidebarFooter>
      </Sidebar>
      <SidebarInset>
        <div className="flex flex-col h-screen p-4 gap-4 bg-background">
          <header className="flex items-center justify-between">
            <h2 className="text-3xl font-bold font-headline">
              Start a New Story
            </h2>
            <SidebarTrigger />
          </header>
          <main className="flex-1 flex flex-col items-center justify-center gap-8 text-center">
            <div className="relative w-64 h-64">
              <Image
                src="https://placehold.co/400x400.png"
                width={256}
                height={256}
                alt="Friendly fish mascot"
                className="object-contain"
                data-ai-hint="artist fish mascot"
              />
            </div>
            <Card className="p-8 rounded-2xl shadow-lg border-2 border-primary/20 max-w-lg w-full">
              <CardContent className="p-0">
                {!audioBlob ? (
                  <div className="flex flex-col items-center gap-4">
                    <p className="text-lg text-muted-foreground">
                      {isRecording ? 'Recording your amazing story...' : "Ready to tell a story? Press the button to start!"}
                    </p>
                    <Button onClick={handleRecord} className="btn-sticker h-24 w-24 p-0 rounded-full">
                      {isRecording ? <Square size={48} /> : <Mic size={48} />}
                    </Button>
                  </div>
                ) : (
                  <div className="flex flex-col items-center gap-4">
                     <p className="text-lg text-muted-foreground">
                      Great story! You can preview it or send it to be drawn.
                    </p>
                    <div className="flex gap-4">
                      <Button onClick={handlePreview} className="btn-sticker h-20 w-20 p-0" disabled={isSending}>
                        {isPlayingAudio ? <Pause size={40} /> : <Play size={40} className="ml-1" />}
                      </Button>
                      <Button onClick={handleRecordAgain} className="btn-sticker h-20 w-20 p-0" variant="outline" disabled={isSending}>
                        <RefreshCcw size={40} />
                      </Button>
                      <Button onClick={handleSend} className="btn-sticker h-20 w-20 p-0" variant="secondary" disabled={isSending}>
                        {isSending ? <Loader2 size={40} className="animate-spin" /> : <Send size={40} />}
                      </Button>
                    </div>
                  </div>
                )}
              </CardContent>
            </Card>
          </main>
        </div>
      </SidebarInset>
      <audio ref={audioRef} />
    </SidebarProvider>
  );
}
