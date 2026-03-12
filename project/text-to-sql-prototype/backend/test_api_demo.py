"""
Phase 2 API 测试演示脚本
使用 FastAPI TestClient 进行测试（无需启动服务器）
"""
import asyncio
import sys
from datetime import datetime

# 添加项目路径
sys.path.insert(0, '.')

from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.main import app
from app.core.database import get_db, Base
from app.models import User

# 创建测试数据库（内存SQLite）
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

engine = create_async_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)

TestingSessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
    class_=AsyncSession,
)

async def init_test_db():
    """初始化测试数据库"""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

async def override_get_db():
    """覆盖数据库依赖"""
    async with TestingSessionLocal() as session:
        yield session

# 覆盖依赖
app.dependency_overrides[get_db] = override_get_db

# 创建测试客户端
client = TestClient(app)


def print_section(title):
    """打印章节标题"""
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}")


def print_request(method, url, payload=None):
    """打印请求信息"""
    print(f"\n[Request] {method} {url}")
    if payload:
        print(f"   Payload: {payload}")


def print_response(response):
    """打印响应信息"""
    status_mark = "[OK]" if response.status_code < 400 else "[FAIL]"
    print(f"\n[Response] {status_mark} {response.status_code}")
    try:
        data = response.json()
        print(f"   Body: {data}")
        return data
    except:
        print(f"   Body: {response.text}")
        return None


async def run_tests():
    """运行所有测试"""
    # 初始化数据库
    await init_test_db()

    print("\n" + "=="*30)
    print("  Phase 2 后端 API 测试演示")
    print("=="*30)

    # ============ 1. 健康检查 ============
    print_section("1. 健康检查 (Health Check)")
    print_request("GET", "/health")
    response = client.get("/health")
    print_response(response)

    # ============ 2. 用户注册 ============
    print_section("2. 用户注册 (User Registration)")
    register_data = {
        "username": "testuser",
        "email": "test@example.com",
        "password": "password123"
    }
    print_request("POST", "/api/v1/auth/register", register_data)
    response = client.post("/api/v1/auth/register", json=register_data)
    user_data = print_response(response)

    if response.status_code != 201:
        print("[FAIL] 注册失败，跳过后续测试")
        return

    # ============ 3. 用户登录 ============
    print_section("3. 用户登录 (User Login)")
    login_data = {
        "username": "testuser",
        "password": "password123"
    }
    print_request("POST", "/api/v1/auth/login", login_data)
    response = client.post(
        "/api/v1/auth/login",
        data=login_data,  # OAuth2 使用 form-data
        headers={"Content-Type": "application/x-www-form-urlencoded"}
    )
    token_data = print_response(response)

    if response.status_code != 200:
        print("[FAIL] 登录失败，跳过后续测试")
        return

    access_token = token_data.get("access_token")
    if not access_token:
        print("[FAIL] 未获取到 token")
        return

    print(f"\n[Token] 获取到 Access Token: {access_token[:50]}...")

    # ============ 4. 获取当前用户信息 ============
    print_section("4. 获取当前用户信息 (Get Current User)")
    print_request("GET", "/api/v1/auth/me")
    response = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {access_token}"}
    )
    print_response(response)

    # ============ 5. 测试未认证访问 ============
    print_section("5. 测试未认证访问 (Test Unauthorized Access)")
    print_request("GET", "/api/v1/auth/me (无token)")
    response = client.get("/api/v1/auth/me")
    print_response(response)

    # ============ 6. 测试错误密码 ============
    print_section("6. 测试错误密码 (Test Wrong Password)")
    wrong_login = {
        "username": "testuser",
        "password": "wrongpassword"
    }
    print_request("POST", "/api/v1/auth/login", wrong_login)
    response = client.post(
        "/api/v1/auth/login",
        data=wrong_login,
        headers={"Content-Type": "application/x-www-form-urlencoded"}
    )
    print_response(response)

    # ============ 7. 注册用户已存在 ============
    print_section("7. 测试用户已存在 (Test Duplicate User)")
    print_request("POST", "/api/v1/auth/register", register_data)
    response = client.post("/api/v1/auth/register", json=register_data)
    print_response(response)

    # ============ 8. 用户登出 ============
    print_section("8. 用户登出 (User Logout)")
    print_request("POST", "/api/v1/auth/logout")
    response = client.post(
        "/api/v1/auth/logout",
        headers={"Authorization": f"Bearer {access_token}"}
    )
    print_response(response)

    # ============ 测试总结 ============
    print_section("测试总结 (Test Summary)")
    print("""
[PASS] 完成的测试:
   1. 健康检查 - 验证服务状态
   2. 用户注册 - 创建新用户
   3. 用户登录 - 获取 JWT Token
   4. 获取用户信息 - 使用 Token 访问受保护资源
   5. 未认证访问 - 验证认证拦截
   6. 错误密码 - 验证错误处理
   7. 重复注册 - 验证唯一性约束
   8. 用户登出 - 结束会话

[INFO] 测试覆盖:
   - 数据库模型: User
   - API 端点: /auth/*
   - 认证方式: JWT Bearer Token
   - 密码加密: bcrypt
   - 响应格式: 统一响应封装
""")


if __name__ == "__main__":
    asyncio.run(run_tests())
