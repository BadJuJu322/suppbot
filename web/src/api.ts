import { getInitData } from "./telegram";

const API_BASE = (import.meta.env.VITE_API_BASE_URL as string) || "http://localhost:8000";
const DEV_OPERATOR_ID = import.meta.env.VITE_DEV_OPERATOR_ID as string | undefined;

function authHeader(): string {
  const initData = getInitData();
  if (initData) return `tma ${initData}`;
  if (DEV_OPERATOR_ID) return `dev ${DEV_OPERATOR_ID}`;
  return "";
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    ...init,
    headers: {
      "Content-Type": "application/json",
      Authorization: authHeader(),
      ...(init?.headers || {}),
    },
  });
  if (!res.ok) {
    const body = await res.text().catch(() => "");
    throw new Error(`${res.status}: ${body || res.statusText}`);
  }
  if (res.status === 204) return undefined as T;
  return res.json();
}

export type ChatStatus = "open" | "in_progress" | "closed";

export interface Chat {
  id: number;
  user_telegram_id: number;
  user_display_name: string;
  status: ChatStatus;
  claimed_by_id: number | null;
  claimed_by_name: string | null;
  last_message: string | null;
  last_message_at: string | null;
  created_at: string;
  updated_at: string;
}

export interface ChatMessage {
  id: number;
  chat_id: number;
  sender_type: "user" | "operator";
  operator_id: number | null;
  text: string;
  created_at: string;
}

export interface Me {
  id: number;
  telegram_id: number;
  display_name: string;
}

export const api = {
  me: () => request<Me>("/me"),
  listChats: (status?: string) => request<Chat[]>(`/chats${status ? `?status=${status}` : ""}`),
  getMessages: (chatId: number) => request<ChatMessage[]>(`/chats/${chatId}/messages`),
  claim: (chatId: number) => request<Chat>(`/chats/${chatId}/claim`, { method: "POST" }),
  release: (chatId: number) => request<Chat>(`/chats/${chatId}/release`, { method: "POST" }),
  close: (chatId: number) => request<Chat>(`/chats/${chatId}/close`, { method: "POST" }),
  sendMessage: (chatId: number, text: string) =>
    request<ChatMessage>(`/chats/${chatId}/messages`, { method: "POST", body: JSON.stringify({ text }) }),
};

export function wsUrl(): string {
  const base = new URL(API_BASE);
  const proto = base.protocol === "https:" ? "wss:" : "ws:";
  const initData = getInitData() || (DEV_OPERATOR_ID ? `dev:${DEV_OPERATOR_ID}` : "");
  return `${proto}//${base.host}/ws?init_data=${encodeURIComponent(initData)}`;
}
