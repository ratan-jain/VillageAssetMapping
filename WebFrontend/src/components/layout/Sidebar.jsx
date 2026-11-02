
import {
  Map,
  Database,
  Layers,
  ChartNoAxesCombined,
  Settings,
  Search,
} from "lucide-react";

const navigation = [
  { label: "Overview", icon: Map, id: "overview" },
  { label: "Assets", icon: Database, id: "assets" },
  { label: "Map Layers", icon: Layers, id: "layers" },
  {
    label: "Service Analysis",
    icon: ChartNoAxesCombined,
    id: "analysis",
  },
  { label: "Settings", icon: Settings, id: "settings" },
];

export default function Sidebar() {
  return (
    <aside className="sidebar">
      <div className="sidebar-brand">
        <div className="brand-symbol">V</div>

        <div className="brand-name">
          <strong>Village Mapping</strong>
          <span>Asset Intelligence</span>
        </div>
      </div>

      <div className="sidebar-search">
        <Search size={16} />
        <span>Find a section</span>
      </div>

      <div className="sidebar-label">WORKSPACE</div>

      <nav className="sidebar-navigation">
        {navigation.map((item, index) => {
          const Icon = item.icon;

          return (
            <button
              key={item.id}
              className={`nav-item ${index === 0 ? "active" : ""}`}
              title={item.label}
            >
              <Icon size={19} strokeWidth={1.8} />
              <span>{item.label}</span>
            </button>
          );
        })}
      </nav>

      <div className="sidebar-bottom">
        <div className="connection-indicator" />
        <span>System workspace</span>
      </div>
    </aside>
  );
}
