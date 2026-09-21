export const cityTranslationKeys: Record<string, string> = {
  "الخرطوم": "cities.khartoum",
  "أم درمان": "cities.omdurman",
  "بحري": "cities.bahri",
  "بورتسودان": "cities.portSudan",
  "كسلا": "cities.kassala",
  "ودمدني": "cities.wadMadani",
  "الأبيض": "cities.elObeid",
};

export function getCityName(city: string, t: (key: string) => string) {
  const key = cityTranslationKeys[city];
  return key ? t(key) : city;
}