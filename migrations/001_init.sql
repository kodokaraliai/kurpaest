CREATE EXTENSION IF NOT EXISTS postgis;

CREATE TABLE IF NOT EXISTS places (
    id UUID PRIMARY KEY,
    name TEXT NOT NULL,
    slug TEXT NOT NULL,
    location geography(Point, 4326) NOT NULL,
    address TEXT NOT NULL,
    city TEXT NOT NULL,
    hours JSONB NOT NULL DEFAULT '[]'::jsonb,
    source TEXT NOT NULL,
    updated_at TIMESTAMPTZ NOT NULL,
    phone TEXT,
    website TEXT,
    UNIQUE (city, slug)
);

CREATE INDEX IF NOT EXISTS places_location_gix ON places USING gist (location);

CREATE TABLE IF NOT EXISTS menus (
    id UUID PRIMARY KEY,
    place_id UUID NOT NULL REFERENCES places (id),
    currency TEXT NOT NULL,
    last_verified_at TIMESTAMPTZ NOT NULL,
    language TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS menu_items (
    id UUID PRIMARY KEY,
    place_id UUID NOT NULL REFERENCES places (id),
    menu_id UUID NOT NULL REFERENCES menus (id),
    name TEXT NOT NULL,
    name_en TEXT,
    description TEXT,
    price_cents INTEGER NOT NULL,
    category TEXT NOT NULL,
    dietary_tags TEXT[] NOT NULL DEFAULT '{}',
    search_tokens TEXT[] NOT NULL DEFAULT '{}'
);

CREATE INDEX IF NOT EXISTS menu_items_place_id_idx ON menu_items (place_id);
CREATE INDEX IF NOT EXISTS menu_items_menu_id_idx ON menu_items (menu_id);
