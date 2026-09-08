import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import textwrap
import unittest


LAUNCHER = (
    Path(__file__).resolve().parents[2]
    / "herdr/.config/herdr/scripts/new-copilot"
)
LAUNCH_COMMAND = "exec env HERDR_AGENT=copilot zsh -ic 'agency copilot --yolo'"
MOCK_HERDR = textwrap.dedent(
    """
    import json
    import os
    import sys

    args = sys.argv[1:]
    mode = os.environ.get("HERDR_TEST_MODE", "ok")
    with open(os.environ["HERDR_TEST_LOG"], "a", encoding="utf-8") as log:
        log.write(json.dumps(args) + "\\n")

    if args[:2] == ["tab", "create"]:
        if mode in {"create-failed", "notification-failed"}:
            sys.exit(1)
        if mode == "invalid-json":
            print("not json")
        else:
            pane_id = {"empty-pane": "", "numeric-pane": 7}.get(mode, "w7:p99")
            print(json.dumps({"result": {"root_pane": {"pane_id": pane_id}}}))
    elif args[:2] == ["pane", "run"]:
        if mode == "launch-failed":
            sys.exit(1)
    elif args[:2] == ["notification", "show"]:
        if mode == "notification-failed":
            sys.exit(1)
    else:
        sys.exit("unexpected Herdr command")
    """
)


class HerdrLauncherTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix="dotfiles-herdr-")
        self.addCleanup(temporary.cleanup)
        self.directory = Path(temporary.name)
        self.log = self.directory / "calls.jsonl"
        self.cwd = self.directory / "project with spaces"
        self.cwd.mkdir()
        self.herdr = self.directory / "herdr"
        self.herdr.write_text("#!" + sys.executable + "\n" + MOCK_HERDR, encoding="utf-8")
        self.herdr.chmod(0o755)
        self.env = {
            **os.environ,
            "HERDR_BIN_PATH": str(self.herdr),
            "HERDR_SOCKET_PATH": str(self.directory / "herdr.sock"),
            "HERDR_ACTIVE_WORKSPACE_ID": "w7",
            "HERDR_ACTIVE_PANE_CWD": str(self.cwd),
            "HERDR_TEST_LOG": str(self.log),
        }

    def run_launcher(self, *, mode="ok", unset=(), extra_args=(), overrides=None):
        if self.log.exists():
            self.log.unlink()
        env = {**self.env, "HERDR_TEST_MODE": mode, **(overrides or {})}
        for key in unset:
            env.pop(key, None)
        result = subprocess.run(
            [str(LAUNCHER), *extra_args],
            env=env,
            capture_output=True,
            text=True,
            timeout=10,
            check=False,
        )
        calls = []
        if self.log.exists():
            calls = [json.loads(line) for line in self.log.read_text().splitlines()]
        return result, calls

    def test_launches_in_the_requested_workspace_and_returned_pane(self):
        result, calls = self.run_launcher()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(
            calls,
            [
                [
                    "tab", "create",
                    "--workspace", "w7",
                    "--cwd", str(self.cwd),
                    "--label", "copilot",
                ],
                ["pane", "run", "w7:p99", LAUNCH_COMMAND],
            ],
        )

    def test_no_herdr_context_cannot_control_a_default_session(self):
        result, calls = self.run_launcher(unset=("HERDR_SOCKET_PATH",))
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(calls, [])
        self.assertIn("Herdr keybinding", result.stderr)

    def test_missing_workspace_or_directory_does_not_create_a_tab(self):
        for key in ("HERDR_ACTIVE_WORKSPACE_ID", "HERDR_ACTIVE_PANE_CWD"):
            with self.subTest(key=key):
                result, calls = self.run_launcher(unset=(key,))
                self.assertNotEqual(result.returncode, 0)
                self.assertEqual(len(calls), 1)
                self.assertEqual(calls[0][:2], ["notification", "show"])

    def test_unexpected_arguments_do_not_create_a_tab(self):
        result, calls = self.run_launcher(extra_args=("unexpected",))
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(calls[0][:2], ["notification", "show"])
        self.assertEqual(len(calls), 1)

    def test_missing_python_does_not_create_a_tab(self):
        result, calls = self.run_launcher(overrides={"PATH": str(self.directory)})
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("python3 is required", result.stderr)
        self.assertEqual(calls[0][:2], ["notification", "show"])
        self.assertEqual(len(calls), 1)

    def test_creation_and_response_errors_never_send_a_launch_command(self):
        for mode in ("create-failed", "invalid-json", "empty-pane", "numeric-pane"):
            with self.subTest(mode=mode):
                result, calls = self.run_launcher(mode=mode)
                self.assertNotEqual(result.returncode, 0)
                self.assertEqual(
                    [call[:2] for call in calls],
                    [["tab", "create"], ["notification", "show"]],
                )

    def test_launch_errors_are_reported(self):
        result, calls = self.run_launcher(mode="launch-failed")
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(
            [call[:2] for call in calls],
            [["tab", "create"], ["pane", "run"], ["notification", "show"]],
        )

    def test_notification_failure_still_reports_an_error(self):
        result, calls = self.run_launcher(mode="notification-failed")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("could not display the error notification", result.stderr)
        self.assertEqual(len(calls), 2)


if __name__ == "__main__":
    unittest.main()
