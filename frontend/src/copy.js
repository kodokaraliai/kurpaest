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
    searching: "Ieškoma…",
    searchError: "Nepavyko ieškoti patiekalų.",
    menu: "Meniu",
    closePlace: "Uždaryti",
    placeError: "Nepavyko įkelti šios vietos meniu.",
    loadingMenu: "Kraunamas meniu…",
    lastVerified: "Patikrinta",
    hours: "Valandos",
    cat_kebab: "Kebabai",
    cat_pizza: "Pica",
    cat_soup: "Sriubos",
    cat_main: "Pagrindiniai",
    cat_dessert: "Desertai",
    cat_drink: "Gėrimai",
    cat_other: "Kita",
    weekday_0: "Pr",
    weekday_1: "An",
    weekday_2: "Tr",
    weekday_3: "Kt",
    weekday_4: "Pn",
    weekday_5: "Št",
    weekday_6: "Sk",
    nut_free: "Be riešutų",
    pescatarian: "Peskatariška",
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
    searching: "Searching…",
    searchError: "Could not search items.",
    menu: "Menu",
    closePlace: "Close",
    placeError: "Could not load this place's menu.",
    loadingMenu: "Loading menu…",
    lastVerified: "Verified",
    hours: "Hours",
    cat_kebab: "Kebabs",
    cat_pizza: "Pizza",
    cat_soup: "Soups",
    cat_main: "Mains",
    cat_dessert: "Desserts",
    cat_drink: "Drinks",
    cat_other: "Other",
    weekday_0: "Mon",
    weekday_1: "Tue",
    weekday_2: "Wed",
    weekday_3: "Thu",
    weekday_4: "Fri",
    weekday_5: "Sat",
    weekday_6: "Sun",
    nut_free: "Nut-free",
    pescatarian: "Pescatarian",
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

export const CATEGORY_ORDER = [
  "kebab",
  "pizza",
  "soup",
  "main",
  "dessert",
  "drink",
  "other",
];

export function categoryLabel(category, copy) {
  return copy[`cat_${category}`] ?? category;
}

export function formatVerified(iso, copy, lang) {
  if (!iso) {
    return null;
  }
  const date = new Date(iso);
  if (Number.isNaN(date.getTime())) {
    return `${copy.lastVerified} ${iso}`;
  }
  const formatted = date.toLocaleDateString(lang === "lt" ? "lt-LT" : "en-GB", {
    year: "numeric",
    month: "short",
    day: "numeric",
  });
  return `${copy.lastVerified} ${formatted}`;
}

export function formatMinutes(total) {
  const hours = Math.floor(total / 60);
  const minutes = total % 60;
  return `${String(hours).padStart(2, "0")}:${String(minutes).padStart(2, "0")}`;
}

export function groupItemsByCategory(items) {
  const groups = new Map();
  for (const item of items) {
    const category = CATEGORY_ORDER.includes(item.category)
      ? item.category
      : "other";
    const bucket = groups.get(category);
    if (bucket) {
      bucket.push(item);
    } else {
      groups.set(category, [item]);
    }
  }
  return CATEGORY_ORDER.filter((category) => groups.has(category)).map(
    (category) => [category, groups.get(category)],
  );
}
