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
}

export interface DrawingCanvasRef {
  exportAsDataUri: () => string | undefined;
  clearCanvas: () => void;
  undo: () => void;
}

const DrawingCanvas = forwardRef<DrawingCanvasRef, DrawingCanvasProps>(
  ({ storyImageUrl, generatedImageUrl, brushColor, brushSize, className, aiHint, isDrawingCanvas = false }, ref) => {
    const canvasRef = useRef<HTMLCanvasElement>(null);
    const contextRef = useRef<CanvasRenderingContext2D | null>(null);
    const [isDrawing, setIsDrawing] = useState(false);
    const [isStoryImageLoading, setIsStoryImageLoading] = useState(true);
    const [history, setHistory] = useState<ImageData[]>([]);

    useEffect(() => {
        if (!isDrawingCanvas) return;
        const canvas = canvasRef.current;
        if (!canvas) return;
        const context = canvas.getContext('2d');
        if (!context) return;
        
        context.lineCap = 'round';
        context.lineJoin = 'round';
        contextRef.current = context;
        saveState();
    }, [isDrawingCanvas]);

    useEffect(() => {
        if (!isDrawingCanvas || !contextRef.current) return;
        contextRef.current.strokeStyle = brushColor;
        contextRef.current.lineWidth = brushSize;
    }, [brushColor, brushSize, isDrawingCanvas]);

    const saveState = () => {
        if (!isDrawingCanvas || !canvasRef.current || !contextRef.current) return;
        const canvas = canvasRef.current;
        const context = contextRef.current;
        const imageData = context.getImageData(0, 0, canvas.width, canvas.height);
        setHistory(prev => [...prev, imageData]);
    }

    const restoreState = (imageData: ImageData) => {
        if (!isDrawingCanvas || !contextRef.current) return;
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
      exportAsDataUri: () => isDrawingCanvas ? canvasRef.current?.toDataURL('image/png') : undefined,
      clearCanvas: () => {
        clear();
      },
      undo: () => {
          undo();
      }
    }));
    
    useEffect(() => {
      if(storyImageUrl) {
        setIsStoryImageLoading(true);
      }
    }, [storyImageUrl]);

    const startDrawing = (event: React.MouseEvent<HTMLCanvasElement>) => {
      if (!isDrawingCanvas) return;
      const { offsetX, offsetY } = event.nativeEvent;
      contextRef.current?.beginPath();
      contextRef.current?.moveTo(offsetX, offsetY);
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
      const { offsetX, offsetY } = event.nativeEvent;
      contextRef.current?.lineTo(offsetX, offsetY);
      contextRef.current?.stroke();
    };

    if (isDrawingCanvas) {
        return (
            <canvas
                ref={canvasRef}
                width={1200}
                height={1600}
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
                <p className="text-xl font-medium">Select a story from the sidebar to begin!</p>
            </div>
        )}
        </div>
    );
  }
);

DrawingCanvas.displayName = 'DrawingCanvas';
export default DrawingCanvas;
