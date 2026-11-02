
import { useEffect, useRef } from "react";
import L from "leaflet";
import "leaflet/dist/leaflet.css";
import "leaflet.markercluster";
import "leaflet.markercluster/dist/MarkerCluster.css";
import "leaflet.markercluster/dist/MarkerCluster.Default.css";

import { Layers, Plus, Minus, Crosshair } from "lucide-react";

const categoryColors = {
  school: "#D6A85F",
  college: "#78958A",
  hospital: "#C97961",
  forest: "#4D8060",
  river: "#6C91A0",
  lake: "#5796AD",
  water_tank: "#438DA8",
  road: "#8B8172",
};

export default function MapWorkspace({ assets = [], onSelectAsset }) {
  const mapElement = useRef(null);
  const mapInstance = useRef(null);
  const clusterLayer = useRef(null);

  useEffect(() => {
    if (!mapElement.current || mapInstance.current) return;

    const map = L.map(mapElement.current, {
      center: [12.9716, 77.5946],
      zoom: 12,
      zoomControl: false,
    });

    L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
      attribution:
        '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
      maxZoom: 19,
    }).addTo(map);

    const clusters = L.markerClusterGroup({
      showCoverageOnHover: false,
      spiderfyOnMaxZoom: true,
      maxClusterRadius: 45,
    });

    map.addLayer(clusters);

    mapInstance.current = map;
    clusterLayer.current = clusters;

    setTimeout(() => map.invalidateSize(), 150);

    return () => {
      map.remove();
      mapInstance.current = null;
      clusterLayer.current = null;
    };
  }, []);

  useEffect(() => {
    if (!clusterLayer.current) return;

    const clusters = clusterLayer.current;
    clusters.clearLayers();

    assets.forEach((asset) => {
      const latitude = Number(asset.latitude);
      const longitude = Number(asset.longitude);

      if (
        !Number.isFinite(latitude) ||
        !Number.isFinite(longitude) ||
        latitude < -90 ||
        latitude > 90 ||
        longitude < -180 ||
        longitude > 180
      ) {
        return;
      }

      const color = categoryColors[asset.category] || "#78958A";

      const marker = L.marker([latitude, longitude], {
        icon: L.divIcon({
          className: "asset-marker-wrapper",
          html: `<div class="asset-marker" style="background:${color}"></div>`,
          iconSize: [18, 18],
          iconAnchor: [9, 9],
        }),
      });

      marker.bindPopup(`
        <strong>${escapeHtml(asset.name)}</strong><br/>
        ${escapeHtml(asset.category)}<br/>
        ${escapeHtml(asset.village)}
      `);

      marker.on("click", () => {
        onSelectAsset?.(asset);
      });

      clusters.addLayer(marker);
    });
  }, [assets, onSelectAsset]);

  const zoomIn = () => mapInstance.current?.zoomIn();
  const zoomOut = () => mapInstance.current?.zoomOut();

  const locate = () => {
    mapInstance.current?.setView([12.9716, 77.5946], 14);
  };

  return (
    <section className="map-workspace">
      <div className="map-toolbar">
        <div>
          <strong>Map View</strong>
          <span>{assets.length} assets loaded</span>
        </div>

        <button
          className="map-tool-button"
          onClick={() => mapInstance.current?.invalidateSize()}
        >
          <Layers size={16} />
          Layers
        </button>
      </div>

      <div className="map-canvas">
        <div ref={mapElement} className="leaflet-map-container" />

        <div className="map-controls">
          <button onClick={zoomIn} title="Zoom in">
            <Plus size={18} />
          </button>
          <button onClick={zoomOut} title="Zoom out">
            <Minus size={18} />
          </button>
          <button onClick={locate} title="Return to Bengaluru">
            <Crosshair size={18} />
          </button>
        </div>
      </div>
    </section>
  );
}

function escapeHtml(value) {
  return String(value ?? "").replace(/[&<>"']/g, (character) => ({
    "&": "&amp;",
    "<": "&lt;",
    ">": "&gt;",
    '"': "&quot;",
    "'": "&#039;",
  })[character]);
}
