import os
from pathlib import Path
import re
import subprocess
import tempfile
import unittest


SETUP = Path(__file__).resolve().parents[2] / "setup.sh"
INSTALLER = re.search(
    r"(?ms)^install_pstack_skills\(\) \{.*?^\}",
    SETUP.read_text(encoding="utf-8"),
).group()
SKILLS = ("unslop", "bro", "show-me-your-work", "teach", "why", "how")
ADD_ARGS = [
    "--yes", "--", "skills", "add",
    "https://github.com/cursor/plugins/tree/main/pstack",
    "--global", "--agent", "github-copilot", "--skill",
]

# Extract the installer function: sourcing setup.sh would run the full install.
HARNESS = r"""
set -e
command_exists() {
    case "$1" in
        copilot) [ "$PSTACK_TEST_COPILOT" = 1 ] ;;
        npx) [ "$PSTACK_TEST_NPX" = 1 ] ;;
        *) command -v "$1" >/dev/null 2>&1 ;;
    esac
}
print_header() { :; }
print_success() { printf 'success: %s\n' "$1"; }
print_warning() { printf 'warning: %s\n' "$1"; }
npx() {
    printf '%s\n' "$@" >> "$PSTACK_TEST_CALLS"
    [ "$PSTACK_TEST_INSTALL_FAIL" = 0 ]
}
"""


class PstackSkillSetupTests(unittest.TestCase):
    def run_installer(self, *, existing=(), copilot=True, npx=True, install_fail=False):
        with tempfile.TemporaryDirectory(prefix="dotfiles-pstack-install-") as temporary:
            home = Path(temporary)
            calls_path = home / "calls"
            existing_files = []
            for directory, skill in existing:
                path = home / directory / "skills" / skill / "SKILL.md"
                path.parent.mkdir(parents=True)
                path.write_text(f"custom {skill}\n", encoding="utf-8")
                existing_files.append(path)
            env = {
                **os.environ,
                "HOME": str(home),
                "PSTACK_TEST_CALLS": str(calls_path),
                "PSTACK_TEST_COPILOT": "1" if copilot else "0",
                "PSTACK_TEST_NPX": "1" if npx else "0",
                "PSTACK_TEST_INSTALL_FAIL": "1" if install_fail else "0",
            }
            result = subprocess.run(
                ["bash", "-c", HARNESS + INSTALLER + "\ninstall_pstack_skills\n"],
                env=env, capture_output=True, text=True, timeout=10, check=False,
            )
            calls = calls_path.read_text().splitlines() if calls_path.exists() else []
            for path in existing_files:
                self.assertEqual(
                    path.read_text(encoding="utf-8"), f"custom {path.parent.name}\n",
                )
            return result, calls

    def test_installs_only_selected_skills_globally_for_copilot(self):
        result, calls = self.run_installer()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(calls, ADD_ARGS + list(SKILLS) + ["--yes"])
        self.assertIn("pstack skills installed for GitHub Copilot", result.stdout)

    def test_installs_only_missing_skills_and_preserves_both_locations(self):
        result, calls = self.run_installer(
            existing=((".agents", "unslop"), (".copilot", "bro")),
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(calls, ADD_ARGS + list(SKILLS[2:]) + ["--yes"])
        self.assertIn("unslop skill already present", result.stdout)
        self.assertIn("bro skill already present", result.stdout)

    def test_skips_installer_when_all_skills_exist_even_without_tools(self):
        existing = tuple(
            (".agents" if index % 2 else ".copilot", skill)
            for index, skill in enumerate(SKILLS)
        )
        result, calls = self.run_installer(existing=existing, copilot=False, npx=False)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(calls, [])
        self.assertEqual(result.stdout.count("leaving it unchanged"), len(SKILLS))
        self.assertNotIn("warning:", result.stdout)

    def test_missing_tools_are_reported_without_attempting_install(self):
        for options in ({"copilot": False}, {"npx": False}):
            with self.subTest(options=options):
                result, calls = self.run_installer(**options)
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertEqual(calls, [])
                self.assertIn("warning:", result.stdout)
                self.assertIn("rerun ./setup.sh", result.stdout)

    def test_install_failure_does_not_report_success(self):
        result, calls = self.run_installer(install_fail=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(calls, ADD_ARGS + list(SKILLS) + ["--yes"])
        self.assertIn("installation failed", result.stdout)
        self.assertNotIn("success:", result.stdout)


if __name__ == "__main__":
    unittest.main()
