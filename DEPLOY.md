# Deploy na Hostinger (VPS KVM)

Guia para subir o backend (Django + MongoDB + Caddy) num VPS KVM da Hostinger,
com HTTPS automático e auto-restart. O app Flutter não é hospedado — ele só
aponta para `https://seu-dominio.com.br`.

## 1. Comprar e acessar o VPS

1. Compre um plano **VPS KVM** (KVM 1 já é suficiente).
2. No painel da Hostinger, escolha o template **Ubuntu 24.04** (ou Ubuntu com Docker pré-instalado).
3. Anote o **IP do servidor** e configure o acesso por **chave SSH** (não senha).
4. Conecte:
   ```bash
   ssh root@SEU_IP
   ```

## 2. Apontar o domínio para o VPS

No painel do seu domínio (Hostinger ou registro.br), crie um registro **A**:

```
Tipo: A    Nome: @ (ou seu-dominio.com.br)    Valor: SEU_IP_DO_VPS
```

Aguarde a propagação (minutos a algumas horas). Teste com `ping seu-dominio.com.br`.

## 3. Instalar Docker (se o template não tiver)

```bash
curl -fsSL https://get.docker.com | sh
```

## 4. Firewall — liberar apenas o necessário

```bash
ufw allow 22/tcp     # SSH
ufw allow 80/tcp     # HTTP (Caddy usa para emitir o certificado)
ufw allow 443/tcp    # HTTPS
ufw enable
```

> O MongoDB e a API **não** abrem porta no firewall — só o Caddy fica exposto.

## 5. Clonar o projeto e configurar o .env

```bash
git clone git@github.com:Henrique-Melo-Rodrigues/folhaDePonto.git
cd folhaDePonto/src/backend

cp .env.prod.example .env
nano .env   # preencha SECRET_KEY, API_KEY, MONGO_ROOT_PASSWORD, ALLOWED_HOSTS
```

Gere os segredos com:
```bash
python3 -c "import secrets; print(secrets.token_urlsafe(50))"   # SECRET_KEY
python3 -c "import secrets; print(secrets.token_urlsafe(32))"   # API_KEY
```

## 6. Configurar o domínio no Caddy

```bash
nano Caddyfile   # troque "seu-dominio.com.br" pelo seu domínio real
```

## 7. Subir tudo

```bash
docker compose -f docker-compose.prod.yml up --build -d
```

O Caddy emite o certificado HTTPS sozinho. Teste:
```bash
curl https://seu-dominio.com.br/api/health/
# {"status":"ok"}
```

## 8. Rebuild do app Flutter apontando para produção

Na sua máquina:
```bash
cd src/mobile
flutter build apk --release \
  --dart-define=API_BASE_URL=https://seu-dominio.com.br \
  --dart-define=API_KEY=<a mesma API_KEY do .env do servidor>
```

Instale o novo APK no celular.

## 9. Backup do banco (recomendado)

Crontab diário com mongodump:
```bash
crontab -e
# Todo dia às 3h, dump para /root/backups
0 3 * * * docker exec folha_mongodb mongodump --username folha_admin --password SUA_SENHA --authenticationDatabase admin --archive=/data/db/backup-$(date +\%F).archive
```

## Comandos úteis

```bash
docker compose -f docker-compose.prod.yml logs -f       # ver logs
docker compose -f docker-compose.prod.yml restart api   # reiniciar API
docker compose -f docker-compose.prod.yml down          # parar tudo
docker compose -f docker-compose.prod.yml pull && \
  docker compose -f docker-compose.prod.yml up --build -d  # atualizar após git pull
```

## Monitoramento de uptime

Crie uma conta grátis no **UptimeRobot** e monitore `https://seu-dominio.com.br/api/health/`.
Você recebe alerta por e-mail se a API cair.
