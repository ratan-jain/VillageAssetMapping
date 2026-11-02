
import { useEffect, useState } from "react";
import Sidebar from "./Sidebar";
import Header from "./Header";
import MapWorkspace from "../map/MapWorkspace";
import { fetchAssets } from "../../services/AssetService";

export default function DashboardLayout() {
  const [assets, setAssets] = useState([]);
  const [selectedAsset, setSelectedAsset] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    async function loadAssets() {
      try {
        setLoading(true);
        const records = await fetchAssets();
        setAssets(records);
        setError("");
      } catch (err) {
        console.error("Asset loading failed:", err);
        setError(err.message || "Unable to load assets.");
      } finally {
        setLoading(false);
      }
    }

    loadAssets();
  }, []);

  return (
    <div className="dashboard-layout">
      <Sidebar />

      <main className="main-area">
        <Header />

        <div className="workspace">
          <aside className="layer-panel">
            <div className="panel-heading">
              <h2>Map Layers</h2>
              <span>{String(assets.length).padStart(2, "0")}</span>
            </div>

            <div className="panel-section">
              <label>GEOGRAPHICAL DATA</label>
              <p>Base map</p>
              <p>Administrative boundaries</p>
              <p>Settlement areas</p>
            </div>

            <div className="panel-section">
              <label>ASSET CATEGORIES</label>
              {[
                "school",
                "college",
                "hospital",
                "forest",
                "river",
                "lake",
                "water_tank",
                "road",
              ].map((category) => (
                <p key={category}>
                  {category.replace("_", " ").replace(/\b\w/g, (c) => c.toUpperCase())}
                  <span>
                    {assets.filter((asset) => asset.category === category).length}
                  </span>
                </p>
              ))}
            </div>
          </aside>

          <div className="map-content">
            {error && (
              <div className="asset-error">
                API connection failed: {error}
              </div>
            )}

            {loading && (
              <div className="asset-loading">Loading village assets...</div>
            )}

            <MapWorkspace
              assets={assets}
              onSelectAsset={setSelectedAsset}
            />
          </div>

          <aside className="inspector-panel">
            <div className="panel-heading">
              <h2>Inspector</h2>
              <span>{selectedAsset ? "01" : "—"}</span>
            </div>

            {selectedAsset ? (
              <div className="inspector-details">
                <label>ASSET INFORMATION</label>
                <h3>{selectedAsset.name}</h3>
                <p><strong>ID:</strong> {selectedAsset.id}</p>
                <p><strong>Village:</strong> {selectedAsset.village}</p>
                <p><strong>Category:</strong> {selectedAsset.category}</p>
                <p><strong>Owner:</strong> {selectedAsset.owner_name || "Not specified"}</p>
                <p><strong>Ownership:</strong> {selectedAsset.owner_type}</p>
                <p><strong>Authority:</strong> {selectedAsset.managing_authority || "Not specified"}</p>
                <p><strong>Verification:</strong> {selectedAsset.verification_status}</p>
                <p><strong>Latitude:</strong> {selectedAsset.latitude}</p>
                <p><strong>Longitude:</strong> {selectedAsset.longitude}</p>

                <button onClick={() => setSelectedAsset(null)}>
                  Clear selection
                </button>
              </div>
            ) : (
              <div className="inspector-empty">
                <div className="inspector-icon">⌖</div>
                <strong>No selection</strong>
                <p>Select an asset marker on the map to inspect its details.</p>
              </div>
            )}
          </aside>
        </div>
      </main>
    </div>
  );
}
