#!/usr/bin/env bash
# deploy/unpause_auto.sh
# 运维急救工具：用于恢复因错误暂停的自动部署，或者快速导出服务日志

STATE_DIR="/home/six_element/deploy_state"
PAUSE_FILE="$STATE_DIR/deploy.paused"
LOCAL_RECORD_FILE="$STATE_DIR/auto_deployed_commit"
PROJECT_DIR="/home/six_element/home/six_element_app/The-Sixth-ELement"
LOG_EXPORT_DIR="/home/six_element/deploy_state/troubleshoot_logs"

mkdir -p "$LOG_EXPORT_DIR"

echo "==================================="
echo "  Sixth Element 运维排障工具箱  "
echo "==================================="
echo "请选择功能："
echo "1) 导出指定容器日志供查看"
echo "2) 尝试解除自动部署的故障暂停状态"
echo "3) 退出"
read -p "请输入序号 [1/2/3]: " CHOICE

if [ "$CHOICE" == "1" ]; then
    echo ""
    echo "请输入您要拉取日志的容器名称 (默认为 web，后端)。常用名称: web, frontend, db"
    read -p "> " CONTAINER_NAME
    [ -z "$CONTAINER_NAME" ] && CONTAINER_NAME="web"

    EXPORT_FILE="${LOG_EXPORT_DIR}/${CONTAINER_NAME}_export.log"
    echo "正在从 Docker 导出 [${CONTAINER_NAME}] 最后 500 行日志..."
    
    cd "$PROJECT_DIR"
    docker compose -f deploy/docker-compose.yml logs --tail=500 "$CONTAINER_NAME" > "$EXPORT_FILE" 2>/dev/null
    
    if [ $? -eq 0 ]; then
        echo "[Success] 日志已成功导出。"
        echo "你可以随时输入这个命令查看: cat $EXPORT_FILE"
    else
        echo "[Failed] 导出失败。你确定这个容器名正确并在运行吗？"
    fi
    exit 0

elif [ "$CHOICE" == "2" ]; then
    if [ ! -f "$PAUSE_FILE" ]; then
        echo "[Info] 当前由于部署并没有报错挂起，并不需要解除暂停，系统正在继续自动轮询中。"
        exit 0
    fi

    echo "[Warning] 发现因严重部署错误而留存的暂停文件: $PAUSE_FILE"
    echo "请确认是否已在 Gitee/GitHub 修复了引发崩溃的大患源码/配置？(y/n)"
    read -r CONFIRM

    if [ "$CONFIRM" == "y" ] || [ "$CONFIRM" == "Y" ]; then
        rm -f "$PAUSE_FILE"
        echo "RETRY_AFTER_FIX" > "$LOCAL_RECORD_FILE"
        echo "[Success] 锁定文件已拆除。"
        echo "下一次 Cron 哨兵（一分钟内）巡查时，如果远端有任何代码变动，都强制视为【新代码】，重新发动总攻。"
    else
        echo "[Abort] 已取消。请先看日志解决异常，然后再回此处解锁启封。"
        exit 1
    fi
    
elif [ "$CHOICE" == "3" ]; then
    exit 0
else
    echo "无效输入"
    exit 1
fi