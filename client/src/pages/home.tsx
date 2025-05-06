import { useState } from "react";
import { Navbar } from "@/components/navbar";
import { Footer } from "@/components/footer";
import { FileUpload } from "@/components/file-upload";
import { LanguageSelector } from "@/components/language-selector";
import { ProcessingSteps } from "@/components/processing-steps";
import { DownloadOptions } from "@/components/download-options";
import { SupportedLanguages } from "@/components/supported-languages";
import { useToast } from "@/hooks/use-toast";
import { Languages } from "lucide-react";
import { useQuery, useMutation } from "@tanstack/react-query";
import { Document } from "@shared/schema";
import { pdfService } from "@/lib/pdf-service";

export default function Home() {
  const { toast } = useToast();
  const [currentStep, setCurrentStep] = useState(1);
  const [fileSelected, setFileSelected] = useState(false);
  const [fileUploaded, setFileUploaded] = useState(false);
  const [isProcessing, setIsProcessing] = useState(false);
  const [translationComplete, setTranslationComplete] = useState(false);
  const [processingStep, setProcessingStep] = useState(1);
  
  const [fileDetails, setFileDetails] = useState<{
    fileName: string;
    fileSize: string;
    file?: File;
  }>({
    fileName: "",
    fileSize: "",
  });
  
  const [currentDocumentId, setCurrentDocumentId] = useState<number | null>(null);
  const [selectedOutputFormat, setSelectedOutputFormat] = useState<"pdf" | "txt" | "dual">("pdf");
  const [detectedLanguage, setDetectedLanguage] = useState<string>("en");
  const [targetLanguage, setTargetLanguage] = useState<string>("es");
  
  // Translation mutation
  const translateMutation = useMutation({
    mutationFn: async () => {
      if (!currentDocumentId) {
        throw new Error("No document selected for translation");
      }
      
      console.log(`Starting translation for document ${currentDocumentId} to ${targetLanguage} in ${selectedOutputFormat} format`);
      return pdfService.translateDocument(
        currentDocumentId,
        targetLanguage,
        selectedOutputFormat
      );
    },
    onSuccess: (data) => {
      console.log("Translation process initiated:", data);
      toast({
        title: "Translation Started",
        description: "Your document is being processed. This will only take a few seconds.",
      });
    },
    onError: (error) => {
      console.error("Translation error:", error);
      setIsProcessing(false);
      toast({
        title: "Translation Failed",
        description: error instanceof Error ? error.message : "Failed to start translation process",
        variant: "destructive",
      });
    }
  });
  
  // Fetch document details if we have a document ID
  const { data: documentData } = useQuery<Document>({
    queryKey: [currentDocumentId ? `/api/documents/${currentDocumentId}` : null],
    enabled: !!currentDocumentId,
    refetchInterval: isProcessing ? 2000 : false, // Poll when processing
  });
  
  // Update UI based on document status
  if (documentData && isProcessing) {
    if (documentData.originalLanguage && detectedLanguage !== documentData.originalLanguage) {
      setDetectedLanguage(documentData.originalLanguage);
    }
    
    if (documentData.status === "language_detected" && processingStep < 2) {
      setProcessingStep(2);
    } else if (documentData.status === "translating" && processingStep < 2) {
      setProcessingStep(2);
    } else if (documentData.status === "generating_output" && processingStep < 3) {
      setProcessingStep(3);
    } else if (documentData.status === "completed") {
      setIsProcessing(false);
      setTranslationComplete(true);
      setCurrentStep(3);
      toast({
        title: "Translation Complete",
        description: "Your document has been translated successfully!",
      });
    } else if (documentData.status === "error") {
      setIsProcessing(false);
      toast({
        title: "Translation Failed",
        description: "There was an error processing your document. Please try again.",
        variant: "destructive",
      });
    }
  }
  
  const handleFileSelect = (file: File) => {
    setFileSelected(true);
    setFileDetails({
      fileName: file.name,
      fileSize: (file.size / (1024 * 1024)).toFixed(1) + " MB",
      file,
    });
  };
  
  const handleRemoveFile = () => {
    setFileSelected(false);
    setFileDetails({
      fileName: "",
      fileSize: "",
    });
  };
  
  const handleProcessFile = () => {
    if (!fileSelected || !fileDetails.file) return;
    
    setFileUploaded(true);
    setCurrentStep(2);
  };
  
  const handleGoBackToUpload = () => {
    setFileUploaded(false);
    setCurrentStep(1);
  };
  
  const handleStartTranslation = async () => {
    if (!currentDocumentId) {
      toast({
        title: "Error",
        description: "Please upload a document first",
        variant: "destructive",
      });
      return;
    }
    
    setIsProcessing(true);
    setProcessingStep(1);
    
    // Start the translation process
    translateMutation.mutate();
  };
  
  const handleTranslateNewDocument = () => {
    setCurrentStep(1);
    setFileSelected(false);
    setFileUploaded(false);
    setIsProcessing(false);
    setTranslationComplete(false);
    setProcessingStep(1);
    setFileDetails({
      fileName: "",
      fileSize: "",
    });
    setCurrentDocumentId(null);
  };
  
  const handleHelp = () => {
    toast({
      title: "Help Center",
      description: "Our documentation and support team are available to assist you.",
      duration: 5000,
    });
  };
  
  return (
    <div className="min-h-screen flex flex-col">
      <Navbar onHelpClick={handleHelp} />
      
      <main className="flex-grow">
        <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
          {/* App Header */}
          <div className="text-center mb-10">
            <h1 className="text-3xl font-bold text-gray-900 mb-2">PDF Translation Tool</h1>
            <p className="text-gray-600 max-w-2xl mx-auto">
              Upload any PDF in any language and convert it to a new document in your preferred language.
            </p>
          </div>
          
          {/* Process Steps */}
          <div className="relative mb-12 hidden sm:block">
            <div className="flex items-center justify-between w-full z-0">
              <div className="flex items-center relative">
                <div className="rounded-full h-10 w-10 flex items-center justify-center bg-primary text-primary-foreground">
                  1
                </div>
                <div className="ml-3 text-sm font-medium text-gray-900">Upload PDF</div>
              </div>
              
              <div className="flex-grow mx-6">
                <div className={`h-1 rounded ${currentStep >= 2 ? 'bg-primary' : 'bg-gray-300'}`}></div>
              </div>
              
              <div className="flex items-center relative">
                <div className={`rounded-full h-10 w-10 flex items-center justify-center ${
                  currentStep >= 2 ? 'bg-primary text-primary-foreground' : 'bg-gray-300 text-gray-500'
                }`}>
                  2
                </div>
                <div className={`ml-3 text-sm font-medium ${
                  currentStep >= 2 ? 'text-gray-900' : 'text-gray-500'
                }`}>
                  Language Selection
                </div>
              </div>
              
              <div className="flex-grow mx-6">
                <div className={`h-1 rounded ${currentStep >= 3 ? 'bg-primary' : 'bg-gray-300'}`}></div>
              </div>
              
              <div className="flex items-center relative">
                <div className={`rounded-full h-10 w-10 flex items-center justify-center ${
                  currentStep >= 3 ? 'bg-primary text-primary-foreground' : 'bg-gray-300 text-gray-500'
                }`}>
                  3
                </div>
                <div className={`ml-3 text-sm font-medium ${
                  currentStep >= 3 ? 'text-gray-900' : 'text-gray-500'
                }`}>
                  Download
                </div>
              </div>
            </div>
          </div>
          
          {/* Main Content Area */}
          <div className="bg-white shadow rounded-lg overflow-hidden">
            {/* Step 1: File Upload */}
            {!fileUploaded && (
              <FileUpload
                fileSelected={fileSelected}
                fileName={fileDetails.fileName}
                fileSize={fileDetails.fileSize}
                onFileSelect={handleFileSelect}
                onRemoveFile={handleRemoveFile}
                onContinue={handleProcessFile}
              />
            )}
            
            {/* Step 2: Language Selection */}
            {fileUploaded && !translationComplete && !isProcessing && (
              <LanguageSelector
                detectedLanguage={detectedLanguage}
                setDetectedLanguage={setDetectedLanguage}
                targetLanguage={targetLanguage}
                setTargetLanguage={setTargetLanguage}
                outputFormat={selectedOutputFormat}
                setOutputFormat={setSelectedOutputFormat}
                onBack={handleGoBackToUpload}
                onTranslate={handleStartTranslation}
              />
            )}
            
            {/* Processing State */}
            {isProcessing && (
              <ProcessingSteps
                step={processingStep}
                documentName={fileDetails.fileName}
              />
            )}
            
            {/* Step 3: Download */}
            {translationComplete && (
              <DownloadOptions
                fileName={fileDetails.fileName}
                documentId={currentDocumentId}
                sourceLanguage={detectedLanguage}
                targetLanguage={targetLanguage}
                onTranslateAnother={handleTranslateNewDocument}
              />
            )}
          </div>
          
          {/* Supported Languages */}
          <SupportedLanguages />
        </div>
      </main>
      
      <Footer />
    </div>
  );
}
