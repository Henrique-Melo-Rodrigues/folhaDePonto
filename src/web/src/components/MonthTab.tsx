import { useEffect, useMemo, useState } from "react";

import { api, UnauthorizedError } from "../api";
import {
  daysInMonth,
  firstWeekday,
  monthLabel,
  nextMonth,
  previousMonth,
  toISO,
  todayISO,
} from "../dates";
import { DAY_TYPE_SHORT_LABELS, STATUS_LABELS, type TimeRecord } from "../types";

interface Props {
  reloadToken: number;
  onEdit: (date: string, record: TimeRecord | null) => void;
  onUnauthorized: () => void;
}

const WEEKDAY_HEADERS = ["dom", "seg", "ter", "qua", "qui", "sex", "sáb"];

export function MonthTab({ reloadToken, onEdit, onUnauthorized }: Props) {
  const today = todayISO();
  const [year, setYear] = useState(() => Number(today.slice(0, 4)));
  const [month, setMonth] = useState(() => Number(today.slice(5, 7)));
  const [records, setRecords] = useState<TimeRecord[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    setError("");

    api
      .getMonth(year, month)
      .then((data) => {
        if (!cancelled) {
          setRecords(data);
        }
      })
      .catch((err: unknown) => {
        if (cancelled) return;
        if (err instanceof UnauthorizedError) {
          onUnauthorized();
          return;
        }
        setError(err instanceof Error ? err.message : "Erro ao carregar o mês.");
      })
      .finally(() => {
        if (!cancelled) {
          setLoading(false);
        }
      });

    return () => {
      cancelled = true;
    };
  }, [year, month, reloadToken, onUnauthorized]);

  const recordsByDate = useMemo(() => {
    const map = new Map<string, TimeRecord>();
    for (const record of records) {
      map.set(record.date, record);
    }
    return map;
  }, [records]);

  const changeMonth = (calc: (y: number, m: number) => [number, number]) => {
    const [newYear, newMonth] = calc(year, month);
    setYear(newYear);
    setMonth(newMonth);
  };

  const totalDays = daysInMonth(year, month);
  const leadingBlanks = firstWeekday(year, month);
  const cells: (number | null)[] = [
    ...Array.from({ length: leadingBlanks }, () => null),
    ...Array.from({ length: totalDays }, (_, index) => index + 1),
  ];

  return (
    <div className="stack">
      <div className="month-nav">
        <button onClick={() => changeMonth(previousMonth)} aria-label="Mês anterior">
          ‹
        </button>
        <span>{monthLabel(year, month)}</span>
        <button onClick={() => changeMonth(nextMonth)} aria-label="Próximo mês">
          ›
        </button>
      </div>

      {error && <p className="error">{error}</p>}

      <div className={loading ? "calendar loading" : "calendar"}>
        {WEEKDAY_HEADERS.map((weekday) => (
          <div key={weekday} className="cal-head">
            {weekday}
          </div>
        ))}

        {cells.map((day, index) => {
          if (day === null) {
            return <div key={`blank-${index}`} className="cal-cell blank" />;
          }

          const isoDate = toISO(year, month, day);
          const record = recordsByDate.get(isoDate) ?? null;
          const classNames = ["cal-cell"];
          if (record) {
            classNames.push(`cal-${record.status}`);
          }
          if (isoDate === today) {
            classNames.push("cal-today");
          }

          const times = record
            ? [
                record.times.arrival,
                record.times.lunch_start,
                record.times.lunch_end,
                record.times.departure,
              ]
            : [];
          const hasAnyTime = times.some(Boolean);

          return (
            <button
              key={isoDate}
              className={classNames.join(" ")}
              onClick={() => onEdit(isoDate, record)}
              title={
                record
                  ? `${DAY_TYPE_SHORT_LABELS[record.day_type]} — ${STATUS_LABELS[record.status]}${record.notes ? `\n${record.notes}` : ""}`
                  : "Criar registro"
              }
            >
              <span className="cal-day-num">
                {day}
                {record?.notes ? <span className="cal-note-dot" /> : null}
              </span>
              {record && (
                <span className="cal-day-body">
                  {hasAnyTime ? (
                    times.map((time, timeIndex) => (
                      <span key={timeIndex} className="cal-time">
                        {time ?? "--:--"}
                      </span>
                    ))
                  ) : (
                    <span className="cal-type">{DAY_TYPE_SHORT_LABELS[record.day_type]}</span>
                  )}
                </span>
              )}
            </button>
          );
        })}
      </div>

      <div className="cal-legend">
        <span>
          <i className="legend-swatch legend-complete" /> Completo
        </span>
        <span>
          <i className="legend-swatch legend-incomplete" /> Incompleto
        </span>
        <span>
          <i className="legend-swatch legend-not_worked" /> Não trabalhado
        </span>
      </div>
      <p className="hint">Toque num dia para criar ou editar o registro.</p>
    </div>
  );
}
