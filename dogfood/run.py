#!/usr/bin/env python3
"""Dogfooding harness — drive Partwright non-interactively for agent fleets.

The `design-part` skill is a single human-gated conversation: it interviews the
maker and will not write a brief until the maker says "yes". That gate is the
right behavior for a real design session, but it makes the flow impossible to
run unattended, which is exactly what orchestrated dogfooding needs.

This runner takes the other, non-interactive path through the same tool:
`partwright new --brief <FILE>` scaffolds a standalone repo directly from a
pre-authored brief, no interview. Point a team of agents at this harness and
each one gets a real, ready-to-build repo plus a place to record what the tool
got wrong.

Stages
------
1. **scaffold** (default, deterministic, no network, no LLM): scaffold every
   brief under ``briefs/`` into a work directory and record success/failure and
   what was produced. Runnable anywhere Partwright runs.
2. **build** (``--build``, needs ``uv`` + network): for each scaffolded repo,
   create the venv, install ``build123d`` + preview deps, and run the
   placeholder ``generate.py`` / ``preview.py`` smoke test so the repo is proven
   to render before an agent touches it. This is the substrate an orchestrated
   build agent then iterates on.
3. **collect** (``--collect``): aggregate every ``DOGFOOD_FEEDBACK.md`` an agent
   left in a work repo into one report, so feedback about the tool comes back
   structured instead of scattered.

A machine-readable ``report.json`` is always written to the work directory, and
a short summary is printed. Standard library only — no third-party imports,
matching Partwright itself.
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time
from pathlib import Path

# dogfood/run.py -> repo root is one level up. The harness drives the *checked
# out* Partwright via `python -m partwright`, so a clone is exercised end to end
# rather than whatever happens to be installed on PATH.
HARNESS_DIR = Path(__file__).resolve().parent
REPO_ROOT = HARNESS_DIR.parent
DEFAULT_BRIEFS_DIR = HARNESS_DIR / "briefs"
DEFAULT_WORK_DIR = HARNESS_DIR / "work"
FEEDBACK_FILENAME = "DOGFOOD_FEEDBACK.md"


def _run(cmd: list[str], cwd: Path, timeout: int) -> tuple[bool, str]:
    """Run a subprocess, returning ``(ok, combined_output)``.

    Never raises for an ordinary command failure or timeout — both become an
    ``ok=False`` result with the captured output — so one bad part can't abort
    the whole sweep.
    """
    env = dict(os.environ)
    # Ensure `python -m partwright` resolves to this clone even if an installed
    # copy exists, by putting the repo root first on the import path.
    env["PYTHONPATH"] = os.pathsep.join(
        [str(REPO_ROOT), env.get("PYTHONPATH", "")]
    ).rstrip(os.pathsep)
    try:
        proc = subprocess.run(
            cmd,
            cwd=str(cwd),
            env=env,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
    except FileNotFoundError as exc:
        return False, f"command not found: {exc}"
    except subprocess.TimeoutExpired:
        return False, f"timed out after {timeout}s: {' '.join(cmd)}"
    output = (proc.stdout or "") + (proc.stderr or "")
    return proc.returncode == 0, output.strip()


def discover_briefs(briefs_dir: Path) -> list[tuple[str, Path]]:
    """Return ``(name, brief_path)`` for every ``*/DESIGN_BRIEF.md`` found.

    The folder name under ``briefs/`` is the project name handed to
    ``partwright new``; the brief's own ``project_name`` frontmatter still drives
    the generated constants, so the two should agree but the folder name is what
    we scaffold as.
    """
    found: list[tuple[str, Path]] = []
    for brief in sorted(briefs_dir.glob("*/DESIGN_BRIEF.md")):
        found.append((brief.parent.name, brief))
    return found


def scaffold_one(name: str, brief: Path, work_dir: Path, timeout: int) -> dict:
    """Scaffold a single brief into ``work_dir`` and describe the outcome."""
    repo = work_dir / name
    result: dict = {"name": name, "brief": str(brief), "repo": str(repo)}

    if repo.exists():
        # Re-running should be idempotent; partwright refuses an existing target.
        result["scaffold"] = "skipped"
        result["detail"] = "repo already exists; delete it to re-scaffold"
        result["files"] = sorted(p.name for p in repo.iterdir())
        return result

    started = time.monotonic()
    ok, output = _run(
        [
            sys.executable,
            "-m",
            "partwright",
            "new",
            name,
            "--brief",
            str(brief),
            "--dest",
            str(work_dir),
            "--no-git",
        ],
        cwd=REPO_ROOT,
        timeout=timeout,
    )
    result["seconds"] = round(time.monotonic() - started, 2)

    if ok and repo.is_dir():
        result["scaffold"] = "ok"
        result["files"] = sorted(p.name for p in repo.iterdir())
    else:
        result["scaffold"] = "fail"
        result["detail"] = output
    return result


def build_one(repo: Path, timeout: int) -> dict:
    """Run the placeholder generate/preview smoke test in a scaffolded repo.

    Proves the repo renders out of the box (the seeded geometry is a cube) so an
    orchestrated build agent starts from a known-good baseline. Each step is
    recorded independently; the first failure short-circuits the rest.
    """
    steps: list[dict] = []

    def step(label: str, cmd: list[str], step_timeout: int) -> bool:
        started = time.monotonic()
        ok, output = _run(cmd, cwd=repo, timeout=step_timeout)
        entry = {
            "step": label,
            "ok": ok,
            "seconds": round(time.monotonic() - started, 2),
        }
        if not ok:
            entry["detail"] = output[-2000:]  # tail is where the error is
        steps.append(entry)
        return ok

    py = repo / ".venv" / "bin" / "python"
    chain = (
        step("uv venv", ["uv", "venv", ".venv", "--python", "3.12"], timeout)
        and step(
            "uv pip install",
            ["uv", "pip", "install", "-p", str(py), "-r", "requirements.txt"],
            timeout,
        )
        and step("generate.py", [str(py), "generate.py"], timeout)
        and step("preview.py", [str(py), "preview.py"], timeout)
    )

    preview_png = repo / "preview.png"
    return {
        "build": "ok" if (chain and preview_png.is_file()) else "fail",
        "preview_png": preview_png.is_file(),
        "steps": steps,
    }


def collect_feedback(work_dir: Path) -> list[dict]:
    """Gather every agent-left feedback file under the work directory."""
    notes: list[dict] = []
    for fb in sorted(work_dir.glob(f"*/{FEEDBACK_FILENAME}")):
        notes.append(
            {
                "part": fb.parent.name,
                "path": str(fb),
                "body": fb.read_text(encoding="utf-8"),
            }
        )
    return notes


def _print_summary(report: dict) -> None:
    parts = report["parts"]
    print(f"\nPartwright dogfood — {report['stage']}")
    print(f"  work dir : {report['work_dir']}")
    print(f"  parts    : {len(parts)}\n")
    for p in parts:
        line = f"  {p['name']:<16} scaffold={p.get('scaffold', '-')}"
        if "build" in p:
            line += f"  build={p['build']}"
        print(line)
        if p.get("scaffold") == "fail" or p.get("build") == "fail":
            detail = p.get("detail") or _first_failed_step(p)
            if detail:
                print(f"      ↳ {detail.splitlines()[0][:200]}")
    if report.get("feedback"):
        print(f"\n  feedback files collected: {len(report['feedback'])}")
    print()


def _first_failed_step(part: dict) -> str:
    for s in part.get("steps", []):
        if not s["ok"]:
            return f"{s['step']}: {s.get('detail', '').splitlines()[0] if s.get('detail') else 'failed'}"
    return ""


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="dogfood/run.py",
        description="Drive Partwright non-interactively for orchestrated dogfooding.",
    )
    parser.add_argument(
        "--briefs-dir",
        type=Path,
        default=DEFAULT_BRIEFS_DIR,
        help="directory of <name>/DESIGN_BRIEF.md fixtures (default: dogfood/briefs)",
    )
    parser.add_argument(
        "--work-dir",
        type=Path,
        default=DEFAULT_WORK_DIR,
        help="where scaffolded repos and report.json land (default: dogfood/work)",
    )
    parser.add_argument(
        "--build",
        action="store_true",
        help="also run the venv + generate/preview smoke test (needs uv + network)",
    )
    parser.add_argument(
        "--collect",
        action="store_true",
        help="aggregate DOGFOOD_FEEDBACK.md files from the work dir into the report",
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=600,
        help="per-subprocess timeout in seconds (default: 600)",
    )
    args = parser.parse_args(argv)

    args.work_dir.mkdir(parents=True, exist_ok=True)
    briefs = discover_briefs(args.briefs_dir)
    if not briefs:
        print(f"no briefs found under {args.briefs_dir}", file=sys.stderr)
        return 1

    stage = "scaffold+build" if args.build else "scaffold"
    parts: list[dict] = []
    for name, brief in briefs:
        part = scaffold_one(name, brief, args.work_dir, args.timeout)
        if args.build and part["scaffold"] in ("ok", "skipped"):
            part.update(build_one(Path(part["repo"]), args.timeout))
        parts.append(part)

    report: dict = {
        "stage": stage,
        "work_dir": str(args.work_dir),
        "parts": parts,
    }
    if args.collect:
        report["feedback"] = collect_feedback(args.work_dir)

    report_path = args.work_dir / "report.json"
    report_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    _print_summary(report)
    print(f"  report   : {report_path}")

    # Non-zero exit if anything failed, so a CI / orchestrator can gate on it.
    failed = any(p.get("scaffold") == "fail" or p.get("build") == "fail" for p in parts)
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
