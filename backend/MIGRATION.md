# 数据库迁移：SQLite → PostgreSQL

## 1. 安装 PostgreSQL 并创建数据库
```sql
CREATE DATABASE interview;
CREATE USER interview_user WITH PASSWORD 'your_password';
GRANT ALL ON DATABASE interview TO interview_user;
```

## 2. 设置环境变量
```bash
export DATABASE_URL="postgresql://interview_user:your_password@localhost:5432/interview"
```

## 3. 自动建表
重启后端，启动时 `Base.metadata.create_all()` 自动创建所有表。

## 4. 数据迁移（可选）
```bash
# 用 pgloader 从 SQLite 迁移到 PostgreSQL
pgloader sqlite://interview.db postgresql://user:pass@localhost/interview
```

## 连接池配置
```bash
DB_POOL_SIZE=10    # 默认10
DB_MAX_OVERFLOW=20 # 默认20
```
