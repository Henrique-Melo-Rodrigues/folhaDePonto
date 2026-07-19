import { useState } from "react";

import { api, UnauthorizedError } from "../api";
import { formatDateBR } from "../dates";
import {
  DAY_TYPES,
  DAY_TYPE_LABELS,
  TIME_FIELDS,
  TIME_FIELD_LABELS,
  type DayType,
  type TimeField,
  type TimeRecord,
  type Times,
} from "../types";

interface Props {
  date: string;
  record: TimeRecord | null;
  onDone: (changed: boolean) => void;
  onUnauthorized: () => void;
}

const EMPTY_TIMES: Times = {
  arrival: null,
  lunch_start: null,
  lunch_end: null,
  departure: null,
};

export function RecordForm({ date, record, onDone, onUnauthorized }: Props) {
  const [dayType, setDayType] = useState<DayType>(record?.day_type ?? "trabalho");
  const [times, setTimes] = useState<Times>(record?.times ?? EMPTY_TIMES);
  const [notes, setNotes] = useState(record?.notes ?? "");
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");

  const setTime = (field: TimeField, value: string) => {
    setTimes((current) => ({ ...current, [field]: value || null }));
  };

  const handleError = (err: unknown) => {
    if (err instanceof UnauthorizedError) {
      onUnauthorized();
      return;
    }
    setError(err instanceof Error ? err.message : "Erro ao salvar.");
  };

  const save = async () => {
    setSaving(true);
    setError("");
    try {
      await api.save({ date, day_type: dayType, times, notes });
      onDone(true);
    } catch (err) {
      handleError(err);
    } finally {
      setSaving(false);
    }
  };

  const remove = async () => {
    if (!window.confirm(`Excluir o registro de ${formatDateBR(date)}?`)) {
      return;
    }
    setSaving(true);
    setError("");
    try {
      await api.remove(date);
      onDone(true);
    } catch (err) {
      handleError(err);
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="app">
      <header className="app-header">
        <button className="link-button" onClick={() => onDone(false)}>
          ‹ Voltar
        </button>
        <h1>{formatDateBR(date)}</h1>
      </header>

      <main className="content stack">
        <label className="field">
          <span>Tipo do dia</span>
          <select
            value={dayType}
            onChange={(event) => setDayType(event.target.value as DayType)}
          >
            {DAY_TYPES.map((type) => (
              <option key={type} value={type}>
                {DAY_TYPE_LABELS[type]}
              </option>
            ))}
          </select>
        </label>

        <div className="times-grid">
          {TIME_FIELDS.map((field) => (
            <label key={field} className="field">
              <span>{TIME_FIELD_LABELS[field]}</span>
              <input
                type="time"
                value={times[field] ?? ""}
                onChange={(event) => setTime(field, event.target.value)}
              />
            </label>
          ))}
        </div>

        <label className="field">
          <span>Observações</span>
          <textarea
            rows={3}
            value={notes}
            onChange={(event) => setNotes(event.target.value)}
            placeholder="Anotações livres sobre o dia"
          />
        </label>

        {error && <p className="error">{error}</p>}

        <button className="primary" onClick={save} disabled={saving}>
          {saving ? "Salvando…" : "Salvar"}
        </button>
        {record && (
          <button className="danger" onClick={remove} disabled={saving}>
            Excluir registro
          </button>
        )}
      </main>
    </div>
  );
}
