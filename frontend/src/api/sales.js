import client from "./client";

export const listSales = () => client.get("/api/sales/").then((r) => r.data);

export const createSale = (payload) => client.post("/api/sales/", payload).then((r) => r.data);
