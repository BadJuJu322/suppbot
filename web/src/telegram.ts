// Тонкая обёртка над официальным Telegram WebApp JS SDK
// (подключён в index.html как <script src="https://telegram.org/js/telegram-web-app.js">).
// Без сторонних npm-пакетов — меньше риска расхождения версий с реальным Telegram-клиентом.

export interface TelegramUser {
  id: number;
  first_name: string;
  last_name?: string;
  username?: string;
  language_code?: string;
}

interface TelegramWebApp {
  initData: string;
  initDataUnsafe: { user?: TelegramUser };
  colorScheme: "light" | "dark";
  themeParams: Record<string, string>;
  ready: () => void;
  expand: () => void;
  MainButton: {
    setText: (text: string) => void;
    show: () => void;
    hide: () => void;
    onClick: (cb: () => void) => void;
  };
  BackButton: {
    show: () => void;
    hide: () => void;
    onClick: (cb: () => void) => void;
  };
  HapticFeedback?: {
    impactOccurred: (style: "light" | "medium" | "heavy") => void;
  };
}

declare global {
  interface Window {
    Telegram?: { WebApp: TelegramWebApp };
  }
}

export function getTelegramWebApp(): TelegramWebApp | null {
  return typeof window !== "undefined" && window.Telegram ? window.Telegram.WebApp : null;
}

/** initData — подписанная строка, которую фронт отправляет в API для проверки оператора (см. тикет auth). */
export function getInitData(): string {
  return getTelegramWebApp()?.initData ?? "";
}

export function getTelegramUser(): TelegramUser | null {
  return getTelegramWebApp()?.initDataUnsafe.user ?? null;
}
