// GERADO por contracts/generate.py a partir de contracts/time_record.json. Nao edite a mao.

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

export const STATUSES = [
  "complete",
  "incomplete",
  "not_worked",
] as const;

export type RecordStatus = (typeof STATUSES)[number];

export const STATUS_LABELS: Record<RecordStatus, string> = {
  complete: "Completo",
  incomplete: "Incompleto",
  not_worked: "Não trabalhado",
};

export const TIME_FIELDS = [
  "arrival",
  "lunch_start",
  "lunch_end",
  "departure",
] as const;

export type TimeField = (typeof TIME_FIELDS)[number];

export const TIME_FIELD_LABELS: Record<TimeField, string> = {
  arrival: "Entrada",
  lunch_start: "Saída almoço",
  lunch_end: "Volta almoço",
  departure: "Saída",
};
