import client from "./client";

export const getMyFarm = () => client.get("/api/farms/mine/").then((r) => r.data);

export const listSheds = () => client.get("/api/farms/sheds/").then((r) => r.data);

export const createShed = (payload) => client.post("/api/farms/sheds/", payload).then((r) => r.data);
