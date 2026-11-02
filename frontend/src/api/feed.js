import client from "./client";

export const listFeedStock = () => client.get("/api/feed/stock/").then((r) => r.data);

export const createFeedStock = (payload) => client.post("/api/feed/stock/", payload).then((r) => r.data);

export const listFeedLogs = () => client.get("/api/feed/logs/").then((r) => r.data);

export const createFeedLog = (payload) => client.post("/api/feed/logs/", payload).then((r) => r.data);
