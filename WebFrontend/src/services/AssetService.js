
const API_URL = "http://127.0.0.1:8000/api";

export async function fetchAssets() {
  const response = await fetch(`${API_URL}/assets`);

  if (!response.ok) {
    throw new Error(`Failed to fetch assets: ${response.status}`);
  }

  const data = await response.json();

  return data.assets ?? [];
}
