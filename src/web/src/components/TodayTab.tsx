import { useEffect, useState } from "react";

import { api, UnauthorizedError } from "../api";
import { todayISO } from "../dates";
import type { TimeRecord } from "../types";
import { RecordCard } from "./RecordCard";

interface Props {
  reloadToken: number;
  onEdit: (date: string, record: TimeRecord | null) => void;
  onUnauthorized: () => void;
}

export function TodayTab({ reloadToken, onEdit, onUnauthorized }: Props) {
  const [record, setRecord] = useState<TimeRecord | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    setError("");

    api
      .getToday()
      .then((data) => {
        if (!cancelled) {
          setRecord(data);
        }
      })
      .catch((err: unknown) => {
        if (cancelled) return;
        if (err instanceof UnauthorizedError) {
          onUnauthorized();
          return;
        }
        setError(err instanceof Error ? err.message : "Erro ao carregar o registro de hoje.");
      })
      .finally(() => {
        if (!cancelled) {
          setLoading(false);
        }
      });

    return () => {
      cancelled = true;
    };
  }, [reloadToken, onUnauthorized]);

  if (loading) return <p className="hint">Carregando…</p>;
  if (error) return <p className="error">{error}</p>;

  return (
    <div className="stack">
      {record ? (
        <RecordCard record={record} onClick={() => onEdit(record.date, record)} />
      ) : (
        <p className="hint">Nenhum registro para hoje ainda.</p>
      )}
      <button className="primary" onClick={() => onEdit(todayISO(), record)}>
        {record ? "Editar registro de hoje" : "Registrar hoje"}
      </button>
    </div>
  );
}
