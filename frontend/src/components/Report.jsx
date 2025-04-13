import React, { useState, useEffect } from "react";
import { useParams } from "react-router-dom";
import { getSessionReport } from "../services/api"; // Import the API function

function Report() {
  const { sessionId } = useParams();
  const [reportData, setReportData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchReport = async () => {
      if (!sessionId) {
        setError("Session ID is missing.");
        setLoading(false);
        return;
      }

      setLoading(true);
      setError(null);
      console.log(`Fetching report for session ${sessionId}...`);
      try {
        const data = await getSessionReport(sessionId);
        console.log("Report data received:", data);

        // Updated validation for the new report structure
        if (
          !data ||
          typeof data.report_content !== "string" || // Check if report_content is a string
          !data.scores || // Check if scores object exists
          typeof data.scores.average_score !== "number" // Check for average_score
          // Optionally check for individual_scores array if needed
        ) {
          console.error(
            "Received incomplete or invalid report data structure:",
            data
          );
          throw new Error(
            "Received incomplete or invalid report data from the server."
          );
        }

        setReportData(data);
      } catch (err) {
        console.error("Failed to fetch report:", err);
        setError(
          err.message ||
            "Failed to fetch report. Please check the session ID or try again later."
        );
      } finally {
        setLoading(false);
      }
    };

    fetchReport();
  }, [sessionId]); // Re-fetch if sessionId changes

  if (loading) return <p className="status-message">Loading report...</p>;
  if (error) return <p className="error-message">Error: {error}</p>;
  if (!reportData)
    return (
      <p className="status-message">
        No report data found for session {sessionId}.
      </p>
    );

  // Destructure based on the new format
  const { report_content, scores } = reportData;
  const averageScore = scores.average_score;
  // const individualScores = scores.individual_scores; // Available if needed

  // Convert average score (assuming 0-1 range) to percentage
  const averageScorePercent = (averageScore * 100).toFixed(1);

  return (
    <div className="report-container container">
      <h1>Assessment Report: {sessionId}</h1>

      {/* Display the main report content */}
      <h2>Report Details:</h2>
      <pre>
        <code>{report_content || "No report content available."}</code>
      </pre>

      {/* Display Average Score */}
      <h2>Overall Score:</h2>
      <p style={{ fontSize: "1.2em", fontWeight: "bold" }}>
        {averageScorePercent}%
      </p>

      {/* 
        Removed the previous "Interactions" block as the new format doesn't 
        directly map to individual interaction Q/R/E. 
        The individual_scores array is available in scores.individual_scores 
        if you need to display those raw numbers.
      */}

      {/* Optionally display generation time or report ID */}
      {reportData.generation_time && (
        <p style={{ fontSize: "0.8em", color: "#aaa", marginTop: "2rem" }}>
          Report generated on:{" "}
          {new Date(reportData.generation_time).toLocaleString()}
        </p>
      )}
    </div>
  );
}

export default Report;
