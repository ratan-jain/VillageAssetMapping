
const API_URL = "http://127.0.0.1:8000/api";

let map;
let allAssets = [];
let markerCluster;
let markers = new Map();
let selectedAssetId = null;

// --------------------------------------------------
// INITIALIZE MAP
// --------------------------------------------------

function initializeMap() {
    map = L.map("map").setView([12.9716, 77.5946], 14);

    L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
        attribution:
            '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
        maxZoom: 19
    }).addTo(map);

    markerCluster = L.markerClusterGroup({
        showCoverageOnHover: false,
        spiderfyOnMaxZoom: true,
        zoomToBoundsOnClick: true,
        maxClusterRadius: 45
    });

    map.addLayer(markerCluster);
}

// --------------------------------------------------
// MARKER COLORS
// --------------------------------------------------

function getMarkerColor(category) {
    const colors = {
        school: "#3b82f6",
        college: "#6366f1",
        hospital: "#ef4444",
        forest: "#22c55e",
        river: "#06b6d4",
        lake: "#0ea5e9",
        water_tank: "#0891b2",
        road: "#f59e0b"
    };

    return colors[category] || "#a855f7";
}

// --------------------------------------------------
// VALIDATE COORDINATES
// --------------------------------------------------

function hasValidCoordinates(asset) {
    return (
        Number.isFinite(Number(asset.latitude)) &&
        Number.isFinite(Number(asset.longitude)) &&
        Number(asset.latitude) >= -90 &&
        Number(asset.latitude) <= 90 &&
        Number(asset.longitude) >= -180 &&
        Number(asset.longitude) <= 180
    );
}

// --------------------------------------------------
// CREATE POPUP
// --------------------------------------------------

function createPopupContent(asset) {
    const popup = document.createElement("div");

    const heading = document.createElement("strong");
    heading.textContent = asset.name;

    const details = [
        `Asset ID: ${asset.id}`,
        `Village: ${asset.village}`,
        `Category: ${asset.category.replaceAll("_", " ")}`,
        `Owner Type: ${asset.owner_type}`,
        `Owner: ${asset.owner_name}`,
        `Managing Authority: ${asset.managing_authority || "Not specified"}`,
        `Verification: ${asset.verification_status}`
    ];

    popup.appendChild(heading);

    details.forEach(detail => {
        const paragraph = document.createElement("p");
        paragraph.textContent = detail;
        popup.appendChild(paragraph);
    });

    return popup;
}

// --------------------------------------------------
// CREATE MARKER
// --------------------------------------------------

function createMarker(asset) {
    const color = getMarkerColor(asset.category);

    const marker = L.circleMarker(
        [Number(asset.latitude), Number(asset.longitude)],
        {
            radius: 8,
            color: "#ffffff",
            weight: 2,
            fillColor: color,
            fillOpacity: 0.95
        }
    );

    marker.bindPopup(createPopupContent(asset));

    marker.on("click", () => {
        selectAsset(asset.id, false);
    });

    return marker;
}

// --------------------------------------------------
// AUTOMATIC MAP POSITIONING
// --------------------------------------------------

function fitMapToAssets(assets) {
    const validAssets = assets.filter(hasValidCoordinates);

    if (validAssets.length === 0) return;

    const coordinates = validAssets.map(asset => [
        Number(asset.latitude),
        Number(asset.longitude)
    ]);

    const bounds = L.latLngBounds(coordinates);

    if (bounds.getNorthEast().equals(bounds.getSouthWest())) {
        map.setView(bounds.getCenter(), 15);
    } else {
        map.fitBounds(bounds, {
            padding: [50, 50],
            maxZoom: 15
        });
    }
}

// --------------------------------------------------
// DISPLAY CLUSTERED MARKERS
// --------------------------------------------------

function displayMarkers(assets) {
    markerCluster.clearLayers();
    markers.clear();

    const validAssets = assets.filter(hasValidCoordinates);

    validAssets.forEach(asset => {
        const marker = createMarker(asset);

        markerCluster.addLayer(marker);

        markers.set(asset.id, marker);
    });

    document.getElementById("visible-assets").textContent =
        validAssets.length;
}

// --------------------------------------------------
// DISPLAY SIDEBAR ASSETS
// --------------------------------------------------

