#!/usr/bin/env bash
# deploy/auto_watch.sh
# 轮询 Gitee 最新 commit，如果发现更新则调用 update_deploy.sh 进行部署

set -Eeuo pipefail

# 配置
PROJECT_DIR="/home/six_element/home/six_element_app/The-Sixth-ELement"
DEPLOY_SCRIPT="$PROJECT_DIR/deploy/update_deploy.sh"
STATE_DIR="/home/six_element/deploy_state"
LOCAL_RECORD_FILE="$STATE_DIR/auto_deployed_commit"
PAUSE_FILE="$STATE_DIR/deploy.paused"
LOG_FILE="/home/six_element/deploy_state/auto_watch.log"

BRANCH="main"
REMOTE_NAME="origin"

mkdir -p "$STATE_DIR"
touch "$LOG_FILE"

log() {
    echo "$(date '+%F %T') $1" | tee -a "$LOG_FILE"
}

cd "$PROJECT_DIR" || { log "ERROR: Project dir not found"; exit 1; }

# 1. 检查是否人工暂停
if [ -f "$PAUSE_FILE" ]; then
    # 由于每分钟轮询，为了少刷日志，暂停时不打印日志直接退出
    exit 0
fi

# 2. 获取远端最新提交的哈希 (只查询哈希不拉取全量代码，速度极快)
REMOTE_HASH=$(git ls-remote "$REMOTE_NAME" "refs/heads/$BRANCH" | awk '{print $1}')

if [ -z "$REMOTE_HASH" ]; then
    log "ERROR: Could not get remote hash for $BRANCH"
    exit 1
fi

# 3. 获取上一次我们自动部署记录的哈希
LOCAL_HASH="none"
if [ -f "$LOCAL_RECORD_FILE" ]; then
    LOCAL_HASH=$(cat "$LOCAL_RECORD_FILE")
fi

# 4. 对比，如果相同则无视，不同则部署
if [ "$REMOTE_HASH" == "$LOCAL_HASH" ]; then
    # 代码已是最新，无事退出
    exit 0
fi

log "Update detected! Remote: $REMOTE_HASH, Local: $LOCAL_HASH"
log "Triggering deploy script..."

# 5. 调用部署主脚本
# 因为 update_deploy.sh 内部有并发锁，所以即使由于某种原因重复调用也不会撞车
if bash "$DEPLOY_SCRIPT"; then
    # 部署完全成功后，记录下这个处理完毕的哈希
    echo "$REMOTE_HASH" > "$LOCAL_RECORD_FILE"
    log "Deploy finished and hash updated to $REMOTE_HASH"
else
    # 部署失败了，日志里记一笔（失败发信和回滚由 update_deploy.sh 接管了）
    log "Deploy failed with exit code $?. Check deployment logs and pause status."
fi
