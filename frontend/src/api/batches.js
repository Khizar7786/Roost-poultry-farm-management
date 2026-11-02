import client from "./client";

export const listBatches = () => client.get("/api/batches/").then((r) => r.data);

export const getBatch = (id) => client.get(`/api/batches/${id}/`).then((r) => r.data);

export const createBatch = (payload) => client.post("/api/batches/", payload).then((r) => r.data);

export const updateBatch = (id, payload) =>
  client.patch(`/api/batches/${id}/`, payload).then((r) => r.data);
