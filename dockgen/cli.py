import argparse
import json
import subprocess
import sys
from pathlib import Path

from dockgen import colors, config, wizard
from dockgen import __version__
from dockgen.renderers import compose, devcontainer


def cmd_new(args):
    existing = config.load(args.workspace)
    if existing and not args.force:
        print(
            colors.error(
                f"error: {args.workspace}/.dockgen.json already exists. "
                "Use 'dockgen config' or pass --force."
            ),
            file=sys.stderr,
        )
        return 1
    answers = wizard.run()
    return _apply(answers, args.workspace)


def cmd_config(args):
    existing = config.load(args.workspace)
    if not existing:
        print(
            colors.error(f"no .dockgen.json in {args.workspace}. Run 'dockgen new' first."),
            file=sys.stderr,
        )
        return 1
    answers = wizard.run(defaults=existing)
    return _apply(answers, args.workspace)


def cmd_add(args):
    existing = config.load(args.workspace)
    if not existing:
        print(colors.error(f"no .dockgen.json in {args.workspace}. Run 'dockgen new' first."), file=sys.stderr)
        return 1

    feature = args.feature
    value = getattr(args, "value", None)

    handlers = {
        "gpu": _add_gpu,
        "display": _add_display,
        "volume": _add_volume,
    }
    if feature not in handlers:
        print(
            colors.error(f"unknown feature '{feature}'. supported: {', '.join(handlers)}"),
            file=sys.stderr,
        )
        return 1
    try:
        return handlers[feature](existing, args.workspace, value)
    except (KeyboardInterrupt, EOFError):
        print(colors.warn("\naborted."), file=sys.stderr)
        return 130


def _add_gpu(answers, workspace, value=None):
    patch = {}
    wizard._step_4a_gpu(patch, answers)
    answers["gpu"] = patch["gpu"]
    return _apply(answers, workspace)


def _add_display(answers, workspace, value=None):
    patch = {}
    wizard._step_4b_display(patch, answers)
    answers["display"] = patch["display"]
    return _apply(answers, workspace)


def _add_volume(answers, workspace, value=None):
    if value:
        mount = value
    else:
        mount = input("  Bind mount (HOST:CONTAINER): ").strip()
    if not mount:
        print("aborted.", file=sys.stderr)
        return 1
    mounts = list(answers.get("extra_mounts") or [])
    if mount in mounts:
        print(f"  already present: {mount}")
        return 0
    mounts.append(mount)
    answers["extra_mounts"] = mounts
    return _apply(answers, workspace)


def cmd_validate(args):
    ws = Path(args.workspace)
    cfg = config.load(args.workspace)
    if not cfg:
        print(colors.error(f"no .dockgen.json in {args.workspace}."), file=sys.stderr)
        return 1

    errors = []
    warnings = []

    output = cfg.get("output_format", "compose")

    if output in ("compose", "both"):
        compose_path = ws / "docker" / "compose.yml"
        if not compose_path.exists():
            errors.append(f"missing {compose_path} — run 'dockgen new' or 'dockgen config'")
        else:
            _validate_yaml(compose_path, errors)
            _validate_compose(compose_path, ws / "docker", warnings, errors)

    if output in ("devcontainer", "both"):
        dc_path = ws / ".devcontainer" / "devcontainer.json"
        if not dc_path.exists():
            errors.append(f"missing {dc_path} — run 'dockgen new' or 'dockgen config'")
        else:
            _validate_json(dc_path, errors)

    for w in warnings:
        print(f"  {colors.yellow('warn:')}  {w}")
    for e in errors:
        print(f"  {colors.error('error:')} {e}", file=sys.stderr)

    if errors:
        return 1
    print(colors.success("validate: OK"))
    return 0


def _validate_yaml(path, errors):
    try:
        import yaml  # PyYAML — optional
        with path.open() as f:
            yaml.safe_load(f)
    except ImportError:
        pass  # no PyYAML; docker compose config covers YAML validation
    except Exception as exc:
        errors.append(f"{path.name}: invalid YAML — {exc}")


def _validate_json(path, errors):
    try:
        with path.open() as f:
            json.load(f)
    except json.JSONDecodeError as exc:
        errors.append(f"{path.name}: invalid JSON — {exc}")


def _validate_compose(compose_path, cwd, warnings, errors):
    docker = _which("docker")
    if not docker:
        warnings.append("docker not on PATH; skipping compose dry-run")
        return
    result = subprocess.run(
        [docker, "compose", "-f", compose_path.name, "config", "--quiet"],
        cwd=str(cwd),
        capture_output=True,
        text=True,
        timeout=15,
    )
    if result.returncode != 0:
        msg = (result.stderr or result.stdout).strip()
        errors.append(f"compose config failed:\n    {msg}")


def _which(cmd):
    import shutil
    return shutil.which(cmd)


def cmd_info(args):
    existing = config.load(args.workspace)
    if not existing:
        print(colors.error(f"no .dockgen.json in {args.workspace}."), file=sys.stderr)
        return 1
    print(json.dumps(existing, indent=2, sort_keys=True))
    return 0


def _apply(answers, workspace):
    cfg_path = config.save(answers, workspace)
    workspace = Path(workspace)
    written = [cfg_path]
    if answers["output_format"] in ("compose", "both"):
        written.extend(compose.render(answers, workspace))
    if answers["output_format"] in ("devcontainer", "both"):
        written.extend(devcontainer.render(answers, workspace))
    print(colors.success("wrote:"))
    for p in written:
        print(f"  {colors.cyan(str(p))}")
    return 0


def main():
    p = argparse.ArgumentParser(prog="dockgen", description="Docker Container Tool")
    p.add_argument(
        "-w", "--workspace", default=".", help="target workspace (default: cwd)"
    )
    p.add_argument(
        "--version", action="version", version=f"dockgen {__version__}"
    )
    sub = p.add_subparsers(dest="cmd", required=True)

    pn = sub.add_parser("new", help="generate a fresh config via the wizard")
    pn.add_argument("--force", action="store_true", help="overwrite existing .dockgen.json")
    pn.set_defaults(func=cmd_new)

    pc = sub.add_parser("config", help="reconfigure an existing .dockgen.json")
    pc.set_defaults(func=cmd_config)

    pa = sub.add_parser("add", help="surgically add a feature")
    pa.add_argument("feature", choices=["gpu", "display", "volume"])
    pa.add_argument("value", nargs="?", help="value for the feature (e.g. HOST:CONTAINER for volume)")
    pa.set_defaults(func=cmd_add)

    pv = sub.add_parser("validate", help="validate generated files")
    pv.set_defaults(func=cmd_validate)

    pi = sub.add_parser("info", help="print current config")
    pi.set_defaults(func=cmd_info)

    args = p.parse_args()
    return args.func(args)
