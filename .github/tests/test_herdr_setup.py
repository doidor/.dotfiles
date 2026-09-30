import json
import os
from pathlib import Path
import re
import subprocess
import tempfile
import unittest


SETUP = Path(__file__).resolve().parents[2] / "setup.sh"
INSTALLER = re.search(
    r"(?ms)^install_herdr_nvim_plugin\(\) \{.*?^\}",
    SETUP.read_text(encoding="utf-8"),
).group()

# Extract the installer function: sourcing setup.sh would run the full install.
HARNESS = r"""
set -e
command_exists() {
    if [ "$1" = herdr ]; then
        [ "$HERDR_TEST_PRESENT" = 1 ]
    else
        command -v "$1" >/dev/null 2>&1
    fi
}
print_header() { :; }
print_success() { printf 'success: %s\n' "$1"; }
print_warning() { printf 'warning: %s\n' "$1"; }
print_error() { printf 'error: %s\n' "$1"; }
herdr() {
    printf '%s\n' "$*" >> "$HERDR_TEST_CALLS"
    case "$*" in
        "plugin list --plugin chmarax.herdr-nvim --json")
            [ "$HERDR_TEST_LIST_FAIL" = 0 ] || return 1
            printf '%s\n' "$HERDR_TEST_RESPONSE"
            ;;
        "plugin install ChmaraX/herdr-nvim --yes")
            [ "$HERDR_TEST_INSTALL_FAIL" = 0 ]
            ;;
        *)
            printf 'Unexpected Herdr call: %s\n' "$*" >&2
            return 2
            ;;
    esac
}
"""
LIST_CALL = "plugin list --plugin chmarax.herdr-nvim --json"
INSTALL_CALL = "plugin install ChmaraX/herdr-nvim --yes"


class HerdrPluginSetupTests(unittest.TestCase):
    def run_installer(
        self, *, plugins=(), present=True, list_fail=False, install_fail=False, response=None
    ):
        with tempfile.TemporaryDirectory(prefix="dotfiles-herdr-install-") as temporary:
            calls_path = Path(temporary) / "calls"
            env = {
                **os.environ,
                "HERDR_TEST_CALLS": str(calls_path),
                "HERDR_TEST_PRESENT": "1" if present else "0",
                "HERDR_TEST_LIST_FAIL": "1" if list_fail else "0",
                "HERDR_TEST_INSTALL_FAIL": "1" if install_fail else "0",
                "HERDR_TEST_RESPONSE": response if response is not None else json.dumps(
                    {"result": {"plugins": list(plugins)}}
                ),
            }
            result = subprocess.run(
                ["bash", "-c", HARNESS + INSTALLER + "\ninstall_herdr_nvim_plugin\n"],
                env=env, capture_output=True, text=True, timeout=10, check=False,
            )
            calls = calls_path.read_text().splitlines() if calls_path.exists() else []
            return result, calls

    def test_installs_missing_plugin(self):
        result, calls = self.run_installer()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(calls, [LIST_CALL, INSTALL_CALL])
        self.assertIn("herdr-nvim installed", result.stdout)

    def test_preserves_installed_plugin_and_disabled_state(self):
        for enabled in (True, False):
            with self.subTest(enabled=enabled):
                plugin = {"plugin_id": "chmarax.herdr-nvim", "enabled": enabled}
                result, calls = self.run_installer(plugins=(plugin,))
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertEqual(calls, [LIST_CALL])
                if enabled:
                    self.assertIn("already installed", result.stdout)
                else:
                    self.assertIn("plugin enable chmarax.herdr-nvim", result.stdout)

    def test_skips_when_herdr_is_not_installed(self):
        result, calls = self.run_installer(present=False)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(calls, [])
        self.assertIn("rerun ./setup.sh", result.stdout)

    def test_list_and_install_errors_do_not_report_success(self):
        for options, expected_calls in (
            ({"list_fail": True}, [LIST_CALL]),
            ({"response": "invalid JSON"}, [LIST_CALL]),
            ({"plugins": ({"plugin_id": "other", "enabled": True},)}, [LIST_CALL]),
            ({"install_fail": True}, [LIST_CALL, INSTALL_CALL]),
        ):
            with self.subTest(options=options):
                result, calls = self.run_installer(**options)
                self.assertNotEqual(result.returncode, 0)
                self.assertEqual(calls, expected_calls)
                self.assertIn("error:", result.stdout)
                self.assertNotIn("success:", result.stdout)


if __name__ == "__main__":
    unittest.main()
