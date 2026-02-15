# 进入项目
cd /home/six_element/home/six_element_app/The-Sixth-ELement

# 1. 备份 deploy/.env
mkdir -p /home/six_element/backups
cp deploy/.env /home/six_element/backups/deploy.env.bak

# 2. 更新代码
git fetch --all
git checkout main
git reset --hard origin/main

# 3. 恢复 .env
cp /home/six_element/backups/deploy.env.bak deploy/.env

# 4. 读取 DB_ROOT_PASSWORD 和 DB_NAME 变量（用于备份）
DB_ROOT_PASSWORD=$(grep '^DB_ROOT_PASSWORD=' deploy/.env | cut -d'=' -f2-)
DB_NAME=$(grep '^DB_NAME=' deploy/.env | cut -d'=' -f2-)

# 5. 备份 MySQL（流式到宿主，避免时间戳问题）
mkdir -p /home/six_element/backups
docker compose -f deploy/docker-compose.yml exec -T db sh -c "mysqldump -uroot -p'$DB_ROOT_PASSWORD' --single-transaction --quick $DB_NAME" > /home/six_element/backups/backup.sql
# 检查文件大小
ls -lh /home/six_element/backups/backup.sql

# 用 root 在容器中创建/授权应用用户（从 deploy/.env 读取）
DB_USER=$(grep '^DB_USER=' deploy/.env | cut -d'=' -f2-)
DB_PASSWORD=$(grep '^DB_PASSWORD=' deploy/.env | cut -d'=' -f2-)
docker compose -f deploy/docker-compose.yml exec -T db sh -c "mysql -uroot -p'$DB_ROOT_PASSWORD' -e \"CREATE DATABASE IF NOT EXISTS \\\`$DB_NAME\\\` DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci; CREATE USER IF NOT EXISTS '$DB_USER'@'%' IDENTIFIED WITH mysql_native_password BY '$DB_PASSWORD'; GRANT ALL PRIVILEGES ON \\\`$DB_NAME\\\`.* TO '$DB_USER'@'%'; FLUSH PRIVILEGES;\""

# 6. 构建镜像（repo 根为 context）
docker build -t backend:latest -f docker/backend.Dockerfile .
docker build -t frontend:latest -f docker/frontend.Dockerfile .

# 7. 启动/替换容器（平滑替换）
docker compose -f deploy/docker-compose.yml up -d --remove-orphans

# 8. 运行迁移与收集静态（若需要）
docker compose -f deploy/docker-compose.yml run --rm web python Main.py migrate
docker compose -f deploy/docker-compose.yml run --rm web python Main.py collectstatic --noinput

# 9. 验证
docker compose -f deploy/docker-compose.yml ps
curl -f http://127.0.0.1:8000/healthz || true