
'use client';

import React, { useState, useRef, useCallback, useEffect } from 'react';
import Image from 'next/image';
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
import { Button } from '@/components/ui/button';
import { useToast } from '@/hooks/use-toast';
import { Paintbrush, LogOut } from 'lucide-react';
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
  const [isPlayingAudio, setIsPlayingAudio] = useState(false);
  
  const drawingCanvasRef = useRef<DrawingCanvasRef>(null);
  const audioRef = useRef<HTMLAudioElement>(null);
  const { toast } = useToast();
  const router = useRouter();
  const { firebaseToken, logout, user } = useAuth();

  useEffect(() => {
    let isMounted = true;
    
    const storedStoryId = sessionStorage.getItem('selectedStoryId');
    if (!storedStoryId) {
      router.push('/');
      return;
    }

    if (firebaseToken) {
      if (isMounted) {
        setLoadingStory(true);
      }
      
      const apiUrl = buildApiUrl(`/api/chats/${storedStoryId}`);
      fetch(apiUrl, {
          headers: {
              'Authorization': `Bearer ${firebaseToken}`
          }
      })
      .then(response => {
          if (!response.ok) {
              throw new Error('Falha ao carregar detalhes da história');
          }
          return response.json();
      })
      .then(fullStoryData => {
          if (isMounted) {
            console.log('Loaded story:', fullStoryData.title, 'Messages:', fullStoryData.messages?.length || 0);
            setSelectedStory(fullStoryData);
            // Set current index to last message by default
            const lastIndex = fullStoryData.messages?.length > 0 ? fullStoryData.messages.length - 1 : 0;
            setCurrentIndex(lastIndex);
          }
      })
      .catch(error => {
          if (isMounted) {
            console.error(error);
            toast({
                variant: 'destructive',
                title: 'Erro',
                description: 'Não foi possível carregar a história. Tente novamente.',
            });
            router.push('/');
          }
      })
      .finally(() => {
          if (isMounted) {
            setLoadingStory(false);
          }
      });
    }
    
    return () => {
      isMounted = false;
    };
  }, [firebaseToken, router, toast]);
  
  // Navigation functions
  const handlePreviousMessage = useCallback(() => {
    if (selectedStory?.messages && currentIndex > 0) {
      setCurrentIndex(currentIndex - 1);
    }
  }, [currentIndex, selectedStory?.messages]);

  const handleNextMessage = useCallback(() => {
    if (selectedStory?.messages && currentIndex < selectedStory.messages.length - 1) {
      setCurrentIndex(currentIndex + 1);
    }
  }, [currentIndex, selectedStory?.messages]);

  // Audio playback functions
  const handlePlayAudio = useCallback(() => {
    if (selectedStory?.messages && selectedStory.messages[currentIndex]?.audio) {
      const audioUrl = selectedStory.messages[currentIndex].audio;
      if (audioRef.current) {
        audioRef.current.src = audioUrl;
        audioRef.current.play();
        setIsPlayingAudio(true);
      }
    }
  }, [selectedStory?.messages, currentIndex]);

  const handleStopAudio = useCallback(() => {
    if (audioRef.current) {
      audioRef.current.pause();
      audioRef.current.currentTime = 0;
      setIsPlayingAudio(false);
    }
  }, []);

  // Audio event handlers
  useEffect(() => {
    const audio = audioRef.current;
    if (audio) {
      const handleEnded = () => setIsPlayingAudio(false);
      const handleError = () => setIsPlayingAudio(false);
      
      audio.addEventListener('ended', handleEnded);
      audio.addEventListener('error', handleError);
      
      return () => {
        audio.removeEventListener('ended', handleEnded);
        audio.removeEventListener('error', handleError);
      };
    }
  }, []);
  
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
  
  // Current message data
  const messagesCount = selectedStory?.messages?.length || 0;
  const currentMessage = selectedStory?.messages?.[currentIndex];
  const currentSubmit = selectedStory?.subimits?.[currentIndex];

  // Navigation states
  const canPrevious = currentIndex > 0;
  const canNext = currentIndex < messagesCount - 1;

  // Check if story has no messages
  const hasNoMessages = messagesCount === 0;

  useEffect(() => {
    if (audioRef.current && currentMessage?.audio) {
      audioRef.current.src = currentMessage.audio;
      audioRef.current.load();
    } else if (audioRef.current) {
      audioRef.current.removeAttribute('src');
      audioRef.current.load();
    }
  }, [currentMessage]);

  // Debug current message (mantenha por enquanto para verificar quando houver mensagens)
  useEffect(() => {
    if (messagesCount > 0) {
      console.log('Current message:', {
        currentIndex,
        image: currentMessage?.image,
        audio: currentMessage?.audio
      });
    }
  }, [currentIndex, currentMessage, messagesCount]);

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
    router.push('/');
    return null; 
  }

  return (
    <SidebarProvider>
      <Sidebar>
        <SidebarHeader>
          <div className="flex items-center gap-2 p-2">
            <Image
              src="/icon.png"
              width={32}
              height={32}
              alt="Ícone do Louie"
              className="w-8 h-8"
            />
            <h1 className="text-2xl font-bold font-headline">{process.env.NEXT_PUBLIC_APP_NAME || 'Louie'}</h1>
          </div>
        </SidebarHeader>
        <Separator />
        <SidebarContent>
          <StoryList onSelectStory={handleSelectStory} selectedStoryId={selectedStory?.chat_id} showNewStoryButton={true} />
        </SidebarContent>
        <SidebarFooter>
          <div className="flex flex-col gap-2 p-2">
            {user && (
              <div className='p-2 text-sm'>
                Bem-vindo, {user.displayName || user.email}
              </div>
            )}
            <Button onClick={logout} variant="outline" className="w-full justify-start gap-2">
              <LogOut size={16} />
              Sair
            </Button>
            <div className="p-2 text-xs text-muted-foreground">
              &copy; 2024 {process.env.NEXT_PUBLIC_APP_NAME || 'Louie'}
            </div>
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
                    {!hasNoMessages ? (
                        <PlaybackControls 
                          audioRef={audioRef} 
                          onNext={handleNextMessage} 
                          onPrevious={handlePreviousMessage}
                          canNext={canNext}
                          canPrevious={canPrevious}
                        />
                    ) : (
                        <div className="text-center text-muted-foreground">
                            <p className="text-sm">Nenhuma mensagem para navegar</p>
                        </div>
                    )}
                </div>
                <Card className="flex-1 relative w-full overflow-hidden rounded-2xl shadow-lg border-4 border-foreground/10 min-h-0">
                  <DrawingCanvas
                    storyImageUrl={currentMessage?.image}
                    isDrawingCanvas={false}
                    brushColor={brushColor}
                    brushSize={brushSize}
                    hasNoMessages={hasNoMessages}
                    storyTitle={selectedStory?.title}
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
      {/* Hidden audio element */}
      <audio ref={audioRef} preload="metadata" />
    </SidebarProvider>
  );
}
