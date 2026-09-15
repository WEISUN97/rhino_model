"""Run launcher.py in the frontmost Rhino 8 window from VS Code on macOS."""

from pathlib import Path
import re
import subprocess


# If macOS reports that Rhino is not running, replace this with its app name.
RHINO_APP_NAME = "Rhino 8"
LAUNCHER_PATH = Path(__file__).with_name("launcher.py")
BUILD_MODULE_PATTERN = re.compile(r"[A-Za-z_]\w*(?:\.[A-Za-z_]\w*)*")


def escape_applescript(value):
    return value.replace("\\", "\\\\").replace('"', '\\"')


def set_build_module(build_module):
    """Write the selected build module into launcher.py before Rhino reloads it."""
    if not BUILD_MODULE_PATTERN.fullmatch(build_module):
        raise ValueError("build_module must be a dotted Python module name.")

    launcher_text = LAUNCHER_PATH.read_text(encoding="utf-8")
    updated_text, replacements = re.subn(
        r"^BUILD_MODULE\s*=\s*.*$",
        'BUILD_MODULE = "{0}"'.format(build_module),
        launcher_text,
        count=1,
        flags=re.MULTILINE,
    )
    if replacements != 1:
        raise RuntimeError("Could not find BUILD_MODULE in launcher.py")
    LAUNCHER_PATH.write_text(updated_text, encoding="utf-8")
    print("Selected Rhino build module:", build_module)


def run_in_rhino(build_module=None):
    if build_module:
        set_build_module(build_module)

    command = "_RunPythonScript"
    script = '''
tell application "{app_name}" to activate
delay 0.5
set the clipboard to "{command}"
tell application "System Events"
    keystroke "v" using command down
    key code 36
end tell
delay 1.0
tell application "System Events"
    keystroke "g" using {{command down, shift down}}
end tell
delay 0.3
set the clipboard to "{launcher_path}"
tell application "System Events"
    keystroke "v" using command down
    key code 36
end tell
delay 0.5
tell application "System Events"
    key code 36
end tell
'''.format(
        app_name=escape_applescript(RHINO_APP_NAME),
        command=escape_applescript(command),
        launcher_path=escape_applescript(str(LAUNCHER_PATH)),
    )

    result = subprocess.run(
        ["osascript", "-e", script],
        text=True,
        capture_output=True,
    )
    if result.returncode:
        raise RuntimeError(result.stderr.strip())
    print("Sent launcher.py to Rhino:", LAUNCHER_PATH)


if __name__ == "__main__":
    try:
        run_in_rhino()
    except Exception as error:
        print("Could not run Rhino:", error)
