import axios from "axios";

const client = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL,
  withCredentials: true,
});

client.interceptors.response.use(
  (response) => response,
  (error) => {
    return Promise.reject(
      error.response?.data?.detail || error.message
    );
  }
);

export default client;