import { useEffect, useRef, useState } from "react";
import { api, type Chat, type ChatMessage, type Me } from "./api";
import { timeOnly } from "./format";

interface Props {
  chat: Chat;
  me: Me | null;
  onBack: () => void;
  onChanged: (chat: Chat) => void;
}

export function ChatThread({ chat, me, onBack, onChanged }: Props) {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [text, setText] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const listRef = useRef<HTMLDivElement>(null);

  const isMine = chat.claimed_by_id === me?.id;
  const isFree = chat.claimed_by_id === null && chat.status !== "closed";
  const canReply = isMine && chat.status !== "closed";

  useEffect(() => {
    api.getMessages(chat.id).then(setMessages).catch((e) => setError(String(e)));
  }, [chat.id]);

  useEffect(() => {
    listRef.current?.scrollTo({ top: listRef.current.scrollHeight });
  }, [messages]);

  async function run(action: () => Promise<Chat>, failMsg: string) {
    setBusy(true);
    setError(null);
    try {
      onChanged(await action());
    } catch {
      setError(failMsg);
    } finally {
      setBusy(false);
    }
  }

  async function handleSend() {
    if (!text.trim()) return;
    setBusy(true);
    setError(null);
    const value = text.trim();
    try {
      const msg = await api.sendMessage(chat.id, value);
      setMessages((prev) => [...prev, msg]);
      setText("");
    } catch {
      setError("Не удалось отправить сообщение");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="thread-screen">
      <header className="thread-header">
        <button className="back-btn" onClick={onBack} aria-label="Назад">←</button>
        <div className="thread-title">
          <span className="thread-name">{chat.user_display_name || `id${chat.user_telegram_id}`}</span>
          <span className="thread-status">
            {chat.status === "closed"
              ? "закрыт"
              : chat.claimed_by_id
                ? isMine
                  ? "в работе — у вас"
                  : `в работе — ${chat.claimed_by_name}`
                : "свободен"}
          </span>
        </div>
        {isMine && chat.status !== "closed" && (
          <div className="thread-actions">
            <button onClick={() => run(() => api.release(chat.id), "Не удалось освободить")} disabled={busy}>
              Освободить
            </button>
            <button
              className="danger"
              onClick={() => run(() => api.close(chat.id), "Не удалось закрыть")}
              disabled={busy}
            >
              Закрыть
            </button>
          </div>
        )}
      </header>

      <div className="thread-messages" ref={listRef}>
        {messages.map((m) => (
          <div key={m.id} className={`bubble bubble-${m.sender_type}`}>
            <span className="bubble-text">{m.text}</span>
            <span className="bubble-time">{timeOnly(m.created_at)}</span>
          </div>
        ))}
      </div>

      {error && <div className="thread-error">{error}</div>}

      <footer className="thread-input">
        {isFree ? (
          <button
            className="claim-btn"
            onClick={() => run(() => api.claim(chat.id), "Не удалось взять чат — возможно, его уже забрали")}
            disabled={busy}
          >
            Взять чат
          </button>
        ) : canReply ? (
          <>
            <input
              value={text}
              onChange={(e) => setText(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && handleSend()}
              placeholder="Сообщение…"
              disabled={busy}
            />
            <button onClick={handleSend} disabled={busy || !text.trim()}>
              Отправить
            </button>
          </>
        ) : (
          <span className="thread-locked">
            {chat.status === "closed" ? "Чат закрыт" : `Занято оператором ${chat.claimed_by_name}`}
          </span>
        )}
      </footer>
    </div>
  );
}
