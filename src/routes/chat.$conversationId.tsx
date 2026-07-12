import { createFileRoute } from "@tanstack/react-router";
import { useState, useRef, useEffect } from "react";
import { Send, BadgeCheck, AlertTriangle } from "lucide-react";
import { MOCK_LISTINGS } from "@/lib/mock-data";

export const Route = createFileRoute("/chat/$conversationId")({
  head: () => ({ meta: [{ title: "محادثة — مسكن" }] }),
  component: Chat,
});

interface Msg {
  id: string;
  text: string;
  from: "me" | "other";
  ts: string;
  read?: boolean;
  warning?: boolean;
}

function isFiltered(t: string) {
  return /\d{8,}/.test(t) || /(whatsapp|واتس|@gmail|\.com)/i.test(t);
}

function Chat() {
  const { conversationId } = Route.useParams();
  const l = MOCK_LISTINGS.find((x) => x.id === conversationId) ?? MOCK_LISTINGS[0];
  const [messages, setMessages] = useState<Msg[]>([
    { id: "1", from: "other", text: "السلام عليكم", ts: "10:30", read: true },
    { id: "2", from: "me", text: "وعليكم السلام، الإعلان متاح للمعاينة؟", ts: "10:32", read: true },
    { id: "3", from: "other", text: "نعم متاح. متى تستطيع المرور؟", ts: "10:33", read: true },
  ]);
  const [text, setText] = useState("");
  const endRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  function send() {
    if (!text.trim()) return;
    const warn = isFiltered(text);
    setMessages((m) => [
      ...m,
      {
        id: String(Date.now()),
        from: "me",
        text: warn ? "*** تمت فلترة بيانات تواصل خارجية ***" : text,
        ts: new Date().toLocaleTimeString("ar", { hour: "2-digit", minute: "2-digit" }),
        warning: warn,
      },
    ]);
    setText("");
  }

  return (
    <div className="mx-auto max-w-7xl px-4 py-6">
      <div className="grid h-[calc(100vh-8rem)] gap-4 lg:grid-cols-[320px_1fr]">
        {/* Conversations list */}
        <aside className="hidden overflow-hidden rounded-2xl border bg-card lg:block">
          <div className="border-b p-4 font-bold">المحادثات</div>
          <ul className="divide-y overflow-y-auto">
            {MOCK_LISTINGS.slice(0, 5).map((c, i) => (
              <li key={c.id}>
                <button
                  className={`flex w-full gap-3 p-3 text-right transition hover:bg-secondary ${
                    c.id === conversationId ? "bg-primary/5" : ""
                  }`}
                >
                  <img
                    src={c.image}
                    alt=""
                    className="h-12 w-12 flex-shrink-0 rounded-lg object-cover"
                  />
                  <div className="min-w-0 flex-1">
                    <div className="truncate text-sm font-semibold">{c.title}</div>
                    <div className="truncate text-xs text-muted-foreground">آخر رسالة...</div>
                  </div>
                  {i === 0 && (
                    <span className="h-2 w-2 self-center rounded-full bg-primary" />
                  )}
                </button>
              </li>
            ))}
          </ul>
        </aside>

        {/* Chat window */}
        <div className="flex flex-col overflow-hidden rounded-2xl border bg-card">
          <div className="flex items-center gap-3 border-b p-4">
            <img src={l.image} alt="" className="h-11 w-11 rounded-lg object-cover" />
            <div className="flex-1">
              <div className="font-bold">{l.title}</div>
              <div className="flex items-center gap-1 text-xs text-muted-foreground">
                تتحدث مع: محمد أحمد <BadgeCheck className="h-3.5 w-3.5 text-success" />
              </div>
            </div>
          </div>

          <div className="flex-1 space-y-3 overflow-y-auto bg-background p-4">
            {messages.map((m) => (
              <div key={m.id} className={`flex ${m.from === "me" ? "justify-start" : "justify-end"}`}>
                <div
                  className={`max-w-[75%] rounded-2xl px-4 py-2 text-sm shadow-sm ${
                    m.warning
                      ? "border border-warning bg-warning/10 text-foreground"
                      : m.from === "me"
                        ? "rounded-bl-none bg-primary text-primary-foreground"
                        : "rounded-br-none bg-card"
                  }`}
                >
                  {m.warning && (
                    <div className="mb-1 flex items-center gap-1 text-xs font-bold text-warning">
                      <AlertTriangle className="h-3 w-3" /> تنبيه: فلترة بيانات
                    </div>
                  )}
                  <p>{m.text}</p>
                  <div
                    className={`mt-1 text-end text-[10px] ${
                      m.from === "me" ? "text-white/70" : "text-muted-foreground"
                    }`}
                  >
                    {m.ts} {m.from === "me" && (m.read ? "✓✓" : "✓")}
                  </div>
                </div>
              </div>
            ))}
            <div ref={endRef} />
          </div>

          <div className="border-t p-3">
            <div className="flex gap-2">
              <input
                value={text}
                onChange={(e) => setText(e.target.value)}
                onKeyDown={(e) => e.key === "Enter" && send()}
                placeholder="اكتب رسالتك..."
                className="flex-1 rounded-lg border bg-card px-4 py-2.5 outline-none focus:border-primary"
              />
              <button
                onClick={send}
                className="flex items-center gap-1 rounded-lg bg-primary px-5 py-2.5 font-bold text-primary-foreground hover:bg-primary-light"
              >
                <Send className="h-4 w-4" /> إرسال
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
