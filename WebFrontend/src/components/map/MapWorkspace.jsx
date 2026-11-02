
import { useEffect, useRef, useState } from "react";
import L from "leaflet";
import "leaflet/dist/leaflet.css";
import "leaflet.markercluster";
import "leaflet.markercluster/dist/MarkerCluster.css";
import "leaflet.markercluster/dist/MarkerCluster.Default.css";

import { Layers, Plus, Minus, Crosshair } from "lucide-react";
import { fetchGeographicalComponents } from "../../services/AssetService";

const categoryColors = {
  building: "#8B8172",
  school: "#D6A85F",
  college: "#78958A",
  hospital: "#C97961",
  forest: "#4D8060",
  river: "#6C91A0",
  lake: "#5796AD",
  water: "#438DA8",
  road: "#8B8172",
  land_use: "#9B8C70",
  public_facility: "#B58B65",
  infrastructure: "#817D91",
  commercial: "#A58A68",
  park: "#638A67",
  transport: "#7895A6",
  railway: "#927D9B",
  settlement: "#A18C76",
  tourism: "#B68B69",
  other: "#898989",
};

export default function MapWorkspace({ onSelectAsset }) {
  const mapElement = useRef(null);
  const mapInstance = useRef(null);
  const clusterLayer = useRef(null);
  const onSelectAssetRef = useRef(onSelectAsset);

  const [components, setComponents] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    onSelectAssetRef.current = onSelectAsset;
  }, [onSelectAsset]);

  // Initialize the Leaflet map.
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
      chunkedLoading: true,
    });

    map.addLayer(clusters);

    mapInstance.current = map;
    clusterLayer.current = clusters;

    let debounceTimer;
    let requestNumber = 0;

    // Fetch only the geographical area visible on the map.
    async function loadVisibleComponents() {
      const currentRequest = ++requestNumber;
      const bounds = map.getBounds();

      try {
        setLoading(true);
        setError("");

        const records = await fetchGeographicalComponents({
          minLat: bounds.getSouth(),
          minLon: bounds.getWest(),
          maxLat: bounds.getNorth(),
          maxLon: bounds.getEast(),
          limit: 5000,
          offset: 0,
        });

        // Ignore outdated responses from previous map movements.
        if (currentRequest !== requestNumber) return;

        setComponents(records);
      } catch (err) {
        if (currentRequest !== requestNumber) return;

        console.error("Geographical data loading failed:", err);
        setError(err.message || "Unable to load geographical data.");
      } finally {
        if (currentRequest === requestNumber) {
          setLoading(false);
        }
      }
    }

    function scheduleDataLoad() {
      clearTimeout(debounceTimer);

      debounceTimer = setTimeout(() => {
        loadVisibleComponents();
      }, 300);
    }

    map.on("moveend", scheduleDataLoad);

    // Initial data load.
    loadVisibleComponents();

    setTimeout(() => map.invalidateSize(), 150);

    return () => {
      clearTimeout(debounceTimer);
      requestNumber++;

      map.off("moveend", scheduleDataLoad);
      map.remove();

      mapInstance.current = null;
      clusterLayer.current = null;
    };
  }, []);

  // Render geographical components as clustered markers.
  useEffect(() => {
    if (!clusterLayer.current) return;

    const clusters = clusterLayer.current;
    clusters.clearLayers();

    const markers = [];

    components.forEach((component) => {
      const latitude = Number(component.latitude);
      const longitude = Number(component.longitude);

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

      const color =
        categoryColors[component.category] || "#78958A";

      const marker = L.marker([latitude, longitude], {
        icon: L.divIcon({
          className: "asset-marker-wrapper",
          html: `<div class="asset-marker" style="background:${color}"></div>`,
          iconSize: [18, 18],
          iconAnchor: [9, 9],
        }),
      });

      marker.bindPopup(`
        <strong>${escapeHtml(component.name || "Unnamed feature")}</strong><br/>
        Category: ${escapeHtml(component.category)}<br/>
        Type: ${escapeHtml(component.component_type || "Not specified")}<br/>
        Source: OpenStreetMap<br/>
        Status: ${escapeHtml(component.verification_status || "unverified")}
      `);

      marker.on("click", () => {
        onSelectAssetRef.current?.(component);
      });

      markers.push(marker);
    });

    clusters.addLayers(markers);
  }, [components]);

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
          <span>
            {loading
              ? "Loading geographical data..."
              : `${components.length.toLocaleString()} components loaded`}
          </span>
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

        {error && (
          <div className="asset-error">
            Data loading failed: {error}
          </div>
        )}

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
