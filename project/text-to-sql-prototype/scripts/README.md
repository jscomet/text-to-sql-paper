# 项目服务管理脚本

这个目录包含用于管理前端和后端服务的脚本。

## 分开管理（推荐）

### 前端脚本

```bash
./scripts/frontend-start.sh    # 启动前端开发服务器
./scripts/frontend-stop.sh     # 停止前端服务
./scripts/frontend-restart.sh  # 重启前端服务
```

前端默认运行在: http://localhost:5173

### 后端脚本

```bash
./scripts/backend-start.sh     # 启动后端API服务器
./scripts/backend-stop.sh      # 停止后端服务
./scripts/backend-restart.sh   # 重启后端服务
```

后端默认运行在: http://localhost:8000
API文档: http://localhost:8000/docs

## 统一管理（可选）

```bash
./scripts/start.sh   [frontend|backend|all]  # 启动服务
./scripts/stop.sh    [frontend|backend|all]  # 停止服务
./scripts/restart.sh [frontend|backend|all]  # 重启服务
./scripts/status.sh                           # 查看服务状态
```

## 使用示例

### 开发时启动所有服务

```bash
./scripts/frontend-start.sh
./scripts/backend-start.sh
```

或

```bash
./scripts/start.sh all
```

### 只重启后端（修改后端代码后）

```bash
./scripts/backend-restart.sh
```

### 查看当前服务状态

```bash
./scripts/status.sh
```

## 日志文件

- 前端日志: `frontend/frontend.log`
- 后端日志: `backend/backend.log`

## 注意事项

1. 后端启动前需要确保虚拟环境已创建并安装了依赖：
   ```bash
   cd backend
   python -m venv venv
   source venv/Scripts/activate  # Windows
   pip install -r requirements.txt
   ```

2. 前端启动前需要确保已安装依赖：
   ```bash
   cd frontend
   npm install
   ```

3. 脚本使用 PID 文件来跟踪服务状态，文件位于：
   - 前端: `frontend/.frontend.pid`
   - 后端: `backend/.backend.pid`
