import os
from pathlib import Path
import re
import shutil
import subprocess
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[2]
INSTALLER = re.search(
    r"(?ms)^install_tmux_plugins\(\) \{.*?^\}",
    (ROOT / "setup.sh").read_text(encoding="utf-8"),
).group()

HARNESS = r"""
set -e
command_exists() { command -v "$1" >/dev/null 2>&1; }
print_header() { :; }
print_success() { printf 'success: %s\n' "$1"; }
print_warning() { printf 'warning: %s\n' "$1"; }
print_error() { printf 'error: %s\n' "$1"; }
"""

MOCK_TMUX = r"""
command_exists() {
    if [ "$1" = tmux ]; then
        [ "$TMUX_TEST_PRESENT" = 1 ]
    else
        command -v "$1" >/dev/null 2>&1
    fi
}
tmux() {
    printf 'tmux: %s\n' "$*" >> "$TMUX_TEST_CALLS"
    [ "$TMUX_TEST_INIT_FAIL" = 0 ]
}
"""


class TmuxPluginSetupTests(unittest.TestCase):
    def run_installer(self, *, present=True, init_fail=False, install_fail=False):
        with tempfile.TemporaryDirectory(prefix="df-tmux-") as temporary:
            home = Path(temporary)
            calls_path = home / "calls"
            installer = home / ".tmux/plugins/tpm/bin/install_plugins"
            installer.parent.mkdir(parents=True)
            installer.write_text(
                "#!/bin/sh\n"
                "printf 'installer\\n' >> \"$TMUX_TEST_CALLS\"\n"
                '[ "$TMUX_TEST_INSTALL_FAIL" = 0 ]\n',
                encoding="utf-8",
            )
            installer.chmod(0o755)
            env = {
                **os.environ,
                "HOME": str(home),
                "TMUX_TEST_CALLS": str(calls_path),
                "TMUX_TEST_PRESENT": "1" if present else "0",
                "TMUX_TEST_INIT_FAIL": "1" if init_fail else "0",
                "TMUX_TEST_INSTALL_FAIL": "1" if install_fail else "0",
            }
            result = subprocess.run(
                ["bash", "-c", HARNESS + MOCK_TMUX + INSTALLER + "\ninstall_tmux_plugins\n"],
                env=env, capture_output=True, text=True, timeout=10, check=False,
            )
            calls = calls_path.read_text().splitlines() if calls_path.exists() else []
            return result, calls

    def test_missing_tmux_warns_and_does_not_run_tpm(self):
        result, calls = self.run_installer(present=False)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(calls, [])
        self.assertIn("warning:", result.stdout)
        self.assertIn("rerun ./setup.sh", result.stdout)
        self.assertNotIn("success:", result.stdout)

    def test_initialization_failure_does_not_run_tpm_or_report_success(self):
        result, calls = self.run_installer(init_fail=True)
        self.assertNotEqual(result.returncode, 0)
        self.assertNotIn("installer", calls)
        self.assertIn("Could not initialize tmux", result.stdout)
        self.assertNotIn("success:", result.stdout)

    def test_plugin_install_failure_remains_fatal(self):
        result, calls = self.run_installer(install_fail=True)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("installer", calls)
        self.assertIn("Failed to install one or more tmux plugins", result.stdout)
        self.assertNotIn("success:", result.stdout)


@unittest.skipUnless(shutil.which("tmux"), "tmux is required for isolated setup tests")
class TmuxPluginSetupIntegrationTests(unittest.TestCase):
    def setUp(self):
        self.tmux_bin = shutil.which("tmux")
        temporary = tempfile.TemporaryDirectory(prefix="df-tmux-")
        self.addCleanup(temporary.cleanup)
        self.home = Path(temporary.name)
        self.socket = self.home / "socket"
        self.env = {
            **os.environ,
            "HOME": str(self.home),
            "XDG_CONFIG_HOME": str(self.home / ".config"),
            "SHELL": "/bin/sh",
            "TERM": "xterm-256color",
            "TMUX_TEST_REAL_TMUX": self.tmux_bin,
            "TMUX_TEST_SOCKET": str(self.socket),
        }
        for name in ("TMUX", "TMUX_PANE", "TMUX_PLUGIN_MANAGER_PATH"):
            self.env.pop(name, None)

        (self.home / ".tmux.conf").symlink_to(ROOT / "tmux/.tmux.conf")
        bin_dir = self.home / "bin"
        bin_dir.mkdir()
        wrapper = bin_dir / "tmux"
        wrapper.write_text(
            "#!/bin/sh\n"
            'exec "$TMUX_TEST_REAL_TMUX" -S "$TMUX_TEST_SOCKET" '
            '-f "$HOME/.tmux.conf" "$@"\n',
            encoding="utf-8",
        )
        wrapper.chmod(0o755)
        self.env["PATH"] = str(bin_dir) + os.pathsep + self.env["PATH"]

        tpm = self.home / ".tmux/plugins/tpm"
        (tpm / "bin").mkdir(parents=True)
        entrypoint = tpm / "tpm"
        entrypoint.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
        entrypoint.chmod(0o755)
        installer = tpm / "bin/install_plugins"
        # Match TPM's lookup without its background initialization or network access.
        installer.write_text(
            r"""#!/bin/sh
path="$(tmux start-server \; show-environment -g TMUX_PLUGIN_MANAGER_PATH | cut -f2 -d=)/"
if [ "$path" = / ]; then
    printf 'FATAL: Tmux Plugin Manager not configured in tmux.conf\n' >&2
    exit 1
fi
printf 'plugin path: %s\n' "$path"
""",
            encoding="utf-8",
        )
        installer.chmod(0o755)
        self.addCleanup(self.stop_server)

    def tmux(self, *arguments):
        return subprocess.run(
            [self.tmux_bin, "-S", str(self.socket), "-f", "/dev/null", *arguments],
            env=self.env, capture_output=True, text=True, timeout=10, check=False,
        )

    def stop_server(self):
        self.tmux("kill-server")

    def run_installer(self):
        return subprocess.run(
            ["bash", "-c", HARNESS + INSTALLER + "\ninstall_tmux_plugins\n"],
            env=self.env, capture_output=True, text=True, timeout=10, check=False,
        )

    def assert_installed(self, result):
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn(f"plugin path: {self.home}/.tmux/plugins/", result.stdout)
        self.assertIn("tmux plugins installed", result.stdout)
        self.assertNotIn("unknown variable", result.stderr)

    def test_fresh_setup_initializes_tpm_without_an_interactive_session(self):
        self.assertFalse(self.socket.exists())
        self.assert_installed(self.run_installer())

    def test_existing_server_is_initialized_without_restarting_its_panes(self):
        started = self.tmux(
            "new-session", "-d", "-s", "existing", "-c", str(self.home), "/bin/cat",
        )
        self.assertEqual(started.returncode, 0, started.stderr)
        before = self.tmux("list-panes", "-a", "-F", "#{pane_id}:#{pane_pid}")
        self.assertEqual(before.returncode, 0, before.stderr)

        self.assert_installed(self.run_installer())

        after = self.tmux("list-panes", "-a", "-F", "#{pane_id}:#{pane_pid}")
        self.assertEqual(after.returncode, 0, after.stderr)
        self.assertEqual(after.stdout, before.stdout)


if __name__ == "__main__":
    unittest.main()
