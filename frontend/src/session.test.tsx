import { fireEvent, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import { SessionProvider, useSessionFlow } from "./session";
import { TOKEN_KEY } from "./services/apiClient";

function StartSessionButton() {
  const { setSessionId } = useSessionFlow();
  return <button onClick={() => setSessionId("session-123")}>Start</button>;
}

describe("SessionProvider page-exit handling", () => {
  afterEach(() => {
    localStorage.clear();
    vi.restoreAllMocks();
  });

  it("cancels an active session with a keepalive request when the page closes", () => {
    localStorage.setItem(TOKEN_KEY, "access-token");
    const fetchMock = vi.fn().mockResolvedValue(new Response());
    vi.stubGlobal("fetch", fetchMock);

    render(
      <SessionProvider>
        <StartSessionButton />
      </SessionProvider>,
    );
    fireEvent.click(screen.getByRole("button", { name: "Start" }));
    window.dispatchEvent(new Event("pagehide"));

    expect(fetchMock).toHaveBeenCalledWith(
      "http://localhost:8000/api/sessions/session-123/cancel",
      expect.objectContaining({
        method: "POST",
        headers: { Authorization: "Bearer access-token" },
        keepalive: true,
      }),
    );
  });
});
