#!/usr/bin/env bash
set -Eeuo pipefail

PROJECT_DIR="/home/six_element/home/six_element_app/The-Sixth-ELement"
BACKUP_DIR="/home/six_element/backups"
STATE_DIR="/home/six_element/deploy_state"
LOCK_FILE="/var/lock/six_element_deploy.lock"
PAUSE_FILE="$STATE_DIR/deploy.paused"
LAST_SUCCESS_FILE="$STATE_DIR/last_success_commit"

mkdir -p "$BACKUP_DIR" "$STATE_DIR"

# 手动与自动部署共用文件锁，防止并发
exec 9>"$LOCK_FILE"
if ! flock -n 9; then
	echo "[deploy] another deployment is running, exit."
	exit 99
fi

cd "$PROJECT_DIR"

if [ ! -f deploy/.env ]; then
	echo "[deploy] deploy/.env not found"
	exit 1
fi

cp deploy/.env "$BACKUP_DIR/deploy.env.bak"

DB_ROOT_PASSWORD=$(grep '^DB_ROOT_PASSWORD=' deploy/.env | cut -d'=' -f2- || true)
DB_NAME=$(grep '^DB_NAME=' deploy/.env | cut -d'=' -f2- || true)
DB_USER=$(grep '^DB_USER=' deploy/.env | cut -d'=' -f2- || true)
DB_PASSWORD=$(grep '^DB_PASSWORD=' deploy/.env | cut -d'=' -f2- || true)

if [ -z "${DB_ROOT_PASSWORD}" ] || [ -z "${DB_NAME}" ]; then
	echo "[deploy] DB_ROOT_PASSWORD or DB_NAME missing in deploy/.env"
	exit 1
fi

send_mail() {
	local subject="$1"
	local body="$2"

	local SMTP_HOST SMTP_PORT SMTP_USER SMTP_PASS SMTP_FROM SMTP_TO
  SMTP_HOST=$(grep '^EMAIL_HOST=' deploy/.env | cut -d'=' -f2- || true)
  [ -z "$SMTP_HOST" ] && SMTP_HOST="smtp.exmail.qq.com"

  SMTP_PORT=$(grep '^EMAIL_PORT=' deploy/.env | cut -d'=' -f2- || true)
  [ -z "$SMTP_PORT" ] && SMTP_PORT="465"
  
  SMTP_USER=$(grep '^EMAIL_INTERNAL_USER=' deploy/.env | cut -d'=' -f2- || true)
  SMTP_PASS=$(grep '^EMAIL_INTERNAL_PASSWORD=' deploy/.env | cut -d'=' -f2- || true)
  
  local DISPLAY_NAME
  DISPLAY_NAME=$(grep '^EMAIL_INTERNAL_NAME=' deploy/.env | cut -d'=' -f2- || true)
  [ -z "$DISPLAY_NAME" ] && DISPLAY_NAME="第六元素部署节点"
  
  SMTP_FROM="${DISPLAY_NAME} <${SMTP_USER}>"
  
  # 收件人也可以用环境变量，没有的话默认发给自己（作为通知管理员）
  SMTP_TO=$(grep '^EMAIL_DEPLOY_NOTIFY_TO=' deploy/.env | cut -d'=' -f2- || true)
  [ -z "$SMTP_TO" ] && SMTP_TO="${SMTP_USER}"

  if [ -z "${SMTP_USER}" ] || [ -z "${SMTP_PASS}" ]; then
    echo "[deploy] SMTP user/pass missing, skip mail: ${subject}"
    return 0
  fi

  python3 - <<PY || true
import smtplib
import ssl
from email.mime.text import MIMEText

host = "${SMTP_HOST}"
port = int("${SMTP_PORT}")
user = "${SMTP_USER}"
password = "${SMTP_PASS}"
mail_from = """${SMTP_FROM}"""
mail_to = [x.strip() for x in "${SMTP_TO}".split(",") if x.strip()]

msg = MIMEText("""${body}""", "plain", "utf-8")
msg["Subject"] = "${subject}"
msg["From"] = mail_from
msg["To"] = ", ".join(mail_to)

ctx = ssl.create_default_context()
with smtplib.SMTP_SSL(host, port, timeout=20, context=ctx) as s:
    s.login(user, password)
    s.sendmail(user, mail_to, msg.as_string())
PY
}

