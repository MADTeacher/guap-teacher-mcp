"""Console entry point for ``guap-teacher``.

Subcommands: ``init`` (seed personal skill copies), ``skills diff``
(compare them with the canonical ones), ``alerts`` (read the local
prompt-injection journal), ``protocol`` (review journal passthrough).
Without a subcommand the MCP server starts on stdio exactly as before,
so existing MCP client configs keep working.
"""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path

from guap_teacher_mcp import distribute, guard, skills

# Publication URL: the repository lives at github.com/MADTeacher/guap-teacher-mcp.
PACKAGE_SOURCE = "git+https://github.com/MADTeacher/guap-teacher-mcp"

MCP_SNIPPETS = f"""\
Подключение MCP-сервера (stdio) в вашем харнессе:

ZCode (~/.zcode/cli/config.json, ключ mcp.servers):
  "mcp": {{"servers": {{"guap-teacher": {{"command": "uvx", "args": ["--from", "{PACKAGE_SOURCE}", "guap-teacher"]}}}}}}

Codex (~/.codex/config.toml):
  [mcp_servers.guap-teacher]
  command = "uvx"
  args = ["--from", "{PACKAGE_SOURCE}", "guap-teacher"]

Qwen Code (~/.qwen/settings.json):
  {{"mcpServers": {{"guap-teacher": {{"command": "uvx", "args": ["--from", "{PACKAGE_SOURCE}", "guap-teacher"]}}}}}}

Локальный clone вместо uvx:
  uv --directory <путь к guap-teacher-mcp> run guap-teacher
"""

_DIFF_HINTS = {
    "missing": " — нет в личном каталоге; guap-teacher init доустановит",
    "differs": " — личная копия отличается от канона (это нормально)",
    "identical": " — совпадает с каноном",
}


def _personal_root(value: str | None) -> Path:
    return Path(value) if value else skills.personal_skills_root()


def _cmd_init(args: argparse.Namespace) -> int:
    canonical_root = skills.canonical_skills_root()
    personal_root = _personal_root(args.skills_dir)
    result = distribute.seed_personal_skills(canonical_root, personal_root)
    print(f"Личный каталог навыков: {personal_root}")
    if result.seeded:
        print("Установлены: " + ", ".join(result.seeded))
    if result.skipped:
        print("Пропущены (уже существуют, не перезаписаны): " + ", ".join(result.skipped))
    if not result.seeded and not result.skipped:
        print("Канонические навыки не найдены.")
    print()
    print(MCP_SNIPPETS)
    return 0


def _cmd_skills_diff(args: argparse.Namespace) -> int:
    canonical_root = skills.canonical_skills_root()
    personal_root = _personal_root(args.skills_dir)
    for item in distribute.diff_personal_skills(canonical_root, personal_root):
        print(f"{item.name}: {item.status}{_DIFF_HINTS[item.status]}")
    return 0


def _download_dir(value: str | None) -> Path:
    # Same rule as server.default_download_dir, repeated here so that
    # `skills diff`/`alerts` do not import the heavy MCP server module.
    if value:
        return Path(value)
    env = os.environ.get("GUAP_DOWNLOAD_DIR")
    return Path(env) if env else Path.cwd() / ".guap_mcp_tmp"


def _cmd_alerts(args: argparse.Namespace) -> int:
    path = guard.alerts_path(_download_dir(args.dir))
    entries = guard.read_alerts(path, args.limit)
    if args.json:
        print(json.dumps(entries, ensure_ascii=False, indent=2))
        return 0
    if not entries:
        print(f"Алертов нет. Журнал: {path}")
        return 0
    print(f"Журнал: {path} (свежие сверху)")
    for entry in reversed(entries):
        student = f" — {entry['student']}" if entry.get("student") else ""
        print(
            f"{entry.get('ts', '?')} [{entry.get('severity', '?').upper()}] "
            f"{entry.get('rule', '?')}{student}"
        )
        print(f"  источник: {entry.get('source', '?')}, поле: {entry.get('location', '?')}")
        print(f"  «{entry.get('excerpt', '')}»")
    return 0


def _cmd_protocol(args: argparse.Namespace) -> int:
    # Lazy import: protocol pulls openpyxl, light subcommands stay light.
    from guap_teacher_mcp import protocol

    return protocol.main(list(args.args))


def main(argv: list[str] | None = None) -> int:
    """Parse CLI args; without a subcommand start the MCP server (stdio)."""
    parser = argparse.ArgumentParser(
        prog="guap-teacher",
        description="MCP-сервер guap-teacher и утилиты распространения навыков",
    )
    sub = parser.add_subparsers(dest="command")

    p_init = sub.add_parser(
        "init", help="посеять канонические навыки в личный каталог (~/.agents/skills)"
    )
    p_init.add_argument(
        "--skills-dir",
        default=None,
        help="каталог личных навыков (по умолчанию GUAP_SKILLS_DIR или ~/.agents/skills)",
    )
    p_init.set_defaults(func=_cmd_init)

    p_skills = sub.add_parser("skills", help="операции с навыками")
    skills_sub = p_skills.add_subparsers(dest="skills_command")
    p_diff = skills_sub.add_parser(
        "diff", help="сравнить личные копии навыков с каноном текущей версии"
    )
    p_diff.add_argument(
        "--skills-dir",
        default=None,
        help="каталог личных навыков (по умолчанию GUAP_SKILLS_DIR или ~/.agents/skills)",
    )
    p_diff.set_defaults(func=_cmd_skills_diff)

    p_alerts = sub.add_parser(
        "alerts", help="журнал промпт-инъекций в работах студентов (security_log.jsonl)"
    )
    p_alerts.add_argument(
        "--limit",
        type=int,
        default=50,
        help="сколько свежих записей показать (по умолчанию 50)",
    )
    p_alerts.add_argument(
        "--dir",
        default=None,
        help="каталог загрузок с журналом (по умолчанию GUAP_DOWNLOAD_DIR или <cwd>/.guap_mcp_tmp)",
    )
    p_alerts.add_argument("--json", action="store_true", help="вывести сырой JSON")
    p_alerts.set_defaults(func=_cmd_alerts)

    p_protocol = sub.add_parser(
        "protocol",
        help="журнал протокола ревью (.xlsx): append / pending / posted",
    )
    # REMAINDER: the whole tail goes to protocol.main() verbatim, so its
    # argparse stays the single source of truth for the journal CLI.
    p_protocol.add_argument("args", nargs=argparse.REMAINDER)
    p_protocol.set_defaults(func=_cmd_protocol)

    args = parser.parse_args(argv)

    skills_dir = getattr(args, "skills_dir", None)
    if skills_dir is not None and not skills_dir.strip():
        parser.error("--skills-dir: путь не может быть пустым")

    if args.command == "skills" and not getattr(args, "skills_command", None):
        parser.error("skills: укажите подкоманду (diff)")

    func = getattr(args, "func", None)
    if func is None:
        # No subcommand: behave exactly like the old console script.
        from guap_teacher_mcp.server import main as serve  # lazy: heavy imports

        serve()
        return 0
    return func(args)
