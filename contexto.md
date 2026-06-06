Projeto: App de Folha de Ponto Pessoal
Ideia principal revisada

Criar um aplicativo Android em Flutter para registro pessoal de horários de trabalho, permitindo que o usuário registre manualmente:

entrada;
saída para almoço;
retorno do almoço;
saída final;
tipo do dia;
observações.

A API será feita em Python com Django, servida em um servidor barato de hospedagem via Docker Compose. O banco de dados escolhido para testes será o MongoDB, usado principalmente para armazenar os registros diários de ponto em formato de documento.

O gerenciamento de pacotes Python será feito desde o início com uv, usando pyproject.toml e uv.lock como base do ambiente. O uv é um gerenciador de projetos e pacotes Python escrito em Rust.

Decisão importante de arquitetura

Eu não tentaria usar o MongoDB como se fosse um banco relacional dentro do ORM do Django.

O melhor caminho para esse projeto é:

Flutter App
   ↓
Django REST API
   ↓
Camada de services/repositories
   ↓
PyMongo
   ↓
MongoDB

Ou seja:

Django cuida da API;
Django REST Framework cuida dos endpoints;
PyMongo cuida da conexão com o MongoDB;
os dados são salvos como documentos;
você não depende do ORM tradicional do Django para os registros de ponto.

PyMongo é o driver oficial/recomendado para trabalhar com MongoDB em Python.

Como ficaria o documento principal no MongoDB

Em vez de várias tabelas, o MongoDB pode guardar cada dia como um documento.

Exemplo de registro:

{
  "user_id": "usuario_001",
  "date": "2026-05-27",
  "day_type": "trabalho",
  "times": {
    "arrival": "07:45",
    "lunch_start": "12:00",
    "lunch_end": "13:00",
    "departure": "14:45"
  },
  "notes": "Dia normal de trabalho",
  "status": "complete",
  "created_at": "2026-05-27T19:00:00",
  "updated_at": "2026-05-27T19:30:00"
}

Para dias sem trabalho:

{
  "user_id": "usuario_001",
  "date": "2026-05-26",
  "day_type": "atividade_teorica",
  "times": {
    "arrival": null,
    "lunch_start": null,
    "lunch_end": null,
    "departure": null
  },
  "notes": "Atividade teórica do mercado de trabalho",
  "status": "not_worked"
}

Isso combina bem com o problema, porque cada dia pode ter uma estrutura simples, flexível e fácil de consultar.

Tipos de dia

Eu manteria isso como enum no backend:

trabalho
atividade_teorica
folga
compensacao
feriado
falta
outro

Isso resolve seu principal problema: segunda-feira não será fixa.

O app não vai assumir que segunda é sempre atividade teórica. Ele vai deixar você classificar cada dia manualmente.

Estrutura inicial do backend

Eu começaria o projeto assim:

backend/
├── pyproject.toml
├── uv.lock
├── manage.py
├── docker-compose.yml
├── Dockerfile
├── .env
├── config/
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
└── apps/
    └── time_records/
        ├── views.py
        ├── serializers.py
        ├── services.py
        ├── repositories.py
        └── urls.py

A divisão seria:

views.py: recebe requisições HTTP;
serializers.py: valida os dados;
services.py: regras de negócio;
repositories.py: conversa diretamente com o MongoDB via PyMongo;
settings.py: configura variáveis de ambiente e conexão.
Dependências iniciais com uv

Para começar o backend, você poderia usar algo nessa linha:

uv init backend
cd backend

uv add django
uv add djangorestframework
uv add pymongo
uv add python-dotenv
uv add gunicorn
uv add django-cors-headers

Mais tarde, se precisar de autenticação:

uv add djangorestframework-simplejwt
Docker Compose inicial

A primeira versão pode ter dois serviços:

services:
  api:
    build: .
    container_name: folha_api
    ports:
      - "8000:8000"
    env_file:
      - .env
    depends_on:
      - mongodb

  mongodb:
    image: mongo:7
    container_name: folha_mongodb
    ports:
      - "27017:27017"
    volumes:
      - mongo_data:/data/db

volumes:
  mongo_data:

Para servidor barato, eu teria cuidado com memória. Se o VPS for muito limitado, talvez seja melhor deixar só a API no servidor e usar um MongoDB externo. Mas para estudo e MVP, subir tudo no Docker Compose é válido.

.env inicial
DEBUG=True
SECRET_KEY=trocar-em-producao
ALLOWED_HOSTS=localhost,127.0.0.1

MONGO_URI=mongodb://mongodb:27017
MONGO_DB_NAME=folha_ponto
Endpoints iniciais do MVP

Eu começaria com poucos endpoints:

POST   /api/time-records/
GET    /api/time-records/today/
GET    /api/time-records/month/?year=2026&month=5
GET    /api/time-records/<date>/
PUT    /api/time-records/<date>/
DELETE /api/time-records/<date>/

Exemplo:

GET /api/time-records/month/?year=2026&month=5

Retorna todos os registros de maio de 2026 organizados por dia.

MVP atualizado
Versão 0.1.0

A primeira versão deve focar só no essencial:

app Android em Flutter;
tela do dia atual;
formulário para preencher horários;
seleção do tipo do dia;
salvar registro via API;
consultar registros do mês;
editar um dia já preenchido;
backend Django;
MongoDB;
Docker Compose;
dependências gerenciadas com uv.

Eu evitaria login na primeira versão, se o app for só seu. Você pode começar com um user_id fixo no backend e adicionar autenticação depois.

Definição final melhorada

O projeto será um aplicativo Android de controle pessoal de folha de ponto, desenvolvido em Flutter, com uma API em Django servida via Docker Compose.

O sistema permitirá registrar manualmente os horários de entrada, almoço, retorno e saída de cada dia, além de classificar dias especiais como atividade teórica, folga, compensação ou feriado.

O banco de dados utilizado será MongoDB, acessado pela API através do PyMongo, com os registros de ponto armazenados como documentos mensais ou diários.

O objetivo principal é substituir anotações soltas por uma visualização organizada por dia e por mês, facilitando o preenchimento da folha de ponto oficial no final do mês.

Minha recomendação direta: use Django como API, mas não tente forçar o ORM do Django em cima do MongoDB. Para esse projeto, Django REST Framework + PyMongo + MongoDB é um caminho mais limpo e mais controlável.