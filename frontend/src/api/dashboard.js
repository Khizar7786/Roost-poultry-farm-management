import client from "./client";

export const getDashboard = () => client.get("/api/dashboard/").then((r) => r.data);
