// Бэкенд отдаёt naive UTC-таймстемпы (SQLite не хранит tzinfo) — добавляем "Z", иначе
// браузер интерпретирует строку как локальное время.
function toDate(iso: string): Date {
  return new Date(iso.endsWith("Z") ? iso : `${iso}Z`);
}

export function relativeTime(iso: string): string {
  const diffMin = Math.round((Date.now() - toDate(iso).getTime()) / 60000);
  if (diffMin < 1) return "только что";
  if (diffMin < 60) return `${diffMin} мин назад`;
  const diffH = Math.round(diffMin / 60);
  if (diffH < 24) return `${diffH} ч назад`;
  const diffD = Math.round(diffH / 24);
  if (diffD === 1) return "вчера";
  if (diffD < 7) return `${diffD} дн назад`;
  return toDate(iso).toLocaleDateString("ru-RU", { day: "2-digit", month: "2-digit" });
}

export function timeOnly(iso: string): string {
  return toDate(iso).toLocaleTimeString("ru-RU", { hour: "2-digit", minute: "2-digit" });
}
