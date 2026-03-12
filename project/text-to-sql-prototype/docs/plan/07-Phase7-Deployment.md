# 阶段7：部署交付

## 阶段目标
完成生产环境部署配置，编写运维文档，项目正式上线交付。

**预计工期**: 1天
**并行度**: 低（步骤有依赖关系）

---

## Agent 协作关系

```
devops (Task 7.1)               devops (Task 7.2)               devops (Task 7.3)
    │                               │                               │
    ├── Docker配置                   ├── CI/CD配置                    ├── 生产部署
    ├── docker-compose.yml           └── GitHub Actions              └── 监控配置
    └── 镜像优化
```

---

## 任务分解

### Task 7.1: Docker容器化
**负责人**: `devops`
**依赖**: 阶段6完成
**参考文档**: `../07-README-Deployment.md`

#### 工作内容

1. **后端Dockerfile** (`backend/Dockerfile`)
   ```dockerfile
   FROM python:3.11-slim

   WORKDIR /app

   COPY requirements.txt .
   RUN pip install --no-cache-dir -r requirements.txt

   COPY app/ ./app/
   COPY alembic/ ./alembic/
   COPY alembic.ini .

   EXPOSE 8000

   CMD ["gunicorn", "app.main:app", "-w", "4", "-k", "uvicorn.workers.UvicornWorker", "-b", "0.0.0.0:8000"]
   ```

2. **前端Dockerfile** (`frontend/Dockerfile`)
   ```dockerfile
   # 构建阶段
   FROM node:18-alpine AS builder
   WORKDIR /app
   COPY package*.json ./
   RUN npm ci
   COPY . .
   RUN npm run build

   # 生产阶段
   FROM nginx:alpine
   COPY --from=builder /app/dist /usr/share/nginx/html
   COPY nginx.conf /etc/nginx/conf.d/default.conf
   EXPOSE 80
   ```

3. **nginx配置** (`frontend/nginx.conf`)
   - 静态文件服务
   - 反向代理到后端
   - Gzip压缩

4. **docker-compose.yml** (根目录)
   ```yaml
   version: '3.8'
   services:
     db:
       image: postgres:15-alpine
       environment:
         POSTGRES_USER: text2sql
         POSTGRES_PASSWORD: ${DB_PASSWORD}
         POSTGRES_DB: text2sql
       volumes:
         - postgres_data:/var/lib/postgresql/data
       healthcheck:
         test: ["CMD-SHELL", "pg_isready -U text2sql"]
         interval: 5s
         timeout: 5s
         retries: 5

     redis:
       image: redis:7-alpine
       volumes:
         - redis_data:/data

     backend:
       build: ./backend
       environment:
         - DATABASE_URL=postgresql://text2sql:${DB_PASSWORD}@db:5432/text2sql
         - SECRET_KEY=${SECRET_KEY}
         - OPENAI_API_KEY=${OPENAI_API_KEY}
       depends_on:
         db:
           condition: service_healthy
       healthcheck:
         test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
         interval: 30s
         timeout: 10s
         retries: 3

     frontend:
       build: ./frontend
       ports:
         - "80:80"
       depends_on:
         - backend

     worker:
       build: ./backend
       command: celery -A app.core.celery worker --loglevel=info
       environment:
         - DATABASE_URL=postgresql://text2sql:${DB_PASSWORD}@db:5432/text2sql
       depends_on:
         - db
         - redis

   volumes:
     postgres_data:
     redis_data:
   ```

5. **镜像优化**
   - 使用多阶段构建
   - 清理缓存
   - 使用轻量级基础镜像

#### 检查点
- [ ] Docker镜像能成功构建
- [ ] 镜像大小合理（前端<50MB，后端<200MB）
- [ ] 容器能正常启动
- [ ] 健康检查配置正确

#### 测试点
```bash
# 本地测试docker-compose
docker-compose up --build -d
curl http://localhost/health
docker-compose down
```

---

### Task 7.2: CI/CD配置
**负责人**: `devops`
**依赖**: Task 7.1完成

#### 工作内容

