import { Button } from "@/components/ui/button";
import { FileUp, X, ArrowRight } from "lucide-react";
import { useRef } from "react";
import { apiRequest } from "@/lib/queryClient";
import { useToast } from "@/hooks/use-toast";
import { useMutation } from "@tanstack/react-query";

interface FileUploadProps {
  fileSelected: boolean;
  fileName: string;
  fileSize: string;
  onFileSelect: (file: File) => void;
  onRemoveFile: () => void;
  onContinue: () => void;
  onDocumentUploaded?: (documentId: number) => void; // Add prop for document ID
}

export function FileUpload({
  fileSelected,
  fileName,
  fileSize,
  onFileSelect,
  onRemoveFile,
  onContinue,
  onDocumentUploaded,
}: FileUploadProps) {
  const fileInputRef = useRef<HTMLInputElement>(null);
  const { toast } = useToast();

  const uploadMutation = useMutation({
    mutationFn: async (file: File) => {
      const formData = new FormData();
      formData.append("file", file);
      console.log("Uploading file:", file.name);
      
      const response = await fetch("/api/upload", {
        method: "POST",
        body: formData,
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.message || "Error uploading file");
      }

      return response.json();
    },
    onSuccess: (data) => {
      console.log("Upload successful:", data);
      
      // Set the document ID in the parent component
      if (data.document && data.document.id && onDocumentUploaded) {
        onDocumentUploaded(data.document.id);
      }
      
      toast({
        title: "File uploaded successfully",
        description: "Your PDF has been uploaded and is ready for translation.",
      });
      onContinue();
    },
    onError: (error) => {
      console.error("Upload error:", error);
      toast({
        title: "Upload failed",
        description: error instanceof Error ? error.message : "Failed to upload PDF file",
        variant: "destructive",
      });
      onRemoveFile();
    },
  });

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      const file = e.target.files[0];
      
      // Check if file is PDF
      if (!file.type.includes("pdf")) {
        toast({
          title: "Invalid file type",
          description: "Please upload a PDF file",
          variant: "destructive",
        });
        return;
      }
      
      // Check file size (max 50MB)
      if (file.size > 50 * 1024 * 1024) {
        toast({
          title: "File too large",
          description: "Maximum file size is 50MB",
          variant: "destructive",
        });
        return;
      }
      
      onFileSelect(file);
    }
  };

  const openFileUpload = () => {
    if (fileInputRef.current) {
      fileInputRef.current.click();
    }
  };

  const handleContinue = () => {
    if (fileSelected && uploadMutation.isPending === false) {
      // Get the selected file
      const fileInput = fileInputRef.current;
      if (fileInput && fileInput.files && fileInput.files[0]) {
        uploadMutation.mutate(fileInput.files[0]);
      }
    }
  };

  return (
    <div className="p-6">
      <h2 className="text-lg font-semibold text-gray-900 mb-4">Upload your PDF file</h2>

      {/* File Uploader */}
      <div
        className="border-2 border-dashed border-gray-300 rounded-lg p-8 text-center cursor-pointer hover:bg-gray-50 transition-colors"
        onClick={openFileUpload}
      >
        <input
          type="file"
          className="hidden"
          ref={fileInputRef}
          accept=".pdf"
          onChange={handleFileSelect}
        />
        <div className="space-y-2">
          <FileUp className="h-12 w-12 mx-auto text-gray-400" />
          <p className="text-gray-600">
            Drag and drop your PDF here or{" "}
            <span className="text-primary font-medium">browse files</span>
          </p>
          <p className="text-xs text-gray-500">
            Supports PDF files up to 50MB in any language
          </p>
        </div>
      </div>

      {/* Selected File */}
      {fileSelected && (
        <div className="mt-6 bg-gray-50 rounded-lg p-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-3">
              <svg
                xmlns="http://www.w3.org/2000/svg"
                className="h-6 w-6 text-red-500"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
                />
              </svg>
              <div>
                <p className="text-sm font-medium text-gray-900">{fileName}</p>
                <p className="text-xs text-gray-500">{fileSize}</p>
              </div>
            </div>
            <button
              type="button"
              className="text-gray-500 hover:text-gray-700"
              onClick={(e) => {
                e.stopPropagation();
                onRemoveFile();
              }}
            >
              <X className="h-5 w-5" />
            </button>
          </div>
        </div>
      )}

      <div className="mt-6 flex justify-end">
        <Button
          onClick={handleContinue}
          disabled={!fileSelected || uploadMutation.isPending}
          className="inline-flex items-center"
        >
          {uploadMutation.isPending ? "Uploading..." : "Continue"}
          {!uploadMutation.isPending && <ArrowRight className="ml-1 h-4 w-4" />}
        </Button>
      </div>
    </div>
  );
}
