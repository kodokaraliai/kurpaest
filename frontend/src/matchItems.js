/** Pins for an item query. Matching itself is GET /items. */

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
