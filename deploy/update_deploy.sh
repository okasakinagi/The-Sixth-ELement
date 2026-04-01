#!/usr/bin/env bash
set -Eeuo pipefail

PROJECT_DIR="/home/six_element/home/six_element_app/The-Sixth-ELement"
BACKUP_DIR="/home/six_element/backups"
STATE_DIR="/home/six_element/deploy_state"
LOCK_FILE="$STATE_DIR/deploy.lock"
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

TS=$(date +%F_%H%M%S)
ENV_BAK="$BACKUP_DIR/deploy.env.bak.${TS}"

# 备份当前的 .env (覆盖最新版并保留历史备份)
cp deploy/.env "$BACKUP_DIR/deploy.env.bak"
cp deploy/.env "$ENV_BAK"

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
			
			# 回滚时强制使用上一版本的 commit 作为 tag，如果镜像还在，秒起；如果不在，docker compose 会自动不重新 build (除非指定)，
			# 但为了确保快速回滚，我们显式恢复
			export APP_VERSION="${ROLLBACK_COMMIT}"
			docker compose -f deploy/docker-compose.yml up -d --remove-orphans || true
		fi
	fi

	touch "$PAUSE_FILE"

	send_mail \
		"【第六元素】 部署失败并已暂停自动部署" \
		"自动化部署遇到错误。

部署前版本: ${CURRENT_COMMIT}
尝试更新到版本: ${TARGET_COMMIT}

安全系统已生成暂停锁定文件: ${PAUSE_FILE}
在人工介入处理并删除该文件前，将不会自动触发新的部署。
请登录服务器检查日志排查问题。"

	exit $code
}
trap on_error ERR

if [ -f "$PAUSE_FILE" ]; then
	echo "[deploy] auto deploy paused by flag: $PAUSE_FILE"
	exit 2
fi

send_mail \
	"【第六元素】 自动部署已开始" \
	"部署任务已启动。

当前服务器版本: ${CURRENT_COMMIT}
执行主机: $(hostname)
启动时间: $(date '+%F %T')"

# 1. 更新代码
git fetch --all
git checkout main
git reset --hard origin/main
TARGET_COMMIT=$(git rev-parse HEAD)

# 2. 恢复 .env
cp "$BACKUP_DIR/deploy.env.bak" deploy/.env

# 3. 备份 MySQL（按时间戳保存）
SQL_BAK="$BACKUP_DIR/backup_${TS}.sql"
docker compose -f deploy/docker-compose.yml exec -T db sh -c "mysqldump -uroot -p'$DB_ROOT_PASSWORD' --single-transaction --quick $DB_NAME" > "$SQL_BAK"
ls -lh "$SQL_BAK"

# 自动清理旧备份，仅保留最近的 5 份数据库备份和 5 份 env 备份（防止短时间频繁部署占满磁盘）
ls -tp "$BACKUP_DIR"/backup_*.sql 2>/dev/null | tail -n +6 | xargs -I {} rm -- "{}" || true
ls -tp "$BACKUP_DIR"/deploy.env.bak.* 2>/dev/null | tail -n +6 | xargs -I {} rm -- "{}" || true
echo "[deploy] old backups cleaned up, keeping last 5."

# 4. 用 root 在容器中创建/授权应用用户（从 deploy/.env 读取）
docker compose -f deploy/docker-compose.yml exec -T db sh -c "mysql -uroot -p'$DB_ROOT_PASSWORD' -e \"CREATE DATABASE IF NOT EXISTS \\\`$DB_NAME\\\` DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci; CREATE USER IF NOT EXISTS '$DB_USER'@'%' IDENTIFIED WITH mysql_native_password BY '$DB_PASSWORD'; GRANT ALL PRIVILEGES ON \\\`$DB_NAME\\\`.* TO '$DB_USER'@'%'; FLUSH PRIVILEGES;\""

# 5. 构建镜像（打上双标签：latest 和当前 commit，用于快速回滚）
# export 变量供 docker-compose 里的 image 引用（如果 docker-compose 做了动态支持，没做的话这里打 tag 也方便以后清理）
docker build -t backend:latest -t backend:${TARGET_COMMIT} -f docker/backend.Dockerfile .
docker build -t frontend:latest -t frontend:${TARGET_COMMIT} -f docker/frontend.Dockerfile .

# 清理旧的无用镜像，保留最近版本，防止打爆磁盘
# docker image prune -f 会删除所有虚悬镜像（没有 tag 的）
docker image prune -f

# 6. 启动/替换容器（平滑替换）
export APP_VERSION="${TARGET_COMMIT}"
docker compose -f deploy/docker-compose.yml up -d --remove-orphans

# 7. 运行迁移与收集静态（若需要）
docker compose -f deploy/docker-compose.yml run --rm web python Main.py migrate
docker compose -f deploy/docker-compose.yml run --rm web python Main.py collectstatic --noinput

# 8. 验证
docker compose -f deploy/docker-compose.yml ps

# 9. 记录成功版本并清理暂停标记
echo "$TARGET_COMMIT" > "$LAST_SUCCESS_FILE"
rm -f "$PAUSE_FILE"

send_mail \
	"【第六元素】部署成功" \
	"系统已成功更新到最新版本。

部署版本: ${TARGET_COMMIT}
数据库备份路径: ${SQL_BAK}
环境变量备份路径: ${ENV_BAK}
完成时间: $(date '+%F %T')"

echo "[deploy] success: ${TARGET_COMMIT}"