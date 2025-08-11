
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
import { LogOut, Send, Loader2 } from 'lucide-react';
import type { Story, Message, SubmitImageMessage } from '@/lib/types';
import DrawingCanvas, { type DrawingCanvasRef } from '@/components/drawing-canvas';
import { StoryList } from '@/components/story-list';
import { DrawingToolbar } from '@/components/drawing-toolbar';
import { PlaybackControls } from '@/components/playback-controls';
import { Card } from '@/components/ui/card';
import { useRouter } from 'next/navigation';
import { useAuth } from '@/hooks/use-auth';
import { Skeleton } from '@/components/ui/skeleton';
import { buildApiUrl, getWebSocketUrl } from '@/lib/api-config';

export default function DrawPage() {
  const [selectedStory, setSelectedStory] = useState<Story | null>(null);
  const [loadingStory, setLoadingStory] = useState(true);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [brushColor, setBrushColor] = useState('#000000');
  const [brushSize, setBrushSize] = useState(5);
  const [isErasing, setIsErasing] = useState(false);
  const [currentIndex, setCurrentIndex] = useState(0);
  
  const drawingCanvasRef = useRef<DrawingCanvasRef>(null);
  const audioRef = useRef<HTMLAudioElement>(null);
  const feedbackAudioRef = useRef<HTMLAudioElement>(null);
  const wsRef = useRef<WebSocket | null>(null);

  const { toast } = useToast();
  const router = useRouter();
  const { firebaseToken, logout, user } = useAuth();

  const cleanupWebSocket = () => {
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      wsRef.current.close();
    }
    wsRef.current = null;
  };

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
      
      const apiUrl = buildApiUrl(`/api/chats/${storedStoryId}/`);
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
            console.log("Fetched Story Data:", fullStoryData);
            setSelectedStory(fullStoryData);
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
      cleanupWebSocket();
    };
  }, [firebaseToken, router, toast]);
  
  const handlePreviousMessage = useCallback(() => {
    if (selectedStory?.messages && currentIndex > 0) {
      const newIndex = currentIndex - 1;
      setCurrentIndex(newIndex);
      drawingCanvasRef.current?.clearCanvas();
    }
  }, [currentIndex, selectedStory?.messages]);

  const handleNextMessage = useCallback(() => {
    if (selectedStory?.messages && currentIndex < selectedStory.messages.length - 1) {
      const newIndex = currentIndex + 1;
      setCurrentIndex(newIndex);
      drawingCanvasRef.current?.clearCanvas();
    }
  }, [currentIndex, selectedStory?.messages]);
  
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

  const toggleEraser = () => {
    setIsErasing(!isErasing);
  }

  const handleSubmitDrawing = async () => {
    if (!drawingCanvasRef.current || !selectedStory || !firebaseToken) return;
    
    const drawingDataUri = drawingCanvasRef.current.exportAsDataUri();
    if (!drawingDataUri) {
        toast({
            variant: 'destructive',
            title: 'Erro',
            description: 'Não foi possível exportar o desenho.',
        });
        return;
    }

    setIsSubmitting(true);
    cleanupWebSocket(); 

    const wsUrl = getWebSocketUrl(`/api/chats/${selectedStory.chat_id}/submit_image_ws/`);
    const ws = new WebSocket(wsUrl);
    wsRef.current = ws;

    ws.onopen = () => {
        ws.send(JSON.stringify({
            type: 'auth',
            token: firebaseToken
        }));
        
        ws.send(JSON.stringify({
            type: 'submit_image',
            image_data: drawingDataUri.split(',')[1], 
            mime_type: 'image/png'
        }));
    };

    ws.onmessage = (event) => {
        const data = JSON.parse(event.data);
        
        if (data.type === 'feedback') {
            const feedbackMessage: SubmitImageMessage = data.message;
            
            if (feedbackAudioRef.current && feedbackMessage.audio) {
                feedbackAudioRef.current.src = feedbackMessage.audio;
                feedbackAudioRef.current.play();
            }

            setSelectedStory(prevStory => {
                if (!prevStory) return null;
                const newSubmits = [...(prevStory.subimits || [])];
                const existingSubmitIndex = newSubmits.findIndex(s => s.message_index === feedbackMessage.message_index);
                if (existingSubmitIndex > -1) {
                    newSubmits[existingSubmitIndex] = feedbackMessage;
                } else {
                    newSubmits.push(feedbackMessage);
                }
                return { ...prevStory, subimits: newSubmits };
            });

            if (!feedbackMessage.data.is_correct) {
                setIsSubmitting(false);
                toast({
                    variant: 'destructive',
                    title: 'Tente Novamente',
                    description: feedbackMessage.data.feedback,
                });
            } else {
                 toast({
                    title: 'Ótimo Trabalho!',
                    description: 'Seu desenho está perfeito! Pegando a próxima parte da história...',
                });
            }

        } else if (data.type === 'new_message') {
            const newMessage: Message = data.message;
            
            setSelectedStory(prevStory => {
                if (!prevStory) return null;
                const updatedMessages = [...prevStory.messages, newMessage];
                setCurrentIndex(updatedMessages.length - 1);
                drawingCanvasRef.current?.clearCanvas();
                return { ...prevStory, messages: updatedMessages };
            });
            
            setIsSubmitting(false);

        } else if (data.type === 'error') {
            toast({
                variant: 'destructive',
                title: 'Erro de Envio',
                description: data.message,
            });
            setIsSubmitting(false);
        }
    };

    ws.onerror = (error) => {
        console.error('WebSocket Error:', error);
        toast({
            variant: 'destructive',
            title: 'Erro de Conexão',
            description: 'Não foi possível conectar ao serviço de envio de desenhos.',
        });
        setIsSubmitting(false);
    };

    ws.onclose = () => {
        // setIsSubmitting(false) is handled in other events
    };
  };
  
  const messagesCount = selectedStory?.messages?.length || 0;
  const currentMessage = selectedStory?.messages?.[currentIndex];
  const currentSubmit = selectedStory?.subimits?.find(s => s.message_index === currentMessage?.message_index);

  const canPrevious = currentIndex > 0;
  const canNext = currentIndex < messagesCount - 1;
  const isLastPage = currentIndex === messagesCount - 1;

  useEffect(() => {
    if (audioRef.current && currentMessage?.audio) {
      audioRef.current.src = currentMessage.audio;
      audioRef.current.load();
    } else if (audioRef.current) {
      audioRef.current.removeAttribute('src');
      audioRef.current.load();
    }
  }, [currentMessage]);
  
  useEffect(() => {
    if (drawingCanvasRef.current) {
      drawingCanvasRef.current.setEraser(isErasing);
    }
  }, [isErasing]);

  if (loadingStory) {
     return (
       <div className="flex h-screen w-full items-center justify-center">
         <div className="flex flex-col items-center gap-4">
           <Skeleton className="h-24 w-24 rounded-full" />
           <Skeleton className="h-8 w-64" />
           <p className="text-lg font-semibold">Carregando sua história incrível...</p>
         </div>
       </div>
     );
  }
  
  if (!selectedStory) {
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
              {/* Removido copyright */}
            </div>
          </div>
        </SidebarFooter>
      </Sidebar>
      <SidebarInset>
        <div className="flex flex-col h-screen p-4 gap-4 bg-background">
          <header className="flex items-center justify-between">
            <h2 className="text-2xl font-bold font-headline">
              {selectedStory?.title || 'Carregando...'}
            </h2>
            <SidebarTrigger />
          </header>

          <main className="flex-1 grid grid-cols-1 md:grid-cols-2 gap-4 min-h-0">
            <div className="flex flex-col gap-4">
                <div className="flex justify-center items-center min-h-[100px] gap-4">
                    {messagesCount > 0 ? (
                        <>
                          <PlaybackControls 
                            audioRef={audioRef} 
                            onNext={handleNextMessage} 
                            onPrevious={handlePreviousMessage}
                            canNext={canNext}
                            canPrevious={canPrevious}
                          />
                           <Button 
                                onClick={handleSubmitDrawing} 
                                className="btn-sticker h-16 w-16 p-0" 
                                variant="secondary" 
                                disabled={isSubmitting || !isLastPage}
                            >
                               {isSubmitting ? <Loader2 size={32} className="animate-spin" /> : <Send size={32} />}
                           </Button>
                        </>
                    ) : (
                        <div className="text-center text-muted-foreground">
                            <p className="text-sm">Esta história ainda não tem mensagens.</p>
                        </div>
                    )}
                </div>
                <Card className="flex-1 relative w-full overflow-hidden rounded-2xl shadow-lg border-4 border-foreground/10 min-h-0">
                  <DrawingCanvas
                    storyImageUrl={currentMessage?.image}
                    isDrawingCanvas={false}
                    brushColor={brushColor}
                    brushSize={brushSize}
                    hasNoMessages={messagesCount === 0}
                    storyTitle={selectedStory?.title}
                  />
                </Card>
            </div>
            <div className="flex flex-col gap-4">
              {isLastPage ? (
                <>
                  <div className="flex justify-center items-center min-h-[100px] gap-4">
                    <DrawingToolbar
                        brushColor={brushColor}
                        setBrushColor={setBrushColor}
                        brushSize={brushSize}
                        setBrushSize={setBrushSize}
                        clearCanvas={handleClearCanvas}
                        undo={handleUndo}
                        isErasing={isErasing}
                        toggleEraser={toggleEraser}
                    />
                  </div>
                  <Card className="flex-1 relative w-full overflow-hidden rounded-2xl shadow-lg border-4 border-foreground/10 min-h-0">
                      <div className="absolute inset-0 p-2">
                         <DrawingCanvas
                            ref={drawingCanvasRef}
                            brushColor={brushColor}
                            brushSize={brushSize}
                            isDrawingCanvas={true}
                            generatedImageUrl={currentSubmit?.image}
                         />
                      </div>
                  </Card>
                </>
              ) : (
                <>
                  <div className="flex justify-center items-center min-h-[100px] gap-4">
                    <p className="text-lg font-semibold text-muted-foreground">Seu Desenho Enviado</p>
                  </div>
                  <Card className="flex-1 relative w-full overflow-hidden rounded-2xl shadow-lg border-4 border-foreground/10 min-h-0">
                      {currentSubmit?.image ? (
                        <Image
                          src={currentSubmit.image}
                          alt="Submitted drawing"
                          fill
                          className="object-contain"
                          unoptimized
                        />
                      ) : (
                        <div className="flex items-center justify-center h-full text-muted-foreground p-8 text-center">
                          <p className="text-xl font-medium">Nenhum desenho foi enviado para esta etapa.</p>
                        </div>
                      )}
                  </Card>
                </>
              )}
            </div>
          </main>
          
          <audio ref={audioRef} />
          <audio ref={feedbackAudioRef} />
        </div>
      </SidebarInset>
      <audio ref={audioRef} preload="metadata" />
    </SidebarProvider>
  );
}
