
"use client";

import React, { useRef, useEffect, useImperativeHandle, forwardRef, useState } from 'react';
import Image from 'next/image';
import { Card } from '@/components/ui/card';
import { Skeleton } from '@/components/ui/skeleton';

interface DrawingCanvasProps {
  storyImageUrl?: string | null;
  generatedImageUrl?: string | null;
  brushColor: string;
  brushSize: number;
  className?: string;
  aiHint?: string;
  isDrawingCanvas?: boolean;
  hasNoMessages?: boolean;
  storyTitle?: string;
}

export interface DrawingCanvasRef {
  exportAsDataUri: () => string | undefined;
  clearCanvas: () => void;
  undo: () => void;
  setEraser: (isErasing: boolean) => void;
}

const DrawingCanvas = forwardRef<DrawingCanvasRef, DrawingCanvasProps>(
  ({ storyImageUrl, generatedImageUrl, brushColor, brushSize, className, aiHint, isDrawingCanvas = false, hasNoMessages = false, storyTitle }, ref) => {
    const canvasRef = useRef<HTMLCanvasElement>(null);
    const contextRef = useRef<CanvasRenderingContext2D | null>(null);
    const [isDrawing, setIsDrawing] = useState(false);
    const [isStoryImageLoading, setIsStoryImageLoading] = useState(true);
    const [history, setHistory] = useState<ImageData[]>([]);

    const setCanvasSize = () => {
      const canvas = canvasRef.current;
      if (!canvas) return;
      const context = canvas.getContext("2d");
      if (!context) return;
      const { width, height } = canvas.getBoundingClientRect();
      if (canvas.width !== width || canvas.height !== height) {
        const { devicePixelRatio: ratio = 1 } = window;
        canvas.width = width * ratio;
        canvas.height = height * ratio;
        context.scale(ratio, ratio);
        return true; // Resized
      }
      return false; // Not resized
    };

    const redrawHistory = () => {
      const canvas = canvasRef.current;
      const context = canvas?.getContext("2d");
      if (!canvas || !context || history.length === 0) return;
      
      const lastState = history[history.length - 1];
      const tempCanvas = document.createElement('canvas');
      tempCanvas.width = lastState.width;
      tempCanvas.height = lastState.height;
      tempCanvas.getContext('2d')?.putImageData(lastState, 0, 0);

      context.clearRect(0, 0, canvas.width, canvas.height);
      context.drawImage(tempCanvas, 0, 0, canvas.offsetWidth, canvas.offsetHeight);
    };

    useEffect(() => {
        if (!isDrawingCanvas) return;
        const canvas = canvasRef.current;
        if (!canvas) return;
        contextRef.current = canvas.getContext('2d');
        if(contextRef.current) {
          contextRef.current.lineCap = 'round';
          contextRef.current.lineJoin = 'round';
        }

        const handleResize = () => {
          if (setCanvasSize()) {
            redrawHistory();
          }
        };

        handleResize(); // Initial size set
        window.addEventListener('resize', handleResize);
        
        if (history.length === 0) {
          saveState();
        }
        
        return () => {
            window.removeEventListener('resize', handleResize);
        }
    }, [isDrawingCanvas]);


    useEffect(() => {
        if (!isDrawingCanvas || !contextRef.current) return;
        contextRef.current.strokeStyle = brushColor;
        contextRef.current.lineWidth = brushSize;
        contextRef.current.globalCompositeOperation = 'source-over';
    }, [brushColor, brushSize, isDrawingCanvas]);

    const saveState = () => {
        if (!isDrawingCanvas || !canvasRef.current || !contextRef.current) return;
        const canvas = canvasRef.current;
        const context = contextRef.current;
        setHistory(prev => [...prev, context.getImageData(0, 0, canvas.width, canvas.height)]);
    }

    const restoreState = (imageData: ImageData) => {
        if (!isDrawingCanvas || !contextRef.current || !canvasRef.current) return;
        const canvas = canvasRef.current;
        contextRef.current.putImageData(imageData, 0, 0);
    }
    
    const clear = () => {
        if (!isDrawingCanvas) return;
        const canvas = canvasRef.current;
        const context = contextRef.current;
        if (canvas && context) {
            context.clearRect(0, 0, canvas.width, canvas.height);
            setHistory([]);
            saveState();
        }
    };

    const undo = () => {
        if (history.length > 1) {
            const newHistory = history.slice(0, -1);
            setHistory(newHistory);
            restoreState(newHistory[newHistory.length - 1]);
        } else if (history.length === 1) {
            clear();
        }
    }
    
    useEffect(() => {
        if (!isDrawingCanvas || !generatedImageUrl) return;
        const image = new window.Image();
        image.crossOrigin = 'anonymous';
        image.src = generatedImageUrl;
        image.onload = () => {
            const canvas = canvasRef.current;
            const context = contextRef.current;
            if (canvas && context) {
                clear();
                const canvasAspect = canvas.width / canvas.height;
                const imageAspect = image.width / image.height;
                let drawWidth = canvas.width;
                let drawHeight = canvas.height;
                let x = 0;
                let y = 0;

                if(imageAspect > canvasAspect) {
                    drawHeight = drawWidth / imageAspect;
                    y = (canvas.height - drawHeight) / 2;
                } else {
                    drawWidth = drawHeight * imageAspect;
                    x = (canvas.width - drawWidth) / 2;
                }
                context.drawImage(image, x, y, drawWidth, drawHeight);
                saveState();
            }
        };
    }, [generatedImageUrl, isDrawingCanvas]);

    useImperativeHandle(ref, () => ({
      exportAsDataUri: () => {
        if (!isDrawingCanvas || !canvasRef.current) return undefined;
        // Create a temporary canvas to export at a specific resolution if needed
        const exportCanvas = document.createElement('canvas');
        exportCanvas.width = 1200;
        exportCanvas.height = 1600;
        const exportCtx = exportCanvas.getContext('2d');
        if (exportCtx && canvasRef.current) {
            exportCtx.drawImage(canvasRef.current, 0, 0, 1200, 1600);
        }
        return exportCanvas.toDataURL('image/png');
      },
      clearCanvas: () => {
        clear();
      },
      undo: () => {
          undo();
      },
      setEraser: (isErasing: boolean) => {
        if (contextRef.current) {
            contextRef.current.globalCompositeOperation = isErasing ? 'destination-out' : 'source-over';
        }
      },
    }));
    
    useEffect(() => {
      if(storyImageUrl) {
        setIsStoryImageLoading(true);
      }
    }, [storyImageUrl]);

    const getCoords = (event: React.MouseEvent<HTMLCanvasElement>): [number, number] | null => {
        const canvas = canvasRef.current;
        if (!canvas) return null;
        return [event.nativeEvent.offsetX, event.nativeEvent.offsetY];
    }
    
    const startDrawing = (event: React.MouseEvent<HTMLCanvasElement>) => {
      if (!isDrawingCanvas) return;
      const coords = getCoords(event);
      if(!coords) return;
      const [x, y] = coords;

      contextRef.current?.beginPath();
      contextRef.current?.moveTo(x, y);
      setIsDrawing(true);
    };

    const finishDrawing = () => {
      if (!isDrawingCanvas || !isDrawing) return;
      contextRef.current?.closePath();
      setIsDrawing(false);
      saveState();
    };

    const draw = (event: React.MouseEvent<HTMLCanvasElement>) => {
      if (!isDrawing || !isDrawingCanvas) return;
      const coords = getCoords(event);
      if(!coords) return;
      const [x, y] = coords;
      
      contextRef.current?.lineTo(x, y);
      contextRef.current?.stroke();
    };

    if (isDrawingCanvas) {
        return (
            <canvas
                ref={canvasRef}
                onMouseDown={startDrawing}
                onMouseUp={finishDrawing}
                onMouseLeave={finishDrawing}
                onMouseMove={draw}
                className="w-full h-full bg-white cursor-crosshair"
            />
        );
    }
    
    return (
        <div className="relative w-full h-full bg-white">
        {storyImageUrl ? (
            <>
            {isStoryImageLoading && <Skeleton className="absolute inset-0 w-full h-full" />}
            <Image
                src={storyImageUrl}
                alt={aiHint || "Story inspiration"}
                fill
                className="object-cover"
                data-ai-hint={aiHint}
                onLoad={() => setIsStoryImageLoading(false)}
                unoptimized
            />
            </>
        ) : (
            <div className="flex items-center justify-center h-full text-muted-foreground p-8 text-center">
                {hasNoMessages && storyTitle ? (
                    <div className="space-y-2">
                        <p className="text-xl font-medium">"{storyTitle}"</p>
                        <p className="text-lg">Esta história ainda não tem mensagens.</p>
                        <p className="text-sm">Comece criando uma nova mensagem!</p>
                    </div>
                ) : (
                    <p className="text-xl font-medium">Selecione uma história para começar!</p>
                )}
            </div>
        )}
        </div>
    );
  }
);

DrawingCanvas.displayName = 'DrawingCanvas';
export default DrawingCanvas;
