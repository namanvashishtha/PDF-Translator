// Map of language codes to names and flags
const languageMap: Record<string, { name: string; flag: string }> = {
  en: { name: "English", flag: "🇺🇸" },
  es: { name: "Spanish", flag: "🇪🇸" },
  fr: { name: "French", flag: "🇫🇷" },
  de: { name: "German", flag: "🇩🇪" },
  it: { name: "Italian", flag: "🇮🇹" },
  pt: { name: "Portuguese", flag: "🇵🇹" },
  ja: { name: "Japanese", flag: "🇯🇵" },
  zh: { name: "Chinese", flag: "🇨🇳" },
  ru: { name: "Russian", flag: "🇷🇺" },
  ar: { name: "Arabic", flag: "🇦🇪" },
  hi: { name: "Hindi", flag: "🇮🇳" },
  nl: { name: "Dutch", flag: "🇳🇱" },
  ko: { name: "Korean", flag: "🇰🇷" },
  tr: { name: "Turkish", flag: "🇹🇷" },
  sv: { name: "Swedish", flag: "🇸🇪" },
  pl: { name: "Polish", flag: "🇵🇱" },
};

/**
 * Get the name of a language from its code
 */
export function getLanguageName(code: string): string {
  return languageMap[code]?.name || code;
}

/**
 * Get the flag emoji for a language from its code
 */
export function getLanguageFlag(code: string): string {
  return languageMap[code]?.flag || "🌐";
}

/**
 * Get all supported languages
 */
export function getAllLanguages(): Array<{ code: string; name: string; flag: string }> {
  return Object.entries(languageMap).map(([code, { name, flag }]) => ({
    code,
    name,
    flag,
  }));
}