function displayAssetList(assets) {
    const assetList = document.getElementById("asset-list");

    assetList.replaceChildren();

    document.getElementById("asset-count").textContent =
        assets.length;

    if (assets.length === 0) {
        const message = document.createElement("p");

        message.className = "loading-message";
        message.textContent = "No matching assets found.";

        assetList.appendChild(message);
        return;
    }

    assets.forEach(asset => {
        const card = document.createElement("div");

        card.className = "asset-card";
        card.dataset.assetId = asset.id;

        if (asset.id === selectedAssetId) {
            card.classList.add("active");
        }

        const heading = document.createElement("h3");
        heading.textContent = asset.name;

        const village = document.createElement("p");
        village.textContent = `${asset.village} · ${asset.id}`;

        const category = document.createElement("span");

        category.className = "asset-category";
        category.textContent =
            asset.category.replaceAll("_", " ");

        card.append(heading, village, category);

        card.addEventListener("click", () => {
            selectAsset(asset.id, true);
        });

        assetList.appendChild(card);
    });
}

// --------------------------------------------------
// SELECT ASSET
// --------------------------------------------------

function selectAsset(assetId, moveMap = true) {
    const asset = allAssets.find(item => item.id === assetId);

    if (!asset) return;

    selectedAssetId = assetId;

    document.querySelectorAll(".asset-card").forEach(card => {
        card.classList.toggle(
            "active",
            card.dataset.assetId === assetId
        );
    });

    const marker = markers.get(assetId);

    if (!marker) return;

    if (moveMap) {
        map.setView(marker.getLatLng(), 17, {
            animate: true
        });
    }

    // Expand the cluster if this marker is currently grouped.
    markerCluster.zoomToShowLayer(marker, () => {
        marker.openPopup();
    });
}

// --------------------------------------------------
// SEARCH AND CATEGORY FILTERS
// --------------------------------------------------

function applyFilters() {
    const searchTerm = document
        .getElementById("search-input")
        .value
        .trim()
        .toLowerCase();

    const selectedCategory = document
        .getElementById("category-filter")
        .value;

    const filteredAssets = allAssets.filter(asset => {
        const matchesSearch = [
            asset.name,
            asset.village,
            asset.owner_name,
            asset.id
        ].some(value =>
            String(value || "")
                .toLowerCase()
                .includes(searchTerm)
        );

        const matchesCategory =
            selectedCategory === "all" ||
            asset.category === selectedCategory;

        return matchesSearch && matchesCategory;
    });

    if (
        selectedAssetId &&
        !filteredAssets.some(asset => asset.id === selectedAssetId)
    ) {
        selectedAssetId = null;
        map.closePopup();
    }

    displayAssetList(filteredAssets);
    displayMarkers(filteredAssets);
}

// --------------------------------------------------
// LOAD ASSETS FROM API
// --------------------------------------------------

async function loadAssets() {
    const connectionStatus =
        document.getElementById("connection-status");

    connectionStatus.textContent = "Loading database assets...";

    try {
        const response = await fetch(`${API_URL}/assets`);

        if (!response.ok) {
            throw new Error(`Server returned ${response.status}`);
        }

        const data = await response.json();

        if (!Array.isArray(data.assets)) {
            throw new Error("Invalid asset data received.");
        }

        allAssets = data.assets;

        document.getElementById("total-assets").textContent =
            data.total;

        displayAssetList(allAssets);
        displayMarkers(allAssets);

        fitMapToAssets(allAssets);

        const validCount = allAssets.filter(hasValidCoordinates).length;

        connectionStatus.textContent =
            `Connected · ${data.total} assets`;

        if (validCount < allAssets.length) {
            console.warn(
                `${allAssets.length - validCount} assets have invalid coordinates.`
            );
        }

        console.log("Assets loaded successfully:", allAssets.length);

    } catch (error) {
        console.error("Failed to load assets:", error);

        connectionStatus.textContent = "API connection failed";

        document.getElementById("total-assets").textContent = "0";
        document.getElementById("visible-assets").textContent = "0";

        document.getElementById("asset-list").textContent =
            "Unable to load assets. Check whether the API server is running.";
    }
}

// --------------------------------------------------
// START APPLICATION
// --------------------------------------------------


document.addEventListener("DOMContentLoaded", () => {
    initializeMap();

    document
        .getElementById("search-input")
        .addEventListener("input", applyFilters);

    document
        .getElementById("category-filter")
        .addEventListener("change", applyFilters);

    // Open Add Asset Modal
    const addAssetButton =
        document.getElementById("add-asset-button");

    const assetModal =
        document.getElementById("asset-modal");

    const closeModalButton =
        document.getElementById("close-modal");

    addAssetButton.addEventListener("click", () => {
        assetModal.hidden = false;
    });

    // Close Add Asset Modal
    closeModalButton.addEventListener("click", () => {
        assetModal.hidden = true;
    });

    // Close modal when clicking outside the form
    assetModal.addEventListener("click", (event) => {
        if (event.target === assetModal) {
            assetModal.hidden = true;
        }
    });

    loadAssets();
});
