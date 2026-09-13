import errno
import fcntl
import json
import os
from pathlib import Path
import pty
import select
import shutil
import struct
import subprocess
import sys
import tempfile
import termios
import time
import unittest


CONFIG = Path(__file__).resolve().parents[2] / "herdr/.config/herdr/config.toml"


def read_config():
    import tomllib

    with CONFIG.open("rb") as source:
        return tomllib.load(source)


@unittest.skipIf(sys.version_info < (3, 11), "Config assertions require Python 3.11+")
class HerdrKeybindingTests(unittest.TestCase):
    def test_agent_navigation_is_native_and_preserves_window_shortcuts(self):
        keys = read_config()["keys"]
        self.assertEqual(keys["focus_agent"], "prefix+ctrl+1..9")
        self.assertEqual(keys["next_agent"], "prefix+ctrl+n")
        self.assertEqual(keys["previous_agent"], "prefix+ctrl+p")
        self.assertEqual(keys["switch_tab"], "prefix+1..9")
        self.assertEqual(keys["next_tab"], "prefix+n")
        self.assertEqual(keys["previous_tab"], "prefix+p")
        commands = {command["key"]: command for command in keys["command"]}
        self.assertIn("new-copilot", commands["prefix+shift+a"]["command"])
        self.assertFalse(any("first-agent" in command["command"] for command in commands.values()))


