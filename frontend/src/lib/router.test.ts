import { describe, expect, it } from "vitest";

import { parseHash } from "./router";

describe("parseHash", () => {
  it("reconoce las rutas", () => {
    expect(parseHash("")).toEqual({ name: "home" });
    expect(parseHash("#/")).toEqual({ name: "home" });
    expect(parseHash("#/history")).toEqual({ name: "history" });
    expect(parseHash("#/play/42")).toEqual({ name: "play", id: 42 });
  });
  it("tolera la barra final", () => {
    expect(parseHash("#/history/")).toEqual({ name: "history" });
  });
  it("lo demás no existe", () => {
    expect(parseHash("#/play/abc")).toEqual({ name: "notfound" });
    expect(parseHash("#/nada")).toEqual({ name: "notfound" });
  });
});
