
'use client';

import React, { useState, useRef, useCallback, useEffect } from 'react';
import {
  Sidebar,
  SidebarProvider,
  SidebarInset,
  SidebarHeader,
  SidebarContent,
  SidebarFooter,
  SidebarTrigger,
} from '@/components/ui/sidebar';
import { Separator } from '@/components/ui/separator';
import { useToast } from '@/hooks/use-toast';
import { Paintbrush } from 'lucide-react';
import type { Story } from '@/lib/types';
import DrawingCanvas, { type DrawingCanvasRef } from '@/components/drawing-canvas';
import { StoryList } from '@/components/story-list';
import { DrawingToolbar } from '@/components/drawing-toolbar';
import { PlaybackControls } from '@/components/playback-controls';
import { Card } from '@/components/ui/card';
import { useRouter } from 'next/navigation';
import { useAuth } from '@/hooks/use-auth';
import { Skeleton } from '@/components/ui/skeleton';
import { buildApiUrl } from '@/lib/api-config';

export default function DrawPage() {
  const [selectedStory, setSelectedStory] = useState<Story | null>(null);
  const [loadingStory, setLoadingStory] = useState(true);
  const [brushColor, setBrushColor] = useState('#000000');
  const [brushSize, setBrushSize] = useState(5);
  const [currentIndex, setCurrentIndex] = useState(0);
  
  const drawingCanvasRef = useRef<DrawingCanvasRef>(null);
  const audioRef = useRef<HTMLAudioElement>(null);
  const { toast } = useToast();
  const router = useRouter();
  const { firebaseToken } = useAuth();

  useEffect(() => {
    const storedStoryId = sessionStorage.getItem('selectedStoryId');
    if (!storedStoryId) {
      router.push('/home');
      return;
    }

    if (firebaseToken) {
      setLoadingStory(true);
      fetch(buildApiUrl(`/api/chats/${storedStoryId}`), {
          headers: {
              'Authorization': `Bearer ${firebaseToken}`
          }
      })
      .then(response => {
          if (!response.ok) {
              throw new Error('Failed to fetch story details');
          }
          return response.json();
      })
      .then(fullStoryData => {
          console.log('Fetched Story Data:', fullStoryData);
          setSelectedStory(fullStoryData);
          setCurrentIndex(0); // Reset index for new story
      })
      .catch(error => {
          console.error(error);
          toast({
              variant: 'destructive',
              title: 'Error',
              description: 'Could not load the story. Please try again.',
          });
          router.push('/home');
      })
      .finally(() => {
          setLoadingStory(false);
      });
    }
  }, [firebaseToken, router, toast]);
  
  const handleSelectStory = useCallback((story: Story) => {
    sessionStorage.setItem('selectedStoryId', story.chat_id);
    window.location.reload(); 
  }, []);
  
  const handleClearCanvas = () => {
    drawingCanvasRef.current?.clearCanvas();
  }

  const handleUndo = () => {
    drawingCanvasRef.current?.undo();
  }
  
  const messagesCount = selectedStory?.messages?.length || 0;

  const handleNext = () => {
    if (currentIndex < messagesCount - 1) {
      setCurrentIndex(currentIndex + 1);
    }
  }

  const handlePrevious = () => {
    if (currentIndex > 0) {
      setCurrentIndex(currentIndex - 1);
    }
  }

  const currentMessage = selectedStory?.messages?.[currentIndex];
  const currentSubmit = selectedStory?.subimits?.[currentIndex];

  useEffect(() => {
    if (audioRef.current && currentMessage?.audio) {
      audioRef.current.src = currentMessage.audio;
      audioRef.current.load();
    } else if (audioRef.current) {
      audioRef.current.removeAttribute('src');
      audioRef.current.load();
    }
  }, [currentMessage]);

  const showDrawingCanvas = !currentSubmit;
  
  if (loadingStory) {
     return (
       <div className="flex h-screen w-full items-center justify-center">
         <div className="flex flex-col items-center gap-4">
           <Skeleton className="h-24 w-24 rounded-full" />
           <Skeleton className="h-8 w-64" />
           <p className="text-lg font-semibold">Loading your amazing story...</p>
         </div>
       </div>
     );
  }
  
  if (!selectedStory) {
    router.push('/home');
    return null; 
  }

  return (
    <SidebarProvider>
      <Sidebar>
        <SidebarHeader>
          <div className="flex items-center gap-2 p-2">
            <Paintbrush className="w-8 h-8 text-primary" />
            <h1 className="text-2xl font-bold font-headline">Story Canvas</h1>
          </div>
        </SidebarHeader>
        <Separator />
        <SidebarContent>
          <StoryList onSelectStory={handleSelectStory} selectedStoryId={selectedStory?.chat_id} />
        </SidebarContent>
        <SidebarFooter>
          <div className="p-4 text-xs text-muted-foreground">
            &copy; 2024 Story Canvas
          </div>
        </SidebarFooter>
      </Sidebar>
      <SidebarInset>
        <div className="flex flex-col h-screen p-4 gap-4 bg-background">
          <header className="flex items-center justify-between">
            <h2 className="text-2xl font-bold font-headline">
              {selectedStory?.title || 'Loading...'}
            </h2>
            <SidebarTrigger />
          </header>

          <main className="flex-1 grid grid-cols-1 md:grid-cols-2 gap-4 min-h-0">
            <div className="flex flex-col gap-4">
                <div className="flex justify-center items-center min-h-[100px]">
                    <PlaybackControls 
                      audioRef={audioRef} 
                      onNext={handleNext} 
                      onPrevious={handlePrevious}
                      canNext={currentIndex < messagesCount - 1}
                      canPrevious={currentIndex > 0}
                    />
                </div>
                <Card className="flex-1 relative w-full overflow-hidden rounded-2xl shadow-lg border-4 border-foreground/10 min-h-0">
                  <DrawingCanvas
                    storyImageUrl={currentMessage?.image}
                    isDrawingCanvas={false}
                  />
                </Card>
            </div>
            <div className="flex flex-col gap-4">
                <div className="flex justify-center items-center min-h-[100px]">
                  {showDrawingCanvas && (
                    <DrawingToolbar
                        brushColor={brushColor}
                        setBrushColor={setBrushColor}
                        brushSize={brushSize}
                        setBrushSize={setBrushSize}
                        clearCanvas={handleClearCanvas}
                        undo={handleUndo}
                    />
                  )}
                </div>
                <Card className="flex-1 relative w-full overflow-hidden rounded-2xl shadow-lg border-4 border-foreground/10 min-h-0">
                    <DrawingCanvas
                        ref={drawingCanvasRef}
                        brushColor={brushColor}
                        brushSize={brushSize}
                        isDrawingCanvas={!!showDrawingCanvas}
                        storyImageUrl={currentSubmit?.image}
                    />
                </Card>
            </div>
          </main>
          
          <audio ref={audioRef} />
        </div>
      </SidebarInset>
    </SidebarProvider>
  );
}
