import { formatDateBR } from "../dates";
import {
  DAY_TYPE_LABELS,
  STATUS_LABELS,
  TIME_FIELDS,
  TIME_FIELD_LABELS,
  type TimeRecord,
} from "../types";

export function RecordCard({ record, onClick }: { record: TimeRecord; onClick: () => void }) {
  return (
    <button className="record-card" onClick={onClick}>
      <div className="record-card-header">
        <span className="record-date">{formatDateBR(record.date)}</span>
        <span className={`badge badge-${record.status}`}>{STATUS_LABELS[record.status]}</span>
      </div>
      <div className="record-day-type">{DAY_TYPE_LABELS[record.day_type]}</div>
      <div className="record-times">
        {TIME_FIELDS.map((field) => (
          <div key={field} className="record-time">
            <span className="record-time-label">{TIME_FIELD_LABELS[field]}</span>
            <span className="record-time-value">{record.times[field] ?? "--:--"}</span>
          </div>
        ))}
      </div>
      {record.notes && <div className="record-notes">{record.notes}</div>}
    </button>
  );
}
