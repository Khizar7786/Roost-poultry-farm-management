import client from "./client";

export const askChatbot = (query) => client.post("/api/chatbot/ask/", { query }).then((r) => r.data);
