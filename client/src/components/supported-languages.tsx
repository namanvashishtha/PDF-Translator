import { useQuery } from "@tanstack/react-query";
import { Language } from "@shared/schema";

export function SupportedLanguages() {
  const { data: languages = [] } = useQuery<Language[]>({
    queryKey: ["/api/languages"],
  });

  return (
    <div className="mt-12 bg-white shadow rounded-lg p-6">
      <h3 className="text-lg font-medium text-gray-900 mb-4">Supported Languages</h3>
      <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 gap-2 text-sm">
        {languages.map((lang) => (
          <div key={lang.code} className="py-1 text-gray-700">
            {lang.flag} {lang.name}
          </div>
        ))}
      </div>
      <p className="text-xs text-gray-500 mt-4">
        We support translation between 40+ languages. Contact us if you need a language that's not listed.
      </p>
    </div>
  );
}
