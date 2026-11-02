import client from "./client";

export const listAlerts = (unacknowledgedOnly = false) =>
  client
    .get("/api/alerts/", { params: unacknowledgedOnly ? { unacknowledged: "true" } : {} })
    .then((r) => r.data);

export const acknowledgeAlert = (id) => client.post(`/api/alerts/${id}/acknowledge/`).then((r) => r.data);
