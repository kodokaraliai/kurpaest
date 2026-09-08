export const COPY = {
  lt: {
    brand: "kurpaest.lt",
    title: "Kur paėst",
    lede: "Žemėlapis valgymo vietų su meniu eilutėmis. Rask pigiausią kebabą — arba tai, kas tinka tau.",
    lookingFor: "Ko ieškai",
    placeholder: "kebabas, cepelinai, pizza…",
    findCheapest: "Rasti pigiausią",
    dietaryAria: "Mitybos poreikiai",
    vegan: "Veganiška",
    vegetarian: "Vegetariška",
    gluten_free: "Be glitimo",
    lactose_free: "Be laktozės",
    halal: "Halal",
    results: "Pigiausi patiekalai",
    searchPrompt: "Įvesk, ko nori — rasime pigiausią.",
    noMatchingItems: "Nėra patiekalų, atitinkančių paiešką ir žymas.",
    noPlacesInView: "Šiame žemėlapio vaizde vietų nėra.",
    mapAria: "Žemėlapis su valgymo vietomis",
    mapError: "Nepavyko įkelti vietų šiam vaizdui.",
    language: "Kalba",
    showingVerified:
      "Rodomi patiekalai su patvirtintomis mitybos žymomis. Nežinomos žymos neatitinka filtro.",
    showOnMap: "Rodyti žemėlapyje",
  },
  en: {
    brand: "kurpaest.lt",
    title: "Where to eat",
    lede: "A queryable map of places to eat, with an itemized menu for each place. Find the cheapest kebab — or anything that matches how you eat.",
    lookingFor: "Looking for",
    placeholder: "kebabas, cepelinai, pizza…",
    findCheapest: "Find cheapest",
    dietaryAria: "Dietary preferences",
    vegan: "Vegan",
    vegetarian: "Vegetarian",
    gluten_free: "Gluten-free",
    lactose_free: "Lactose-free",
    halal: "Halal",
    results: "Cheapest items",
    searchPrompt: "Enter a dish — we will find the cheapest match.",
    noMatchingItems: "No items match this search and dietary tags.",
    noPlacesInView: "No places in this map view.",
    mapAria: "Map of places to eat",
    mapError: "Could not load places for this map view.",
    language: "Language",
    showingVerified:
      "Showing items with verified dietary tags. Unknown tags do not match a filter.",
    showOnMap: "Show on map",
  },
};

export const DIETARY_IDS = [
  "vegan",
  "vegetarian",
  "gluten_free",
  "lactose_free",
  "halal",
];

export function formatPrice(priceCents, lang) {
  const value = (priceCents / 100).toFixed(2);
  if (lang === "lt") {
    return `${value.replace(".", ",")} €`;
  }
  return `€${value}`;
}

export function itemLabel(item, lang) {
  if (lang === "en" && item.name_en) {
    return item.name_en;
  }
  return item.name;
}
