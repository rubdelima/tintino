
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
import { useAuth } from '@/hooks/use-auth';
import { useToast } from '@/hooks/use-toast';
import { getApiEndpoint } from '@/lib/api-config';

const appName = process.env.NEXT_PUBLIC_APP_NAME || 'Louie';

export default function HomePage() {
  const [isRecording, setIsRecording] = useState(false);
  const [audioBlob, setAudioBlob] = useState<Blob | null>(null);
  const [selectedStory, setSelectedStory] = useState<Story | null>(null);
  const [isPlayingAudio, setIsPlayingAudio] = useState(false);
  const [isSending, setIsSending] = useState(false);
  const [availableVoices, setAvailableVoices] = useState<string[]>([]);
  const [selectedVoice, setSelectedVoice] = useState<string>('Kore');
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const audioRef = useRef<HTMLAudioElement>(null);
  const router = useRouter();
  const { logout, user, firebaseToken } = useAuth();
  const { toast } = useToast();

  // ...restante do código...

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
            title: 'Erro de Gravação',
            description: 'Não foi possível iniciar a gravação. Certifique-se de ter um microfone e de ter concedido permissão para usá-lo.',
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
      formData.append('voice_name', selectedVoice || 'Kore');

      const response = await fetch(getApiEndpoint('CHATS'), {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${firebaseToken}`,
        },
        body: formData,
      });

      if (!response.ok) {
        throw new Error('Falha ao criar uma nova história.');
      }
      
      const newStory = await response.json();
      sessionStorage.setItem('selectedStoryId', newStory.chat_id);
      router.push('/draw');

    } catch (error: any) {
      toast({
        variant: 'destructive',
        title: 'Falha no Upload',
        description: error.message || 'Não foi possível criar a história. Tente novamente.',
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
            <Image
              src="/icon.png"
              width={32}
              height={32}
              alt="Ícone do Louie"
              className="w-8 h-8"
            />
            <h1 className="text-2xl font-bold font-headline">{appName}</h1>
          </div>
        </SidebarHeader>
        <Separator />
        <SidebarContent>
          <StoryList onSelectStory={handleSelectStory} selectedStoryId={selectedStory?.chat_id} onVoicesLoaded={setAvailableVoices} />
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
            <h2 className="text-3xl font-bold font-headline">
              Começar uma Nova História
            </h2>
            <SidebarTrigger />
          </header>
          <main className="flex-1 flex flex-col items-center justify-center gap-8 text-center">
            <div className="relative w-64 h-64">
              <Image
                src="/icon.png"
                width={256}
                height={256}
                alt="Mascote amigável do Louie"
                className="object-contain"
              />
            </div>
            <Card className="p-8 rounded-2xl shadow-lg border-2 border-primary/20 max-w-lg w-full">
              <CardContent className="p-0">
                <div className="flex flex-col items-center gap-4">
                  <label htmlFor="voice-select" className="text-base font-medium text-primary">Escolha a voz da narração:</label>
                  <select
                    id="voice-select"
                    className="border rounded-lg px-3 py-2 text-base focus:outline-primary"
                    value={selectedVoice}
                    onChange={e => setSelectedVoice(e.target.value)}
                    disabled={isRecording || isSending}
                  >
                    {availableVoices.map((voice) => (
                      <option key={voice} value={voice}>{voice}</option>
                    ))}
                  </select>
                </div>
                {!audioBlob ? (
                  <div className="flex flex-col items-center gap-4 mt-4">
                    <p className="text-lg text-muted-foreground">
                      {isRecording ? 'Gravando sua história incrível...' : "Pronto para contar uma história? Aperte o botão para começar!"}
                    </p>
                    <Button onClick={handleRecord} className="btn-sticker h-24 w-24 p-0 rounded-full">
                      {isRecording ? <Square size={48} /> : <Mic size={48} />}
                    </Button>
                  </div>
                ) : (
                  <div className="flex flex-col items-center gap-4 mt-4">
                     <p className="text-lg text-muted-foreground">
                      Ótima história! Você pode ouvir uma prévia ou enviá-la para ser desenhada.
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
