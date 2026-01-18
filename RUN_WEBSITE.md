# 🚀 运行和访问网站完全指南

## 📋 前置检查

确保已安装：
- Python 3.9+ 
- Node.js 16+
- MySQL 服务启动
- 依赖已安装

```powershell
# 检查 Python
python --version

# 检查 Node.js
node --version
npm --version

# 检查 MySQL (确保服务运行)
# Windows: 检查任务管理器或运行 mysql -u sixth_element -p
```

---

## 🎯 第 1 步：启动后端服务

打开 **PowerShell 终端 1**，进入项目目录：

```powershell
cd d:\The-Sixth-ELement

# 启动 Django 开发服务器
python Main.py runserver
```

**输出应该显示：**
```
Starting development server at http://127.0.0.1:8000/
Django version 6.0, using settings 'survey_app.settings'
Press CTRL+BREAK to quit.
```

✅ **后端已启动** - 可在 `http://127.0.0.1:8000` 访问

---

## 🎯 第 2 步：启动前端服务

打开 **PowerShell 终端 2**，进入前端目录：

```powershell
cd d:\The-Sixth-ELement\frontend\sixth_element

# 启动 Vite 开发服务器
npm run dev
```

**输出应该显示：**
```
  ➜  Local:   http://localhost:5173/
  ➜  press h + enter to show help
```

✅ **前端已启动** - 可在 `http://localhost:5173` 访问

---

## 🌐 第 3 步：访问网站

在浏览器打开：
```
http://localhost:5173
```

你会看到：
- 主页面 (Task Hall - 任务大厅)
- 导航菜单
- 登录/注册表单

---

## 📝 完整工作流

### A. 首次使用 - 注册账户

1. **打开** `http://localhost:5173`
2. **点击** "注册" 或 "Sign Up"
3. **填写表单：**
   - Email: `test@example.com`
   - Password: `password123`
   - Nickname: `我的昵称`
4. **点击** "Register"
5. ✅ 注册成功，自动登录

### B. 已有账户 - 直接登录

1. **打开** `http://localhost:5173`
2. **填写登录信息：**
   - Email: `test@example.com`
   - Password: `password123`
3. **点击** "Login"
4. ✅ 登录成功

### C. 浏览页面功能

登录后，你可以访问：

| 页面 | 路由 | 功能 |
|-----|-----|------|
| 任务大厅 | `/` | 浏览和填答问卷 |
| 问卷管理 | `/surveys` | 管理发布的问卷 |
| 新建问卷 | `/survey/new` | 创建新问卷 |
| 数据分析 | `/survey/:id/analytics` | 查看问卷统计 |
| 个人资料 | `/profile` | 编辑用户信息 |
| **积分记录** | `/points` | 💫 新功能！查看积分和荣誉 |

### D. 测试新功能 - 积分记录页面

1. **登录后访问：** `http://localhost:5173/points`
2. **看到：**
   - 🎖️ 荣誉卡片（如果信用分 >= 85）
   - 当前余额显示
   - 积分交易明细
   - 筛选和分页功能

---

## 🔧 常用命令

### 启动/重启服务

```powershell
# ===== 终端 1：后端 =====
cd d:\The-Sixth-ELement
python Main.py runserver

# 若要在其他端口运行
python Main.py runserver 0.0.0.0:9000

# ===== 终端 2：前端 =====
cd d:\The-Sixth-ELement\frontend\sixth_element
npm run dev

# 若要在其他端口运行
npm run dev -- --port 3000
```

### 停止服务

```powershell
# 在对应终端按：Ctrl + C
```

---

## 📊 数据库管理

### 应用迁移（第一次运行）

```powershell
cd d:\The-Sixth-ELement

# 应用数据库迁移
python Main.py migrate

# 查看迁移状态
python Main.py showmigrations
```

### 创建超级用户（可选）

```powershell
python Main.py createsuperuser

# 然后访问 http://127.0.0.1:8000/admin
```

### 进入 Django Shell 调试

```powershell
python Main.py shell

# 在 shell 中执行 Python 代码
from core.models import AppUser
users = AppUser.objects.all()
print(users)
```

---

## 🐛 常见问题

### ❌ 前端显示"连接被拒绝"

**原因：** 后端服务未启动

