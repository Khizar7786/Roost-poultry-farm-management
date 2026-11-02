import client from "./client";

export const listCountingSessions = () =>
  client.get("/api/monitoring/counting-sessions/").then((r) => r.data);

export const submitCountingSession = (batchId, imageFile) => {
  const form = new FormData();
  form.append("batch", batchId);
  form.append("image", imageFile);
  return client
    .post("/api/monitoring/counting-sessions/", form, {
      headers: { "Content-Type": "multipart/form-data" },
    })
    .then((r) => r.data);
};

export const listMortalityEvents = () =>
  client.get("/api/monitoring/mortality-events/").then((r) => r.data);

export const logMortalityEvent = (payload) =>
  client.post("/api/monitoring/mortality-events/", payload).then((r) => r.data);

export const listPricePredictions = () =>
  client.get("/api/monitoring/price-predictions/").then((r) => r.data);

export const triggerPricePrediction = (horizonDays) =>
  client
    .post("/api/monitoring/price-predictions/trigger/", { horizon_days: horizonDays })
    .then((r) => r.data);
