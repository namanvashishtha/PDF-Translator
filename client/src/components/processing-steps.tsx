import { Loader2, CheckCircle2, Clock } from "lucide-react";

interface ProcessingStepsProps {
  step: number;
  documentName: string;
}

export function ProcessingSteps({ step, documentName }: ProcessingStepsProps) {
  const getStepLabel = () => {
    switch (step) {
      case 1:
        return "Extracting text from PDF...";
      case 2:
        return "Translating content...";
      case 3:
        return "Generating output document...";
      default:
        return "Processing your document...";
    }
  };

  return (
    <div className="p-8">
      <div className="text-center">
        <div className="inline-block mb-6">
          <Loader2 className="animate-spin h-12 w-12 text-primary mx-auto" />
        </div>
        <h3 className="text-lg font-medium text-gray-900 mb-2">
          {getStepLabel()}
        </h3>
        <p className="text-sm text-gray-500 mb-6">
          This may take a few moments depending on the document size.
        </p>

        <div className="max-w-md mx-auto">
          <ol className="space-y-4">
            {/* Step 1: Extract text */}
            <li className="flex items-start">
              <div className="flex-shrink-0">
                <div className="h-6 w-6 flex items-center justify-center rounded-full bg-primary-100 text-primary">
                  <CheckCircle2 className="h-4 w-4" />
                </div>
              </div>
              <p className="ml-3 text-sm text-gray-700 text-left">
                Extracting text from PDF
              </p>
            </li>

            {/* Step 2: Translate */}
            <li className="flex items-start">
              <div className="flex-shrink-0">
                <div
                  className={`h-6 w-6 flex items-center justify-center rounded-full ${
                    step >= 2
                      ? "bg-primary-100 text-primary"
                      : "bg-primary text-white"
                  }`}
                >
                  {step >= 2 ? (
                    <CheckCircle2 className="h-4 w-4" />
                  ) : (
                    <Loader2 className="h-4 w-4 animate-spin" />
                  )}
                </div>
              </div>
              <p className="ml-3 text-sm text-gray-700 text-left">
                Translating content
              </p>
            </li>

            {/* Step 3: Generate output */}
            <li className="flex items-start">
              <div className="flex-shrink-0">
                <div
                  className={`h-6 w-6 flex items-center justify-center rounded-full ${
                    step >= 3
                      ? "bg-primary-100 text-primary"
                      : step === 2
                      ? "bg-primary text-white"
                      : "bg-gray-200 text-gray-400"
                  }`}
                >
                  {step >= 3 ? (
                    <CheckCircle2 className="h-4 w-4" />
                  ) : step === 2 ? (
                    <Loader2 className="h-4 w-4 animate-spin" />
                  ) : (
                    <Clock className="h-4 w-4" />
                  )}
                </div>
              </div>
              <p
                className={`ml-3 text-sm text-left ${
                  step >= 3 ? "text-gray-700" : "text-gray-500"
                }`}
              >
                Generating output document
              </p>
            </li>
          </ol>
        </div>
      </div>
    </div>
  );
}
