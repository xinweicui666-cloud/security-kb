# 安全合规知识库

> 让组织里的安全与合规知识可查询、可复用、可沉淀。

## 项目说明

安全合规知识库项目，包含 8 个模块共 79 个文件（286+ 问答），通过 MCP Server、后端 API 和前端界面提供检索和内容填充能力。

## 可用 Skill

- `/security-kb` — 安全合规知识库问答，通过 MCP 工具检索知识库内容并给出专业解答

## 系统组件

| 组件 | 目录 | 说明 |
|------|------|------|
| MCP Server | `mcp-server/` | 提供 search_kb / read_kb_file / list_kb_categories / ask_compliance 4个工具 |
| 后端 API | `kb-backend/` | FastAPI + SQLite，端口 8000，提供文件 CRUD / 搜索 / 合规查询 / 状态跟踪 |
| 前端界面 | `kb-frontend/` | React + Ant Design，端口 5173，可视化浏览+编辑+搜索 |

## 启动方式

```bash
# 后端
cd kb-backend && python main.py          # http://localhost:8000

# 前端
cd kb-frontend && npm run dev            # http://localhost:5173

# MCP Server（自动由 Claude Code 连接）
# 配置在 .mcp.json
```

## 知识库结构

| 模块 | 路径 | 文件数 | 填充状态 |
|------|------|--------|---------|
| 制度体系 | `01-制度体系/` | 8 | 2 已填充 |
| 技术基线 | `02-技术基线/` | 20+ | 含4个FAQ新文件 |
| 合规框架 | `03-合规框架/` | 13 | 4 已填充 |
| 审计与整改 | `04-审计与整改/` | 6 | 1 已填充 |
| 风险案例 | `05-风险案例/` | 5 | 0 已填充 |
| 应急响应 | `06-应急响应/` | 11+ | 含1个FAQ新文件 |
| FAQ | `07-FAQ/` | 5 | 5 已填充（286问答） |
| 模板中心 | `08-模板中心/` | 10 | 0 已填充 |