"""Snapshot tmux topology and recreate it as fresh shells in Herdr."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import re
import shlex
import subprocess
import sys


SNAPSHOT_FORMAT = "tmux-to-herdr"
TOPOLOGY_FORMAT = "#{session_id} #{window_id} #{window_index} #{window_layout}"
CALLER_CONTEXT = (
    "HERDR_SOCKET_PATH",
    "HERDR_SESSION",
    "HERDR_WORKSPACE_ID",
    "HERDR_TAB_ID",
    "HERDR_PANE_ID",
    "HERDR_ACTIVE_WORKSPACE_ID",
    "HERDR_ACTIVE_TAB_ID",
    "HERDR_ACTIVE_PANE_ID",
    "HERDR_ACTIVE_PANE_CWD",
)


class MigrationError(Exception):
    pass


def run(command, env=None):
    try:
        return subprocess.run(
            command, env=env, capture_output=True, text=True, check=True, timeout=30
        ).stdout
    except subprocess.CalledProcessError as error:
        detail = error.stderr.strip() or error.stdout.strip()
        raise MigrationError(
            f"{shlex.join(command)} failed ({error.returncode}): {detail}"
        ) from error
    except subprocess.TimeoutExpired as error:
        raise MigrationError(f"{shlex.join(command)} timed out") from error
    except OSError as error:
        raise MigrationError(f"Cannot run {command[0]!r}: {error}") from error


def require(value, kind, context):
    if type(value) is not kind:
        raise MigrationError(f"{context} must be a {kind.__name__}")
    return value


def text(value, context):
    require(value, str, context)
    if not value or "\0" in value:
        raise MigrationError(f"{context} must be nonempty and contain no NUL bytes")
    return value


def source_id(value, prefix, context):
    text(value, context)
    if not re.fullmatch(re.escape(prefix) + r"[0-9]+", value):
        raise MigrationError(f"Invalid {context}: {value!r}")
    return value


class LayoutParser:
    def __init__(self, layout):
        checksum, separator, self.body = layout.partition(",")
        if not separator or not re.fullmatch(r"[0-9a-fA-F]{4}", checksum):
            raise MigrationError("Invalid tmux layout checksum header")
        actual = 0
        for character in self.body:
            actual = ((actual >> 1) | ((actual & 1) << 15)) + ord(character)
            actual &= 0xFFFF
        if actual != int(checksum, 16):
            raise MigrationError("Tmux layout checksum mismatch")
        self.position = 0

    def parse(self):
        node = self.node(0)
        if self.position != len(self.body):
            raise MigrationError("Unexpected trailing tmux layout data")
        return node

    def node(self, depth):
        if depth > 128:
            raise MigrationError("Tmux layout is too deeply nested")
        match = re.match(
            r"([0-9]+)x([0-9]+),([0-9]+),([0-9]+)", self.body[self.position:]
        )
        if not match:
            raise MigrationError(f"Invalid tmux layout at offset {self.position}")
        width, height, x, y = map(int, match.groups())
        if width < 1 or height < 1:
            raise MigrationError("Tmux layout dimensions must be positive")
        self.position += match.end()
        node = {"width": width, "height": height, "x": x, "y": y}
        marker = self.body[self.position:self.position + 1]
        self.position += 1
        if marker == ",":
            pane = re.match(r"[0-9]+", self.body[self.position:])
            if not pane:
                raise MigrationError("Tmux layout leaf is missing its pane ID")
            self.position += pane.end()
            node["pane_id"] = "%" + pane.group()
            return node
        if marker not in ("{", "["):
            raise MigrationError("Tmux layout node must be a pane or a split")

        node["direction"] = "right" if marker == "{" else "down"
        closing = "}" if marker == "{" else "]"
        children = [self.node(depth + 1)]
        while self.body[self.position:self.position + 1] == ",":
            self.position += 1
            children.append(self.node(depth + 1))
        if self.body[self.position:self.position + 1] != closing:
            raise MigrationError("Unclosed tmux layout split")
        self.position += 1
        if len(children) < 2:
            raise MigrationError("Tmux split must contain at least two children")
        axis, size, cross, cross_size = (
            ("x", "width", "y", "height") if marker == "{"
            else ("y", "height", "x", "width")
        )
        position = node[axis]
        for child in children:
            if (
                child[axis] != position
                or child[cross] != node[cross]
                or child[cross_size] != node[cross_size]
            ):
                raise MigrationError("Inconsistent tmux split geometry")
            position += child[size] + 1
        if position - 1 != node[axis] + node[size]:
            raise MigrationError("Tmux split children do not fill their parent")
        node["children"] = children
        return node


def leaves(node):
    if "pane_id" in node:
        return [node["pane_id"]]
    return [pane for child in node["children"] for pane in leaves(child)]


def validate_snapshot(document):
    require(document, dict, "Snapshot")
    if (
        document.get("format") != SNAPSHOT_FORMAT
        or type(document.get("version")) is not int
        or document["version"] != 1
    ):
        raise MigrationError("Expected a tmux-to-herdr version 1 snapshot")
    sessions = require(document.get("sessions"), list, "sessions")
    if not sessions:
        raise MigrationError("Snapshot contains no sessions")
    result = []
    seen_sessions, seen_names = set(), set()
    for session in sessions:
        require(session, dict, "session")
        sid = source_id(session.get("id"), "$", "session ID")
        name = text(session.get("name"), "session name")
        if sid in seen_sessions or name in seen_names:
            raise MigrationError(f"Duplicate session: {name!r} ({sid})")
        seen_sessions.add(sid)
        seen_names.add(name)
        windows = require(session.get("windows"), list, f"{name!r} windows")
        if not windows:
            raise MigrationError(f"Session {name!r} contains no windows")
        parsed_windows, seen_windows, seen_indices = [], set(), set()
        for window in windows:
            require(window, dict, "window")
            wid = source_id(window.get("id"), "@", "window ID")
            index = require(window.get("index"), int, "window index")
            if index < 0 or index in seen_indices or wid in seen_windows:
                raise MigrationError(f"Invalid or duplicate window in {name!r}")
            seen_indices.add(index)
            seen_windows.add(wid)
            label = text(window.get("name"), "window name")
            layout = LayoutParser(text(window.get("layout"), "window layout")).parse()
            panes = {}
            for pane in require(window.get("panes"), list, "window panes"):
                require(pane, dict, "pane")
                pid = source_id(pane.get("id"), "%", "pane ID")
                cwd = text(pane.get("cwd"), f"{pid} working directory")
                if pid in panes or not os.path.isabs(cwd):
                    raise MigrationError(f"Duplicate pane or non-absolute cwd: {pid}")
                panes[pid] = cwd
            layout_panes = leaves(layout)
            if len(set(layout_panes)) != len(layout_panes) or set(layout_panes) != set(panes):
                raise MigrationError(f"Pane inventory does not match layout in {name!r}/{label!r}")
            parsed_windows.append(
                {"id": wid, "index": index, "name": label, "layout": layout, "panes": panes}
            )
        result.append(
            {"id": sid, "name": name, "windows": sorted(parsed_windows, key=lambda w: w["index"])}
        )
    return result


class Tmux:
    def __init__(self, socket_path=None):
        self.command = [os.environ.get("TMUX_BIN_PATH", "tmux")]
        if socket_path is not None:
            self.command += ["-S", str(Path(socket_path).expanduser().absolute())]

    def query(self, *arguments):
        return run([*self.command, *arguments])

    def display(self, target, field):
        return self.query("display-message", "-p", "-t", target, "#{" + field + "}").removesuffix("\n")


def capture_snapshot(tmux, selected):
    before = tmux.query("list-windows", "-a", "-F", TOPOLOGY_FORMAT)
    sessions = []
    unmatched = set(selected)
    for sid in tmux.query("list-sessions", "-F", "#{session_id}").splitlines():
        name = tmux.display(sid, "session_name")
        if selected and sid not in selected and name not in selected:
            continue
        unmatched.difference_update((sid, name))
        windows = []
        for row in tmux.query(
            "list-windows", "-t", sid, "-F", "#{window_id} #{window_index} #{window_layout}"
        ).splitlines():
            fields = row.split(" ", 2)
            if len(fields) != 3 or not fields[1].isdigit():
                raise MigrationError(f"Invalid tmux window response: {row!r}")
            wid, index, layout = fields
            panes = [
                {"id": pid, "cwd": tmux.display(pid, "pane_current_path")}
                for pid in tmux.query("list-panes", "-t", wid, "-F", "#{pane_id}").splitlines()
            ]
            windows.append(
                {"id": wid, "index": int(index), "name": tmux.display(wid, "window_name"),
                 "layout": layout, "panes": panes}
            )
        sessions.append({"id": sid, "name": name, "windows": windows})
    if unmatched:
        raise MigrationError(f"Tmux sessions not found: {', '.join(sorted(unmatched))}")
    if before != tmux.query("list-windows", "-a", "-F", TOPOLOGY_FORMAT):
        raise MigrationError("Tmux topology changed during capture; retry without changing layouts")
    document = {
        "format": SNAPSHOT_FORMAT, "version": 1,
        "captured_at": datetime.now(timezone.utc).isoformat(), "sessions": sessions,
    }
    validate_snapshot(document)
    return document


def binary_layout(node):
    if "pane_id" in node:
        return {"pane_id": node["pane_id"]}
    return binary_group(node["children"], node["direction"])


def binary_group(children, direction):
    if len(children) == 1:
        return binary_layout(children[0])
    dimension = "width" if direction == "right" else "height"
    weights = [child[dimension] for child in children]
    total = sum(weights)
    # Ignore tmux separator cells; Herdr draws borders inside its own rectangles.
    # Balance multi-way splits so large rows do not hit Herdr's 10% minimum.
    cut = min(range(1, len(children)), key=lambda i: abs(sum(weights[:i]) / total - 0.5))
    ratio = sum(weights[:cut]) / total
    if not 0.1 <= ratio <= 0.9:
        raise MigrationError(
            f"Split ratio {ratio:.2%} is outside Herdr's 10%-90% range; "
            "adjust the tmux layout and take another snapshot"
        )
    return {
        "direction": direction, "ratio": ratio,
        "first": binary_group(children[:cut], direction),
        "second": binary_group(children[cut:], direction),
    }


def first_pane(node):
    while "pane_id" not in node:
        node = node["first"]
    return node["pane_id"]


def herdr_label(value):
    # Herdr scans global flags even when an argument is a label value.
    reserved = {
        "--session", "--remote", "--remote-keybindings", "--handoff",
        "--default-config", "--skill", "--version", "-V", "--help", "-h",
    }
    if value in reserved or any(value.startswith(flag + "=") for flag in reserved):
        raise MigrationError(
            f"Label {value!r} conflicts with Herdr CLI flags; rename it before importing"
        )
    return value


def make_plan(document, prefix):
    sessions = validate_snapshot(document)
    for session in sessions:
        session["name"] = herdr_label(
            text(prefix + session["name"], "destination workspace name")
        )
        for window in session["windows"]:
            window["name"] = herdr_label(window["name"])
            for pid, cwd in window["panes"].items():
                if not Path(cwd).is_dir():
                    raise MigrationError(f"{session['name']!r}/{window['name']!r} {pid}: directory unavailable: {cwd!r}")
            try:
                window["layout"] = binary_layout(window["layout"])
            except MigrationError as error:
                raise MigrationError(f"{session['name']!r}/{window['name']!r}: {error}") from error
    return sessions


def counts(sessions):
    return {
        "workspaces": len(sessions),
        "tabs": sum(len(session["windows"]) for session in sessions),
        "panes": sum(len(window["panes"]) for session in sessions for window in session["windows"]),
    }


class Herdr:
    def __init__(self, session=None, socket_path=None):
        if bool(session) == bool(socket_path):
            raise MigrationError("Select exactly one Herdr session or socket")
        self.command = [os.environ.get("HERDR_BIN_PATH", "herdr")]
        self.env = {key: value for key, value in os.environ.items() if key not in CALLER_CONTEXT}
        if session:
            self.command += ["--session", session]
            self.destination = {"session": session}
        else:
            path = str(Path(socket_path).expanduser().absolute())
            self.env["HERDR_SOCKET_PATH"] = path
            self.destination = {"socket": path}

    def call(self, *arguments):
        output = run([*self.command, *arguments], env=self.env)
        try:
            response = json.loads(output)
        except json.JSONDecodeError as error:
            raise MigrationError(f"Herdr returned invalid JSON for {arguments[:2]}") from error
        require(response, dict, "Herdr response")
        if "error" in response:
            raise MigrationError(f"Herdr error: {response['error']}")
        return require(response.get("result"), dict, "Herdr result")


def identifier(result, section, key):
    item = require(result.get(section), dict, f"Herdr {section}")
    return text(item.get(key), f"Herdr {key}")


def check_destination(herdr, sessions):
    result = herdr.call("workspace", "list")
    existing = set()
    for workspace in require(result.get("workspaces"), list, "Herdr workspaces"):
        require(workspace, dict, "Herdr workspace")
        existing.add(text(workspace.get("label"), "Herdr workspace label"))
    collisions = existing.intersection(session["name"] for session in sessions)
    if collisions:
        raise MigrationError(
            f"Destination already contains workspace(s): {', '.join(sorted(collisions))}. "
            "Use a different session or --prefix; nothing was created."
        )


def recreate_tree(herdr, tree, root_id, cwds, mapping):
    if "pane_id" in tree:
        mapping[tree["pane_id"]] = root_id
        return
    result = herdr.call(
        "pane", "split", "--pane", root_id, "--direction", tree["direction"],
        "--ratio", format(tree["ratio"], ".9g"),
        "--cwd", cwds[first_pane(tree["second"])], "--no-focus",
    )
    second_id = identifier(result, "pane", "pane_id")
    recreate_tree(herdr, tree["first"], root_id, cwds, mapping)
    recreate_tree(herdr, tree["second"], second_id, cwds, mapping)


def restore_snapshot(herdr, sessions):
    check_destination(herdr, sessions)
    report = {"destination": herdr.destination, "counts": counts(sessions), "workspaces": []}
    try:
        for session in sessions:
            first = session["windows"][0]
            created = herdr.call(
                "workspace", "create", "--label", session["name"],
                "--cwd", first["panes"][first_pane(first["layout"])], "--no-focus",
            )
            workspace_id = identifier(created, "workspace", "workspace_id")
            entry = {"tmux_session": session["id"], "workspace_id": workspace_id, "tabs": []}
            report["workspaces"].append(entry)
            print(f"Created workspace {session['name']!r}: {workspace_id}", file=sys.stderr, flush=True)
            for number, window in enumerate(session["windows"]):
                if number:
                    created = herdr.call(
                        "tab", "create", "--workspace", workspace_id,
                        "--label", window["name"],
                        "--cwd", window["panes"][first_pane(window["layout"])], "--no-focus",
                    )
                tab_id = identifier(created, "tab", "tab_id")
                root_id = identifier(created, "root_pane", "pane_id")
                if not number:
                    herdr.call("tab", "rename", tab_id, window["name"])
                mapping = {}
                recreate_tree(herdr, window["layout"], root_id, window["panes"], mapping)
                entry["tabs"].append(
                    {"tmux_window": window["id"], "tab_id": tab_id, "panes": mapping}
                )
    except (MigrationError, KeyboardInterrupt):
        known = ", ".join(entry["workspace_id"] for entry in report["workspaces"]) or "no IDs returned"
        print(
            f"Import interrupted; partial workspaces may remain ({known}). "
            "Nothing was closed or rolled back automatically.",
            file=sys.stderr,
        )
        raise
    return report


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Copy tmux topology into Herdr as fresh shells; never transfer or replay processes."
    )
    commands = parser.add_subparsers(dest="operation", required=True)
    snapshot = commands.add_parser("snapshot", help="Capture tmux without changing it")
    snapshot.add_argument("file", type=Path, help="New JSON snapshot file; never overwritten")
    snapshot.add_argument("--tmux-socket", help="Explicit tmux socket path (otherwise the current server)")
    snapshot.add_argument("--session", action="append", default=[], help="Tmux session name or ID; repeat to filter")
    restore = commands.add_parser("restore", help="Recreate a snapshot in an already-running local Herdr session")
    restore.add_argument("file", type=Path)
    target = restore.add_mutually_exclusive_group(required=True)
    target.add_argument("--herdr-session", help="Explicit destination session name; 'default' is allowed")
    target.add_argument("--herdr-socket", help="Explicit destination API socket path")
    restore.add_argument("--prefix", default="", help="Prefix imported workspace names")
    restore.add_argument("--dry-run", action="store_true", help="Validate directories, ratios and destination names without creating anything")
    args = parser.parse_args(argv)
    try:
        path = args.file.expanduser()
        if args.operation == "snapshot":
            document = capture_snapshot(Tmux(args.tmux_socket), args.session)
            fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
            with os.fdopen(fd, "w", encoding="utf-8") as output:
                json.dump(document, output, indent=2)
                output.write("\n")
            print(f"Saved {path}: {counts(document['sessions'])}", file=sys.stderr)
        else:
            with path.open(encoding="utf-8") as source:
                document = json.load(source)
            sessions = make_plan(document, args.prefix)
            herdr = Herdr(args.herdr_session, args.herdr_socket)
            if args.dry_run:
                check_destination(herdr, sessions)
                report = {
                    "dry_run": True, "destination": herdr.destination,
                    "counts": counts(sessions), "workspaces": sessions,
                }
            else:
                report = restore_snapshot(herdr, sessions)
            json.dump(report, sys.stdout, indent=2)
            print()
    except (MigrationError, OSError, json.JSONDecodeError) as error:
        print(f"tmux-to-herdr: {error}", file=sys.stderr)
        return 1
    except KeyboardInterrupt:
        print("tmux-to-herdr: cancelled", file=sys.stderr)
        return 130
    return 0


if __name__ == "__main__":
    sys.exit(main())
