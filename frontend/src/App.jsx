import { useCallback, useEffect, useMemo, useState } from "react";
import PlacesMap from "./PlacesMap.jsx";
import ResultsList from "./ResultsList.jsx";
import { COPY, DIETARY_IDS } from "./copy.js";
import { matchingItems, placesForItems } from "./matchItems.js";
import MOCK_ITEMS from "./mock/items.json";
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
  const results = useMemo(
    () => matchingItems(MOCK_ITEMS, { term, dietary }),
    [term, dietary],
  );
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
          labels={{
            mapAria: copy.mapAria,
            mapError: copy.mapError,
            noPlacesInView: copy.noPlacesInView,
          }}
        />
        <ResultsList
          items={results}
          active={queryActive}
          lang={lang}
          copy={copy}
          selectedId={selectedId}
          onSelect={(item) => setSelectedId(item.id)}
        />
      </div>
    </div>
  );
}

export default App;
