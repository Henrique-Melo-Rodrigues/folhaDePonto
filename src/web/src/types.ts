import type { DayType, RecordStatus } from "./domain.generated";

// O vocabulário do domínio (tipos de dia, status, campos de horário e labels)
// vem de contracts/time_record.json — veja src/domain.generated.ts.
export {
  DAY_TYPES,
  DAY_TYPE_LABELS,
  DAY_TYPE_SHORT_LABELS,
  STATUSES,
  STATUS_LABELS,
  TIME_FIELDS,
  TIME_FIELD_LABELS,
} from "./domain.generated";
export type { DayType, RecordStatus, TimeField } from "./domain.generated";

export interface Times {
  arrival: string | null;
  lunch_start: string | null;
  lunch_end: string | null;
  departure: string | null;
}

export interface TimeRecord {
  user_id: string;
  date: string;
  day_type: DayType;
  times: Times;
  notes: string;
  status: RecordStatus;
  created_at: string;
  updated_at: string;
}

export interface TimeRecordInput {
  date: string;
  day_type: DayType;
  times: Times;
  notes: string;
}
