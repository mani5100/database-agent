// frontend/src/App.jsx

import { useSessionStore } from "./store/sessionStore";
import ConnectPage from "./pages/ConnectPage";
import TableSelectionPage from "./pages/TableSelectionPage";
import ReviewPage from "./pages/ReviewPage";
import AskPage from "./pages/AskPage";
import StepIndicator from "./components/StepIndicator";

function App() {
  const currentStep = useSessionStore((state) => state.currentStep);

  return (
    <div>
      <StepIndicator currentStep={currentStep} />
      {currentStep === "connect" && <ConnectPage />}
      {currentStep === "select" && <TableSelectionPage />}
      {currentStep === "review" && <ReviewPage />}
      {currentStep === "ask" && <AskPage />}
    </div>
  );
}

export default App;