@unittest.skipUnless(
    os.environ.get("HERDR_KEYBINDINGS_INTEGRATION") == "1" and sys.version_info >= (3, 11),
    "Set HERDR_KEYBINDINGS_INTEGRATION=1 for isolated native keyboard coverage",
)
class HerdrKeyboardIntegrationTests(unittest.TestCase):
    def test_control_numbers_select_agents_but_plain_one_selects_tab(self):
        herdr_bin = shutil.which("herdr")
        if not herdr_bin:
            self.fail("The integration test requires Herdr")
        temporary = tempfile.TemporaryDirectory(prefix="herdr-keys-", dir="/tmp")
        self.addCleanup(temporary.cleanup)
        directory = Path(temporary.name)
        home = directory / "home"
        config = home / ".config/herdr/config.toml"
        config.parent.mkdir(parents=True)
        keys = read_config()["keys"]
        native_keys = ("prefix", "detach", "switch_tab", "focus_agent", "next_agent", "previous_agent")
        config.write_text(
            'onboarding = false\n'
            '[update]\nversion_check = false\nmanifest_check = false\n'
            '[terminal]\ndefault_shell = "/bin/sh"\nshell_mode = "non_login"\n'
            '[ui]\nagent_panel_sort = "priority"\nwindow_title = "{workspace}|{tab}"\n'
            '[ui.toast]\ndelivery = "off"\n[ui.sound]\nenabled = false\n'
            '[keys]\n'
            + "".join(f"{key} = {json.dumps(keys[key])}\n" for key in native_keys),
            encoding="utf-8",
        )
        env = {
            key: value for key, value in os.environ.items()
            if not key.startswith(("HERDR_", "WEZTERM_", "TMUX"))
        }
        env.update(
            HOME=str(home), XDG_CONFIG_HOME=str(home / ".config"),
            XDG_STATE_HOME=str(home / ".local/state"), HERDR_CONFIG_PATH=str(config),
            SHELL="/bin/sh", TERM="xterm-256color",
        )
        command = [herdr_bin, "--session", "test"]

        def call(*args):
            result = subprocess.run(
                [*command, *args], env=env, capture_output=True, text=True,
                timeout=10, check=True,
            )
            return json.loads(result.stdout)["result"]

        log_path = directory / "server.log"
        log = log_path.open("wb")
        self.addCleanup(log.close)
        server = subprocess.Popen(
            [*command, "server"], env=env, stdin=subprocess.DEVNULL,
            stdout=log, stderr=subprocess.STDOUT,
        )

        def stop_server():
            if server.poll() is not None:
                return
            try:
                subprocess.run(
                    [*command, "server", "stop"], env=env,
                    capture_output=True, timeout=10, check=True,
                )
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
                call("workspace", "list")
                break
            except subprocess.CalledProcessError as error:
                last_error = error.stderr
                time.sleep(0.1)
        else:
            self.fail(f"Isolated Herdr did not start: {last_error}")

        first = call("workspace", "create", "--label", "working", "--cwd", str(directory), "--focus")
        first_pane = first["root_pane"]["pane_id"]
        second = call("workspace", "create", "--label", "attention", "--cwd", str(directory), "--no-focus")
        shell_pane = second["root_pane"]["pane_id"]
        second_tab = call(
            "tab", "create", "--workspace", second["workspace"]["workspace_id"],
            "--label", "blocked", "--cwd", str(directory), "--no-focus",
        )
        top_agent = second_tab["root_pane"]["pane_id"]
        titles = {
            first_pane: f"working|{first['tab']['label']}",
            shell_pane: f"attention|{second['tab']['label']}",
            top_agent: "attention|blocked",
        }
        extra_panes = []
        for number in range(3, 10):
            created = call(
                "workspace", "create", "--label", f"agent-{number}",
                "--cwd", str(directory), "--no-focus",
            )
            pane_id = created["root_pane"]["pane_id"]
            extra_panes.append(pane_id)
            titles[pane_id] = f"agent-{number}|{created['tab']['label']}"
        for pane_id in (first_pane, top_agent, *extra_panes):
            state = "blocked" if pane_id == top_agent else "working"
            subprocess.run(
                [*command, "pane", "report-agent", pane_id, "--source", "dotfiles-test",
                 "--agent", "test-agent", "--state", state],
                env=env, capture_output=True, text=True, timeout=10, check=True,
            )

        master, slave = pty.openpty()
        self.addCleanup(os.close, master)
        fcntl.ioctl(slave, termios.TIOCSWINSZ, struct.pack("HHHH", 60, 180, 0, 0))
        client = subprocess.Popen(command, env=env, stdin=slave, stdout=slave, stderr=slave)
        os.close(slave)

        def stop_client():
            if client.poll() is None:
                client.terminate()
                client.wait(timeout=10)

        self.addCleanup(stop_client)
        screen = bytearray()

        def drain():
            while select.select([master], [], [], 0)[0]:
                try:
                    data = os.read(master, 65536)
                except OSError as error:
                    if error.errno == errno.EIO:
                        break
                    raise
                if not data:
                    break
                screen.extend(data)

        deadline = time.monotonic() + 10
        while time.monotonic() < deadline:
            drain()
            if b"agents" in screen and b"attention" in screen:
                break
            if client.poll() is not None:
                self.fail(screen.decode("utf-8", errors="replace"))
            time.sleep(0.05)
        else:
            self.fail("Herdr client did not render: " + screen.decode("utf-8", errors="replace")[-4000:])

        def press_and_expect(sequence, target):
            drain()
            output_start = len(screen)
            os.write(master, sequence)
            deadline = time.monotonic() + 5
            while time.monotonic() < deadline:
                drain()
                focused = call("api", "snapshot")["snapshot"]["focused_pane_id"] == target
                rendered = titles[target].encode("utf-8") in screen[output_start:]
                if focused and rendered:
                    return
                time.sleep(0.05)
            self.fail(
                f"{sequence!r} did not focus {target}; terminal output: "
                + screen.decode("utf-8", errors="replace")[-4000:]
            )

        # CSI-u preserves Ctrl on a number; plain digits retain tab navigation.
        priority_order = [top_agent, *reversed(extra_panes), first_pane]
        for number, target in enumerate(priority_order, 1):
            press_and_expect(f"\x02\x1b[{48 + number};5u".encode("ascii"), target)
        press_and_expect(b"\x02\x1b[49;5u", top_agent)
        press_and_expect(b"\x021", shell_pane)
        press_and_expect(b"\x02\x0e", top_agent)
        press_and_expect(b"\x02\x10", first_pane)
        press_and_expect(b"\x02\x1b[49;5u", top_agent)


if __name__ == "__main__":
    unittest.main()
