import { useCallback, useEffect, useRef, useState } from "react";
import {
  MapContainer,
  Marker,
  Popup,
  TileLayer,
  useMap,
  useMapEvents,
} from "react-leaflet";
import L from "leaflet";
import "leaflet/dist/leaflet.css";
import markerIcon from "leaflet/dist/images/marker-icon.png";
import markerIcon2x from "leaflet/dist/images/marker-icon-2x.png";
import markerShadow from "leaflet/dist/images/marker-shadow.png";

delete L.Icon.Default.prototype._getIconUrl;
L.Icon.Default.mergeOptions({
  iconUrl: markerIcon,
  iconRetinaUrl: markerIcon2x,
  shadowUrl: markerShadow,
});

const VILNIUS = [54.6872, 25.2798];
const DEFAULT_ZOOM = 13;
const DEBOUNCE_MS = 300;

function bboxQuery(bounds) {
  const south = bounds.getSouth();
  const west = bounds.getWest();
  const north = bounds.getNorth();
  const east = bounds.getEast();
  return `${south},${west},${north},${east}`;
}

function BoundsFetcher({ onBounds, enabled }) {
  const map = useMapEvents({
    moveend() {
      if (enabled) onBounds(map.getBounds());
    },
    zoomend() {
      if (enabled) onBounds(map.getBounds());
    },
  });

  useEffect(() => {
    if (enabled) onBounds(map.getBounds());
  }, [enabled, map, onBounds]);

  return null;
}

function FlyTo({ place }) {
  const map = useMap();
  useEffect(() => {
    if (!place) return;
    map.flyTo(
      [place.lat, place.lng],
      Math.max(map.getZoom(), 15),
      { duration: 0.35 },
    );
  }, [place, map]);
  return null;
}

export default function PlacesMap({
  places: controlledPlaces,
  selectedPlace,
  labels,
  onSelectPlace,
}) {
  const fetchMode = controlledPlaces == null;
  const [fetched, setFetched] = useState([]);
  const [fetchedLoaded, setFetchedLoaded] = useState(false);
  const [fetchError, setFetchError] = useState(null);
  const timer = useRef(null);
  const places = fetchMode ? fetched : controlledPlaces;
  const loaded = fetchMode ? fetchedLoaded : true;
  const error = fetchMode ? fetchError : null;

  const loadBounds = useCallback(
    (bounds) => {
      if (!fetchMode) return;
      if (timer.current) window.clearTimeout(timer.current);
      timer.current = window.setTimeout(async () => {
        const bbox = bboxQuery(bounds);
        try {
          const response = await fetch(
            `/api/places?bbox=${encodeURIComponent(bbox)}`,
          );
          if (!response.ok) {
            throw new Error(`places ${response.status}`);
          }
          const body = await response.json();
          const next = Array.isArray(body.places) ? body.places : [];
          setFetched(next);
          setFetchError(null);
          setFetchedLoaded(true);
        } catch {
          setFetchError(labels.mapError);
          setFetchedLoaded(true);
        }
      }, DEBOUNCE_MS);
    },
    [fetchMode, labels.mapError],
  );

  useEffect(() => {
    return () => {
      if (timer.current) window.clearTimeout(timer.current);
    };
  }, []);

  const empty = loaded && !error && places.length === 0;

  return (
    <section className="places-map-wrap" aria-label={labels.mapAria}>
      {error ? (
        <p className="map-status" role="status">
          {error}
        </p>
      ) : null}
      {empty ? (
        <p className="map-status" role="status">
          {labels.noPlacesInView}
        </p>
      ) : null}
      <MapContainer
        className="places-map"
        center={VILNIUS}
        zoom={DEFAULT_ZOOM}
        scrollWheelZoom
      >
        <TileLayer
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
        />
        <BoundsFetcher onBounds={loadBounds} enabled={fetchMode} />
        <FlyTo place={selectedPlace} />
        {places.map((place) => (
          <Marker
            key={place.id}
            position={[place.lat, place.lng]}
            title={place.name}
            eventHandlers={{
              click: () => onSelectPlace?.(place),
            }}
          >
            <Popup>
              <strong>{place.name}</strong>
              <br />
              {place.address}
            </Popup>
          </Marker>
        ))}
      </MapContainer>
    </section>
  );
}
