"""Install the macOS Finder Quick Action using the existing transcription command."""

import ctypes
import plistlib
import shlex
import shutil
import sys
import uuid
from pathlib import Path


BUNDLE_ID = "com.samebase.transcribe.finder"
ACTION_NAME = "Transcribe to SRT"


def install_finder_action(launcher: Path, services: Path, ffmpeg_directory: Path) -> Path:
    workflow = services / f"{ACTION_NAME}.workflow"
    contents = workflow / "Contents"
    info_path = contents / "Info.plist"
    if workflow.exists():
        if not info_path.is_file():
            raise FileExistsError(f"Refusing to replace an unrelated workflow: {workflow}")
        with info_path.open("rb") as file:
            installed_info = plistlib.load(file)
        if installed_info.get("CFBundleIdentifier") != BUNDLE_ID:
            raise FileExistsError(f"Refusing to replace an unrelated workflow: {workflow}")

    path = f"{launcher.parent}/.venv/bin:{ffmpeg_directory}:/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin"
    command = f'''set -euo pipefail
export PATH={shlex.quote(path)}
for input_file in "$@"; do
    {shlex.quote(str(launcher))} "$input_file" >/dev/null
done
'''
    info = {
        "CFBundleIdentifier": BUNDLE_ID,
        "CFBundleName": ACTION_NAME,
        "NSServices": [{
            "NSMenuItem": {"default": ACTION_NAME},
            "NSMessage": "runWorkflowAsService",
            "NSRequiredContext": {"NSApplicationIdentifier": "com.apple.finder"},
            "NSSendFileTypes": ["public.movie", "public.audio"],
        }],
    }
    document = {
        "AMDocumentVersion": "2",
        "actions": [{"action": {
            "ActionBundlePath": "/System/Library/Automator/Run Shell Script.action",
            "ActionName": "Run Shell Script",
            "ActionParameters": {
                "CheckedForUserDefaultShell": True,
                "COMMAND_STRING": command,
                "inputMethod": 1,
                "shell": "/bin/bash",
                "source": "",
            },
            "AMAccepts": {"Container": "List", "Optional": True, "Types": ["com.apple.cocoa.string"]},
            "AMProvides": {"Container": "List", "Types": ["com.apple.cocoa.string"]},
            "BundleIdentifier": "com.apple.RunShellScript",
            "Class Name": "RunShellScriptAction",
            "InputUUID": str(uuid.uuid4()),
            "OutputUUID": str(uuid.uuid4()),
            "UUID": str(uuid.uuid4()),
        }}],
        "connectors": {},
        "workflowMetaData": {
            "applicationBundleID": "com.apple.finder",
            "applicationBundleIDsByPath": {"/System/Library/CoreServices/Finder.app": "com.apple.finder"},
            "applicationPath": "/System/Library/CoreServices/Finder.app",
            "applicationPaths": ["/System/Library/CoreServices/Finder.app"],
            "inputTypeIdentifier": "com.apple.Automator.fileSystemObject",
            "outputTypeIdentifier": "com.apple.Automator.nothing",
            "presentationMode": 15,
            "processesInput": False,
            "serviceApplicationBundleID": "com.apple.finder",
            "serviceApplicationPath": "/System/Library/CoreServices/Finder.app",
            "serviceInputTypeIdentifier": "com.apple.Automator.fileSystemObject",
            "serviceOutputTypeIdentifier": "com.apple.Automator.nothing",
            "serviceProcessesInput": False,
            "systemImageName": "NSActionTemplate",
            "useAutomaticInputType": False,
            "workflowTypeIdentifier": "com.apple.Automator.servicesMenu",
        },
    }
    contents.mkdir(parents=True, exist_ok=True)
    for filename, data in [("Info.plist", info), ("document.wflow", document)]:
        with (contents / filename).open("wb") as file:
            plistlib.dump(data, file)
    return workflow


if __name__ == "__main__":
    if sys.platform != "darwin":
        raise SystemExit("Finder Quick Actions require macOS.")
    ffmpeg = shutil.which("ffmpeg")
    if ffmpeg is None:
        raise SystemExit("ffmpeg is missing. Run bash deps.sh before installing the Finder action.")
    workflow = install_finder_action(
        Path(__file__).resolve().with_name("transcribe"),
        Path.home() / "Library/Services",
        Path(ffmpeg).parent,
    )
    appkit = ctypes.CDLL("/System/Library/Frameworks/AppKit.framework/AppKit")
    appkit.NSUpdateDynamicServices.argtypes = []
    appkit.NSUpdateDynamicServices.restype = None
    appkit.NSUpdateDynamicServices()
    print(f"Installed {workflow}")
    print(f"In Finder, right-click a recording and choose Services > {ACTION_NAME}.")
