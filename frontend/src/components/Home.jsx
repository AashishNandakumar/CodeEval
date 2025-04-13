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
    <div className="home-container container">
      <h1>Start Coding Assessment</h1>
      <p>
        <strong>Problem:</strong> {DEFAULT_PROBLEM_STATEMENT}
      </p>
      <button onClick={handleStartSession} disabled={isLoading}>
        {isLoading ? "Starting..." : "Start New Session"}
      </button>
      {error && <p className="error-message">Error: {error}</p>}
    </div>
  );
}

export default Home;
