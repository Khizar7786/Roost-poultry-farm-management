import client from "./client";

export const registerFarm = (payload) => client.post("/api/auth/register/", payload).then((r) => r.data);

export const login = (username, password) =>
  client.post("/api/auth/login/", { username, password }).then((r) => r.data);

export const getMe = () => client.get("/api/auth/me/").then((r) => r.data);

export const listEmployees = () => client.get("/api/auth/employees/").then((r) => r.data);

export const registerEmployee = (payload) =>
  client.post("/api/auth/employees/register/", payload).then((r) => r.data);

export const deactivateEmployee = (id) =>
  client.post(`/api/auth/employees/${id}/deactivate/`).then((r) => r.data);
