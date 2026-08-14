import { useCallback, useEffect, useState } from "react";
import { api, type Chat, type Me } from "./api";
import { ChatList, type Filter } from "./ChatList";
import { ChatThread } from "./ChatThread";
import { useRealtime } from "./useRealtime";
import { getTelegramWebApp } from "./telegram";

function App() {
  const [me, setMe] = useState<Me | null>(null);
  const [authError, setAuthError] = useState<string | null>(null);
  const [chats, setChats] = useState<Chat[]>([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState<Filter>("open");
  const [selected, setSelected] = useState<Chat | null>(null);

  const refresh = useCallback(async () => {
    try {
      const list = await api.listChats();
      setChats(list);
      setSelected((prev) => (prev ? (list.find((c) => c.id === prev.id) ?? prev) : prev));
      setAuthError(null);
    } catch (e) {
      setAuthError(String(e));
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    const webApp = getTelegramWebApp();
    webApp?.ready();
    webApp?.expand();
    api.me().then(setMe).catch((e) => setAuthError(String(e)));
    refresh();
  }, [refresh]);

  useRealtime(refresh);

  useEffect(() => {
    const webApp = getTelegramWebApp();
    if (!webApp) return;
    if (selected) {
      const handler = () => setSelected(null);
      webApp.BackButton.onClick(handler);
      webApp.BackButton.show();
      return () => webApp.BackButton.hide();
    }
    webApp.BackButton.hide();
  }, [selected]);

  if (authError) {
    return (
      <div className="shell">
        <div className="empty error">
          Нет доступа: {authError}
          <br />
          Откройте miniapp через бота под аккаунтом оператора из allowlist.
        </div>
      </div>
    );
  }

  return (
    <div className="shell">
      {selected ? (
        <ChatThread
          chat={selected}
          me={me}
          onBack={() => setSelected(null)}
          onChanged={(updated) => {
            setSelected(updated);
            setChats((prev) => prev.map((c) => (c.id === updated.id ? updated : c)));
          }}
        />
      ) : (
        <>
          <header className="shell-header">
            <span className="dot" data-live="true" />
            <h1>Support Console</h1>
            {me && <span className="me-badge">{me.display_name}</span>}
          </header>
          <ChatList
            me={me}
            chats={chats}
            loading={loading}
            filter={filter}
            onFilterChange={setFilter}
            onSelect={setSelected}
          />
        </>
      )}
    </div>
  );
}

export default App;
