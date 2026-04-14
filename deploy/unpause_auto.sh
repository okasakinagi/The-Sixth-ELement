#!/usr/bin/env bash
# deploy/unpause_auto.sh
# 运维急救工具：用于恢复因错误暂停的自动部署，或者快速导出服务日志

STATE_DIR="/home/six_element/deploy_state"
PAUSE_FILE="$STATE_DIR/deploy.paused"
LOCAL_RECORD_FILE="$STATE_DIR/auto_deployed_commit"
PROJECT_DIR="/home/six_element/home/six_element_app/The-Sixth-ELement"
LOG_EXPORT_DIR="/home/six_element/deploy_state/troubleshoot_logs"
AUTO_WATCH_LOG_FILE="$STATE_DIR/auto_watch.log"
UPDATE_DEPLOY_LOG_FILE="$STATE_DIR/update_deploy.log"
CRON_LOG_FILE="$STATE_DIR/cron.log"
CRON_LOG_FILE_FALLBACK="/var/log/cron.log"

mkdir -p "$LOG_EXPORT_DIR"

resolve_cron_log_file() {
    if [ -f "$CRON_LOG_FILE" ]; then
        echo "$CRON_LOG_FILE"
        return
    fi
    if [ -f "$CRON_LOG_FILE_FALLBACK" ]; then
        echo "$CRON_LOG_FILE_FALLBACK"
        return
    fi
    echo ""
}

echo "==================================="
echo "  Sixth Element 运维排障工具箱  "
echo "==================================="
echo "请选择功能："
echo "1) 导出指定容器日志供查看"
echo "2) 尝试解除自动部署的故障暂停状态"
echo "3) 显示部署日志"
echo "4) 退出"
read -p "请输入序号 [1/2/3/4]: " CHOICE

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
    echo "请选择日志来源："
    echo "1) 自动巡检日志 (auto_watch.log, 轮询与触发记录)"
    echo "2) 部署命令日志 (update_deploy.log, 部署脚本执行细节)"
    echo "3) Cron 调度日志 (cron.log, 定时任务是否触发/报错)"
    read -p "请输入序号 [1/2/3] (默认 1): " LOG_CHOICE
    [ -z "$LOG_CHOICE" ] && LOG_CHOICE="1"

    if [ "$LOG_CHOICE" == "1" ]; then
        SELECTED_LOG_FILE="$AUTO_WATCH_LOG_FILE"
        LOG_LABEL="auto_watch.log"
    elif [ "$LOG_CHOICE" == "2" ]; then
        SELECTED_LOG_FILE="$UPDATE_DEPLOY_LOG_FILE"
        LOG_LABEL="update_deploy.log"
    elif [ "$LOG_CHOICE" == "3" ]; then
        SELECTED_LOG_FILE="$(resolve_cron_log_file)"
        LOG_LABEL="cron.log"
    else
        echo "无效输入"
        exit 1
    fi

    if [ -z "$SELECTED_LOG_FILE" ] || [ ! -f "$SELECTED_LOG_FILE" ]; then
        if [ "$LOG_CHOICE" == "1" ]; then
            echo "[Info] 尚未找到部署日志文件: $AUTO_WATCH_LOG_FILE"
            echo "请先等待自动部署巡检任务执行，或确认 auto_watch.sh 已配置并运行。"
        elif [ "$LOG_CHOICE" == "2" ]; then
            echo "[Info] 尚未找到部署命令日志文件: $UPDATE_DEPLOY_LOG_FILE"
            echo "请先执行一次 update_deploy.sh，日志文件会自动生成。"
        else
            echo "[Info] 尚未找到 Cron 执行日志。"
            echo "已检查: $CRON_LOG_FILE"
            echo "已检查: $CRON_LOG_FILE_FALLBACK"
            echo "请确认你的 crontab 是否将输出重定向到 cron.log。"
        fi
        exit 0
    fi

    read -p "请输入要显示的日志行数（默认 200）: " TAIL_LINES
    [ -z "$TAIL_LINES" ] && TAIL_LINES="200"

    if ! [[ "$TAIL_LINES" =~ ^[0-9]+$ ]]; then
        echo "[Failed] 行数必须是正整数。"
        exit 1
    fi

    echo ""
    echo "===== 最近 ${TAIL_LINES} 行部署日志 (${LOG_LABEL}) ====="
    tail -n "$TAIL_LINES" "$SELECTED_LOG_FILE"
    echo "===== 日志结尾 ====="

    read -p "是否继续实时跟踪日志？(y/n): " FOLLOW
    if [ "$FOLLOW" == "y" ] || [ "$FOLLOW" == "Y" ]; then
        echo "按 Ctrl+C 可退出实时跟踪。"
        tail -f "$SELECTED_LOG_FILE"
    fi
    exit 0

elif [ "$CHOICE" == "4" ]; then
    exit 0
else
    echo "无效输入"
    exit 1
fi