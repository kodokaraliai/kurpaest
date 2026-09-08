import { useCallback, useEffect, useMemo, useState } from "react";
import PlacePanel from "./PlacePanel.jsx";
import PlacesMap from "./PlacesMap.jsx";
import ResultsList from "./ResultsList.jsx";
import { COPY, DIETARY_IDS } from "./copy.js";
import { placesForItems } from "./matchItems.js";
import "./App.css";

const LANG_KEY = "kurpaest.lang";

function readLang() {
  try {
    const stored = window.localStorage.getItem(LANG_KEY);
    if (stored === "en" || stored === "lt") {
      return stored;
    }
  } catch {
    // private mode
  }
  return "lt";
}

function App() {
  const [lang, setLang] = useState(readLang);
  const [term, setTerm] = useState("");
  const [dietary, setDietary] = useState([]);
  const [selectedId, setSelectedId] = useState(null);
  const [openPlaceId, setOpenPlaceId] = useState(null);
  const [results, setResults] = useState([]);
  const [searchLoading, setSearchLoading] = useState(false);
  const [searchError, setSearchError] = useState(null);
  const copy = COPY[lang];

  useEffect(() => {
    document.documentElement.lang = lang;
    try {
      window.localStorage.setItem(LANG_KEY, lang);
    } catch {
      // private mode
    }
  }, [lang]);

  const queryActive = term.trim() !== "" || dietary.length > 0;

  useEffect(() => {
    if (!queryActive) {
      setResults([]);
      setSearchError(null);
      setSearchLoading(false);
      return undefined;
    }
    const controller = new AbortController();
    setSearchLoading(true);
    const timer = window.setTimeout(async () => {
      const params = new URLSearchParams();
      if (term.trim()) {
        params.set("q", term.trim());
      }
      params.set("sort", "price");
      if (dietary.length > 0) {
        params.set("dietary", dietary.join(","));
      }
      try {
        const response = await fetch(`/api/items?${params.toString()}`, {
          signal: controller.signal,
        });
        if (!response.ok) {
          throw new Error(`items ${response.status}`);
        }
        const body = await response.json();
        setResults(Array.isArray(body.items) ? body.items : []);
        setSearchError(null);
      } catch (err) {
        if (err instanceof DOMException && err.name === "AbortError") {
          return;
        }
        setResults([]);
        setSearchError(copy.searchError);
      } finally {
        if (!controller.signal.aborted) {
          setSearchLoading(false);
        }
      }
    }, 300);
    return () => {
      window.clearTimeout(timer);
      controller.abort();
    };
  }, [term, dietary, queryActive, copy.searchError]);

  const mapPlaces = useMemo(
    () => (queryActive ? placesForItems(results) : undefined),
    [queryActive, results],
  );
  const selectedItem = results.find((item) => item.id === selectedId) ?? null;

  const toggleDietary = useCallback((id) => {
    setDietary((current) =>
      current.includes(id)
        ? current.filter((tag) => tag !== id)
        : [...current, id],
    );
  }, []);

  return (
    <div className="app">
      <header className="topbar">
        <div className="topbar-row">
          <p className="brand">{copy.brand}</p>
          <div className="lang" role="group" aria-label={copy.language}>
            <button
              type="button"
              className="lang-btn"
              aria-pressed={lang === "lt"}
              onClick={() => setLang("lt")}
            >
              LT
            </button>
            <button
              type="button"
              className="lang-btn"
              aria-pressed={lang === "en"}
              onClick={() => setLang("en")}
            >
              EN
            </button>
          </div>
        </div>
        <h1>{copy.title}</h1>
        <p className="lede">{copy.lede}</p>
      </header>

      <form
        className="search"
        role="search"
        onSubmit={(event) => event.preventDefault()}
      >
        <label htmlFor="item-query">{copy.lookingFor}</label>
        <div className="search-row">
          <input
            id="item-query"
            name="q"
            type="search"
            value={term}
            onChange={(event) => setTerm(event.target.value)}
            placeholder={copy.placeholder}
            autoComplete="off"
          />
          <button type="submit">{copy.findCheapest}</button>
        </div>
      </form>

      <div className="chips" role="group" aria-label={copy.dietaryAria}>
        {DIETARY_IDS.map((id) => (
          <label
            key={id}
            className={dietary.includes(id) ? "chip is-on" : "chip"}
          >
            <input
              type="checkbox"
              name="dietary"
              value={id}
              checked={dietary.includes(id)}
              onChange={() => toggleDietary(id)}
            />
            {copy[id]}
          </label>
        ))}
      </div>
      {dietary.length > 0 ? (
        <p className="filter-note" role="status">
          {copy.showingVerified}
        </p>
      ) : null}

      <div className="workspace">
        <PlacesMap
          places={mapPlaces}
          selectedPlace={selectedItem?.place}
          onSelectPlace={(place) => setOpenPlaceId(place.id)}
          labels={{
            mapAria: copy.mapAria,
            mapError: copy.mapError,
            noPlacesInView: copy.noPlacesInView,
          }}
        />
        {openPlaceId ? (
          <PlacePanel
            placeId={openPlaceId}
            lang={lang}
            copy={copy}
            onClose={() => setOpenPlaceId(null)}
          />
        ) : (
          <ResultsList
            items={results}
            active={queryActive}
            lang={lang}
            copy={copy}
            selectedId={selectedId}
            onSelect={(item) => setSelectedId(item.id)}
            loading={searchLoading}
            error={searchError}
          />
        )}
      </div>
    </div>
  );
}

export default App;
