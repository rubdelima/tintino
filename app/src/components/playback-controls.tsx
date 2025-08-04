'use client';

import { useState, useEffect, RefObject } from 'react';
import { Button } from '@/components/ui/button';
import { Play, Pause, RotateCcw, RotateCw } from 'lucide-react';

interface PlaybackControlsProps {
  audioRef: RefObject<HTMLAudioElement>;
  onNext: () => void;
  onPrevious: () => void;
  canNext: boolean;
  canPrevious: boolean;
}

export function PlaybackControls({ audioRef, onNext, onPrevious, canNext, canPrevious }: PlaybackControlsProps) {
  const [isPlaying, setIsPlaying] = useState(false);
  const [isAudioAvailable, setIsAudioAvailable] = useState(false);

  const handlePlayPause = () => {
    if(!isAudioAvailable) return;
    if (isPlaying) {
      audioRef.current?.pause();
    } else {
      audioRef.current?.play().catch(e => console.error("Error playing audio:", e));
    }
  };

  useEffect(() => {
    const audioElement = audioRef.current;
    if (!audioElement) return;

    const onPlay = () => setIsPlaying(true);
    const onPause = () => setIsPlaying(false);
    const onLoadedData = () => setIsAudioAvailable(true);
    const onEmptied = () => setIsAudioAvailable(false);

    audioElement.addEventListener('play', onPlay);
    audioElement.addEventListener('pause', onPause);
    audioElement.addEventListener('ended', onPause);
    audioElement.addEventListener('loadeddata', onLoadedData);
    audioElement.addEventListener('emptied', onEmptied);
    
    // Initial check
    setIsAudioAvailable(!!audioElement.src && audioElement.readyState > 0);


    return () => {
      audioElement.removeEventListener('play', onPlay);
      audioElement.removeEventListener('pause', onPause);
      audioElement.removeEventListener('ended', onPause);
      audioElement.removeEventListener('loadeddata', onLoadedData);
      audioElement.removeEventListener('emptied', onEmptied);
    };
  }, [audioRef]);

  return (
      <div className="flex items-center gap-4">
        <Button onClick={onPrevious} className="btn-sticker h-16 w-16 p-0" variant="secondary" disabled={!canPrevious}>
          <RotateCcw size={32} strokeWidth={2.5} />
        </Button>
        <Button onClick={handlePlayPause} className="btn-sticker h-16 w-16 p-0" disabled={!isAudioAvailable}>
          {isPlaying ? (
            <Pause size={32} strokeWidth={2.5} />
          ) : (
            <Play size={32} strokeWidth={2.5} className="ml-2" />
          )}
        </Button>
        <Button onClick={onNext} className="btn-sticker h-16 w-16 p-0" variant="secondary" disabled={!canNext}>
          <RotateCw size={32} strokeWidth={2.5} />
        </Button>
      </div>
  );
}
