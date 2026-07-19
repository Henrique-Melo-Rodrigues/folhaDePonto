export const DAY_TYPES = [
  "trabalho",
  "atividade_teorica",
  "folga",
  "compensacao",
  "feriado",
  "falta",
  "outro",
] as const;

export type DayType = (typeof DAY_TYPES)[number];

export const DAY_TYPE_LABELS: Record<DayType, string> = {
  trabalho: "Trabalho",
  atividade_teorica: "Atividade teórica",
  folga: "Folga",
  compensacao: "Compensação",
  feriado: "Feriado",
  falta: "Falta",
  outro: "Outro",
};

export const DAY_TYPE_SHORT_LABELS: Record<DayType, string> = {
  trabalho: "Trabalho",
  atividade_teorica: "Teórica",
  folga: "Folga",
  compensacao: "Comp.",
  feriado: "Feriado",
  falta: "Falta",
  outro: "Outro",
};

export type RecordStatus = "complete" | "incomplete" | "not_worked";

export const STATUS_LABELS: Record<RecordStatus, string> = {
  complete: "Completo",
  incomplete: "Incompleto",
  not_worked: "Não trabalhado",
};

export interface Times {
  arrival: string | null;
  lunch_start: string | null;
  lunch_end: string | null;
  departure: string | null;
}

export const TIME_FIELDS = ["arrival", "lunch_start", "lunch_end", "departure"] as const;

export type TimeField = (typeof TIME_FIELDS)[number];

export const TIME_FIELD_LABELS: Record<TimeField, string> = {
  arrival: "Entrada",
  lunch_start: "Saída almoço",
  lunch_end: "Volta almoço",
  departure: "Saída",
};

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
