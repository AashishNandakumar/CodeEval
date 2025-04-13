import React, { useState, useEffect } from "react";
import { useParams, Link } from "react-router-dom";
import { getSessionReport } from "../services/api"; // Import the API function

function Report() {
  const { sessionId } = useParams();
  const [reportData, setReportData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [activeSection, setActiveSection] = useState("summary");

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

  if (loading) {
    return (
      <div className="report-container">
        <div className="loading-spinner-container">
          <div className="loading-spinner report-spinner"></div>
          <p className="loading-text">Generating report...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="report-container">
        <div className="report-error">
          <svg
            xmlns="http://www.w3.org/2000/svg"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="2"
            strokeLinecap="round"
            strokeLinejoin="round"
            className="report-error-icon"
          >
            <circle cx="12" cy="12" r="10"></circle>
            <line x1="12" y1="8" x2="12" y2="12"></line>
            <line x1="12" y1="16" x2="12.01" y2="16"></line>
          </svg>
          <h2>Error Loading Report</h2>
          <p>{error}</p>
          <Link to="/" className="btn-primary return-home-btn">
            Return to Home
          </Link>
        </div>
      </div>
    );
  }

  if (!reportData) {
    return (
      <div className="report-container">
        <div className="report-error">
          <svg
            xmlns="http://www.w3.org/2000/svg"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="2"
            strokeLinecap="round"
            strokeLinejoin="round"
            className="report-warning-icon"
          >
            <circle cx="12" cy="12" r="10"></circle>
            <line x1="12" y1="8" x2="12" y2="12"></line>
            <line x1="12" y1="16" x2="12.01" y2="16"></line>
          </svg>
          <h2>No Report Available</h2>
          <p>No report data found for session {sessionId}.</p>
          <Link to="/" className="btn-primary return-home-btn">
            Return to Home
          </Link>
        </div>
      </div>
    );
  }

  // Destructure based on the new format
  const { report_content, scores } = reportData;
  const averageScore = scores.average_score;
  // const individualScores = scores.individual_scores; // Available if needed

  // Convert average score (assuming 0-1 range) to percentage
  const averageScorePercent = (averageScore * 100).toFixed(1);

  // Get score evaluation
  const getScoreEvaluation = (score) => {
    const numScore = parseFloat(score);
    if (numScore >= 90) return { label: "Excellent", color: "#38a169" }; // Green
    if (numScore >= 80) return { label: "Good", color: "#4299e1" }; // Blue
    if (numScore >= 70) return { label: "Satisfactory", color: "#805ad5" }; // Purple
    if (numScore >= 60) return { label: "Needs Improvement", color: "#ed8936" }; // Orange
    return { label: "Poor", color: "#e53e3e" }; // Red
  };

  const scoreEval = getScoreEvaluation(averageScorePercent);

  // Function to parse report content into sections
  const parseReportContent = (content) => {
    // Simple parser for demonstration
    // For a real implementation, you might want to use more robust parsing
    // This assumes the report content has sections formatted with headings

    // Split by lines and process
    const lines = content.split("\n");
    let sections = [];
    let currentSection = null;

    lines.forEach((line) => {
      if (line.startsWith("# ")) {
        // Main heading - start a new section
        if (currentSection) {
          sections.push(currentSection);
        }
        currentSection = {
          title: line.substring(2).trim(),
          content: [],
        };
      } else if (line.startsWith("## ") && currentSection) {
        // Subheading - add as a styled line
        currentSection.content.push(`<h4>${line.substring(3).trim()}</h4>`);
      } else if (currentSection) {
        // Regular content - just add to current section
        currentSection.content.push(line);
      }
    });

    // Add the last section
    if (currentSection) {
      sections.push(currentSection);
    }

    // If no sections were parsed, create a single section with all content
    if (sections.length === 0) {
      sections = [
        {
          title: "Report",
          content: content.split("\n"),
        },
      ];
    }

    return sections;
  };

  const reportSections = parseReportContent(report_content);

  return (
    <div className="report-container">
      <div className="report-header">
        <div className="report-header-content">
          <h1 className="report-title">Assessment Report</h1>
          <div className="report-meta">
            <span className="report-session-id">
              <svg
                xmlns="http://www.w3.org/2000/svg"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                strokeWidth="2"
                strokeLinecap="round"
                strokeLinejoin="round"
                className="meta-icon"
              >
                <rect x="3" y="4" width="18" height="18" rx="2" ry="2"></rect>
                <line x1="16" y1="2" x2="16" y2="6"></line>
                <line x1="8" y1="2" x2="8" y2="6"></line>
                <line x1="3" y1="10" x2="21" y2="10"></line>
              </svg>
              {reportData.generation_time && (
                <span>
                  Generated on{" "}
                  {new Date(reportData.generation_time).toLocaleString()}
                </span>
              )}
            </span>
            <span className="report-session-id">
              <svg
                xmlns="http://www.w3.org/2000/svg"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                strokeWidth="2"
                strokeLinecap="round"
                strokeLinejoin="round"
                className="meta-icon"
              >
                <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"></path>
                <circle cx="12" cy="7" r="4"></circle>
              </svg>
              Session ID: {sessionId}
            </span>
          </div>
        </div>

        <div className="score-overview">
          <div
            className="score-circle"
            style={{ "--score-color": scoreEval.color }}
          >
            <div className="score-percentage">{averageScorePercent}%</div>
            <div className="score-label">{scoreEval.label}</div>
          </div>
        </div>
      </div>

      <div className="report-content-container">
        <div className="report-navigation">
          <button
            className={`nav-section-btn ${
              activeSection === "summary" ? "active" : ""
            }`}
            onClick={() => setActiveSection("summary")}
          >
            <svg
              xmlns="http://www.w3.org/2000/svg"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth="2"
              strokeLinecap="round"
              strokeLinejoin="round"
              className="section-icon"
            >
              <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path>
              <polyline points="14 2 14 8 20 8"></polyline>
              <line x1="16" y1="13" x2="8" y2="13"></line>
              <line x1="16" y1="17" x2="8" y2="17"></line>
              <polyline points="10 9 9 9 8 9"></polyline>
            </svg>
            Summary
          </button>

          <button
            className={`nav-section-btn ${
              activeSection === "details" ? "active" : ""
            }`}
            onClick={() => setActiveSection("details")}
          >
            <svg
              xmlns="http://www.w3.org/2000/svg"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth="2"
              strokeLinecap="round"
              strokeLinejoin="round"
              className="section-icon"
            >
              <circle cx="12" cy="12" r="10"></circle>
              <polyline points="12 6 12 12 16 14"></polyline>
            </svg>
            Full Details
          </button>

          <Link to="/" className="nav-section-btn">
            <svg
              xmlns="http://www.w3.org/2000/svg"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth="2"
              strokeLinecap="round"
              strokeLinejoin="round"
              className="section-icon"
            >
              <line x1="19" y1="12" x2="5" y2="12"></line>
              <polyline points="12 19 5 12 12 5"></polyline>
            </svg>
            Return Home
          </Link>
        </div>

        <div className="report-content-sections">
          {activeSection === "summary" && reportSections.length > 0 && (
            <div className="report-summary">
              {/* Display a cleaner summary view with formatted sections */}
              {reportSections.map((section, index) => (
                <div key={index} className="report-section">
                  <h3 className="section-title">{section.title}</h3>
                  <div className="section-content">
                    {section.content.map((line, lineIndex) => {
                      if (line.startsWith("<h4>")) {
                        // It's a subheading we identified
                        return (
                          <h4 key={lineIndex} className="subsection-title">
                            {line.replace("<h4>", "").replace("</h4>", "")}
                          </h4>
                        );
                      } else {
                        return <p key={lineIndex}>{line}</p>;
                      }
                    })}
                  </div>
                </div>
              ))}
            </div>
          )}

          {activeSection === "details" && (
            <div className="report-details">
              <div className="report-section">
                <h3 className="section-title">Full Assessment Report</h3>
                <div className="raw-report-content">
                  <pre className="report-content">
                    {report_content || "No report content available."}
                  </pre>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>

      <div className="report-actions">
        <Link to="/" className="btn-primary">
          Start New Assessment
        </Link>
        <button className="btn-secondary" onClick={() => window.print()}>
          <svg
            xmlns="http://www.w3.org/2000/svg"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="2"
            strokeLinecap="round"
            strokeLinejoin="round"
            className="btn-icon"
          >
            <polyline points="6 9 6 2 18 2 18 9"></polyline>
            <path d="M6 18H4a2 2 0 0 1-2-2v-5a2 2 0 0 1 2-2h16a2 2 0 0 1 2 2v5a2 2 0 0 1-2 2h-2"></path>
            <rect x="6" y="14" width="12" height="8"></rect>
          </svg>
          Print Report
        </button>
      </div>
    </div>
  );
}

export default Report;
