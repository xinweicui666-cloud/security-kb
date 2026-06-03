---
name: compliance-gap-check
version: 1.1.0
description: 合规差距智能排查 — 对照等保2.0/网安法/数据安全法/个人信息保护法/ISO27001/SOC2/GDPR，自动识别合规差距并生成整改建议
author: 安全合规团队
license: MIT

# Skill 元数据
skill:
  # 分类标签
  category: security-compliance
  tags: [合规排查, 等保2.0, 网络安全法, 数据安全法, 个人信息保护法, ISO27001, SOC2, GDPR, 差距分析, AI增强, 知识库对接]

  # 调用方式
  interfaces:
    - type: http-api
      port: 3100
      baseUrl: /api
      endpoints:
        - method: GET
          path: /standards
          description: 列出内置合规标准
        - method: GET
          path: /standards/{name}/clauses
          description: 获取指定标准的条款列表
        - method: POST
          path: /gap-check
          description: 执行合规差距排查
          body:
            standardName: string (必填) — 标准名称
            workContent: string (可选) — 直接输入工作内容
            workFile: string (可选) — 工作内容文件路径
            summaryCenterUrl: string (可选) — Summary Center API地址
            useAI: boolean (可选, 默认true) — 是否启用AI增强
            useKB: boolean (可选, 默认true) — 是否启用知识库增强
            kbBaseUrl: string (可选) — 知识库API地址(覆盖配置)
        - method: GET
          path: /gap-check/history
          description: 查看排查历史
        - method: GET
          path: /gap-check/history/{id}
          description: 查看历史详情
        - method: POST
          path: /gap-check/export
          description: 导出报告 (json/markdown/html)
        - method: GET
          path: /health
          description: 健康检查(含知识库连接状态)

    - type: cli
      entry: bin/cli.js
      commands:
        - cmd: standards
          description: 列出内置合规标准
        - cmd: clauses --standard <名称>
          description: 查看某标准的所有条款
        - cmd: check --standard <名称> --work <内容>
          description: 执行差距排查(直接输入)
        - cmd: check --standard <名称> --file <路径>
          description: 执行差距排查(从文件读取)
        - cmd: check --standard <名称> --work <内容> --no-kb
          description: 执行差距排查(禁用知识库)
        - cmd: check --standard <名称> --work <内容> --kb-url <URL>
          description: 执行差距排查(指定知识库地址)
        - cmd: history
          description: 查看排查历史

  # 内置数据
  data:
    standards:
      - name: 等保2.0
        code: GB/T 22239-2019
        clauseCount: 48
      - name: 网络安全法
        code: 中华人民共和国网络安全法
        clauseCount: 15
      - name: 数据安全法
        code: 中华人民共和国数据安全法
        clauseCount: 12
      - name: 个人信息保护法
        code: 中华人民共和国个人信息保护法
        clauseCount: 18
      - name: ISO27001
        code: ISO/IEC 27001:2022
        clauseCount: 49
      - name: SOC2
        code: AICPA SOC2 TSC
        clauseCount: 30
      - name: GDPR
        code: EU General Data Protection Regulation
        clauseCount: 25

  # 依赖
  dependencies:
    runtime:
      - express ^4.21.0
      - cors ^2.8.5
      - better-sqlite3 ^11.6.0
    optional:
      - "@anthropic-ai/sdk" (AI增强 - Claude)
      - "@zhipuai/sdk" (AI增强 - GLM)

  # 配置
  config:
    envVars:
      - name: CGC_PORT
        description: HTTP服务端口 (默认3100)
      - name: CGC_DB_PATH
        description: SQLite数据库路径 (默认./db/clauses.db)
      - name: CGC_AI_PROVIDER
        description: AI提供商 (claude|glm|minimax)
      - name: CGC_AI_API_KEY
        description: AI API密钥
      - name: CGC_AI_MODEL
        description: AI模型名称
      - name: CGC_AI_BASE_URL
        description: AI API基础URL
      - name: CGC_KB_BASE_URL
        description: 知识库API地址 (如 http://localhost:8000/api/v1)
      - name: CGC_KB_ENABLED
        description: 是否启用知识库增强 (true|false, 默认true)
      - name: CGC_KB_TIMEOUT
        description: 知识库请求超时毫秒数 (默认5000)

  # 输入输出
  input:
    - 工作内容文本 (直接输入/文件/Summary Center API)
    - 合规标准名称
    - 知识库证据 (自动从安全合规知识库获取, 可选)
  output:
    - 覆盖率统计
    - 已覆盖/未覆盖条款列表
    - 整改建议
    - 知识库增强信息 (kbEnhanced, kbFilesUsed)
    - 报告 (JSON/Markdown/HTML)

  # 算法说明
  algorithm:
    step1: 从SQLite加载指定标准的全部条款
    step2: 获取工作内容 (三种来源: 直接输入/文件/Summary Center)
    step3: 获取知识库内容 (证据通道: 制度体系+技术基线+应急响应 → 合并到工作内容)
    step4: 对每个条款执行关键词匹配 → 计算匹配置信度 (基于合并后的内容)
    step5: confidence >= 0.15 → 标记为covered, 否则 → gap
    step6: AI增强(可选): 发送未覆盖条款+工作内容+知识库上下文给AI, 判断隐含覆盖+生成整改建议
    step7: 计算覆盖率, 生成总结, 保存历史(含KB信息)

  # 知识库对接
  knowledgeBase:
    backend: FastAPI (端口8000)
    baseUrl: /api/v1
    channels:
      evidence: [01-制度体系, 02-技术基线, 06-应急响应] → 合并到工作内容, 参与关键词匹配
      context: [03-合规框架, 04-审计与整改] → 仅注入AI Prompt, 辅助隐含覆盖判断
    standardMapping:
      等保2.0: 等保2.0
      ISO27001: ISO27001
      SOC2: SOC2
      GDPR: GDPR
    fallback: 网络安全法/数据安全法/个人信息保护法 → 关键词搜索兜底
    degradation: KB不可用时返回空结果, 不影响排查
---

# compliance-gap-check

合规差距智能排查 Skill — 对照等保2.0/网安法/数据安全法/个人信息保护法/ISO27001/SOC2/GDPR，自动识别合规差距并生成整改建议。

## 快速开始

```bash
# 安装依赖
npm install

# 启动HTTP API服务
npm start

# 使用CLI — 基础用法
node bin/cli.js standards
node bin/cli.js check --standard "等保2.0" --work "完成等保三级测评备案、漏洞扫描修复"

# 使用CLI — 启用知识库增强
set CGC_KB_BASE_URL=http://localhost:8000/api/v1
node bin/cli.js check --standard "等保2.0" --work "完成等保三级测评备案、漏洞扫描修复"

# 使用CLI — 指定知识库地址
node bin/cli.js check --standard "等保2.0" --work "漏洞扫描修复" --kb-url http://localhost:8000/api/v1

# 使用CLI — 禁用知识库
node bin/cli.js check --standard "等保2.0" --work "漏洞扫描修复" --no-kb
```

## 核心能力

- **关键词匹配**: 基于条款关键词库自动匹配工作内容，计算匹配置信度
- **AI增强**: 可选接入 Claude/GLM/MiniMax，对关键词未覆盖条款进行隐含覆盖判断和整改建议生成
- **知识库对接**: 自动从安全合规知识库获取已落地的制度/基线/预案作为合规证据，提升覆盖率准确性
- **双接口**: HTTP API (端口3100) + CLI，适配自动化调用与手动使用
- **内置条款库**: 等保2.0(48条) + 网安法(15条) + 数据安全法(12条) + 个人信息保护法(18条) + ISO27001(49条) + SOC2(30条) + GDPR(25条)
- **历史追溯**: SQLite持久化存储每次排查结果，支持回溯分析

## 知识库对接说明

### 数据流

```
用户工作内容 ─┐
              ├→ 合并内容 → 关键词匹配 → AI增强(KB上下文注入) → 覆盖率计算 → 报告
KB证据内容 ───┘         ↑
KB上下文内容 ────────────┘ (仅注入AI Prompt)
```

### 两个通道

| 通道 | 知识库类目 | 用途 |
|------|-----------|------|
| 证据通道 | 01-制度体系、02-技术基线、06-应急响应 | 已落地措施 → 合并到工作内容 → 参与关键词匹配 |
| 上下文通道 | 03-合规框架、04-审计与整改 | 映射表/审计记录 → 注入AI Prompt → 辅助隐含覆盖判断 |

### 配置方式

**方式一：环境变量**
```bash
set CGC_KB_BASE_URL=http://localhost:8000/api/v1
```

**方式二：配置文件** (`config.js`)
```js
module.exports = {
  knowledgeBase: {
    baseUrl: 'http://localhost:8000/api/v1',
  },
};
```

**方式三：CLI参数**
```bash
node bin/cli.js check --standard "等保2.0" --work "..." --kb-url http://localhost:8000/api/v1
```

**方式四：API参数**
```json
{ "standardName": "等保2.0", "workContent": "...", "useKB": true, "kbBaseUrl": "http://localhost:8000/api/v1" }
```

### 前提条件

1. 启动知识库后端：`cd 01-安全合规知识库/安全合规知识库/kb-backend && python main.py`
2. 知识库有已填充内容（当前已有：数据安全管理制度、供应商安全管理制度、等保2.0映射表、ISO27001映射表、应急响应总体预案等）
3. 不配置KB时行为与v1.0.0完全一致，KB不可用时优雅降级