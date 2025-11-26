import React from "react";
import type { RunTrack } from "../api";

// These imports require: npm i react-leaflet leaflet
import { MapContainer, TileLayer, Polyline, Marker, useMap, ZoomControl } from "react-leaflet";
import L from "leaflet";

const startIcon = L.divIcon({
  className: "",
  html: '<div style="width:10px;height:10px;background:#10b981;border:2px solid #064e3b;border-radius:9999px"></div>',
  iconSize: [14, 14],
  iconAnchor: [7, 7],
});
const endIcon = L.divIcon({
  className: "",
  html: '<div style="width:10px;height:10px;background:#ef4444;border:2px solid #7f1d1d;border-radius:9999px"></div>',
  iconSize: [14, 14],
  iconAnchor: [7, 7],
});

function FitBounds({ bounds }: { bounds: L.LatLngBoundsExpression }) {
  const map = useMap();
  React.useEffect(() => {
    map.fitBounds(bounds, { padding: [12, 12] });
  }, [map, bounds]);
  return null;
}

export default function RunMap({ track }: { track: RunTrack }) {
  if (!track.geojson || !track.bounds) return <p className="text-slate-500">No GPS track</p>;
  const positions = track.geojson.coordinates.map(([lon, lat]) => [lat, lon]) as [number, number][];
  const bounds: L.LatLngBoundsExpression = [
    [track.bounds.minLat, track.bounds.minLon],
    [track.bounds.maxLat, track.bounds.maxLon],
  ];

  const start = positions[0];
  const end = positions[positions.length - 1];

  return (
    <div className="rounded-lg border border-slate-700 overflow-hidden">
      <MapContainer
        style={{ height: 260, width: "100%" }}
        bounds={bounds}
        scrollWheelZoom={false}
        dragging={true}
        zoomControl={true}
        attributionControl={false}
      >
        {/* Dark, modern basemap (Carto Dark Matter) */}
        <TileLayer
          url="https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png"
          attribution="&copy; <a href='https://www.openstreetmap.org/copyright'>OSM</a> &copy; <a href='https://carto.com/attributions'>CARTO</a>"
        />
        {/* Route with subtle glow (stacked polylines) */}
        <Polyline positions={positions} color="#06b6d4" weight={8} opacity={0.25} />
        <Polyline positions={positions} color="#38bdf8" weight={4} opacity={0.95} />
        <Marker position={start} icon={startIcon} />
        <Marker position={end} icon={endIcon} />
        <FitBounds bounds={bounds} />
        <ZoomControl position="topright" />
      </MapContainer>
    </div>
  );
}
