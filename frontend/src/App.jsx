// frontend/src/App.jsx

import { useEffect } from "react";
import { useSessionStore } from "./store/sessionStore";
import ConnectPage from "./pages/ConnectPage";
import TableSelectionPage from "./pages/TableSelectionPage";
import ReviewPage from "./pages/ReviewPage";
import AskPage from "./pages/AskPage";
import ConnectionsPage from "./pages/ConnectionsPage";
import StepIndicator from "./components/StepIndicator";

function App() {
  const currentStep = useSessionStore((state) => state.currentStep);
  const setGoogleSessionId = useSessionStore((state) => state.setGoogleSessionId);

  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    const googleSessionId = params.get("google_session_id");
    if (googleSessionId) {
      setGoogleSessionId(googleSessionId);
      window.history.replaceState({}, "", window.location.pathname); // clean the URL
    }
  }, [setGoogleSessionId]);

  return (
    <div>
      <StepIndicator currentStep={currentStep} />
      {currentStep === "connect" && <ConnectPage />}
      {currentStep === "select" && <TableSelectionPage />}
      {currentStep === "review" && <ReviewPage />}
      {currentStep === "ask" && <AskPage />}
      {currentStep === "connections" && <ConnectionsPage />}
    </div>
  );
}

export default App;