CURRENT_COMMIT=$(git rev-parse HEAD || echo "unknown")
TARGET_COMMIT="unknown"

on_error() {
	local code=$?
	echo "[deploy] failed with code=${code}"

	if [ -f "$LAST_SUCCESS_FILE" ]; then
		ROLLBACK_COMMIT=$(cat "$LAST_SUCCESS_FILE" || true)
		if [ -n "${ROLLBACK_COMMIT}" ]; then
			echo "[deploy] try rollback to ${ROLLBACK_COMMIT}"
			git fetch --all
			git reset --hard "${ROLLBACK_COMMIT}" || true
			cp "$BACKUP_DIR/deploy.env.bak" deploy/.env || true
			docker compose -f deploy/docker-compose.yml up -d --remove-orphans || true
		fi
	fi

	touch "$PAUSE_FILE"

	send_mail \
		"[SixthElement][FAIL] deployment failed and auto paused" \
		"Deploy failed.
Current commit(before deploy): ${CURRENT_COMMIT}
Target commit: ${TARGET_COMMIT}
Auto deploy paused: ${PAUSE_FILE}
Please check logs and unpause manually."

	exit $code
}
trap on_error ERR

if [ -f "$PAUSE_FILE" ]; then
	echo "[deploy] auto deploy paused by flag: $PAUSE_FILE"
	exit 2
fi

send_mail \
	"[SixthElement][START] deployment started" \
	"Deploy started.
Current commit: ${CURRENT_COMMIT}
Host: $(hostname)
Time: $(date '+%F %T')"

# 1. 更新代码
git fetch --all
git checkout main
git reset --hard origin/main
TARGET_COMMIT=$(git rev-parse HEAD)

# 2. 恢复 .env
cp "$BACKUP_DIR/deploy.env.bak" deploy/.env

# 3. 备份 MySQL（按时间戳保存）
TS=$(date +%F_%H%M%S)
SQL_BAK="$BACKUP_DIR/backup_${TS}.sql"
docker compose -f deploy/docker-compose.yml exec -T db sh -c "mysqldump -uroot -p'$DB_ROOT_PASSWORD' --single-transaction --quick $DB_NAME" > "$SQL_BAK"
ls -lh "$SQL_BAK"

# 4. 用 root 在容器中创建/授权应用用户（从 deploy/.env 读取）
docker compose -f deploy/docker-compose.yml exec -T db sh -c "mysql -uroot -p'$DB_ROOT_PASSWORD' -e \"CREATE DATABASE IF NOT EXISTS \\\`$DB_NAME\\\` DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci; CREATE USER IF NOT EXISTS '$DB_USER'@'%' IDENTIFIED WITH mysql_native_password BY '$DB_PASSWORD'; GRANT ALL PRIVILEGES ON \\\`$DB_NAME\\\`.* TO '$DB_USER'@'%'; FLUSH PRIVILEGES;\""

# 5. 构建镜像（repo 根为 context）
docker build -t backend:latest -f docker/backend.Dockerfile .
docker build -t frontend:latest -f docker/frontend.Dockerfile .

# 6. 启动/替换容器（平滑替换）
docker compose -f deploy/docker-compose.yml up -d --remove-orphans

# 7. 运行迁移与收集静态（若需要）
docker compose -f deploy/docker-compose.yml run --rm web python Main.py migrate
docker compose -f deploy/docker-compose.yml run --rm web python Main.py collectstatic --noinput

# 8. 验证（失败会触发 on_error）
docker compose -f deploy/docker-compose.yml ps
curl -f http://127.0.0.1:8000/healthz

# 9. 记录成功版本并清理暂停标记
echo "$TARGET_COMMIT" > "$LAST_SUCCESS_FILE"
rm -f "$PAUSE_FILE"

send_mail \
	"[SixthElement][OK] deployment succeeded" \
	"Deploy succeeded.
Commit: ${TARGET_COMMIT}
Backup: ${SQL_BAK}
Time: $(date '+%F %T')"

echo "[deploy] success: ${TARGET_COMMIT}"