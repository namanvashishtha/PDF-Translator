import { useState, useEffect, useRef } from "react";
import { Button } from "@/components/ui/button";
import { ArrowLeft, ArrowRight, X, ZoomIn, ZoomOut, RotateCw } from "lucide-react";

interface PDFPreviewProps {
  file: File | null;
  onClose: () => void;
}

export function PDFPreview({ file, onClose }: PDFPreviewProps) {
  const [currentPage, setCurrentPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [zoom, setZoom] = useState(1);
  const [rotation, setRotation] = useState(0);
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const [pdfUrl, setPdfUrl] = useState<string | null>(null);
  
  // Load the PDF.js library dynamically
  useEffect(() => {
    if (!file) return;
    
    // Create a URL for the file
    const objectUrl = URL.createObjectURL(file);
    setPdfUrl(objectUrl);
    
    // Clean up the URL when component unmounts
    return () => {
      URL.revokeObjectURL(objectUrl);
    };
  }, [file]);
  
  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 z-50 flex items-center justify-center">
      <div className="bg-white rounded-lg shadow-lg w-full max-w-4xl max-h-screen flex flex-col">
        <div className="flex items-center justify-between p-4 border-b">
          <h3 className="text-lg font-medium">PDF Preview: {file?.name}</h3>
          <button 
            onClick={onClose}
            className="text-gray-500 hover:text-gray-700"
          >
            <X className="h-5 w-5" />
          </button>
        </div>
        
        <div className="flex-1 overflow-auto p-4 flex items-center justify-center bg-gray-100">
          {pdfUrl ? (
            <iframe 
              src={`${pdfUrl}#toolbar=0&navpanes=0`} 
              className="w-full h-full border-0"
              style={{ 
                transform: `scale(${zoom}) rotate(${rotation}deg)`,
                transformOrigin: 'center center',
                transition: 'transform 0.2s ease'
              }}
            />
          ) : (
            <div className="text-center text-gray-500">
              No PDF selected
            </div>
          )}
        </div>
        
        <div className="p-4 border-t flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <Button 
              variant="outline" 
              size="icon"
              onClick={() => setZoom(prev => Math.max(0.5, prev - 0.1))}
              title="Zoom out"
            >
              <ZoomOut className="h-4 w-4" />
            </Button>
            <span className="text-sm">{Math.round(zoom * 100)}%</span>
            <Button 
              variant="outline" 
              size="icon"
              onClick={() => setZoom(prev => Math.min(2, prev + 0.1))}
              title="Zoom in"
            >
              <ZoomIn className="h-4 w-4" />
            </Button>
            <Button 
              variant="outline" 
              size="icon"
              onClick={() => setRotation(prev => (prev + 90) % 360)}
              title="Rotate"
            >
              <RotateCw className="h-4 w-4" />
            </Button>
          </div>
          
          <Button onClick={onClose}>
            Close
          </Button>
        </div>
      </div>
    </div>
  );
}