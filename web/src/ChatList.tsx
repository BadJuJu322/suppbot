import type { Chat, Me } from "./api";
import { relativeTime } from "./format";

export type Filter = "open" | "mine" | "all" | "closed";

const FILTERS: { key: Filter; label: string }[] = [
  { key: "open", label: "Свободные" },
  { key: "mine", label: "Мои" },
  { key: "all", label: "Все" },
  { key: "closed", label: "Закрытые" },
];

const STATUS_LABEL: Record<Chat["status"], string> = {
  open: "открыт",
  in_progress: "в работе",
  closed: "закрыт",
};

interface Props {
  me: Me | null;
  chats: Chat[];
  loading: boolean;
  filter: Filter;
  onFilterChange: (f: Filter) => void;
  onSelect: (chat: Chat) => void;
}

export function ChatList({ me, chats, loading, filter, onFilterChange, onSelect }: Props) {
  const visible = chats.filter((c) => {
    if (filter === "open") return c.status === "open";
    if (filter === "mine") return c.claimed_by_id === me?.id && c.status !== "closed";
    if (filter === "closed") return c.status === "closed";
    return true;
  });

  return (
    <div className="list-screen">
      <div className="tabs">
        {FILTERS.map((f) => (
          <button
            key={f.key}
            className="tab"
            data-active={filter === f.key}
            onClick={() => onFilterChange(f.key)}
          >
            {f.label}
          </button>
        ))}
      </div>

      {loading && chats.length === 0 ? (
        <div className="empty">Загрузка…</div>
      ) : visible.length === 0 ? (
        <div className="empty">Здесь пока пусто</div>
      ) : (
        <ul className="chat-list">
          {visible.map((c) => (
            <li key={c.id} className="chat-item" onClick={() => onSelect(c)}>
              <span className="avatar">{(c.user_display_name || "?").slice(0, 1).toUpperCase()}</span>
              <span className="chat-item-body">
                <span className="chat-item-top">
                  <span className="chat-item-name">{c.user_display_name || `id${c.user_telegram_id}`}</span>
                  <span className="chat-item-time">{relativeTime(c.last_message_at || c.updated_at)}</span>
                </span>
                <span className="chat-item-bottom">
                  <span className="chat-item-preview">{c.last_message || "нет сообщений"}</span>
                  <span className={`status-pill status-${c.status}`}>{STATUS_LABEL[c.status]}</span>
                </span>
                {c.claimed_by_id && (
                  <span className="chat-item-claimed">
                    {c.claimed_by_id === me?.id ? "у вас" : `занято: ${c.claimed_by_name}`}
                  </span>
                )}
              </span>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
