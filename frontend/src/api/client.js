import axios from "axios";

export const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";

const client = axios.create({
  baseURL: API_BASE_URL,
});

function getTokens() {
  return {
    access: localStorage.getItem("roost_access"),
    refresh: localStorage.getItem("roost_refresh"),
  };
}

export function setTokens({ access, refresh }) {
  if (access) localStorage.setItem("roost_access", access);
  if (refresh) localStorage.setItem("roost_refresh", refresh);
}

export function clearTokens() {
  localStorage.removeItem("roost_access");
  localStorage.removeItem("roost_refresh");
}

client.interceptors.request.use((config) => {
  const { access } = getTokens();
  if (access) {
    config.headers.Authorization = `Bearer ${access}`;
  }
  return config;
});

let refreshPromise = null;

client.interceptors.response.use(
  (response) => response,
  async (error) => {
    const original = error.config;
    const { refresh } = getTokens();

    if (error.response?.status === 401 && refresh && !original._retried) {
      original._retried = true;
      try {
        if (!refreshPromise) {
          refreshPromise = axios
            .post(`${API_BASE_URL}/api/auth/login/refresh/`, { refresh })
            .then((res) => {
              setTokens({ access: res.data.access });
              return res.data.access;
            })
            .finally(() => {
              refreshPromise = null;
            });
        }
        const newAccess = await refreshPromise;
        original.headers.Authorization = `Bearer ${newAccess}`;
        return client(original);
      } catch (refreshError) {
        clearTokens();
        window.location.href = "/login";
        return Promise.reject(refreshError);
      }
    }

    return Promise.reject(error);
  }
);

/** Pulls a clean, displayable message out of a DRF error response. */
export function extractErrorMessage(error) {
  const data = error?.response?.data;
  if (!data) return error?.message || "Something went wrong. Please try again.";
  if (typeof data === "string") return data;
  if (data.detail) return data.detail;
  // DRF validation errors: { field: ["msg"] } or { field: "msg" }
  const firstKey = Object.keys(data)[0];
  if (firstKey) {
    const val = data[firstKey];
    const msg = Array.isArray(val) ? val[0] : val;
    return `${firstKey === "non_field_errors" ? "" : `${firstKey}: `}${msg}`;
  }
  return "Something went wrong. Please try again.";
}

export default client;