**解决：**
```powershell
# 在终端 1 启动后端
python Main.py runserver
```

### ❌ 后端显示"端口 8000 已被占用"

**解决方案 1：** 使用其他端口
```powershell
python Main.py runserver 8001
```

**解决方案 2：** 查找占用进程
```powershell
# 查找占用 8000 端口的进程
netstat -ano | findstr :8000

# 杀死进程 (替换 PID)
taskkill /PID 1234 /F
```

### ❌ npm: 找不到命令

**解决：** 确保已安装 Node.js
```powershell
# 从这里下载：https://nodejs.org/
# 然后重启 PowerShell
node --version
npm --version
```

### ❌ MySQL 连接错误

**检查数据库配置：**
```powershell
# 编辑这个文件看数据库设置
notepad d:\The-Sixth-ELement\module\survey_app\settings.py

# 查找 DATABASES 配置，确保：
# - HOST: 127.0.0.1
# - PORT: 3306
# - NAME: sixth_element
# - USER: sixth_element
# - PASSWORD: 123456
```

**测试连接：**
```powershell
mysql -u sixth_element -p123456 -h 127.0.0.1
# 应该能连接到数据库
```

---

## 🎬 完整启动脚本

创建 `start.bat`（Windows）：

```batch
@echo off
echo 🚀 启动 The Sixth Element 应用
echo.

REM 检查 Python
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ 错误：未安装 Python
    exit /b 1
)

REM 检查 Node.js
node --version >nul 2>&1
if errorlevel 1 (
    echo ❌ 错误：未安装 Node.js
    exit /b 1
)

echo ✅ 环境检查通过
echo.

REM 启动后端
echo 🔧 启动后端服务 (终端 1)...
start "Backend" cmd /k "cd /d d:\The-Sixth-ELement && python Main.py runserver"

REM 等待 2 秒
timeout /t 2 /nobreak

REM 启动前端
echo 🎨 启动前端服务 (终端 2)...
start "Frontend" cmd /k "cd /d d:\The-Sixth-ELement\frontend\sixth_element && npm run dev"

echo.
echo ✅ 应用启动中...
echo.
echo 📱 前端: http://localhost:5173
echo 🔌 后端: http://127.0.0.1:8000
echo.
echo 💡 提示：关闭这个窗口后，前两个窗口仍会继续运行
pause
```

使用方法：
```powershell
# 将脚本保存为 start.bat，然后运行
.\start.bat
```

---

## 🌟 快速访问链接

运行后，你可以快速访问：

| 功能 | 链接 |
|-----|------|
| 网站首页 | http://localhost:5173 |
| 后端 API 基础 | http://127.0.0.1:8000/api/v1 |
| Django Admin | http://127.0.0.1:8000/admin |
| Vite HMR 日志 | 浏览器 DevTools - Console |

---

## 📚 后续操作

### 开发 API

```powershell
# 启动后端服务后，测试 API
curl -X GET "http://127.0.0.1:8000/api/v1/surveys" `
  -H "Authorization: Bearer YOUR_TOKEN"
```

### 修改前端代码

```powershell
# 前端支持热重载 (Hot Module Replacement)
# 修改 .vue 文件后，浏览器会自动刷新
# 无需重启 npm 服务
```

### 查看日志

```powershell
# 后端日志在启动的终端中显示
# 前端日志在浏览器的 DevTools → Console

# 生产日志重定向到文件
python Main.py runserver > backend.log 2>&1
```

---

## ✅ 检查清单

启动前，确认：

- [ ] Python 已安装并能运行
- [ ] Node.js 和 npm 已安装
- [ ] MySQL 服务正在运行
- [ ] 项目依赖已安装 (`pip install -r requirements.txt`)
- [ ] 前端依赖已安装 (`npm install` in frontend 目录)
- [ ] 数据库迁移已应用 (`python Main.py migrate`)

启动后，检查：

- [ ] 终端 1 显示 "Starting development server at http://127.0.0.1:8000/"
- [ ] 终端 2 显示 "Local: http://localhost:5173/"
- [ ] 浏览器能访问 http://localhost:5173
- [ ] 登录功能正常
- [ ] 可以浏览问卷列表

---

现在，打开两个 PowerShell 终端，分别运行后端和前端，就可以看到你的网站了！🎉
