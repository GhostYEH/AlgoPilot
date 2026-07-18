# AlgoPilot Backend

FastAPI + SQLAlchemy 后端，提供认证、学习进度、学生画像、学习记忆、多智能体编排、资源生成、OJ、Trace、掌握度评估和教师看板。

## 启动

```powershell
.\.venv\Scripts\python.exe -m uvicorn main:app --host 127.0.0.1 --port 9000
```

默认 SQLite 数据库为 `data/alp_learning.db`。启动时会自动执行 Alembic 迁移到最新版本。

也可以在部署或维护窗口显式执行迁移：

```powershell
.\.venv\Scripts\python.exe -m alembic upgrade head
```

修改 ORM 模型后，应新增版本化迁移，不要再依赖 `Base.metadata.create_all()` 更新旧数据库：

```powershell
.\.venv\Scripts\python.exe -m alembic revision --autogenerate -m "describe change"
```

## 关键接口

- `POST /api/auth/register`
- `POST /api/auth/login`
- `GET|PUT /api/me/learning-progress`
- `GET /api/memory/summary`
- `GET /api/events/recent`
- `GET /api/orchestrator/persona/profile`
- `POST /api/orchestrator/resources/generate`
- `GET /api/orchestrator/learning-path/plan`
- `GET /api/teacher/dashboard-summary`

公开注册只创建学生账号。教师账号应由部署管理员在受控流程中创建。

## 测试

```powershell
.\.venv\Scripts\python.exe -m pytest
```
