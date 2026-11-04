import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest


MANIFEST = (
    Path(__file__).resolve().parents[2]
    / "herdr/.config/herdr/agent-detection/copilot.toml"
)
HERDR = shutil.which("herdr")
SPINNER_FRAMES = ("\u25cb", "\u25ce", "\u25c9", "\u25cf")
FOOTER_PREFIXES = (
    "",
    "Autopilot \u00b7 Allow All \u00b7 ",
    "Interactive \u00b7 Allow All \u00b7 ",
)


@unittest.skipUnless(HERDR, "Herdr is required to evaluate detection manifests")
class HerdrDetectionTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix="dotfiles-herdr-detection-")
        self.addCleanup(temporary.cleanup)
        self.directory = Path(temporary.name)
        self.config_dir = self.directory / ".config"
        override = self.config_dir / "herdr/agent-detection/copilot.toml"
        override.parent.mkdir(parents=True)
        shutil.copyfile(MANIFEST, override)
        self.override = override
        self.screen = self.directory / "screen.txt"
        self.env = {
            key: value for key, value in os.environ.items()
            if not key.startswith("HERDR_")
        }
        self.env.update(
            HOME=str(self.directory),
            XDG_CONFIG_HOME=str(self.config_dir),
            XDG_STATE_HOME=str(self.directory / ".local/state"),
            HERDR_CONFIG_PATH=str(self.config_dir / "herdr/config.toml"),
        )

    def explain(self, screen):
        self.screen.write_text(screen, encoding="utf-8")
        result = subprocess.run(
            [HERDR, "agent", "explain", "--file", str(self.screen),
             "--agent", "copilot", "--json"],
            env=self.env, capture_output=True, text=True, timeout=10, check=False,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        report = json.loads(result.stdout)
        self.assertEqual(report["manifest_source"], str(self.override))
        self.assertIsNone(report["warning"])
        return report

    def test_background_wait_stays_working_for_every_spinner_frame(self):
        for prefix in FOOTER_PREFIXES:
            for marker in SPINNER_FRAMES:
                for suffix in ("", " esc stop agents", " \u00b7 15.2 KiB esc stop agents"):
                    with self.subTest(prefix=prefix, marker=marker, suffix=suffix):
                        report = self.explain(
                            f"\n > \n\n {prefix}{marker} Waiting for background agents{suffix}\n"
                        )
                        self.assertEqual(report["state"], "working")
                        self.assertEqual(report["matched_rule"]["id"], "background_agents_working")
                        self.assertTrue(report["visible_working"])

    def test_ordinary_working_hints_are_preserved(self):
        for hint in ("esc to cancel", "esc cancel", "esc again to cancel", "esc interrupt"):
            with self.subTest(hint=hint):
                report = self.explain("Thinking... " + hint)
                self.assertEqual(report["state"], "working")
                self.assertEqual(report["matched_rule"]["id"], "working_cancel_hint")

    def test_current_working_footer_for_every_spinner_frame(self):
        for prefix in FOOTER_PREFIXES:
            for marker in SPINNER_FRAMES:
                for activity in ("Working", "Thinking", "Waiting for background shells"):
                    with self.subTest(prefix=prefix, marker=marker, activity=activity):
                        report = self.explain(
                            " ~/.dotfiles\n\n"
                            f" {prefix}{marker} {activity} \u00b7 2.8 KiB ctrl+c interrupt"
                            "    GPT-6.1 Sol \u00b7 922K context\n"
                        )
                        self.assertEqual(report["state"], "working")
                        self.assertEqual(report["matched_rule"]["id"], "working_interrupt_footer")
                        self.assertTrue(report["visible_working"])

    def test_approval_prompts_still_override_background_wait(self):
        report = self.explain(
            "Allow this tool?\nEnter to select \u00b7 Esc to cancel\n"
            "\u25cf Waiting for background agents"
        )
        self.assertEqual(report["state"], "blocked")
        self.assertEqual(report["matched_rule"]["id"], "selection_blocker")
        self.assertTrue(report["visible_blocker"])

    def test_approval_prompts_still_override_current_working_footer(self):
        report = self.explain(
            "Allow this tool?\nEnter to select \u00b7 Esc to cancel\n"
            "Autopilot \u00b7 Allow All \u00b7 \u25cf Working \u00b7 2.8 KiB ctrl+c interrupt"
        )
        self.assertEqual(report["state"], "blocked")
        self.assertEqual(report["matched_rule"]["id"], "selection_blocker")
        self.assertTrue(report["visible_blocker"])

    def test_idle_prompt_and_transcript_mentions_do_not_look_working(self):
        screens = (
            "Finished.\n> ",
            "I was Waiting for background agents earlier.\n> ",
            "\u25cf Waiting for background agentship",
            "   > \u25cf Waiting for background agents",
            "The working footer says ctrl+c interrupt.\n> ",
            "   > \u25cf Working \u00b7 2.8 KiB ctrl+c interrupt\n> ",
            "   > Autopilot \u00b7 Allow All \u00b7 \u25cf Working \u00b7 ctrl+c interrupt\n> ",
            "Autopilot \u00b7 Allow All \u00b7 / commands \u00b7 tab next tab",
            "\u25cf Working \u00b7 ctrl+c interrupting",
            "Autopilot \u00b7 Allow All \u00b7 \u25cf Working \u00b7 ctrl+c interrupting",
            "Autopilot \u00b7 Allow All \u00b7 \u25cf Working \u00b7 ctrl+c interrupt\n"
            + "\n".join(f"Later output {index}" for index in range(6)),
            "\u25cf Working \u00b7 2.8 KiB ctrl+c interrupt\n" + "\n".join(
                f"Later output {index}" for index in range(6)
            ),
            "\u25cf Waiting for background agents\n" + "\n".join(
                f"Later output {index}" for index in range(6)
            ),
        )
        for screen in screens:
            with self.subTest(screen=screen):
                report = self.explain(screen)
                self.assertEqual(report["state"], "idle")
                self.assertIsNone(report["matched_rule"])
                self.assertFalse(report["visible_working"])


if __name__ == "__main__":
    unittest.main()
