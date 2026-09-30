import os
import plistlib
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from install_finder_action import install_finder_action

SCRIPT = Path(__file__).with_name("install_finder_action.py")


@unittest.skipIf(os.name == "nt", "macOS shell workflow")
class FinderActionTests(unittest.TestCase):
    def test_workflow_runs_selected_paths_and_reinstalls(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            repo = root / "clone with ' quotes"
            repo.mkdir()
            launcher = repo / "transcribe"
            launcher.write_text('#!/bin/sh\nprintf "%s\\0" "$@" >> "$TRANSCRIBE_TEST_ARGS"\n')
            launcher.chmod(0o755)
            services = root / "Services"
            for _ in range(2):
                workflow = install_finder_action(launcher, services, Path("/usr/bin"))
            with (workflow / "Contents/Info.plist").open("rb") as file:
                info = plistlib.load(file)
            service = info["NSServices"][0]
            self.assertEqual(service["NSMenuItem"]["default"], "Transcribe to SRT")
            self.assertEqual(service["NSSendFileTypes"], ["public.movie", "public.audio"])
            with (workflow / "Contents/document.wflow").open("rb") as file:
                document = plistlib.load(file)
            params = document["actions"][0]["action"]["ActionParameters"]
            self.assertEqual(params["inputMethod"], 1)
            arguments_file = root / "arguments"
            inputs = [str(root / "clip with spaces.mov"), str(root / "$(touch unexpected).mp4")]
            subprocess.run(
                [params["shell"], "-c", params["COMMAND_STRING"], "transcribe", *inputs],
                check=True, cwd=root,
                env={**os.environ, "PATH": "/usr/bin:/bin", "TRANSCRIBE_TEST_ARGS": str(arguments_file)},
            )
            self.assertEqual(arguments_file.read_bytes(), b"".join(path.encode() + b"\0" for path in inputs))
            self.assertFalse((root / "unexpected").exists())

    def test_preserves_an_unrelated_workflow_with_the_same_name(self):
        with tempfile.TemporaryDirectory() as tmp:
            services = Path(tmp)
            workflow = services / "Transcribe to SRT.workflow"
            workflow.mkdir()
            marker = workflow / "user-file"
            marker.write_text("keep")
            with self.assertRaises(FileExistsError):
                install_finder_action(SCRIPT, services, Path("/usr/bin"))
            self.assertEqual(marker.read_text(), "keep")
            contents = workflow / "Contents"
            contents.mkdir()
            info_path = contents / "Info.plist"
            original_info = plistlib.dumps({"CFBundleIdentifier": "com.example.another-service"})
            info_path.write_bytes(original_info)
            with self.assertRaises(FileExistsError):
                install_finder_action(SCRIPT, services, Path("/usr/bin"))
            self.assertEqual(info_path.read_bytes(), original_info)
            self.assertEqual(marker.read_text(), "keep")

    @unittest.skipUnless(sys.platform == "darwin", "native Automator runtime")
    def test_automator_runs_the_installed_workflow(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            launcher = root / "transcribe"
            launcher.write_text('#!/bin/sh\nprintf "%s\\n" "$1" > "$1.result"\n')
            launcher.chmod(0o755)
            recording = root / "selected video.mp4"
            recording.touch()
            workflow = install_finder_action(launcher, root / "Services", Path("/usr/bin"))

            subprocess.run(
                ["/usr/bin/automator", "-i", str(recording), str(workflow)],
                check=True, capture_output=True, text=True, timeout=30,
            )

            self.assertEqual(Path(f"{recording}.result").read_text().strip(), str(recording))
