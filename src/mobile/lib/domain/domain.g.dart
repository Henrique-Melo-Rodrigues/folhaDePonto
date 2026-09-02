// GERADO por contracts/generate.py a partir de contracts/time_record.json. Nao edite a mao.

const dayTypes = <String>[
  'trabalho',
  'atividade_teorica',
  'folga',
  'compensacao',
  'feriado',
  'falta',
  'outro',
];

const dayTypeLabels = <String, String>{
  'trabalho': 'Trabalho',
  'atividade_teorica': 'Atividade teórica',
  'folga': 'Folga',
  'compensacao': 'Compensação',
  'feriado': 'Feriado',
  'falta': 'Falta',
  'outro': 'Outro',
};

const dayTypeShortLabels = <String, String>{
  'trabalho': 'Trabalho',
  'atividade_teorica': 'Teórica',
  'folga': 'Folga',
  'compensacao': 'Comp.',
  'feriado': 'Feriado',
  'falta': 'Falta',
  'outro': 'Outro',
};

const notWorkedDayTypes = <String>{
  'atividade_teorica',
  'folga',
  'compensacao',
  'feriado',
  'falta',
  'outro',
};

const statuses = <String>[
  'complete',
  'incomplete',
  'not_worked',
];

const statusComplete = 'complete';
const statusIncomplete = 'incomplete';
const statusNotWorked = 'not_worked';

const statusLabels = <String, String>{
  'complete': 'Completo',
  'incomplete': 'Incompleto',
  'not_worked': 'Não trabalhado',
};

const timeFields = <String>[
  'arrival',
  'lunch_start',
  'lunch_end',
  'departure',
];

const timeFieldLabels = <String, String>{
  'arrival': 'Entrada',
  'lunch_start': 'Saída almoço',
  'lunch_end': 'Volta almoço',
  'departure': 'Saída',
};

const timePattern = r'^\d{2}:\d{2}$';
