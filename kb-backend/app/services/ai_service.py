import json
import logging
import re

import httpx

from config import AI_CONFIG

logger = logging.getLogger(__name__)


async def call_ai(prompt: str) -> str | None:
    config = AI_CONFIG
    provider = config.get("provider", "")
    api_key = config.get("api_key", "")
    if not provider or not api_key:
        return None

    try:
        if provider == "claude":
            return await _call_claude(prompt, api_key, config.get("model"))
        elif provider == "glm":
            return await _call_glm(prompt, api_key, config.get("model"), config.get("base_url"))
        elif provider == "minimax":
            return await _call_minimax(prompt, api_key, config.get("model"), config.get("base_url"))
        else:
            raise ValueError(f"不支持的AI提供商: {provider}")
    except Exception as e:
        logger.warning(f"[ai] AI增强失败: {e}")
        return None


async def _call_claude(prompt: str, api_key: str, model: str | None) -> str:
    try:
        from anthropic import AsyncAnthropic
    except ImportError:
        raise ImportError("anthropic 包未安装，请运行: pip install anthropic")

    client = AsyncAnthropic(api_key=api_key)
    msg = await client.messages.create(
        model=model or "claude-sonnet-4-20250514",
        max_tokens=4096,
        messages=[{"role": "user", "content": prompt}],
    )
    return msg.content[0].text


async def _call_glm(prompt: str, api_key: str, model: str | None, base_url: str | None) -> str:
    url = f"{base_url or 'https://open.bigmodel.cn/api/paas'}/v4/chat/completions"
    async with httpx.AsyncClient(timeout=60) as client:
        res = await client.post(
            url,
            headers={"Content-Type": "application/json", "Authorization": f"Bearer {api_key}"},
            json={
                "model": model or "glm-4",
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": 4096,
            },
        )
        data = res.json()
    return data.get("choices", [{}])[0].get("message", {}).get("content", "")


async def _call_minimax(prompt: str, api_key: str, model: str | None, base_url: str | None) -> str:
    url = f"{base_url or 'https://api.minimax.chat'}/v1/text/chatcompletion_v2"
    async with httpx.AsyncClient(timeout=60) as client:
        res = await client.post(
            url,
            headers={"Content-Type": "application/json", "Authorization": f"Bearer {api_key}"},
            json={
                "model": model or "MiniMax-Text-01",
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": 4096,
            },
        )
        data = res.json()
    return data.get("choices", [{}])[0].get("message", {}).get("content", "")


def build_gap_check_prompt(gap_clauses: list[dict], work_content: str, kb_context: str = "") -> str:
    clause_list = "\n".join(
        f"{i + 1}. [{c['clause_id']}] {c['section']} — {c['clause_text']}"
        for i, c in enumerate(gap_clauses)
    )

    kb_section = f"\n## 组织合规现状（来自安全合规知识库）\n{kb_context}\n" if kb_context else ""
    kb_instruction = (
        "\n注意：如果组织已有相关制度或技术措施（见\"组织合规现状\"部分），即使工作内容中没有直接提及，也应判断为隐含覆盖。"
        if kb_context
        else ""
    )

    return f"""你是一名网络安全合规专家。请根据以下工作内容和组织合规现状，判断哪些合规条款可能已被隐含覆盖，并为未覆盖条款提供整改建议。

## 工作内容
{work_content}
{kb_section}
## 未覆盖条款
{clause_list}

## 输出要求
请以JSON格式输出，格式如下：
{{
  "reassessed": [
    {{"clause_id": "条款ID", "covered": true/false, "confidence": 0.0-1.0, "reason": "判断理由"}}
  ],
  "suggestions": [
    {{"clause_id": "条款ID", "suggestion": "整改建议", "priority": "高/中/低"}}
  ]
}}
{kb_instruction}
只输出JSON，不要输出其他内容。"""


def parse_ai_response(text: str) -> dict | None:
    if not text:
        return None
    cleaned = re.sub(r"```json\n?", "", text).replace("```", "").strip()
    try:
        return json.loads(cleaned)
    except (json.JSONDecodeError, ValueError):
        return None
