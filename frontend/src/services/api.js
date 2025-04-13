import axios from "axios";

const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL || "http://localhost:8000"; // Use env var or default

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    "Content-Type": "application/json",
  },
});

/**
 * Starts a new coding assessment session.
 * @param {string} problemStatement The problem statement for the session.
 * @returns {Promise<object>} The session data (e.g., { session_id: string }).
 */
export const startSession = async (problemStatement) => {
  try {
    const response = await apiClient.post("/sessions/", {
      problem_statement: problemStatement,
    });
    console.log("Session started:", response.data);
    return response.data;
  } catch (error) {
    console.error("Error starting session:", error);
    throw error; // Re-throw to allow components to handle
  }
};

/**
 * Fetches the report for a completed session.
 * @param {string} sessionId The ID of the session.
 * @returns {Promise<object>} The report data.
 */
export const getSessionReport = async (sessionId) => {
  try {
    const response = await apiClient.get(`/sessions/${sessionId}/report`);
    return response.data;
  } catch (error) {
    console.error(`Error fetching report for session ${sessionId}:`, error);
    throw error;
  }
};

/**
 * Ends an ongoing coding session and triggers report generation.
 * @param {string} sessionId The ID of the session to end.
 * @returns {Promise<object>} Response data from the end session endpoint (e.g., confirmation message).
 */
export const endSession = async (sessionId) => {
  try {
    // Assuming the backend expects a POST request to end the session
    const response = await apiClient.post(`/sessions/${sessionId}/end`);
    return response.data;
  } catch (error) {
    console.error(`Error ending session ${sessionId}:`, error);
    throw error;
  }
};

// Add other API functions as needed (e.g., if there are user endpoints, etc.)

export default apiClient; // Export the configured instance if needed elsewhere
