import { Button } from "@/components/ui/button";
import { ArrowLeft } from "lucide-react";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { RadioGroup, RadioGroupItem } from "@/components/ui/radio-group";
import { Label } from "@/components/ui/label";
import { Checkbox } from "@/components/ui/checkbox";
import { useQuery } from "@tanstack/react-query";
import { Language } from "@shared/schema";
import { getLanguageFlag, getLanguageName } from "@/lib/languages";

interface LanguageSelectorProps {
  detectedLanguage: string;
  setDetectedLanguage: (language: string) => void;
  targetLanguage: string;
  setTargetLanguage: (language: string) => void;
  outputFormat: "pdf" | "txt" | "dual";
  setOutputFormat: (format: "pdf" | "txt" | "dual") => void;
  preserveImages: boolean;
  setPreserveImages: (preserve: boolean) => void;
  onBack: () => void;
  onTranslate: () => void;
}

export function LanguageSelector({
  detectedLanguage,
  setDetectedLanguage,
  targetLanguage,
  setTargetLanguage,
  outputFormat,
  setOutputFormat,
  preserveImages,
  setPreserveImages,
  onBack,
  onTranslate,
}: LanguageSelectorProps) {
  // Fetch available languages
  const { data: languages = [] } = useQuery<Language[]>({
    queryKey: ["/api/languages"],
  });

  return (
    <div className="p-6">
      <h2 className="text-lg font-semibold text-gray-900 mb-4">Language Options</h2>

      <div className="space-y-6">
        {/* Source Language */}
        <div>
          <Label className="block text-sm font-medium text-gray-700 mb-1">
            <span className="text-base">Source Language (Original Document)</span>
          </Label>
          <Select value={detectedLanguage} onValueChange={setDetectedLanguage}>
            <SelectTrigger className="w-full">
              <SelectValue placeholder="Select source language" />
            </SelectTrigger>
            <SelectContent>
              {languages.map((lang) => (
                <SelectItem key={lang.code} value={lang.code}>
                  {lang.flag} {lang.name} {lang.code === detectedLanguage && "(Detected)"}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
          <p className="mt-1 text-xs text-gray-500">
            This is the language of your original document. Our system has detected it automatically.
          </p>
        </div>

        {/* Target Language */}
        <div>
          <Label className="block text-sm font-medium text-gray-700 mb-1">
            <span className="text-lg text-primary font-bold">Target Language (Translation Output)</span>
          </Label>
          <Select value={targetLanguage} onValueChange={setTargetLanguage}>
            <SelectTrigger className="w-full border-2 border-primary">
              <SelectValue placeholder="Select target language" />
            </SelectTrigger>
            <SelectContent>
              {languages.map((lang) => (
                <SelectItem key={lang.code} value={lang.code}>
                  {lang.flag} {lang.name} {lang.code === "en" && "- English"}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
          <p className="mt-1 text-sm text-gray-700 bg-yellow-50 p-2 rounded border border-yellow-200">
            <span className="font-semibold">IMPORTANT:</span> Select the language you want your 
            document to be translated INTO. For Spanish→English translation, select English here.
          </p>
        </div>

        {/* Output Format */}
        <div>
          <Label className="block text-sm font-medium text-gray-700 mb-2">
            Output Format
          </Label>
          <RadioGroup
            value={outputFormat}
            onValueChange={(value) => setOutputFormat(value as "pdf" | "txt" | "dual")}
            className="flex space-x-4"
          >
            <div className="flex items-center space-x-2">
              <RadioGroupItem value="pdf" id="option-pdf" />
              <Label htmlFor="option-pdf" className="text-sm text-gray-700">PDF Document</Label>
            </div>
            <div className="flex items-center space-x-2">
              <RadioGroupItem value="txt" id="option-txt" />
              <Label htmlFor="option-txt" className="text-sm text-gray-700">Plain Text (.txt)</Label>
            </div>
            <div className="flex items-center space-x-2">
              <RadioGroupItem value="dual" id="option-dual" />
              <Label htmlFor="option-dual" className="text-sm text-gray-700">Dual Language PDF</Label>
            </div>
          </RadioGroup>
        </div>
        
        {/* Preserve Images Option (only show for PDF output) */}
        {outputFormat === "pdf" && (
          <div>
            <div className="flex items-center space-x-2">
              <Checkbox 
                id="preserve-images" 
                checked={preserveImages}
                onCheckedChange={(checked) => setPreserveImages(checked as boolean)}
              />
              <Label 
                htmlFor="preserve-images" 
                className="text-sm font-medium text-gray-700"
              >
                Preserve images and layout
              </Label>
            </div>
            <p className="mt-1 text-xs text-gray-500 ml-6">
              When enabled, we'll maintain the original document's images and attempt to preserve the layout.
            </p>
          </div>
        )}
      </div>

      <div className="mt-8 flex justify-between">
        <Button variant="outline" onClick={onBack} className="inline-flex items-center">
          <ArrowLeft className="mr-1 h-4 w-4" /> Back
        </Button>
        <Button 
          onClick={onTranslate} 
          className="text-lg font-bold bg-primary hover:bg-primary/90 px-6 py-2"
        >
          Translate from {getLanguageName(detectedLanguage)} to {getLanguageName(targetLanguage)}
        </Button>
      </div>
      
      {/* Add clear warning about common confusion */}
      {detectedLanguage === targetLanguage && (
        <div className="mt-4 p-3 bg-red-50 border border-red-200 rounded-md text-red-800 text-sm">
          <strong>Warning:</strong> You have selected the same language for both source and target. 
          This means no translation will occur. If you want to translate the document, please select 
          different languages.
        </div>
      )}
    </div>
  );
}
