# Agent guidance for transcribe

This repo is a Windows and macOS/Linux command-line transcription tool. All source
files live here. `install.ps1` creates Windows command stubs and Explorer verbs;
`install.sh` links the POSIX launcher into `~/.local/bin`. On macOS it also calls
`install_finder_action.py` to install the Finder service. `--no-finder` installs
only the terminal command.

## Working rules

- Use test-first development for non-trivial changes. Write or update the test
  first, then implement until it passes. Extract a test seam if needed.
- When behaviour or a tested contract changes, update its tests and rerun them.
- Before committing, run `python3 -m unittest discover -v` and smoke-test the
  actual launcher. The tests need `requirements.txt`, `numpy` and `torch`, but no
  downloaded models, GPU, Hugging Face token or pyannote pipeline.
- Parse every `.ps1` file with PowerShell's
  `[System.Management.Automation.Language.Parser]::ParseFile`. On Windows, also
  run the installer and uninstaller and check exit codes.
- Keep `.bat` files ASCII. Generate them with `-Encoding ASCII` in PowerShell.
- Never put source files in `C:\dev\tools`. It holds generated stubs and large
  binaries only. Do not commit `.exe`, `.dll` or model files.
- Preserve `EXEDIR` support in `transcribe.bat`. The installed stub sets it to
  its own directory; direct calls fall back to the launcher's directory.
- Reinstall after moving the clone or changing installation wiring. Editing
  existing source does not need a reinstall because stubs point at live files.
- Keep the shared Explorer `MikesTools` submenu. Only add/remove `Transcribe`
  and `TranscribeSpeakers`; never delete other tools' verbs or the shared root.

## Dependency scripts

- `deps.ps1` must be self-contained, idempotent and safe to run directly with
  `.\deps.ps1`. The installer runs it unless `-SkipDeps` is passed.
- Check large manual-download binaries and print helpful download links rather
  than downloading them. Use `Get-Command` for system tools and check Python
  imports before recommending package installation.
- Use clear `Write-Host` output with colour for checks.
- `deps.sh` sets up ffmpeg and faster-whisper. `--with-diarize` also installs
  pyannote.audio. Keep this optional. All Python installation paths use
  `requirements.txt` to preserve dependency compatibility.

## transcribe details

- `transcribe.bat` uses `ffmpeg.exe`, `faster-whisper-xxl.exe` and `_models`
  under `C:\dev\tools`, with CUDA and a CPU retry. `--diarize` switches to Python.
- `transcribe` resolves its symlink and launches `transcribe.py` using the clone's
  `.venv/bin/python3` when present, or `python3` from PATH otherwise. `deps.sh`
  selects the same interpreter. The Python path uses ffmpeg on PATH and pip faster-whisper.
- The Finder service runs that same launcher for each selected media file, with
  an explicit PATH. Its installer only replaces workflows with our bundle ID.
  Native Automator execution is covered by `test_finder_action.py` on macOS.
- `.env` is loaded next to `transcribe.py`, regardless of the working directory.
  Existing environment variables take precedence. Document variables in `.env.example`.
- Output is `<input_basename>.srt` beside the input. Temporary WAV files are
  cleaned up. Speaker IDs describe turns, not real-world identities.
