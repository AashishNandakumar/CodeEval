import React, { useState } from "react";
import { useNavigate } from "react-router-dom";
import { startSession } from "../services/api"; // Import the API function

// TODO: Get this from a config or user input later
const DEFAULT_PROBLEM_STATEMENT = "Write a function that reverses a string.";

function Home() {
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);
  const navigate = useNavigate();

  const handleStartSession = async () => {
    setIsLoading(true);
    setError(null);
    try {
      const problemStatement = DEFAULT_PROBLEM_STATEMENT; // Use the default
      const data = await startSession(problemStatement);
      if (data && data.id) {
        // Pass the problem statement in the navigation state
        navigate(`/session/${data.id}`, {
          state: { problemStatement },
        });
      } else {
        throw new Error("Failed to get session ID from API response.");
      }
    } catch (err) {
      console.error("Failed to start session:", err);
      setError(
        err.message || "Could not start a new session. Please try again."
      );
      setIsLoading(false);
    }
    // No need to set isLoading to false on success because we navigate away
  };

  return (
    <div className="home-container">
      <div className="welcome-section">
        <h1 className="welcome-title">Welcome to CodeEval</h1>
        <p className="welcome-subtitle">
          Improve your coding skills with interactive assessments and real-time
          feedback.
        </p>
      </div>

      <div className="problem-card">
        <div className="problem-card-header">
          <h2 className="problem-card-title">Today's Challenge</h2>
          <span className="problem-difficulty easy">Easy</span>
        </div>

        <div className="problem-card-body">
          <div className="problem-description">
            <h3 className="problem-title">String Reversal</h3>
            <div className="problem-prompt">
              <p className="prompt-text">{DEFAULT_PROBLEM_STATEMENT}</p>

              <div className="problem-examples">
                <div className="example">
                  <h4>Example:</h4>
                  <div className="example-box">
                    <p>
                      <strong>Input:</strong> "hello"
                    </p>
                    <p>
                      <strong>Output:</strong> "olleh"
                    </p>
                  </div>
                </div>
              </div>
            </div>
          </div>

          <div className="problem-actions">
            <button
              className="btn-primary btn-start-session"
              onClick={handleStartSession}
              disabled={isLoading}
            >
              {isLoading ? (
                <span className="loading-indicator">
                  <span className="loading-spinner"></span>
                  Starting...
                </span>
              ) : (
                <>Start Coding</>
              )}
            </button>

            {error && (
              <div className="alert alert-danger" role="alert">
                <svg
                  xmlns="http://www.w3.org/2000/svg"
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="currentColor"
                  strokeWidth="2"
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  className="alert-icon"
                >
                  <circle cx="12" cy="12" r="10"></circle>
                  <line x1="12" y1="8" x2="12" y2="12"></line>
                  <line x1="12" y1="16" x2="12.01" y2="16"></line>
                </svg>
                {error}
              </div>
            )}
          </div>
        </div>
      </div>

      <div className="features-section">
        <div className="feature-card">
          <div className="feature-icon">
            <svg
              xmlns="http://www.w3.org/2000/svg"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth="2"
              strokeLinecap="round"
              strokeLinejoin="round"
            >
              <polyline points="22 12 18 12 15 21 9 3 6 12 2 12"></polyline>
            </svg>
          </div>
          <h3 className="feature-title">Real-time Analysis</h3>
          <p className="feature-description">
            Get instant feedback on your code as you write, helping you identify
            improvements.
          </p>
        </div>

        <div className="feature-card">
          <div className="feature-icon">
            <svg
              xmlns="http://www.w3.org/2000/svg"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth="2"
              strokeLinecap="round"
              strokeLinejoin="round"
            >
              <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path>
              <polyline points="14 2 14 8 20 8"></polyline>
              <line x1="16" y1="13" x2="8" y2="13"></line>
              <line x1="16" y1="17" x2="8" y2="17"></line>
              <polyline points="10 9 9 9 8 9"></polyline>
            </svg>
          </div>
          <h3 className="feature-title">Detailed Reports</h3>
          <p className="feature-description">
            Receive comprehensive assessment reports to help track your
            progress.
          </p>
        </div>

        <div className="feature-card">
          <div className="feature-icon">
            <svg
              xmlns="http://www.w3.org/2000/svg"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth="2"
              strokeLinecap="round"
              strokeLinejoin="round"
            >
              <circle cx="12" cy="12" r="10"></circle>
              <polyline points="12 6 12 12 16 14"></polyline>
            </svg>
          </div>
          <h3 className="feature-title">Timed Challenges</h3>
          <p className="feature-description">
            Practice under real interview conditions with timed coding
            challenges.
          </p>
        </div>
      </div>
    </div>
  );
}

export default Home;
