
import CrowdAnimation from "./CrowdAnimation";
import "./LoadingScreen.css";

export default function LoadingScreen() {
  return (
    <div className="loading-screen">
      <CrowdAnimation
        src="/images/peeps/all-peeps.png"
        rows={15}
        cols={7}
      />
    </div>
  );
}
