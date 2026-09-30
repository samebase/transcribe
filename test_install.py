import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


REPO = Path(__file__).resolve().parent


@unittest.skipIf(os.name == "nt", "POSIX launcher installer")
class PosixInstallTests(unittest.TestCase):
    def test_launcher_uses_clone_venv_without_activation(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp) / "clone with spaces"
            repo.mkdir()
            shutil.copy(REPO / "transcribe", repo / "transcribe")
            shutil.copy(REPO / "install.sh", repo / "install.sh")
            (repo / "transcribe.py").write_text(
                "import sys\nprint(sys.prefix)\nprint(sys.argv[1])\n", encoding="utf-8"
            )
            venv = repo / ".venv"
            subprocess.run([sys.executable, "-m", "venv", "--without-pip", str(venv)], check=True)
            target = Path(tmp) / "bin"
            subprocess.run(["bash", str(repo / "install.sh"), "--no-finder", str(target)], check=True, capture_output=True)

            result = subprocess.run(
                [str(target / "transcribe"), "video with spaces.mov"],
                cwd=tmp, check=True, capture_output=True, text=True,
            )

            prefix, argument = result.stdout.splitlines()
            self.assertEqual(Path(prefix).resolve(), venv.resolve())
            self.assertEqual(argument, "video with spaces.mov")

    def test_install_twice_from_another_directory_and_run_link_with_spaces(self):
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / "bin with spaces"
            for _ in range(2):
                subprocess.run(["bash", str(REPO / "install.sh"), "--no-finder", str(target)], cwd=tmp, check=True, capture_output=True)
            launcher = target / "transcribe"
            self.assertTrue(launcher.is_symlink())
            self.assertEqual(launcher.resolve(), REPO / "transcribe")
            result = subprocess.run([str(launcher), "--help"], cwd=tmp, check=True, capture_output=True, text=True)
            self.assertIn("Transcribe video to SRT", result.stdout)
            self.assertIn("--diarize", result.stdout)

    def test_install_preserves_existing_regular_command(self):
        with tempfile.TemporaryDirectory() as tmp:
            launcher = Path(tmp) / "transcribe"
            launcher.write_text("existing command", encoding="utf-8")
            result = subprocess.run(["bash", str(REPO / "install.sh"), "--no-finder", tmp], capture_output=True, text=True)
            self.assertNotEqual(result.returncode, 0)
            self.assertEqual(launcher.read_text(encoding="utf-8"), "existing command")
