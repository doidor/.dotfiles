import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[2]
PACKAGE = ROOT / "copilot"
STOW_FUNCTION = re.search(
    r"(?ms)^stow_dotfiles\(\) \{.*?^\}",
    (ROOT / "setup.sh").read_text(encoding="utf-8"),
).group()
MANAGED_FILES = (
    ".agents/skills/build-crew/SKILL.md",
    ".copilot/copilot-instructions.md",
    ".copilot/agents/paranoid.agent.md",
    ".copilot/agents/surveyor.agent.md",
)
MANAGED_DIRECTORIES = sorted(
    {
        parent.as_posix()
        for filename in MANAGED_FILES
        for parent in Path(filename).parents
        if parent != Path(".")
    }
)
HARNESS = r"""
set -e
print_header() { :; }
print_success() { printf 'success: %s\n' "$1"; }
print_warning() { printf 'warning: %s\n' "$1"; }
print_error() { printf 'error: %s\n' "$1"; }
"""


@unittest.skipUnless(shutil.which("stow"), "stow is required for temporary-home tests")
class CopilotStowTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix="dotfiles-copilot-")
        self.addCleanup(temporary.cleanup)
        self.directory = Path(temporary.name)
        self.repo = self.directory / "repo"
        self.home = self.directory / "home"
        self.repo.mkdir()
        self.home.mkdir()
        shutil.copytree(PACKAGE, self.repo / "copilot")
        shutil.copy2(ROOT / "setup.sh", self.repo / "setup.sh")
        (self.repo / "nvim").mkdir()
        self.env = {
            **os.environ,
            "HOME": str(self.home),
            "COPILOT_HOME": str(self.home / ".copilot"),
            "XDG_CONFIG_HOME": str(self.home / ".config"),
        }
        self.sources = {
            filename: (self.repo / "copilot" / filename).read_bytes()
            for filename in MANAGED_FILES
        }

    def write_home(self, filename, contents):
        path = self.home / filename
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(contents, encoding="utf-8")
        return path

    def stow(self):
        return subprocess.run(
            [
                "bash", "-c", HARNESS + STOW_FUNCTION + "\nstow_dotfiles\n",
                str(self.repo / "setup.sh"),
            ],
            cwd=self.repo, env=self.env, capture_output=True, text=True,
            timeout=20, check=False,
        )

    def assert_managed_links(self):
        for filename in MANAGED_FILES:
            with self.subTest(filename=filename):
                target = self.home / filename
                source = self.repo / "copilot" / filename
                self.assertTrue(target.is_symlink(), str(target))
                self.assertEqual(target.resolve(), source.resolve())
                self.assertEqual(source.read_bytes(), self.sources[filename])
        for directory in MANAGED_DIRECTORIES:
            with self.subTest(directory=directory):
                target = self.home / directory
                self.assertTrue(target.is_dir(), str(target))
                self.assertFalse(target.is_symlink(), str(target))

    def test_fresh_install_keeps_later_app_data_outside_the_repository(self):
        package_files = {
            path.relative_to(PACKAGE).as_posix()
            for path in PACKAGE.rglob("*")
            if path.is_file()
        }
        self.assertEqual(package_files, set(MANAGED_FILES))

        result = self.stow()
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        for filename in (
            ".copilot/auth.json",
            ".copilot/session-state/local/session.json",
            ".agents/skills/local-only/SKILL.md",
        ):
            data = self.write_home(filename, "local-only data\n")
            self.assertFalse(
                data.resolve().is_relative_to(self.repo.resolve()), str(data.resolve()),
            )
        self.assert_managed_links()

    def test_existing_files_are_backed_up_and_repeat_install_preserves_state(self):
        originals = {
            filename: f"original local file: {filename}\n"
            for filename in MANAGED_FILES
        }
        for filename, contents in originals.items():
            self.write_home(filename, contents)
        unrelated = {
            ".copilot/config.json": '{"local": true}\n',
            ".copilot/session-state/existing/session.json": "existing session\n",
            ".agents/skills/other/SKILL.md": "unmanaged skill\n",
        }
        for filename, contents in unrelated.items():
            self.write_home(filename, contents)

        result = self.stow()
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assert_managed_links()
        backups = list(self.home.glob(".dotfiles-backup-*"))
        self.assertEqual(len(backups), 1)
        for filename, contents in originals.items():
            self.assertEqual((backups[0] / filename).read_text(), contents)
        for filename, contents in unrelated.items():
            self.assertEqual((self.home / filename).read_text(), contents)

        repeated = self.stow()
        self.assertEqual(repeated.returncode, 0, repeated.stdout + repeated.stderr)
        self.assertNotIn("Backing up", repeated.stdout)
        self.assertNotIn("Backed up", repeated.stdout)
        self.assertEqual(list(self.home.glob(".dotfiles-backup-*")), backups)
        self.assert_managed_links()
        for filename, contents in unrelated.items():
            self.assertEqual((self.home / filename).read_text(), contents)

    def test_directory_links_are_rejected_before_any_file_is_moved(self):
        for directory in MANAGED_DIRECTORIES:
            with self.subTest(directory=directory):
                case = self.directory / directory.replace("/", "-")
                self.home = case / "home"
                self.home.mkdir(parents=True)
                self.env.update(
                    HOME=str(self.home),
                    COPILOT_HOME=str(self.home / ".copilot"),
                    XDG_CONFIG_HOME=str(self.home / ".config"),
                )
                foreign = case / "foreign"
                foreign.mkdir()
                target = self.home / directory
                target.parent.mkdir(parents=True, exist_ok=True)
                target.symlink_to(foreign, target_is_directory=True)
                originals = {
                    filename: f"keep original: {filename}\n"
                    for filename in MANAGED_FILES
                }
                for filename, contents in originals.items():
                    self.write_home(filename, contents)

                result = self.stow()
                self.assertNotEqual(result.returncode, 0)
                self.assertIn(str(target), result.stdout)
                self.assertTrue(target.is_symlink())
                self.assertEqual(target.resolve(), foreign.resolve())
                self.assertEqual(list(self.home.glob(".dotfiles-backup-*")), [])
                for filename, contents in originals.items():
                    self.assertEqual((self.home / filename).read_text(), contents)

    def test_foreign_file_links_are_not_replaced_or_backed_up(self):
        original = self.write_home(".copilot/copilot-instructions.md", "keep my rules\n")
        foreign = self.directory / "foreign-reviewer.md"
        foreign.write_text("keep my reviewer\n", encoding="utf-8")
        target = self.home / ".copilot/agents/paranoid.agent.md"
        target.parent.mkdir(parents=True)
        target.symlink_to(foreign)

        result = self.stow()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn(str(target), result.stdout)
        self.assertEqual(original.read_text(), "keep my rules\n")
        self.assertTrue(target.is_symlink())
        self.assertEqual(foreign.read_text(), "keep my reviewer\n")
        self.assertEqual(list(self.home.glob(".dotfiles-backup-*")), [])

    @unittest.skipUnless(shutil.which("copilot"), "Copilot CLI is required for discovery")
    def test_copilot_discovers_the_file_linked_skill(self):
        result = self.stow()
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assert_managed_links()
        initialized = subprocess.run(
            ["git", "init", "--quiet", str(self.home)],
            env=self.env, capture_output=True, text=True, timeout=10, check=False,
        )
        self.assertEqual(initialized.returncode, 0, initialized.stderr)
        # Keep the launcher's normal HOME/cache; discover the fixture as a project.
        listed = subprocess.run(
            ["copilot", "skill", "list", "--json"],
            cwd=self.home, env=os.environ.copy(), capture_output=True, text=True,
            timeout=30, check=False,
        )
        self.assertEqual(listed.returncode, 0, listed.stdout + listed.stderr)
        skills = json.loads(listed.stdout)
        self.assertIsInstance(skills, list)
        expected = self.repo / "copilot/.agents/skills/build-crew/SKILL.md"
        matches = [
            skill for skill in skills
            if skill["name"] == "build-crew"
            and (Path(skill["path"]) / "SKILL.md").resolve() == expected.resolve()
        ]
        self.assertEqual(len(matches), 1, listed.stdout)
        self.assertTrue(matches[0]["enabled"])


if __name__ == "__main__":
    unittest.main()
