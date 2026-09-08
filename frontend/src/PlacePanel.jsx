import { useEffect, useState } from "react";
import {
  categoryLabel,
  formatMinutes,
  formatPrice,
  formatVerified,
  groupItemsByCategory,
  itemLabel,
} from "./copy.js";

function HoursList({ hours, copy }) {
  if (!Array.isArray(hours) || hours.length === 0) {
    return null;
  }
  return (
    <section className="place-hours" aria-label={copy.hours}>
      <h3>{copy.hours}</h3>
      <ul>
        {hours.map((interval) => (
          <li key={`${interval.weekday}-${interval.open_minute}`}>
            <span>{copy[`weekday_${interval.weekday}`] ?? interval.weekday}</span>
            <span>
              {formatMinutes(interval.open_minute)}–
              {formatMinutes(interval.close_minute)}
            </span>
          </li>
        ))}
      </ul>
    </section>
  );
}

function TagList({ tags, copy }) {
  if (!tags || tags.length === 0) {
    return null;
  }
  return (
    <ul className="item-tags">
      {tags.map((tag) => (
        <li key={tag}>{copy[tag] ?? tag}</li>
      ))}
    </ul>
  );
}

export default function PlacePanel({ placeId, lang, copy, onClose }) {
  const [place, setPlace] = useState(null);
  const [menu, setMenu] = useState(null);
  const [error, setError] = useState(null);
  const [loaded, setLoaded] = useState(false);

  useEffect(() => {
    let cancelled = false;
    setLoaded(false);
    setError(null);
    setPlace(null);
    setMenu(null);

    async function load() {
      try {
        const [placeRes, menuRes] = await Promise.all([
          fetch(`/api/places/${placeId}`),
          fetch(`/api/places/${placeId}/menu`),
        ]);
        if (!placeRes.ok || !menuRes.ok) {
          throw new Error("place menu fetch failed");
        }
        const placeBody = await placeRes.json();
        const menuBody = await menuRes.json();
        if (!cancelled) {
          setPlace(placeBody);
          setMenu(menuBody);
          setLoaded(true);
        }
      } catch {
        if (!cancelled) {
          setError(copy.placeError);
          setLoaded(true);
        }
      }
    }

    load();
    return () => {
      cancelled = true;
    };
  }, [placeId, copy.placeError]);

  const verified = formatVerified(
    menu?.last_verified_at ?? place?.last_verified_at,
    copy,
    lang,
  );
  const groups = groupItemsByCategory(menu?.items ?? []);

  let body;
  if (!loaded) {
    body = (
      <p className="empty-state" role="status">
        {copy.loadingMenu}
      </p>
    );
  } else if (error) {
    body = (
      <p className="empty-state" role="status">
        {error}
      </p>
    );
  } else {
    body = (
      <>
        <p className="place-address">{place.address}</p>
        {verified ? (
          <p className="place-verified" role="status">
            {verified}
          </p>
        ) : null}
        <HoursList hours={place.hours} copy={copy} />
        {groups.map(([category, items]) => (
          <section key={category} className="menu-group">
            <h3>{categoryLabel(category, copy)}</h3>
            <ul className="menu-items">
              {items.map((item) => (
                <li key={item.id} className="menu-item">
                  <div className="menu-item-row">
                    <span className="result-name">{itemLabel(item, lang)}</span>
                    <span className="result-price">
                      {formatPrice(item.price_cents, lang)}
                    </span>
                  </div>
                  {item.description ? (
                    <p className="menu-item-desc">{item.description}</p>
                  ) : null}
                  <TagList tags={item.dietary_tags} copy={copy} />
                </li>
              ))}
            </ul>
          </section>
        ))}
      </>
    );
  }

  return (
    <aside className="results place-panel" aria-label={copy.menu}>
      <div className="place-panel-head">
        <h2>{place?.name ?? copy.menu}</h2>
        <button type="button" className="place-close" onClick={onClose}>
          {copy.closePlace}
        </button>
      </div>
      {body}
    </aside>
  );
}
