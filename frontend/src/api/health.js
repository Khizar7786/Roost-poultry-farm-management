import client from "./client";

export const listVaccinations = () => client.get("/api/health/vaccinations/").then((r) => r.data);

export const scheduleVaccination = (payload) =>
  client.post("/api/health/vaccinations/", payload).then((r) => r.data);

export const markVaccinationAdministered = (id) =>
  client.post(`/api/health/vaccinations/${id}/administer/`).then((r) => r.data);
