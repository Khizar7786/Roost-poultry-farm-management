import { useState, useRef, useEffect } from "react";
import { MessageCircle, X, Send, Bird } from "lucide-react";
import { askChatbot } from "../api/chatbot";
import { cx } from "../lib/utils";

const GREETING = {
  role: "bot",
  text: "Hi! I'm the Roost assistant. Ask me about chick counting, mortality, feed, vaccinations, or price forecasts.",
};

export default function ChatbotWidget() {
  const [open, setOpen] = useState(false);
  const [messages, setMessages] = useState([GREETING]);
  const [input, setInput] = useState("");
  const [sending, setSending] = useState(false);
  const scrollRef = useRef(null);

  useEffect(() => {
    scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight, behavior: "smooth" });
  }, [messages, open]);

  const send = async (e) => {
    e.preventDefault();
    const query = input.trim();
    if (!query || sending) return;
    setMessages((m) => [...m, { role: "user", text: query }]);
    setInput("");
    setSending(true);
    try {
      const res = await askChatbot(query);
      setMessages((m) => [...m, { role: "bot", text: res.answer }]);
    } catch {
      setMessages((m) => [
        ...m,
        { role: "bot", text: "I couldn't reach the assistant service just now — please try again." },
      ]);
    } finally {
      setSending(false);
    }
  };

  return (
    <>
      <button
        onClick={() => setOpen((o) => !o)}
        className={cx(
          "fixed bottom-5 right-5 z-50 h-14 w-14 rounded-full shadow-lift flex items-center justify-center transition-transform",
          // Ring keeps the disc's silhouette readable: solid yellow on the
          // off-white canvas is only ~1.7:1 at the edge.
          "bg-gold text-ink-darker ring-2 ring-ink-darker hover:scale-105 active:scale-95"
        )}
        aria-label="Open chat assistant"
      >
        {open ? <X size={22} /> : <MessageCircle size={22} strokeWidth={2.2} />}
      </button>

      {open && (
        <div className="fixed bottom-24 right-5 z-50 w-[22rem] max-w-[calc(100vw-2.5rem)] h-[30rem] bg-white rounded-2xl shadow-lift border border-ink-light flex flex-col overflow-hidden">
          <div className="bg-ink-darker text-white px-4 py-3.5 flex items-center gap-2.5">
            <span className="h-8 w-8 rounded-full bg-gold flex items-center justify-center">
              <Bird size={16} className="text-ink-darker" />
            </span>
            <div>
              <div className="text-sm font-semibold">Roost Assistant</div>
              <div className="text-xs text-white/50">Usually replies instantly</div>
            </div>
          </div>

          <div ref={scrollRef} className="flex-1 overflow-y-auto px-4 py-4 space-y-3">
            {messages.map((m, i) => (
              <div
                key={i}
                className={cx(
                  "text-sm px-3.5 py-2.5 rounded-2xl max-w-[85%] leading-relaxed",
                  m.role === "bot"
                    ? "bg-ink-light text-ink-darker rounded-tl-sm"
                    : "bg-ink text-white ml-auto rounded-tr-sm"
                )}
              >
                {m.text}
              </div>
            ))}
            {sending && (
              <div className="bg-ink-light text-ink-darker text-sm px-3.5 py-2.5 rounded-2xl rounded-tl-sm max-w-[85%]">
                <span className="inline-flex gap-1">
                  <span className="h-1.5 w-1.5 rounded-full bg-ink/50 animate-bounce [animation-delay:-0.2s]" />
                  <span className="h-1.5 w-1.5 rounded-full bg-ink/50 animate-bounce [animation-delay:-0.1s]" />
                  <span className="h-1.5 w-1.5 rounded-full bg-ink/50 animate-bounce" />
                </span>
              </div>
            )}
          </div>

          <form onSubmit={send} className="p-3 border-t border-ink-light flex gap-2">
            <input
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder="Ask a question…"
              className="flex-1 text-sm px-3.5 py-2.5 rounded-xl border border-ink-light focus:border-ink/40 outline-none"
            />
            <button
              type="submit"
              disabled={!input.trim() || sending}
              className="h-10 w-10 shrink-0 rounded-xl bg-ink text-white flex items-center justify-center disabled:opacity-40"
              aria-label="Send"
            >
              <Send size={16} />
            </button>
          </form>
        </div>
      )}
    </>
  );
}
