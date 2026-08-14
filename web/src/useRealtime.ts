import { useEffect, useRef } from "react";
import { wsUrl } from "./api";

/** Подписка на WS-события api; при любом апдейте зовёт onUpdate (список/тред сами решают, что перезапросить). */
export function useRealtime(onUpdate: () => void) {
  const cbRef = useRef(onUpdate);
  cbRef.current = onUpdate;

  useEffect(() => {
    let ws: WebSocket | null = null;
    let closedByUs = false;
    let retryDelay = 1000;
    let retryTimer: ReturnType<typeof setTimeout>;

    function connect() {
      ws = new WebSocket(wsUrl());
      ws.onmessage = () => cbRef.current();
      ws.onclose = () => {
        if (closedByUs) return;
        retryTimer = setTimeout(connect, retryDelay);
        retryDelay = Math.min(retryDelay * 1.5, 10000);
      };
    }
    connect();

    return () => {
      closedByUs = true;
      clearTimeout(retryTimer);
      ws?.close();
    };
  }, []);
}