1. **GitHub Actions配置** (`.github/workflows/ci.yml`)
   ```yaml
   name: CI/CD

   on:
     push:
       branches: [main, develop]
     pull_request:
       branches: [main]

   jobs:
     test-backend:
       runs-on: ubuntu-latest
       steps:
         - uses: actions/checkout@v3
         - name: Set up Python
           uses: actions/setup-python@v4
           with:
             python-version: '3.11'
         - name: Install dependencies
           run: |
             cd backend
             pip install -r requirements.txt
         - name: Run tests
           run: |
             cd backend
             pytest --cov=app

     test-frontend:
       runs-on: ubuntu-latest
       steps:
         - uses: actions/checkout@v3
         - name: Set up Node
           uses: actions/setup-node@v3
           with:
             node-version: '18'
         - name: Install dependencies
           run: |
             cd frontend
             npm ci
         - name: Run tests
           run: |
             cd frontend
             npm run test:unit
             npm run build

     build-and-push:
       needs: [test-backend, test-frontend]
       runs-on: ubuntu-latest
       if: github.ref == 'refs/heads/main'
       steps:
         - uses: actions/checkout@v3
         - name: Build and push images
           run: |
             docker build -t text2sql-backend:${{ github.sha }} ./backend
             docker build -t text2sql-frontend:${{ github.sha }} ./frontend
             # Push to registry
   ```

2. **部署脚本** (`scripts/deploy.sh`)
   - 拉取最新镜像
   - 执行数据库迁移
   - 滚动更新
   - 健康检查
   - 回滚机制

3. **版本管理**
   - 使用Git标签标记版本
   - 生成CHANGELOG
   - 镜像标签策略（latest, v1.0.0, git-sha）

#### 检查点
- [ ] CI流程能成功运行
- [ ] 测试失败时阻止部署
- [ ] 镜像能推送到仓库
- [ ] 部署脚本可执行

#### 测试点
```bash
# 测试部署脚本
./scripts/deploy.sh staging
```

---

### Task 7.3: 生产部署与监控
**负责人**: `devops`
**依赖**: Task 7.1, 7.2完成

#### 工作内容

1. **生产环境配置**
   - `.env.production` 配置
   - SSL证书配置
   - 域名配置
   - 防火墙规则

2. **监控配置**
   - 日志收集（ELK或Loki）
   - 指标监控（Prometheus + Grafana）
   - 告警规则（CPU、内存、磁盘、API错误率）
   - 健康检查端点

3. **备份策略**
   - 数据库自动备份
   - 备份保留策略
   - 恢复测试

4. **运维文档**
   - 部署手册
   - 故障排查指南
   - 回滚流程
   - 监控面板说明

#### 检查点
- [ ] 生产环境可访问
- [ ] HTTPS正常工作
- [ ] 监控数据正常采集
- [ ] 告警能正常触发
- [ ] 备份任务正常运行

#### 测试点
```bash
# 测试生产环境
curl https://your-domain.com/health
# 检查监控数据
curl http://prometheus:9090/api/v1/query?query=up
```

---

## 阶段交付物

| 交付物 | 位置 | 验收标准 |
|--------|------|----------|
| Docker配置 | `backend/Dockerfile`, `frontend/Dockerfile`, `docker-compose.yml` | 镜像构建成功，容器运行正常 |
| CI/CD配置 | `.github/workflows/ci.yml` | CI流程通过，自动部署 |
| 部署脚本 | `scripts/deploy.sh` | 可执行，支持回滚 |
| 生产配置 | `.env.production` | 配置完整，安全 |
| 监控配置 | `monitoring/` | 监控数据正常，告警有效 |
| 运维文档 | `docs/OPERATIONS.md` | 完整可执行 |

---

## 阶段检查清单

### 部署检查
- [ ] Docker镜像构建成功
- [ ] 容器在本地能正常启动
- [ ] 生产环境部署成功
- [ ] HTTPS配置正确
- [ ] 域名可访问

### 监控检查
- [ ] 日志收集正常
- [ ] 指标监控正常
- [ ] 告警能正常触发
- [ ] 健康检查通过

### 运维检查
- [ ] 备份任务运行正常
- [ ] 恢复流程测试通过
- [ ] 回滚流程测试通过
- [ ] 运维文档完整

---

## 项目交付完成标准

1. ✅ 所有阶段完成
2. ✅ 生产环境部署成功
3. ✅ 监控告警配置完成
4. ✅ 文档齐全（开发文档+运维文档）
5. ✅ 代码已合并到main分支
6. ✅ 已打版本标签

---

## 风险与应对

| 风险 | 应对措施 |
|------|----------|
| 部署失败 | 先在staging环境测试，有回滚方案 |
| 配置泄露 | 使用环境变量，敏感信息不提交到Git |
| 服务不可用 | 配置健康检查，自动重启 |
| 数据丢失 | 定期备份，测试恢复流程 |

---

*依赖文档: ../07-README-Deployment.md*
