# Deploy no Termux (celular antigo como servidor)

Guia para rodar o app completo (API Django + SQLite + frontend web) num celular
Android antigo com Termux, administrado por SSH a partir do PC. Sem Docker,
sem MongoDB — só Python.

## Visão geral

```
[PC / outros aparelhos]  --HTTP-->  [Celular antigo]
   navegador                          Termux
                                      ├─ Django (API + frontend buildado)
                                      ├─ SQLite (db.sqlite3)
                                      └─ sshd (administração)
```

## 1. Instalar o Termux

Instale o Termux pelo **F-Droid** (a versão da Play Store está desatualizada):
<https://f-droid.org/packages/com.termux/>

No Termux:

```bash
pkg update && pkg upgrade
pkg install python git openssh
```

## 2. Habilitar o SSH para administrar pelo PC

No Termux:

```bash
passwd          # define uma senha para o SSH
whoami          # anote o usuário (ex.: u0_a123)
ifconfig wlan0  # anote o IP do celular na rede (ex.: 192.168.0.50)
sshd            # inicia o servidor SSH na porta 8022
```

No PC:

```bash
ssh -p 8022 u0_a123@192.168.0.50
```

Dica: configure chave SSH para não digitar senha:

```bash
ssh-copy-id -p 8022 u0_a123@192.168.0.50
```

## 3. Clonar o projeto e instalar dependências

No celular (via SSH):

```bash
git clone https://github.com/Henrique-Melo-Rodrigues/folhaDePonto.git
cd folhaDePonto/src/backend
pip install -r requirements.txt
```

## 4. Configurar o .env

```bash
cp .env.example .env
nano .env
```

Preencha:

```env
DEBUG=False
SECRET_KEY=<gere abaixo>
ALLOWED_HOSTS=localhost,127.0.0.1,192.168.0.50   # inclua o IP do celular
FIXED_USER_ID=usuario_001
API_KEY=<gere abaixo>
```

Gere os segredos:

```bash
python -c "import secrets; print(secrets.token_urlsafe(50))"   # SECRET_KEY
python -c "import secrets; print(secrets.token_urlsafe(32))"   # API_KEY
```

## 5. Enviar o build do frontend

O build do Vite (`src/web/dist`) não é versionado. Gere no PC e envie por scp:

```bash
# No PC:
cd src/web
npm install
npm run build
scp -P 8022 -r dist u0_a123@192.168.0.50:~/folhaDePonto/src/web/
```

Repita esse passo sempre que mudar o frontend.

## 6. Criar o banco e subir o servidor

No celular:

```bash
cd ~/folhaDePonto/src/backend
python manage.py migrate
python manage.py runserver 0.0.0.0:8000
```

Pronto. De qualquer aparelho da rede, acesse:

```
http://192.168.0.50:8000
```

Na primeira visita o app pede a **chave de API** (a mesma `API_KEY` do `.env`).

## 7. Manter rodando com a tela desligada

O Android mata processos em segundo plano agressivamente. Para evitar:

1. Na notificação do Termux, toque em **Acquire wakelock**.
2. Desative a otimização de bateria para o Termux
   (Configurações → Bateria → Termux → Sem restrições).
3. Rode o servidor de forma persistente:

```bash
nohup python manage.py runserver 0.0.0.0:8000 > ~/folha.log 2>&1 &
```

Para parar depois: `pkill -f runserver`.

## 8. Atualizar após mudanças no código

```bash
# No celular (via SSH):
cd ~/folhaDePonto
git pull
cd src/backend
pip install -r requirements.txt
python manage.py migrate
pkill -f runserver
nohup python manage.py runserver 0.0.0.0:8000 > ~/folha.log 2>&1 &
```

(E reenvie o `dist` do passo 5 se o frontend mudou.)

## 9. Backup do banco

O banco é um arquivo único. Do PC:

```bash
scp -P 8022 u0_a123@192.168.0.50:~/folhaDePonto/src/backend/db.sqlite3 ./backup-$(date +%F).sqlite3
```

## Solução de problemas

- **`DisallowedHost`**: adicione o IP do celular em `ALLOWED_HOSTS` no `.env`.
- **Página 503 "Frontend não encontrado"**: o `dist` não foi enviado (passo 5).
- **403 nas chamadas da API**: a chave digitada no app difere da `API_KEY` do `.env`.
- **IP do celular mudou**: fixe o IP no roteador (reserva DHCP) para não mudar.
