
import { useEffect, useState } from "react";
import DashboardLayout from "./components/layout/DashboardLayout";
import LoadingScreen from "./components/LoadingScreen";
import "./App.css";

export default function App() {
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const timer = setTimeout(() => {
      setLoading(false);
    }, 2500);

    return () => clearTimeout(timer);
  }, []);

  return (
    <>
      <DashboardLayout />
      {loading && <LoadingScreen />}
    </>
  );
}
