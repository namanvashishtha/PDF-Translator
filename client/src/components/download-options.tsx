import { Button } from "@/components/ui/button";
import { Eye, Download, Share, Flag, PlusCircle } from "lucide-react";
import { useToast } from "@/hooks/use-toast";
import { getLanguageFlag, getLanguageName } from "@/lib/languages";

interface DownloadOptionsProps {
  fileName: string;
  documentId: number | null;
  sourceLanguage: string;
  targetLanguage: string;
  onTranslateAnother: () => void;
}

export function DownloadOptions({
  fileName,
  documentId,
  sourceLanguage,
  targetLanguage,
  onTranslateAnother,
}: DownloadOptionsProps) {
  const { toast } = useToast();
  const translatedFileName = fileName.replace(/\.pdf$/i, "") + "-translated.pdf";

  const handlePreviewDocument = () => {
    toast({
      title: "Preview not available",
      description: "This feature is coming soon.",
    });
  };

  const handleDownloadDocument = () => {
    if (!documentId) {
      toast({
        title: "Document not found",
        description: "Could not find document for download",
        variant: "destructive",
      });
      return;
    }

    // Open the download URL in a new tab
    window.open(`/api/download/${documentId}`, "_blank");
    
    toast({
      title: "Download started",
      description: "Your translated document is downloading.",
    });
  };

  const handleShareDocument = () => {
    toast({
      title: "Share feature",
      description: "This feature is coming soon.",
    });
  };

  const handleReportIssue = () => {
    toast({
      title: "Report issue",
      description: "Thanks for helping us improve. The reporting feature is coming soon.",
    });
  };

  return (
    <div className="p-6">
      <div className="text-center mb-6">
        <div className="inline-flex items-center justify-center h-16 w-16 rounded-full bg-green-100 mb-4">
          <svg
            className="h-8 w-8 text-green-500"
            xmlns="http://www.w3.org/2000/svg"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M5 13l4 4L19 7"
            />
          </svg>
        </div>
        <h2 className="text-lg font-semibold text-gray-900">
          Translation Complete!
        </h2>
        <p className="text-gray-600 mt-1">
          Your document has been successfully translated and is ready for download.
        </p>
      </div>

      {/* Download Options */}
      <div className="bg-gray-50 rounded-lg p-4 mb-6">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between">
          <div className="flex items-center space-x-3 mb-3 sm:mb-0">
            <svg
              className="h-6 w-6 text-primary"
              xmlns="http://www.w3.org/2000/svg"
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
              <p className="text-sm font-medium text-gray-900">
                {translatedFileName}
              </p>
              <div className="flex items-center text-xs text-gray-500">
                <span>{getLanguageFlag(sourceLanguage)} {getLanguageName(sourceLanguage)}</span>
                <svg
                  className="h-3 w-3 mx-1"
                  xmlns="http://www.w3.org/2000/svg"
                  fill="none"
                  viewBox="0 0 24 24"
                  stroke="currentColor"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M13 7l5 5m0 0l-5 5m5-5H6"
                  />
                </svg>
                <span>{getLanguageFlag(targetLanguage)} {getLanguageName(targetLanguage)}</span>
              </div>
            </div>
          </div>
          <div className="flex items-center space-x-2">
            <Button
              variant="outline"
              size="sm"
              onClick={handlePreviewDocument}
              className="inline-flex items-center"
            >
              <Eye className="mr-1 h-4 w-4" /> Preview
            </Button>
            <Button
              size="sm"
              onClick={handleDownloadDocument}
              className="inline-flex items-center"
            >
              <Download className="mr-1 h-4 w-4" /> Download
            </Button>
          </div>
        </div>
      </div>

      {/* Additional Actions */}
      <div className="border-t border-gray-200 pt-4">
        <div className="flex flex-col sm:flex-row sm:justify-between sm:items-center space-y-4 sm:space-y-0">
          <div>
            <Button
              variant="outline"
              onClick={onTranslateAnother}
              className="inline-flex items-center"
            >
              <PlusCircle className="mr-1 h-4 w-4" /> Translate Another Document
            </Button>
          </div>
          <div className="flex items-center space-x-4">
            <button
              type="button"
              className="inline-flex items-center text-sm text-gray-500 hover:text-gray-700"
              onClick={handleShareDocument}
            >
              <Share className="mr-1 h-4 w-4" /> Share
            </button>
            <button
              type="button"
              className="inline-flex items-center text-sm text-gray-500 hover:text-gray-700"
              onClick={handleReportIssue}
            >
              <Flag className="mr-1 h-4 w-4" /> Report Issue
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
