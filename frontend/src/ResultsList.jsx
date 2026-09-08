import { formatPrice, itemLabel } from "./copy.js";

export default function ResultsList({
  items,
  active,
  lang,
  copy,
  selectedId,
  onSelect,
  loading = false,
  error = null,
}) {
  let body;
  if (!active) {
    body = (
      <p className="empty-state" role="status">
        {copy.searchPrompt}
      </p>
    );
  } else if (loading) {
    body = (
      <p className="empty-state" role="status">
        {copy.searching}
      </p>
    );
  } else if (error) {
    body = (
      <p className="empty-state" role="status">
        {error}
      </p>
    );
  } else if (items.length === 0) {
    body = (
      <p className="empty-state" role="status">
        {copy.noMatchingItems}
      </p>
    );
  } else {
    body = (
      <ol className="results-list">
        {items.map((item) => {
          const selected = item.id === selectedId;
          return (
            <li key={item.id}>
              <button
                type="button"
                className={selected ? "result-row is-selected" : "result-row"}
                onClick={() => onSelect(item)}
                aria-current={selected ? "true" : undefined}
              >
                <span className="result-name">{itemLabel(item, lang)}</span>
                <span className="result-place">{item.place.name}</span>
                <span className="result-price">
                  {formatPrice(item.price_cents, lang)}
                </span>
                <span className="visually-hidden">{copy.showOnMap}</span>
              </button>
            </li>
          );
        })}
      </ol>
    );
  }

  return (
    <aside className="results" aria-label={copy.results}>
      <h2>{copy.results}</h2>
      {body}
    </aside>
  );
}
