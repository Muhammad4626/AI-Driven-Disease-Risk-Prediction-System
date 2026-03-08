const API_BASE = process.env.REACT_APP_API_URL || "http://localhost:8000";

type RequestOptions = {
  method?: string;
  body?: any;
  headers?: Record<string, string>;
};

async function request(path: string, options: RequestOptions = {}) {
  const { method = "GET", body, headers = {} } = options;

  const res = await fetch(`${API_BASE}${path}`,{
    method,
    headers: {
      "Content-Type": "application/json",
      ...headers,
    },
    body: body ? JSON.stringify(body) : undefined,
  });

  if (!res.ok) {
    const errText = await res.text();
    throw new Error(errText || "API request failed");
  }

  try {
    return await res.json();
  } catch {
    return null;
  }
}

export default {
  get: (path: string) => request(path),
  post: (path: string, body: any) => request(path, { method: "POST", body }),
  put: (path: string, body: any) => request(path, { method: "PUT", body }),
  delete: (path: string) => request(path, { method: "DELETE" }),
};