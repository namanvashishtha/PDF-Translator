import { apiRequest } from "./queryClient";

/**
 * Service for handling PDF translation functionality
 */
export const pdfService = {
  /**
   * Upload a PDF file for translation
   */
  async uploadPdf(file: File) {
    const formData = new FormData();
    formData.append("file", file);
    
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
  
  /**
   * Start translation process for a document
   */
  async translateDocument(documentId: number, targetLanguage: string, outputFormat: string, preserveImages: boolean = true) {
    const response = await apiRequest("POST", "/api/translate", {
      documentId,
      targetLanguage,
      outputFormat,
      preserveImages,
    });
    
    return response.json();
  },
  
  /**
   * Check the status of a translation
   */
  async checkTranslationStatus(documentId: number) {
    const response = await fetch(`/api/translate/status/${documentId}`);
    
    if (!response.ok) {
      throw new Error("Error checking translation status");
    }
    
    return response.json();
  },
  
  /**
   * Get download URL for a translated document
   */
  getDownloadUrl(documentId: number) {
    return `/api/download/${documentId}`;
  }
};
