import contextlib
import copy
import importlib.util
import io
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import time
import unittest
from unittest import mock


ROOT = Path(__file__).resolve().parents[2]
HELPER = ROOT / "herdr/.config/herdr/scripts/tmux-to-herdr"
SPEC = importlib.util.spec_from_file_location(
    "tmux_to_herdr", ROOT / "herdr/.config/herdr/lib/tmux_to_herdr.py"
)
importer = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(importer)


def layout(body):
    checksum = 0
    for character in body:
        checksum = ((checksum >> 1) | ((checksum & 1) << 15)) + ord(character)
        checksum &= 0xFFFF
    return f"{checksum:04x},{body}"


def snapshot(cwds):
    return {
        "format": "tmux-to-herdr",
        "version": 1,
        "sessions": [
            {
                "id": "$7", "name": "project with spaces",
                "windows": [
                    {
                        "id": "@2", "index": 1, "name": "main window",
                        "layout": layout(
                            "120x80,0,0{71x80,0,0,1,48x80,72,0"
                            "[48x39,72,0,2,48x40,72,40,3]}"
                        ),
                        "panes": [
                            {"id": f"%{index}", "cwd": str(cwd)}
                            for index, cwd in enumerate(cwds[:3], 1)
                        ],
                    },
                    {
                        "id": "@9", "index": 4, "name": "--literal; $(not-a-command)",
                        "layout": layout("120x80,0,0,4"),
                        "panes": [{"id": "%4", "cwd": str(cwds[0])}],
                    },
                ],
            },
        ],
    }


class FakeTmux:
    def __init__(self, document, changing=False):
        self.document = document
        self.changing = changing
        self.topology_reads = 0
        self.calls = []

    def query(self, *args):
        self.calls.append(args)
        if args[:2] == ("list-windows", "-a"):
            self.topology_reads += 1
            return "changed" if self.changing and self.topology_reads > 1 else "stable"
        if args[0] == "list-sessions":
            return "".join(session["id"] + "\n" for session in self.document["sessions"])
        for session in self.document["sessions"]:
            if args[:3] == ("list-windows", "-t", session["id"]):
                return "".join(
                    f"{window['id']} {window['index']} {window['layout']}\n"
                    for window in session["windows"]
                )
            for window in session["windows"]:
                if args[:3] == ("list-panes", "-t", window["id"]):
                    return "".join(pane["id"] + "\n" for pane in window["panes"])
        raise AssertionError(args)

    def display(self, target, field):
        for session in self.document["sessions"]:
            if target == session["id"] and field == "session_name":
                return session["name"]
            for window in session["windows"]:
                if target == window["id"] and field == "window_name":
                    return window["name"]
                for pane in window["panes"]:
                    if target == pane["id"] and field == "pane_current_path":
                        return pane["cwd"]
        raise AssertionError((target, field))


class FakeHerdr:
    destination = {"session": "test-import"}

    def __init__(self, existing=(), failure=None):
        self.calls = []
        self.existing = list(existing)
        self.failure = failure
        self.workspaces = []
        self.tabs = {}
        self.panes = {}

    def root(self, workspace, label, cwd):
        tab_id = f"returned-tab-{len(self.tabs) + 1}"
        pane_id = self.pane(cwd, tab_id)
        self.tabs[tab_id] = {"workspace": workspace, "label": label}
        return {"tab": {"tab_id": tab_id}, "root_pane": {"pane_id": pane_id}}

    def pane(self, cwd, tab_id):
        pane_id = f"returned-pane-{len(self.panes) + 1}"
        self.panes[pane_id] = {"cwd": cwd, "tab": tab_id}
        return pane_id

    def call(self, *args):
        self.calls.append(args)
        if args[:2] == self.failure:
            raise importer.MigrationError("simulated Herdr failure")
        if args[:2] == ("workspace", "list"):
            return {"workspaces": [{"label": name} for name in self.existing] + self.workspaces}
        if args[:2] == ("workspace", "create"):
            workspace = {
                "workspace_id": f"returned-workspace-{len(self.workspaces) + 1}",
                "label": args[args.index("--label") + 1],
            }
            self.workspaces.append(workspace)
            root = self.root(workspace["workspace_id"], "default", args[args.index("--cwd") + 1])
            return {"workspace": workspace, **root}
        if args[:2] == ("tab", "rename"):
            if len(args) != 4:
                raise AssertionError("Herdr joins all arguments after the tab ID into its label")
            self.tabs[args[2]]["label"] = args[3]
            return {}
        if args[:2] == ("tab", "create"):
            return self.root(
                args[args.index("--workspace") + 1],
                args[args.index("--label") + 1],
                args[args.index("--cwd") + 1],
            )
        if args[:2] == ("pane", "split"):
            parent = self.panes[args[args.index("--pane") + 1]]
            pane_id = self.pane(args[args.index("--cwd") + 1], parent["tab"])
            return {"pane": {"pane_id": pane_id}}
        raise AssertionError(args)


class TmuxImportTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix="dotfiles-tmux-import-")
        self.addCleanup(temporary.cleanup)
        self.directory = Path(temporary.name)
        self.cwds = [self.directory / name for name in ("project one", "a; $literal", "third")]
        for cwd in self.cwds:
            cwd.mkdir()
        self.document = snapshot(self.cwds)
        self.path = self.directory / "snapshot.json"
        self.path.write_text(json.dumps(self.document), encoding="utf-8")

    def restore(self, client, document=None, prefix=""):
        plan = importer.make_plan(document or self.document, prefix)
        with contextlib.redirect_stderr(io.StringIO()):
            return importer.restore_snapshot(client, plan)

    def cli(self, args, client=None):
        output, errors = io.StringIO(), io.StringIO()
        with (
            contextlib.redirect_stdout(output),
            contextlib.redirect_stderr(errors),
            mock.patch.object(importer, "Herdr", return_value=client),
        ):
            status = importer.main(args)
        return status, output.getvalue(), errors.getvalue()

    def test_parser_accepts_real_tmux_checksum_and_split_geometry(self):
        tree = importer.LayoutParser(
            "008b,289x81,0,0{186x81,0,0,7,102x81,187,0,128}"
        ).parse()
        self.assertEqual(importer.leaves(tree), ["%7", "%128"])
        self.assertEqual(tree["direction"], "right")

    def test_invalid_layouts_are_rejected(self):
        for value in (
            "bad", "0000,120x80,0,0,1",
            layout("120x80,0,0,1trailing"),
            layout("120x80,0,0{60x80,0,0,1,60x80,61,0,2}"),
            layout("120x80,0,0{59x79,0,0,1,60x80,60,0,2}"),
            layout("120x80,0,0{120x80,0,0,1}"),
            layout("120x80,0,0{59x80,0,0,1,60x80,60,0,2"),
            layout("0x80,0,0,1"),
        ):
            with self.subTest(value=value), self.assertRaises(importer.MigrationError):
                importer.LayoutParser(value).parse()

    def test_balanced_multiway_conversion_preserves_order_and_proportions(self):
        children = ",".join(f"10x20,{index * 11},0,{index}" for index in range(12))
        source = importer.LayoutParser(layout(f"131x20,0,0{{{children}}}")).parse()
        tree = importer.binary_layout(source)
        shares = {}

        def walk(node, share):
            if "pane_id" in node:
                shares[node["pane_id"]] = share
            else:
                self.assertGreaterEqual(node["ratio"], 0.1)
                self.assertLessEqual(node["ratio"], 0.9)
                walk(node["first"], share * node["ratio"])
                walk(node["second"], share * (1 - node["ratio"]))

        walk(tree, 1)
        self.assertEqual(list(shares), [f"%{index}" for index in range(12)])
        for share in shares.values():
            self.assertAlmostEqual(share, 1 / 12)

    def test_snapshot_is_read_only_and_filters_exact_session_name_or_id(self):
        for selected in ([], ["$7"], ["project with spaces"]):
            with self.subTest(selected=selected):
                tmux = FakeTmux(self.document)
                result = importer.capture_snapshot(tmux, selected)
                self.assertEqual(result["sessions"], self.document["sessions"])
                self.assertTrue(all(call[0].startswith("list-") for call in tmux.calls))
                for session in result["sessions"]:
                    self.assertEqual(set(session), {"id", "name", "windows"})
                    for window in session["windows"]:
                        self.assertEqual(
                            set(window), {"id", "index", "name", "layout", "panes"}
                        )
                        for pane in window["panes"]:
                            self.assertEqual(set(pane), {"id", "cwd"})

    def test_unknown_session_and_changing_topology_do_not_produce_snapshots(self):
        for tmux, selected in (
            (FakeTmux(self.document), ["missing"]),
            (FakeTmux(self.document, changing=True), []),
        ):
            with self.subTest(selected=selected), self.assertRaises(importer.MigrationError):
                importer.capture_snapshot(tmux, selected)

    def test_snapshot_does_not_overwrite_and_is_private(self):
        output = self.directory / "new.json"
        with (
            mock.patch.object(importer, "Tmux", return_value=FakeTmux(self.document)),
            contextlib.redirect_stderr(io.StringIO()),
        ):
            self.assertEqual(importer.main(["snapshot", str(output)]), 0)
            self.assertEqual(output.stat().st_mode & 0o777, 0o600)
            before = output.read_bytes()
            self.assertEqual(importer.main(["snapshot", str(output)]), 1)
            self.assertEqual(output.read_bytes(), before)

    def test_display_keeps_embedded_and_trailing_newlines(self):
        with mock.patch.object(importer, "run", return_value="/directory\nname\n\n"):
            self.assertEqual(importer.Tmux().display("%1", "pane_current_path"), "/directory\nname\n")

    def test_restore_preserves_names_cwds_order_and_nested_split_ratios(self):
        client = FakeHerdr(existing=("unrelated",))
        document = copy.deepcopy(self.document)
        document["sessions"][0]["windows"].reverse()
        result = self.restore(client, document)
        self.assertEqual(result["counts"], {"workspaces": 1, "tabs": 2, "panes": 4})
        self.assertEqual(client.workspaces[0]["label"], "project with spaces")
        self.assertEqual(
            [tab["label"] for tab in client.tabs.values()],
            ["main window", "--literal; $(not-a-command)"],
        )
        self.assertEqual(
            [pane["cwd"] for pane in client.panes.values()],
            [str(cwd) for cwd in [*self.cwds, self.cwds[0]]],
        )
        splits = [call for call in client.calls if call[:2] == ("pane", "split")]
        self.assertEqual([call[call.index("--direction") + 1] for call in splits], ["right", "down"])
        self.assertAlmostEqual(float(splits[0][splits[0].index("--ratio") + 1]), 71 / 119)
        self.assertAlmostEqual(float(splits[1][splits[1].index("--ratio") + 1]), 39 / 79)
        self.assertEqual(
            result["workspaces"][0]["tabs"][0]["panes"],
            {"%1": "returned-pane-1", "%2": "returned-pane-2", "%3": "returned-pane-3"},
        )
        for call in client.calls:
            self.assertNotIn(call[1], ("close", "focus", "run", "send-keys", "send-text"))
            if call[1] in ("create", "split"):
                self.assertIn("--no-focus", call)

    def test_linked_tmux_windows_become_independent_tabs_in_each_workspace(self):
        document = copy.deepcopy(self.document)
        linked = copy.deepcopy(document["sessions"][0])
        linked.update(id="$8", name="linked session")
        document["sessions"].append(linked)
        client = FakeHerdr()
        result = self.restore(client, document)
        self.assertEqual(result["counts"], {"workspaces": 2, "tabs": 4, "panes": 8})
        self.assertNotEqual(
            result["workspaces"][0]["tabs"][0]["panes"]["%1"],
            result["workspaces"][1]["tabs"][0]["panes"]["%1"],
        )

    def test_duplicate_destination_aborts_before_creating_any_workspace(self):
        client = FakeHerdr(existing=("project with spaces",))
        with self.assertRaisesRegex(importer.MigrationError, "already contains"):
            self.restore(client)
        self.assertEqual(client.calls, [("workspace", "list")])
        result = self.restore(client, prefix="tmux-")
        self.assertEqual(result["counts"]["workspaces"], 1)
        with self.assertRaisesRegex(importer.MigrationError, "already contains"):
            self.restore(client, prefix="tmux-")
        self.assertEqual(len(client.workspaces), 1)

    def test_missing_directories_and_unrepresentable_ratios_fail_preflight(self):
        missing = copy.deepcopy(self.document)
        missing["sessions"][0]["windows"][1]["panes"][0]["cwd"] = str(self.directory / "missing")
        extreme = copy.deepcopy(self.document)
        window = extreme["sessions"][0]["windows"][0]
        window["layout"] = layout("101x80,0,0{5x80,0,0,1,95x80,6,0,2}")
        window["panes"].pop()
        for document, error in ((missing, "directory unavailable"), (extreme, "10%-90%")):
            with self.subTest(error=error), self.assertRaisesRegex(importer.MigrationError, error):
                importer.make_plan(document, "")

    def test_imported_names_cannot_retarget_global_herdr_options(self):
        for label in ("--session=another", "--session", "--help", "--version", "--remote=host"):
            document = copy.deepcopy(self.document)
            document["sessions"][0]["windows"][0]["name"] = label
            with self.subTest(label=label), self.assertRaisesRegex(importer.MigrationError, "CLI flags"):
                importer.make_plan(document, "")

    def test_invalid_snapshot_types_ids_and_inventories_are_rejected(self):
        invalid = [None, {}, {"format": "tmux-to-herdr", "version": True}, {**self.document, "sessions": []}]
        for field, value in (("version", 2), ("sessions", "not a list")):
            invalid.append({**self.document, field: value})
        for change in ("duplicate-pane", "missing-pane", "bad-id", "relative-cwd", "duplicate-index", "duplicate-session"):
            document = copy.deepcopy(self.document)
            session = document["sessions"][0]
            window = session["windows"][0]
            if change == "duplicate-pane":
                window["panes"].append(window["panes"][0])
            elif change == "missing-pane":
                window["panes"].pop()
            elif change == "bad-id":
                window["panes"][0]["id"] = "1"
            elif change == "relative-cwd":
                window["panes"][0]["cwd"] = "relative"
            elif change == "duplicate-index":
                session["windows"][1]["index"] = 1
            else:
                document["sessions"].append(session)
            invalid.append(document)
        for document in invalid:
            with self.subTest(document=document), self.assertRaises(importer.MigrationError):
                importer.validate_snapshot(document)

    def test_partial_import_is_reported_and_never_deletes_workspaces(self):
        client = FakeHerdr(failure=("pane", "split"))
        errors = io.StringIO()
        with contextlib.redirect_stderr(errors), self.assertRaises(importer.MigrationError):
            importer.restore_snapshot(client, importer.make_plan(self.document, ""))
        self.assertIn("partial workspaces may remain", errors.getvalue())
        self.assertIn("returned-workspace-1", errors.getvalue())
        self.assertFalse(any("close" in call for call in client.calls))

    def test_dry_run_only_reads_destination_and_prints_the_plan(self):
        client = FakeHerdr()
        status, output, errors = self.cli(
            ["restore", str(self.path), "--herdr-session", "test-import", "--dry-run"],
            client,
        )
        self.assertEqual(status, 0, errors)
        report = json.loads(output)
        self.assertTrue(report["dry_run"])
        self.assertEqual(report["counts"], {"workspaces": 1, "tabs": 2, "panes": 4})
        self.assertEqual(client.calls, [("workspace", "list")])

    def test_restore_requires_an_explicit_destination(self):
        with contextlib.redirect_stderr(io.StringIO()), self.assertRaises(SystemExit) as error:
            importer.main(["restore", str(self.path)])
        self.assertEqual(error.exception.code, 2)

    def test_explicit_destination_discards_inherited_socket_and_pane_context(self):
        with mock.patch.dict(os.environ, {
            "HERDR_BIN_PATH": "/custom/herdr",
            "HERDR_SESSION": "wrong",
            "HERDR_SOCKET_PATH": "/wrong.sock",
            "HERDR_PANE_ID": "wrong-pane",
            "HERDR_ACTIVE_WORKSPACE_ID": "wrong-workspace",
        }):
            client = importer.Herdr(session="chosen")
            self.assertEqual(client.command, ["/custom/herdr", "--session", "chosen"])
            for key in importer.CALLER_CONTEXT:
                self.assertNotIn(key, client.env)
            client = importer.Herdr(socket_path="/chosen.sock")
            self.assertEqual(client.command, ["/custom/herdr"])
            self.assertEqual(client.env["HERDR_SOCKET_PATH"], "/chosen.sock")
            self.assertNotIn("HERDR_SESSION", client.env)

    def test_malformed_herdr_responses_are_errors_not_empty_successes(self):
        for response in ("not json", "[]", "{}", '{"result": []}', '{"error": "failed"}'):
            with (
                self.subTest(response=response),
                mock.patch.object(importer, "run", return_value=response),
                self.assertRaises(importer.MigrationError),
            ):
                importer.Herdr(session="test").call("workspace", "list")
        for response in ({}, {"pane": {}}, {"pane": {"pane_id": 3}}):
            with self.subTest(response=response), self.assertRaises(importer.MigrationError):
                importer.identifier(response, "pane", "pane_id")

    def test_subprocess_errors_surface_without_retries(self):
        for error in (
            FileNotFoundError("missing binary"),
            subprocess.TimeoutExpired(["herdr"], 30),
            subprocess.CalledProcessError(1, ["herdr"], "", "server unavailable"),
        ):
            with (
                self.subTest(error=error),
                mock.patch.object(importer.subprocess, "run", side_effect=error) as run,
                self.assertRaises(importer.MigrationError),
            ):
                importer.run(["herdr", "workspace", "list"])
            self.assertEqual(run.call_count, 1)

    def test_shell_entrypoint_exposes_both_commands(self):
        result = subprocess.run(
            [str(HELPER), "--help"], capture_output=True, text=True, timeout=10, check=False
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("snapshot", result.stdout)
        self.assertIn("restore", result.stdout)


@unittest.skipUnless(
    os.environ.get("HERDR_IMPORT_INTEGRATION") == "1",
    "Set HERDR_IMPORT_INTEGRATION=1 for isolated tmux/Herdr round-trip coverage",
)
class TmuxImportIntegrationTests(unittest.TestCase):
    def test_real_snapshot_restore_preserves_topology_and_leaves_source_running(self):
        herdr_bin = shutil.which("herdr")
        tmux_bin = shutil.which("tmux")
        if not herdr_bin or not tmux_bin:
            self.fail("The integration test requires installed herdr and tmux binaries")
        temporary = tempfile.TemporaryDirectory(prefix="herdr-import-", dir="/tmp")
        self.addCleanup(temporary.cleanup)
        directory = Path(temporary.name)
        home = directory / "home"
        config = home / ".config/herdr/config.toml"
        config.parent.mkdir(parents=True)
        config.write_text(
            'onboarding = false\n'
            '[update]\nversion_check = false\nmanifest_check = false\n'
            '[terminal]\ndefault_shell = "/bin/sh"\nshell_mode = "non_login"\n'
            '[server]\nheadless_cols = 200\nheadless_rows = 100\n',
            encoding="utf-8",
        )
        env = {
            key: value for key, value in os.environ.items()
            if not key.startswith("HERDR_") and key != "TMUX"
        }
        env.update(
            HOME=str(home), HERDR_CONFIG_PATH=str(config),
            XDG_CONFIG_HOME=str(home / ".config"),
            XDG_STATE_HOME=str(home / ".local/state"),
            HERDR_BIN_PATH=herdr_bin, TMUX_BIN_PATH=tmux_bin, SHELL="/bin/sh",
            PATH=str(Path(sys.executable).parent) + os.pathsep + env.get("PATH", ""),
        )
        environment = mock.patch.dict(os.environ, env, clear=True)
        environment.start()
        self.addCleanup(environment.stop)
        cwds = [directory / name for name in ("project one", "project two", "third")]
        for cwd in cwds:
            cwd.mkdir()

        tmux = importer.Tmux(str(directory / "tmux.sock"))
        tmux.command += ["-f", "/dev/null"]
        tmux.query(
            "new-session", "-d", "-s", "alpha", "-n", "main window",
            "-x", "200", "-y", "100", "-c", str(cwds[0]), "/bin/sh",
        )
        self.addCleanup(tmux.query, "kill-server")
        tmux.query("set-window-option", "-g", "automatic-rename", "off")
        pane = tmux.query(
            "split-window", "-h", "-t", "alpha:0", "-l", "40%",
            "-c", str(cwds[1]), "-P", "-F", "#{pane_id}", "/bin/sh",
        ).strip()
        tmux.query(
            "split-window", "-v", "-t", pane, "-l", "40%",
            "-c", str(cwds[2]), "/bin/sh",
        )
        tmux.query(
            "new-window", "-t", "alpha:", "-n", "--literal; $(not-a-command)",
            "-c", str(cwds[0]), "/bin/sh",
        )
        tmux.query(
            "new-session", "-d", "-s", "beta", "-n", "third window",
            "-c", str(cwds[1]), "/bin/sh",
        )
        source_topology = tmux.query("list-windows", "-a", "-F", importer.TOPOLOGY_FORMAT)
        source_processes = tmux.query("list-panes", "-a", "-F", "#{pane_id} #{pane_pid}")

        session = "roundtrip"
        client = importer.Herdr(session=session)
        log_path = directory / "server.log"
        log = log_path.open("wb")
        self.addCleanup(log.close)
        server = subprocess.Popen(
            [herdr_bin, "--session", session, "server"], env=env,
            stdin=subprocess.DEVNULL, stdout=log, stderr=subprocess.STDOUT,
        )

        def stop_server():
            if server.poll() is not None:
                return
            try:
                importer.run([*client.command, "server", "stop"], env=client.env)
            finally:
                try:
                    server.wait(timeout=10)
                except subprocess.TimeoutExpired:
                    server.terminate()
                    server.wait(timeout=10)

        self.addCleanup(stop_server)
        deadline = time.monotonic() + 15
        last_error = None
        while time.monotonic() < deadline:
            if server.poll() is not None:
                self.fail(log_path.read_text(encoding="utf-8", errors="replace"))
            try:
                client.call("workspace", "list")
                break
            except importer.MigrationError as error:
                last_error = error
                time.sleep(0.1)
        else:
            self.fail(f"Isolated Herdr did not start: {last_error}")

        existing = client.call(
            "workspace", "create", "--label", "untouched",
            "--cwd", str(cwds[0]), "--focus",
        )["workspace"]["workspace_id"]
        original_count = len(client.call("workspace", "list")["workspaces"])
        snapshot_path = directory / "snapshot.json"

        def script(*args):
            return subprocess.run(
                [str(HELPER), *args], env=env, capture_output=True,
                text=True, timeout=90, check=False,
            )

        captured = script("snapshot", str(snapshot_path), "--tmux-socket", str(directory / "tmux.sock"))
        self.assertEqual(captured.returncode, 0, captured.stderr)
        document = json.loads(snapshot_path.read_text(encoding="utf-8"))
        self.assertEqual(importer.counts(document["sessions"]), {"workspaces": 2, "tabs": 3, "panes": 5})
        plan = importer.make_plan(document, "")
        restored = script("restore", str(snapshot_path), "--herdr-session", session)
        self.assertEqual(restored.returncode, 0, restored.stderr)
        report = json.loads(restored.stdout)
        self.assertEqual(report["counts"], {"workspaces": 2, "tabs": 3, "panes": 5})
        workspaces = client.call("workspace", "list")["workspaces"]
        self.assertEqual(len(workspaces), original_count + 2)
        self.assertTrue(next(workspace for workspace in workspaces if workspace["workspace_id"] == existing)["focused"])

        def planned_splits(node):
            if "pane_id" in node:
                return []
            return [
                (node["direction"], node["ratio"]),
                *planned_splits(node["first"]), *planned_splits(node["second"]),
            ]

        for source, target in zip(plan, report["workspaces"]):
            workspace = next(row for row in workspaces if row["workspace_id"] == target["workspace_id"])
            self.assertEqual(workspace["label"], source["name"])
            tabs = client.call("tab", "list", "--workspace", target["workspace_id"])["tabs"]
            self.assertEqual([tab["label"] for tab in tabs], [window["name"] for window in source["windows"]])
            for window, tab in zip(source["windows"], target["tabs"]):
                self.assertEqual(set(tab["panes"]), set(window["panes"]))
                for source_pane, target_pane in tab["panes"].items():
                    pane = client.call("pane", "get", target_pane)["pane"]
                    self.assertEqual(pane["cwd"], window["panes"][source_pane])
                root = tab["panes"][importer.first_pane(window["layout"])]
                native = client.call("pane", "layout", "--pane", root)["layout"]
                expected = planned_splits(window["layout"])
                self.assertEqual(len(native["panes"]), len(window["panes"]))
                self.assertEqual(len(native["splits"]), len(expected))
                for actual, (direction, ratio) in zip(native["splits"], expected):
                    self.assertEqual(actual["direction"], direction)
                    self.assertAlmostEqual(actual["ratio"], ratio, places=6)

        repeated = script("restore", str(snapshot_path), "--herdr-session", session)
        self.assertNotEqual(repeated.returncode, 0)
        self.assertIn("already contains", repeated.stderr)
        self.assertEqual(len(client.call("workspace", "list")["workspaces"]), original_count + 2)
        self.assertEqual(tmux.query("list-windows", "-a", "-F", importer.TOPOLOGY_FORMAT), source_topology)
        self.assertEqual(tmux.query("list-panes", "-a", "-F", "#{pane_id} #{pane_pid}"), source_processes)


if __name__ == "__main__":
    unittest.main()
