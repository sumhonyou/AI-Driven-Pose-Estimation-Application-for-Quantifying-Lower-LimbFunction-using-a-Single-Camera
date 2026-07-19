export const TOKEN_KEY = "physiofit-token";

// Exported for callers that need to fetch a non-JSON authenticated response
// directly (e.g. reminderService's .ics download), bypassing apiRequest's
// JSON-only assumption.
export const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL?.replace(/\/$/, "") || "http://localhost:8000";

export class ApiError extends Error {
  status: number;

  constructor(status: number, message: string) {
    super(message);
    this.name = "ApiError";
    this.status = status;
  }
}

type RequestOptions = Omit<RequestInit, "body"> & {
  body?: unknown;
  auth?: boolean;
};

export async function apiRequest<T>(
  path: string,
  { body, auth = true, headers, ...options }: RequestOptions = {},
): Promise<T> {
  const token = localStorage.getItem(TOKEN_KEY);
  const requestHeaders = new Headers(headers);

  if (body !== undefined) requestHeaders.set("Content-Type", "application/json");
  if (auth && token) requestHeaders.set("Authorization", `Bearer ${token}`);

  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...options,
    headers: requestHeaders,
    body: body !== undefined ? JSON.stringify(body) : undefined,
  });

  if (response.status === 401) {
    localStorage.removeItem(TOKEN_KEY);
  }

  const isJson = response.headers.get("content-type")?.includes("application/json");
  const payload = isJson ? await response.json() : null;

  if (!response.ok) {
    const message =
      typeof payload?.detail === "string"
        ? payload.detail
        : "The server could not complete this request.";
    throw new ApiError(response.status, message);
  }

  return payload as T;
}
