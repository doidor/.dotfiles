import errno
import fcntl
import json
import os
from pathlib import Path
import pty
import select
import shlex
import shutil
import struct
import subprocess
import sys
import tempfile
import termios
import textwrap
import time
import unittest


ROOT = Path(__file__).resolve().parents[2]
CONFIG = ROOT / "herdr/.config/herdr/config.toml"
ESCAPE_PRESS = b"\x1b[27;1u"


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


@unittest.skipUnless(shutil.which("wezterm"), "WezTerm is required to evaluate its Lua configuration")
class WezTermHerdrKeyTests(unittest.TestCase):
    def test_scoped_escape_and_number_encodings_preserve_other_applications(self):
        with tempfile.TemporaryDirectory(prefix="dotfiles-wezterm-keys-") as temporary:
            directory = Path(temporary)
            marker = directory / "passed"
            config = directory / "test.lua"
            config.write_text(textwrap.dedent(r"""
                local stub = {
                  home_dir = os.getenv('HOME'),
                  config_builder = function() return {} end,
                  font = function() return {} end,
                  action_callback = function(callback) return callback end,
                  action = {
                    SendString = function(text) return { kind = 'text', text = text } end,
                    SendKey = function(key) return { kind = 'key', key = key.key, mods = key.mods } end,
                  },
                }
                package.loaded.wezterm = stub
                local config = dofile(os.getenv('DOTFILES_WEZTERM_CONFIG'))
                assert(config.enable_kitty_keyboard == false)
                assert(#config.keys == 10)
                local bindings = {}
                for _, binding in ipairs(config.keys) do
                  bindings[binding.mods .. ':' .. binding.key] = binding
                end
                local cases = { { 'Escape', 'NONE', '\x1b[27;1u' } }
                for number = 1, 9 do
                  table.insert(cases, { tostring(number), 'CTRL',
                    string.format('\x1b[%d;5u', 48 + number) })
                end
                for _, case in ipairs(cases) do
                  local key, mods, sequence = table.unpack(case)
                  local binding = assert(bindings[mods .. ':' .. key])
                  for _, process in ipairs({
                    '/usr/local/bin/herdr', 'herdr',
                    '/bin/zsh', '/usr/bin/ssh', '/usr/bin/not-herdr', false,
                  }) do
                    local sent = {}
                    local pane = {
                      get_foreground_process_name = function() return process or nil end,
                    }
                    local window = {
                      perform_action = function(_, action, target)
                        assert(target == pane)
                        table.insert(sent, action)
                      end,
                    }
                    binding.action(window, pane)
                    assert(#sent == 1)
                    if process == '/usr/local/bin/herdr' or process == 'herdr' then
                      assert(sent[1].kind == 'text' and sent[1].text == sequence)
                    else
                      assert(sent[1].kind == 'key')
                      assert(sent[1].key == key and sent[1].mods == mods)
                    end
                  end
                end
                local marker = assert(io.open(os.getenv('DOTFILES_WEZTERM_RESULT'), 'w'))
                marker:write('ok')
                marker:close()
                return {}
            """), encoding="utf-8")
            result = subprocess.run(
                [shutil.which("wezterm"), "--config-file", str(config), "show-keys"],
                env={
                    **os.environ,
                    "DOTFILES_WEZTERM_CONFIG": str(ROOT / "wezterm/.wezterm.lua"),
                    "DOTFILES_WEZTERM_RESULT": str(marker),
                },
                capture_output=True, text=True, timeout=15, check=False,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertTrue(marker.exists(), result.stderr)
            self.assertEqual(marker.read_text(encoding="utf-8"), "ok")


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

        reader = directory / "capture_keys.py"
        captured = directory / "captured_keys"
        reader.write_text(textwrap.dedent("""
            import os
            from pathlib import Path
            import sys
            import termios
            import tty

            output = Path(sys.argv[1])
            temporary = output.with_suffix(".tmp")
            data = bytearray()
            saved = termios.tcgetattr(sys.stdin.fileno())
            try:
                tty.setraw(sys.stdin.fileno())
                output.write_bytes(b"")
                while True:
                    chunk = os.read(sys.stdin.fileno(), 1024)
                    if not chunk or chunk == b"q":
                        break
                    data.extend(chunk)
                    temporary.write_bytes(data)
                    temporary.replace(output)
            finally:
                termios.tcsetattr(sys.stdin.fileno(), termios.TCSADRAIN, saved)
        """), encoding="utf-8")
        captured_tab = call(
            "tab", "create", "--workspace", second["workspace"]["workspace_id"],
            "--label", "key-capture", "--cwd", str(directory), "--no-focus",
        )
        captured_pane = captured_tab["root_pane"]["pane_id"]
        titles[captured_pane] = "attention|key-capture"
        subprocess.run(
            [*command, "pane", "run", captured_pane,
             shlex.join(["exec", sys.executable, str(reader), str(captured)])],
            env=env, capture_output=True, text=True, timeout=10, check=True,
        )
        deadline = time.monotonic() + 5
        while time.monotonic() < deadline:
            drain()
            if captured.exists() and b"key-capture" in screen:
                break
            time.sleep(0.05)
        else:
            self.fail("The isolated raw key reader did not become ready")
        press_and_expect(b"\x023", captured_pane)
        os.write(master, ESCAPE_PRESS * 3)
        deadline = time.monotonic() + 2
        while captured.read_bytes() != b"\x1b" * 3 and time.monotonic() < deadline:
            drain()
            time.sleep(0.05)
        self.assertEqual(captured.read_bytes(), b"\x1b" * 3, "Rapid Escape presses must arrive once each")
        os.write(master, b"q")


if __name__ == "__main__":
    unittest.main()
