import type { TimeRecord, TimeRecordInput } from "./types";

const API_KEY_STORAGE = "folha-ponto-api-key";

export function getStoredApiKey(): string {
  return localStorage.getItem(API_KEY_STORAGE) ?? "";
}

export function storeApiKey(key: string): void {
  localStorage.setItem(API_KEY_STORAGE, key);
}

export function clearApiKey(): void {
  localStorage.removeItem(API_KEY_STORAGE);
}

export class UnauthorizedError extends Error {
  constructor() {
    super("Chave de API inválida.");
  }
}

export class ApiError extends Error {
  constructor(status: number, message: string) {
    super(message || `Erro ${status} na API.`);
  }
}

async function request<T>(path: string, init: RequestInit = {}): Promise<T | null> {
  const response = await fetch(`/api${path}`, {
    ...init,
    headers: {
      "Content-Type": "application/json",
      "X-Api-Key": getStoredApiKey(),
      ...init.headers,
    },
  });

  if (response.status === 401 || response.status === 403) {
    throw new UnauthorizedError();
  }
  if (response.status === 404) {
    return null;
  }
  if (!response.ok) {
    const body = await response.text();
    throw new ApiError(response.status, body);
  }
  if (response.status === 204) {
    return null;
  }
  return (await response.json()) as T;
}

export const api = {
  async getToday(): Promise<TimeRecord | null> {
    return request<TimeRecord>("/time-records/today/");
  },

  async getByDate(date: string): Promise<TimeRecord | null> {
    return request<TimeRecord>(`/time-records/${date}/`);
  },

  async getMonth(year: number, month: number): Promise<TimeRecord[]> {
    const data = await request<{ results: TimeRecord[] }>(
      `/time-records/month/?year=${year}&month=${month}`,
    );
    return data?.results ?? [];
  },

  async save(input: TimeRecordInput): Promise<TimeRecord> {
    const record = await request<TimeRecord>(`/time-records/${input.date}/`, {
      method: "PUT",
      body: JSON.stringify(input),
    });
    if (!record) {
      throw new ApiError(404, "Falha ao salvar o registro.");
    }
    return record;
  },

  async remove(date: string): Promise<void> {
    await request<void>(`/time-records/${date}/`, { method: "DELETE" });
  },
};
