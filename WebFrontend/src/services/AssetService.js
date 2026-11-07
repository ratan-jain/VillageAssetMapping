
const API_URL = "http://127.0.0.1:8000/api";

// Existing sample-assets API — retained temporarily.
export async function fetchAssets() {
  const response = await fetch(`${API_URL}/assets`);

  if (!response.ok) {
    throw new Error(`Failed to fetch assets: ${response.status}`);
  }

  const data = await response.json();
  return data.assets ?? [];
}

// New OpenStreetMap geographical-components API.
export async function fetchGeographicalComponents({
  minLat,
  minLon,
  maxLat,
  maxLon,
  category = null,
  limit = 5000,
  offset = 0,
}) {
  const params = new URLSearchParams({
    min_lat: String(minLat),
    min_lon: String(minLon),
    max_lat: String(maxLat),
    max_lon: String(maxLon),
    limit: String(limit),
    offset: String(offset),
  });

  if (category) {
    params.set("category", category);
  }

  const response = await fetch(
    `${API_URL}/geographical-components?${params.toString()}`
  );

  if (!response.ok) {
    throw new Error(
      `Failed to fetch geographical components: ${response.status}`
    );
  }

  const data = await response.json();

  return data.components ?? [];
}
