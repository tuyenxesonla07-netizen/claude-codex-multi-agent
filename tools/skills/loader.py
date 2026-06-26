# tools/skills/loader.py

"""
Skill 加载器 — 从 SKILL.md 文件加载技能定义。

SKILL.md 格式:
    ---
    name: code-review
    description: Code review best practices
    triggers: [review, check, audit]
    ---

    # Content
    Markdown body with instructions...

约定:
    - 顶层 `skills/` 目录放 SKILL.md 文件
    - 按相关性注入 prompt（无需写代码）
    - YAML frontmatter 可选（默认从文件名推断 name）
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional

logger = logging.getLogger(__name__)

# YAML frontmatter 解析（不依赖 pyyaml，纯正则）
FRONTMATTER_RE = re.compile(r"^---\s*\n(.*?)\n---\s*\n", re.DOTALL)


@dataclass
class Skill:
    """一个技能定义"""
    name: str
    description: str
    system_snippet: str = ""       # 注入 system prompt 的内容
    context_snippet: str = ""      # 注入上下文的内容
    triggers: list[str] = field(default_factory=list)  # 触发关键词
    metadata: dict = field(default_factory=dict)

    @property
    def full_snippet(self) -> str:
        """完整的注入内容"""
        parts = []
        if self.system_snippet:
            parts.append(self.system_snippet)
        if self.context_snippet:
            parts.append(self.context_snippet)
        return "\n\n".join(parts)


def _parse_frontmatter(text: str) -> tuple:
    """
    解析 SKILL.md 的 frontmatter。

    Returns:
        (metadata_dict, body_text)
    """
    match = FRONTMATTER_RE.match(text)
    if not match:
        return {}, text

    frontmatter = match.group(1)
    body = text[match.end():]

    # 简单 YAML 解析（key: value 格式）
    meta = {}
    for line in frontmatter.strip().split("\n"):
        if ":" in line:
            key, _, value = line.partition(":")
            key = key.strip()
            value = value.strip().strip('"').strip("'")

            # 处理列表值: [a, b, c]
            if value.startswith("[") and value.endswith("]"):
                value = [v.strip().strip('"').strip("'") for v in value[1:-1].split(",") if v.strip()]

            meta[key] = value

    return meta, body


class SkillLoader:
    """
    Skill 文件加载器。

    从指定目录加载所有 SKILL.md 文件。

    用法:
        loader = SkillLoader("tools/skills/builtin")
        skills = loader.load_all()
        skill = loader.load("code-review")
    """

    def __init__(self, skills_dir: str = "tools/skills/builtin"):
        self.skills_dir = Path(skills_dir)

    def load_all(self) -> List[Skill]:
        """加载目录下所有 SKILL.md 文件"""
        skills = []
        if not self.skills_dir.exists():
            logger.warning("[SkillLoader] Directory not found: %s", self.skills_dir)
            return skills

        for path in sorted(self.skills_dir.rglob("SKILL.md")):
            try:
                skill = self._load_file(path)
                skills.append(skill)
            except Exception as e:
                logger.error("[SkillLoader] Failed to load %s: %s", path, e)

        logger.info("[SkillLoader] Loaded %d skills from %s", len(skills), self.skills_dir)
        return skills

    def load(self, name: str) -> Optional[Skill]:
        """加载指定名称的 skill"""
        for path in self.skills_dir.rglob("SKILL.md"):
            if path.parent.name == name or path.stem == name:
                try:
                    return self._load_file(path)
                except Exception as e:
                    logger.error("[SkillLoader] Failed to load %s: %s", path, e)
        return None

    def _load_file(self, path: Path) -> Skill:
        """从文件加载单个 skill"""
        content = path.read_text(encoding="utf-8")
        meta, body = _parse_frontmatter(content)

        name = meta.get("name", path.parent.name)
        description = meta.get("description", "")
        triggers = meta.get("triggers", [])

        # 如果 triggers 是字符串，转为列表
        if isinstance(triggers, str):
            triggers = [triggers]

        # 分离 system_snippet 和 context_snippet
        # 默认整个 body 作为 system_snippet
        system_snippet = body.strip()
        context_snippet = ""

        # 如果有 ## Context 部分，拆分
        context_marker = "## Context"
        if context_marker in body:
            parts = body.split(context_marker, 1)
            system_snippet = parts[0].strip()
            context_snippet = parts[1].strip()

        return Skill(
            name=name,
            description=description,
            system_snippet=system_snippet,
            context_snippet=context_snippet,
            triggers=triggers,
            metadata=meta,
        )
