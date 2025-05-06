import { Button } from "@/components/ui/button";
import { ArrowLeft } from "lucide-react";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { RadioGroup, RadioGroupItem } from "@/components/ui/radio-group";
import { Label } from "@/components/ui/label";
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
            Detected Language
          </Label>
          <Select value={detectedLanguage} onValueChange={setDetectedLanguage}>
            <SelectTrigger className="w-full">
              <SelectValue placeholder="Select language" />
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
            We've detected the source language. You can change it if needed.
          </p>
        </div>

        {/* Target Language */}
        <div>
          <Label className="block text-sm font-medium text-gray-700 mb-1">
            Target Language
          </Label>
          <Select value={targetLanguage} onValueChange={setTargetLanguage}>
            <SelectTrigger className="w-full">
              <SelectValue placeholder="Select language" />
            </SelectTrigger>
            <SelectContent>
              {languages.map((lang) => (
                <SelectItem key={lang.code} value={lang.code}>
                  {lang.flag} {lang.name}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
          <p className="mt-1 text-xs text-gray-500">
            Select the language you want to translate the document into.
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
      </div>

      <div className="mt-8 flex justify-between">
        <Button variant="outline" onClick={onBack} className="inline-flex items-center">
          <ArrowLeft className="mr-1 h-4 w-4" /> Back
        </Button>
        <Button onClick={onTranslate}>
          Translate Document
        </Button>
      </div>
    </div>
  );
}
