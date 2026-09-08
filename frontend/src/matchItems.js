/** Client-side stand-in until WP-5/WP-6 hang off GET /items. */

export function matchingItems(items, { term, dietary }) {
  const query = term.trim().toLowerCase();
  const tags = dietary;
  const found = items.filter((item) => {
    if (tags.length > 0) {
      const have = new Set(item.dietary_tags ?? []);
      if (!tags.every((tag) => have.has(tag))) {
        return false;
      }
    }
    if (!query) {
      return tags.length > 0;
    }
    const hay = [item.name, item.name_en, ...(item.search_tokens ?? [])]
      .filter(Boolean)
      .join(" ")
      .toLowerCase();
    return hay.includes(query);
  });
  return found.slice().sort((a, b) => a.price_cents - b.price_cents);
}

export function placesForItems(items) {
  const seen = new Set();
  const places = [];
  for (const item of items) {
    const place = item.place;
    if (!place || seen.has(place.id)) {
      continue;
    }
    seen.add(place.id);
    places.push(place);
  }
  return places;
}
