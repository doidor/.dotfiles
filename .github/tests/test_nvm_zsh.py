import os
from pathlib import Path
import subprocess
import tempfile
import textwrap
import unittest


ZSHRC = Path(__file__).resolve().parents[2] / "zsh/.zshrc"
NVM_CONFIG = (
    ZSHRC.read_text(encoding="utf-8")
    .split("# NVM (Node Version Manager)\n", 1)[1]
    .split("# Direnv\n", 1)[0]
)
MOCK_NVM = textwrap.dedent(
    """
    nvm_find_nvmrc() {
      local directory="$PWD"
      while [ -n "$directory" ] && [ "$directory" != "/" ]; do
        if [ -f "$directory/.nvmrc" ]; then
          print -r -- "$directory/.nvmrc"
          return
        fi
        directory="${directory:h}"
      done
    }

    nvm() {
      case "$1" in
        version)
          case "${2-}" in
            "") print -r -- "$TEST_NODE_VERSION" ;;
            default) print -r -- "v22.0.0" ;;
            v20.0.0|v22.0.0) print -r -- "$2" ;;
            *) print -r -- "N/A"; return 3 ;;
          esac
          ;;
        use|install)
          print -r -- "$*" >> "$TEST_NVM_LOG"
          if [ "$TEST_NVM_FAIL" = "$1" ]; then
            print -u2 -- "nvm $1 failed"
            return 1
          fi
          if [ "${2-}" = "default" ]; then
            TEST_NODE_VERSION="v22.0.0"
          else
            TEST_NODE_VERSION="$(cat "$(nvm_find_nvmrc)")"
          fi
          ;;
        *) print -u2 -- "Unexpected nvm command: $*"; return 1 ;;
      esac
    }
    """
)


class NvmZshTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix="dotfiles-nvm-zsh-")
        self.addCleanup(temporary.cleanup)
        self.directory = Path(temporary.name)
        self.project = self.directory / "project with spaces"
        self.child = self.project / "child"
        self.child.mkdir(parents=True)
        self.nvmrc = self.project / ".nvmrc"
        self.nvmrc.write_text("v20.0.0\n", encoding="utf-8")
        self.nvm_dir = self.directory / ".nvm"
        self.nvm_dir.mkdir()
        self.nvm_script = self.nvm_dir / "nvm.sh"
        self.nvm_script.write_text(MOCK_NVM, encoding="utf-8")
        self.log = self.directory / "nvm.log"

    def run_shell(self, script="", *, cwd=None, current="v22.0.0", fail=""):
        if self.log.exists():
            self.log.unlink()
        result = subprocess.run(
            ["zsh", "-dfc", NVM_CONFIG + "\n" + script],
            cwd=cwd or self.directory,
            env={
                "PATH": os.environ["PATH"],
                "HOME": str(self.directory),
                "OLDPWD": str(self.directory),
                "TEST_NODE_VERSION": current,
                "TEST_NVM_FAIL": fail,
                "TEST_NVM_LOG": str(self.log),
            },
            capture_output=True,
            text=True,
            timeout=10,
            check=False,
        )
        calls = self.log.read_text().splitlines() if self.log.exists() else []
        return result, calls

    def test_switching_on_startup_and_directory_changes(self):
        cases = [
            ("startup", self.project, "", "v22.0.0", ["use"]),
            ("parent nvmrc", self.child, "", "v22.0.0", ["use"]),
            ("entering", self.directory, 'cd "project with spaces"', "v22.0.0", ["use"]),
            ("staying", self.project, "cd child", "v22.0.0", ["use"]),
            ("already active", self.project, "", "v20.0.0", []),
            ("leaving", self.project, 'cd "$HOME"', "v22.0.0", ["use", "use default"]),
            ("outside project", self.directory, "cd .nvm", "v20.0.0", []),
        ]
        for name, cwd, script, current, expected in cases:
            with self.subTest(name=name):
                result, calls = self.run_shell(script, cwd=cwd, current=current)
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertEqual(result.stderr, "")
                self.assertEqual(calls, expected)

    def test_installs_a_missing_version(self):
        self.nvmrc.write_text("v24.0.0\n", encoding="utf-8")
        result, calls = self.run_shell(cwd=self.project)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(calls, ["install"])

    def test_nvm_errors_are_not_hidden(self):
        for action, version in (("use", "v20.0.0"), ("install", "v24.0.0")):
            with self.subTest(action=action):
                self.nvmrc.write_text(version + "\n", encoding="utf-8")
                result, calls = self.run_shell(cwd=self.project, fail=action)
                self.assertNotEqual(result.returncode, 0)
                self.assertIn(f"nvm {action} failed", result.stderr)
                self.assertEqual(calls, [action])

    def test_reloading_registers_the_hook_only_once(self):
        result, calls = self.run_shell(
            NVM_CONFIG + '\nprint -rl -- "${chpwd_functions[@]}"'
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout.splitlines(), ["load-nvmrc"])
        self.assertEqual(calls, [])

    def test_missing_nvm_does_not_register_the_hook(self):
        self.nvm_script.unlink()
        for directory_exists in (True, False):
            with self.subTest(directory_exists=directory_exists):
                if not directory_exists:
                    self.nvm_dir.rmdir()
                result, calls = self.run_shell(
                    'print -r -- "${+functions[load-nvmrc]}"; '
                    'print -rl -- "${chpwd_functions[@]}"'
                )
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertEqual(result.stderr, "")
                self.assertEqual(result.stdout.strip(), "0")
                self.assertEqual(calls, [])


if __name__ == "__main__":
    unittest.main()
