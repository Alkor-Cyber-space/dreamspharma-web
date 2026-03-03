import axios from "axios";

// Base URL
const serverUrl = "http://127.0.0.1:8000/api/";

// ==================
// 🔐 LOGIN API
// ==================
export const loginAPI = async (loginData) => {
  try {
    const response = await axios.post(
      `${serverUrl}auth/login/`,
      loginData
    );
    return response;
  } catch (error) {
    throw error;
  }
};