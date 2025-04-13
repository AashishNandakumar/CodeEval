import "./App.css";
import { BrowserRouter as Router, Route, Routes, Link } from "react-router-dom";
import Home from "./components/Home";
import CodingSession from "./components/CodingSession";
import Report from "./components/Report";

function App() {
  return (
    <Router>
      <div>
        <nav>
          <ul>
            <li>
              <Link to="/">Home</Link>
            </li>
            {/* Add other navigation links as needed */}
          </ul>
        </nav>

        <hr />

        <Routes>
          <Route path="/" element={<Home />} />
          <Route path="/session/:sessionId" element={<CodingSession />} />
          <Route path="/report/:sessionId" element={<Report />} />
        </Routes>
      </div>
    </Router>
  );
}

export default App;
