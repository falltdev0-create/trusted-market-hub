import {
  createContext,
  useContext,
  useEffect,
  useState,
  type ReactNode,
} from "react";

import ar from "./ar";
import en from "./en";

export type Language = "ar" | "en";

const translations = {
  ar,
  en,
};

interface LanguageContextValue {
  language: Language;
  setLanguage: (language: Language) => void;
  isArabic: boolean;
  t: (key: string, variables?: Record<string, string | number>) => string;
}

const LanguageContext = createContext<LanguageContextValue | undefined>(
  undefined,
);

export function LanguageProvider({ children }: { children: ReactNode }) {
  const [language, setLanguageState] = useState<Language>(() => {
    if (typeof window === "undefined") {
      return "ar";
    }

    const saved = localStorage.getItem("maskan-language");

    return saved === "en" || saved === "ar" ? saved : "ar";
  });

  const setLanguage = (newLanguage: Language) => {
    setLanguageState(newLanguage);
    localStorage.setItem("maskan-language", newLanguage);
  };

  useEffect(() => {
    document.documentElement.lang = language;
    document.documentElement.dir = language === "ar" ? "rtl" : "ltr";
  }, [language]);

  const t = (key: string, variables?: Record<string, string | number>): string => {
    const keys = key.split(".");

    let value: unknown = translations[language];

    for (const currentKey of keys) {
      if (
        typeof value === "object" &&
        value !== null &&
        currentKey in value
      ) {
        value = (value as Record<string, unknown>)[currentKey];
      } else {
        return key;
      }
    }

    if (typeof value !== "string") return key;

    return value.replace(/\{(\w+)\}/g, (match, variable: string) =>
      variables?.[variable] === undefined ? match : String(variables[variable]),
    );
  };

  return (
    <LanguageContext.Provider
      value={{
        language,
        setLanguage,
        isArabic: language === "ar",
        t,
      }}
    >
      {children}
    </LanguageContext.Provider>
  );
}

export function useLanguage() {
  const context = useContext(LanguageContext);

  if (!context) {
    throw new Error("useLanguage must be used inside LanguageProvider");
  }

  return context;
}