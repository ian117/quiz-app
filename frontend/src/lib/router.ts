import { useSyncExternalStore } from "react";

export type Route =
  | { name: "home" }
  | { name: "history" }
  | { name: "play"; id: number }
  | { name: "notfound" };

export function parseHash(hash: string): Route {
  const path = hash.replace(/^#/, "").replace(/\/+$/, "") || "/";
  if (path === "/") return { name: "home" };
  if (path === "/history") return { name: "history" };
  const play = /^\/play\/(\d+)$/.exec(path);
  if (play) return { name: "play", id: Number(play[1]) };
  return { name: "notfound" };
}

export const paths = {
  home: "#/",
  history: "#/history",
  play: (id: number) => `#/play/${id}`,
};

function subscribe(onChange: () => void) {
  window.addEventListener("hashchange", onChange);
  return () => window.removeEventListener("hashchange", onChange);
}

const snapshot = () => window.location.hash;

export function useHash(): string {
  return useSyncExternalStore(subscribe, snapshot);
}

export function go(hash: string) {
  window.location.hash = hash;
}
