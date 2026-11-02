
import { Search, Sun, ChevronDown } from "lucide-react";

export default function Header() {
  return (
    <header className="app-header">
      <div className="header-title">
        <div className="breadcrumb">Workspace / Overview</div>
        <h1>Geographical Overview</h1>
      </div>

      <div className="header-actions">
        <div className="header-search">
          <Search size={17} />
          <input placeholder="Search assets, villages..." />
          <kbd>Ctrl K</kbd>
        </div>

        <button className="theme-button" title="Theme options">
          <Sun size={18} />
        </button>

        <button className="region-button">
          Bengaluru
          <ChevronDown size={15} />
        </button>
      </div>
    </header>
  );
}
