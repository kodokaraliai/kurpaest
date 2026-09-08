import "./App.css";

const DIETARY = [
  { id: "vegan", label: "Vegan" },
  { id: "vegetarian", label: "Vegetarian" },
  { id: "gluten_free", label: "Gluten-free" },
  { id: "lactose_free", label: "Lactose-free" },
  { id: "halal", label: "Halal" },
];

function App() {
  return (
    <div className="app">
      <header className="topbar">
        <p className="brand">kurpaest.lt</p>
        <h1>Kur paėst</h1>
        <p className="lede">
          A queryable map of places to eat, with an itemized menu for each
          place. Find the cheapest kebab — or anything that matches how you
          eat.
        </p>
      </header>

      <form
        className="search"
        role="search"
        onSubmit={(event) => event.preventDefault()}
      >
        <label htmlFor="item-query">Looking for</label>
        <div className="search-row">
          <input
            id="item-query"
            name="q"
            type="search"
            placeholder="kebabas, cepelinai, pizza…"
            autoComplete="off"
          />
          <button type="submit">Find cheapest</button>
        </div>
      </form>

      <div className="chips" role="group" aria-label="Dietary preferences">
        {DIETARY.map((tag) => (
          <label key={tag.id} className="chip">
            <input type="checkbox" name="dietary" value={tag.id} />
            {tag.label}
          </label>
        ))}
      </div>

      <section
        className="map-placeholder"
        aria-label="Map of places to eat"
      >
        <p>
          The map, itemized menus, cheapest-item search, and dietary filters
          are the work packages in{" "}
          <code>docs/architecture.md</code> — this page is the launchable
          shell.
        </p>
      </section>
    </div>
  );
}

export default App;
