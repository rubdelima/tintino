
'use client';

import React, { useState, useRef } from 'react';
import { Button } from '@/components/ui/button';
import { Slider } from '@/components/ui/slider';
import { Eraser, Undo2, Pipette, Trash2 } from 'lucide-react';
import { Card } from '@/components/ui/card';
import { Popover, PopoverContent, PopoverTrigger } from '@/components/ui/popover';

interface DrawingToolbarProps {
  brushColor: string;
  setBrushColor: (color: string) => void;
  brushSize: number;
  setBrushSize: (size: number) => void;
  clearCanvas: () => void;
  undo: () => void;
  isErasing: boolean;
  toggleEraser: () => void;
}

const initialColors = [
  '#000000', '#B10DC9', '#0074D9', '#2ECC40', '#FFDC00', '#FF851B', '#FF4136'
];

export function DrawingToolbar({
  brushColor,
  setBrushColor,
  brushSize,
  setBrushSize,
  clearCanvas,
  undo,
  isErasing,
  toggleEraser
}: DrawingToolbarProps) {
  const [colors, setColors] = useState(initialColors);
  const [popoverOpen, setPopoverOpen] = useState(false);
  const [tempColor, setTempColor] = useState(brushColor);
  const colorInputRef = useRef<HTMLInputElement>(null);

  const handleColorConfirm = () => {
    setBrushColor(tempColor);
    setColors(prevColors => {
      const newColors = [tempColor, ...prevColors.filter(c => c !== tempColor)];
      if (newColors.length > 7) {
        return newColors.slice(0, 7);
      }
      return newColors;
    });
    setPopoverOpen(false);
  };
  
  const handleColorPickerClick = () => {
    setTempColor(brushColor);
    setPopoverOpen(true);
  };
  
  const handlePickerChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    setTempColor(event.target.value);
  }

  return (
    <Card className="flex w-full flex-col gap-4 p-2 rounded-2xl border-2 border-border shadow-lg bg-card">
      <div className="flex items-center justify-between gap-4 px-2">
        {colors.map((color) => (
          <button
            key={color}
            onClick={() => setBrushColor(color)}
            className={`w-8 h-8 rounded-full transition-transform transform hover:scale-110 border-2 ${
              brushColor === color && !isErasing ? 'border-primary ring-2 ring-primary ring-offset-2' : 'border-transparent'
            }`}
            style={{ backgroundColor: color }}
            aria-label={`Selecionar cor ${color}`}
          />
        ))}
        <Popover open={popoverOpen} onOpenChange={setPopoverOpen}>
          <PopoverTrigger asChild>
            <Button onClick={handleColorPickerClick} variant="ghost" className="btn-sticker-sm h-10 w-10 p-0 shrink-0">
                <Pipette size={20} strokeWidth={2.5} />
            </Button>
          </PopoverTrigger>
          <PopoverContent className="w-auto p-4">
            <div className="flex flex-col gap-4 items-center">
                <div 
                    className="w-64 h-32 rounded-lg border-2 border-border" 
                    style={{ backgroundColor: tempColor }}
                />
                 <input
                    ref={colorInputRef}
                    type="color"
                    value={tempColor}
                    onChange={handlePickerChange}
                    className="sr-only"
                />
                <Button onClick={() => colorInputRef.current?.click()} className="btn-sticker-sm w-full">Choose color</Button>
                <Button onClick={handleColorConfirm} className="btn-sticker-sm w-full">OK</Button>
            </div>
          </PopoverContent>
        </Popover>

      </div>
      <div className="flex items-center justify-between px-2 gap-4">
        <div className="flex items-center gap-2 flex-1">
            <span className="text-sm font-medium">Size</span>
            <Slider
              value={[brushSize]}
              onValueChange={(value) => setBrushSize(value[0])}
              min={1}
              max={50}
              step={1}
              className="w-full"
            />
        </div>
        <div className="flex items-center gap-2">
            <Button onClick={toggleEraser} variant="ghost" className="btn-sticker-sm h-10 w-10 p-0" data-active={isErasing}>
                <Eraser size={20} strokeWidth={2.5} />
            </Button>
            <Button onClick={undo} variant="ghost" className="btn-sticker-sm h-10 w-10 p-0">
                <Undo2 size={20} strokeWidth={2.5} />
            </Button>
            <Button onClick={clearCanvas} variant="ghost" className="btn-sticker-sm h-10 w-10 p-0">
                <Trash2 size={20} strokeWidth={2.5} />
            </Button>
        </div>
      </div>
    </Card>
  );
}
