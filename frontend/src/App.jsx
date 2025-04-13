import "./App.css";
import {
  BrowserRouter as Router,
  Route,
  Routes,
  Link,
  NavLink,
} from "react-router-dom";
import Home from "./components/Home";
import CodingSession from "./components/CodingSession";
import Report from "./components/Report";

function App() {
  return (
    <Router>
      <div className="app-container">
        <header className="app-header">
          <div className="header-container">
            <div className="logo-container">
              <Link to="/" className="nav-logo">
                <span className="logo-text-primary">Code</span>
                <span className="logo-text-secondary">Eval</span>
              </Link>
            </div>

            <nav className="app-nav">
              <ul className="nav-links">
                <li>
                  <NavLink
                    to="/"
                    className={({ isActive }) =>
                      isActive ? "nav-link active" : "nav-link"
                    }
                  >
                    Home
                  </NavLink>
                </li>
                <li>
                  <NavLink
                    to="/problems"
                    className={({ isActive }) =>
                      isActive ? "nav-link active" : "nav-link"
                    }
                  >
                    Problems
                  </NavLink>
                </li>
                <li>
                  <NavLink
                    to="/leaderboard"
                    className={({ isActive }) =>
                      isActive ? "nav-link active" : "nav-link"
                    }
                  >
                    Leaderboard
                  </NavLink>
                </li>
              </ul>
            </nav>

            <div className="user-controls">
              <button className="btn-user">
                <svg
                  xmlns="http://www.w3.org/2000/svg"
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="currentColor"
                  strokeWidth="2"
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  className="user-icon"
                >
                  <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"></path>
                  <circle cx="12" cy="7" r="4"></circle>
                </svg>
              </button>
            </div>
          </div>
        </header>

        <main className="app-main">
          <Routes>
            <Route path="/" element={<Home />} />
            <Route path="/session/:sessionId" element={<CodingSession />} />
            <Route path="/report/:sessionId" element={<Report />} />
            {/* These routes are placeholders for the nav menu items */}
            <Route
              path="/problems"
              element={
                <div className="placeholder-content">
                  Problems list will be here
                </div>
              }
            />
            <Route
              path="/leaderboard"
              element={
                <div className="placeholder-content">
                  Leaderboard will be here
                </div>
              }
            />
          </Routes>
        </main>

        <footer className="app-footer">
          <div className="footer-container">
            <div className="footer-logo">
              <span className="logo-text-primary">Code</span>
              <span className="logo-text-secondary">Eval</span>
            </div>
            <div className="footer-links">
              <a href="#" className="footer-link">
                About
              </a>
              <a href="#" className="footer-link">
                Help
              </a>
              <a href="#" className="footer-link">
                Contact
              </a>
              <a href="#" className="footer-link">
                Terms
              </a>
              <a href="#" className="footer-link">
                Privacy
              </a>
            </div>
            <div className="footer-copyright">
              © {new Date().getFullYear()} CodeEval. All rights reserved.
            </div>
          </div>
        </footer>
      </div>
    </Router>
  );
}

export default App;
