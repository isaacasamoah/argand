/** JSON requests to the local backend. Provider credentials never enter the browser. */
export async function api<T>(path: string, body?: unknown): Promise<T> {
  const response = await fetch(
    "/api/" + path,
    body === undefined
      ? undefined
      : {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(body),
        },
  );
  const data = await response.json();
  if (!response.ok) throw new Error(data.detail || "Request failed");
  return data as T;
}
