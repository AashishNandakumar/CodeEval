import React, { useState, useEffect, useRef, useCallback } from "react";
import { useParams, useNavigate, useLocation } from "react-router-dom";
import { endSession } from "../services/api"; // Import endSession API
import CodeMirror from "@uiw/react-codemirror"; // Import CodeMirror
import { javascript } from "@codemirror/lang-javascript"; // Import JS language support
import { okaidia } from "@uiw/codemirror-theme-okaidia"; // Import a theme (e.g., okaidia)

// Simple debounce function
function debounce(func, wait) {
  let timeout;
  return function executedFunction(...args) {
    const later = () => {
      clearTimeout(timeout);
      func(...args);
    };
    clearTimeout(timeout);
    timeout = setTimeout(later, wait);
  };
}

const WS_BASE_URL = import.meta.env.VITE_WS_BASE_URL || "ws://localhost:8000"; // Use env var or default
const RECONNECT_DELAY_BASE = 2000; // Initial reconnect delay (ms)
const MAX_RECONNECT_ATTEMPTS = 5;

function CodingSession() {
  const { sessionId } = useParams();
  const navigate = useNavigate();
  const location = useLocation(); // Get location object
  const [problemStatement, setProblemStatement] = useState(
    "Loading problem statement..."
  );
  const [code, setCode] = useState("// Start coding here...\n");
  const [question, setQuestion] = useState("");
  const [response, setResponse] = useState("");
  const [interactionId, setInteractionId] = useState("");
  const [lastEvaluation, setLastEvaluation] = useState(null); // State for last evaluation text
  const [lastScore, setLastScore] = useState(null); // State for last evaluation score
  const [connectionStatus, setConnectionStatus] = useState("Initializing...");
  const [isEnding, setIsEnding] = useState(false); // State for end session button
  const [error, setError] = useState(null); // General error state
  const ws = useRef(null);
  const reconnectAttempts = useRef(0);
  const reconnectTimeoutId = useRef(null); // Store reconnect timeout ID
  const codeUpdateQueue = useRef(null); // To store the latest code for debounced sending

  // Debounced function to send code updates
  const sendCodeUpdate = useCallback(
    debounce((currentCode) => {
      console.log("currentCode", currentCode);
      if (ws.current && ws.current.readyState === WebSocket.OPEN) {
        console.log("Sending code update...");
        ws.current.send(
          JSON.stringify({
            message_type: "code_update",
            code: currentCode,
          })
        );
      } else {
        console.warn("WebSocket not open. Code update not sent.");
        setError("Connection is not active. Code changes are not being saved.");
      }
    }, 1000),
    [setError]
  ); // Debounce by 1 second

  // Effect to get problem statement from location state
  useEffect(() => {
    if (location.state && location.state.problemStatement) {
      setProblemStatement(location.state.problemStatement);
    } else {
      console.warn("Problem statement not found in location state.");
      setProblemStatement(
        "Problem statement not available. Attempting to code without it."
      );
    }
  }, [location.state]);

  // Function to connect WebSocket
  const connectWebSocket = useCallback(() => {
    if (!sessionId || isEnding) return; // Don't connect if no session ID or if ending

    // Clear previous reconnect timeout if any
    if (reconnectTimeoutId.current) {
      clearTimeout(reconnectTimeoutId.current);
      reconnectTimeoutId.current = null;
    }

    // Clean up existing connection if necessary (though cleanup effect should handle this)
    if (ws.current && ws.current.readyState !== WebSocket.CLOSED) {
      console.log("Closing existing WebSocket before reconnecting...");
      ws.current.close();
    }

    const wsUrl = `${WS_BASE_URL}/ws/session/${sessionId}`;
    console.log(
      `Attempting to connect WebSocket (Attempt: ${
        reconnectAttempts.current + 1
      })...`
    );
    setConnectionStatus("Connecting...");
    setError(null);

    ws.current = new WebSocket(wsUrl);

    ws.current.onopen = () => {
      console.log("WebSocket connection opened successfully.");
      setConnectionStatus("Connected");
      setError(null);
      reconnectAttempts.current = 0; // Reset attempts on successful connection
    };

    ws.current.onmessage = (event) => {
      try {
        const message = JSON.parse(event.data);
        console.log("Message from server ", message);
        if (message.message_type === "question") {
          // set interaction_id
          setInteractionId(message.interaction_id);
          setQuestion(message.question);
          setLastEvaluation(null); // Clear previous evaluation on new question
          setLastScore(null);
          setError(null);
        } else if (message.message_type === "evaluation_result") {
          // Handle the new evaluation result message
          setLastEvaluation(
            message.evaluation || "No evaluation text provided."
          );
          setLastScore(
            typeof message.score === "number" ? message.score : null
          );
          console.log(
            `Received evaluation: Score ${message.score}, Text: ${message.evaluation}`
          );
        } else if (message.message_type === "error") {
          const errorMsg = message.detail || "Unknown server error";
          console.error("Server error:", errorMsg);
          setError(`Server error: ${errorMsg}`);
          setConnectionStatus("Error");
        } else {
          console.log("Received unhandled message type:", message.message_type);
        }
      } catch (e) {
        console.error("Failed to parse message or handle incoming ws data:", e);
        setError("Failed to process message from server.");
      }
    };

    ws.current.onerror = (event) => {
      console.error("WebSocket error:", event);
      // Don't set status/error here directly, let onclose handle retry logic
    };

    ws.current.onclose = (event) => {
      console.log(
        "WebSocket connection closed:",
        event.code,
        event.reason,
        `Was Clean: ${event.wasClean}`
      );

      // Don't try to reconnect if session ended cleanly by user or normal closure (1000)
      if (event.code === 1000 || isEnding) {
        setConnectionStatus(`Closed (${event.code})`);
        return;
      }

      // Reconnection logic
      setConnectionStatus("Disconnected. Reconnecting...");
      reconnectAttempts.current += 1;

      if (reconnectAttempts.current <= MAX_RECONNECT_ATTEMPTS) {
        const delay =
          RECONNECT_DELAY_BASE * Math.pow(2, reconnectAttempts.current - 1);
        console.log(
          `Will attempt reconnect #${reconnectAttempts.current} in ${delay}ms`
        );
        setError(
          `Connection lost. Attempting to reconnect (${reconnectAttempts.current}/${MAX_RECONNECT_ATTEMPTS})...`
        );
        reconnectTimeoutId.current = setTimeout(connectWebSocket, delay);
      } else {
        console.error("Max reconnect attempts reached.");
        setError(
          "Connection failed after multiple attempts. Please refresh the page or check your connection."
        );
        setConnectionStatus("Failed to connect");
      }
    };
  }, [sessionId, isEnding]); // Dependencies for connect function

  // Effect for initial connection and cleanup
  useEffect(() => {
    connectWebSocket(); // Initial connection attempt

    // Cleanup function
    return () => {
      console.log("Cleaning up WebSocket connection effect...");
      // Clear any pending reconnect timeout
      if (reconnectTimeoutId.current) {
        clearTimeout(reconnectTimeoutId.current);
        reconnectTimeoutId.current = null;
      }
      // Close WebSocket connection if open
      if (ws.current && ws.current.readyState === WebSocket.OPEN) {
        console.log(
          "Closing WebSocket connection on component unmount/cleanup."
        );
        ws.current.close(1000, "Component unmounting"); // Use normal closure code
      }
      ws.current = null; // Clear the ref
      setConnectionStatus("Closed");
    };
  }, [connectWebSocket]); // Depend on the memoized connect function

  // CodeMirror onChange handler
  const handleCodeChange = useCallback(
    (value) => {
      setCode(value);
      codeUpdateQueue.current = value; // Store the latest code
      sendCodeUpdate(value); // Trigger the debounced send function
    },
    [sendCodeUpdate]
  );

  const handleResponseChange = (event) => {
    setResponse(event.target.value);
  };

  const submitResponse = () => {
    setError(null); // Clear previous errors
    if (ws.current && ws.current.readyState === WebSocket.OPEN) {
      console.log("Sending response submission...");
      ws.current.send(
        JSON.stringify({
          message_type: "response_submitted",
          interaction_id: interactionId,
          response: response,
        })
      );
      setResponse(""); // Clear response input
      setQuestion(""); // Clear question immediately on submission
      // Note: Evaluation feedback will arrive separately via WebSocket
    } else {
      console.warn("WebSocket not open. Response not sent.");
      setError("Cannot submit response: Connection is not active."); // Use general error state
    }
  };

  const handleEndSession = async () => {
    if (
      !confirm(
        "Are you sure you want to end the session? The final report will be generated."
      )
    ) {
      return;
    }
    setIsEnding(true); // Set isEnding flag *before* closing WS/calling API
    setError(null); // Clear previous errors
    try {
      console.log(`Ending session ${sessionId}...`);
      // Close WebSocket *before* navigating away or calling API that might take time
      if (ws.current && ws.current.readyState !== WebSocket.CLOSED) {
        ws.current.close(1000, "Session ended by user");
      }
      await endSession(sessionId);
      navigate(`/report/${sessionId}`); // Navigate to the report page
    } catch (err) {
      console.error("Failed to end session:", err);
      setError(`Error ending session: ${err.message || "Unknown error"}`); // Use general error state
      setIsEnding(false); // Reset flag if ending fails
    }
  };

  // Determine if actions should be disabled based on connection status
  const isConnected = connectionStatus === "Connected";

  return (
    <div className="session-container container">
      <h1>Coding Session: {sessionId}</h1>
      <p className="status-message">Status: {connectionStatus}</p>

      {/* Display general errors */}
      {error && <p className="error-message">{error}</p>}

      {/* Display Problem Statement */}
      <div className="problem-statement">
        <h2>Problem Statement</h2>
        <p style={{ whiteSpace: "pre-wrap" }}>{problemStatement}</p>
      </div>

      <CodeMirror
        value={code}
        height="400px"
        theme={okaidia}
        extensions={[javascript({ jsx: true })]}
        onChange={handleCodeChange}
        style={{
          textAlign: "left",
          border: "1px solid #555",
          borderRadius: "4px",
        }}
        readOnly={!isConnected} // Make editor readonly if not connected
      />

      {/* Display Latest Evaluation Feedback */}
      {lastEvaluation && (
        <div
          className="evaluation-block container"
          style={{ marginTop: "15px", borderColor: "#646cff" }}
        >
          <h4>Feedback on Last Response:</h4>
          <p style={{ whiteSpace: "pre-wrap" }}>{lastEvaluation}</p>
          {lastScore !== null && (
            <p>
              <strong>Score:</strong> {(lastScore * 100).toFixed(1)}%
            </p>
          )}
        </div>
      )}

      {/* Question/Response Block */}
      {question && (
        <div className="question-block" style={{ marginTop: "15px" }}>
          <h2>Question:</h2>
          <p style={{ whiteSpace: "pre-wrap" }}>{question}</p>
          <textarea
            value={response}
            onChange={handleResponseChange}
            rows="6"
            placeholder="Your response..."
            disabled={!isConnected} // Disable textarea if not connected
          />
          <button onClick={submitResponse} disabled={!response || !isConnected}>
            Submit Response
          </button>
        </div>
      )}

      <div style={{ marginTop: "20px", textAlign: "right" }}>
        <button onClick={handleEndSession} disabled={isEnding || !isConnected}>
          {isEnding ? "Ending..." : "End Session & View Report"}
        </button>
      </div>
    </div>
  );
}

export default CodingSession;
