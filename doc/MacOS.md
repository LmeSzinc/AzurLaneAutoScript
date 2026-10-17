# macOS Setup (Apple Silicon)

This guide adapts Alas OCR for Apple Silicon Macs. It uses the game-text models already in the repository with ONNX Runtime; Tesseract and MXNet are not required. Chinese, Japanese, traditional Chinese, and game-specific OCR models are converted locally, so no separate model download is needed.

## Requirements

- An Apple Silicon Mac running macOS 13 or later, with an existing Alas checkout and working Python environment. This change adapts OCR; it is not a bootstrap installer for all Alas dependencies.
- Azur Lane running in MuMu Player Pro. Configure the usual MuMu ADB serial in `config/alas.json`.
- Android platform-tools with `adb` on `PATH`; alternatively, set `ADB` to its executable path when launching.
- The adapter was validated with Python 3.10. For another Python environment, set `ALAS_PYTHON` to its interpreter.

## Install the OCR runtime

From the repository root:

```sh
PYTHON="${ALAS_PYTHON:-python3}"
"$PYTHON" -m pip install --no-deps --only-binary=:all: \
  --target deploy/macos/packages -r deploy/macos/requirements-ocr.txt
PYTHONPATH=deploy/macos/packages "$PYTHON" deploy/macos/convert_models.py
chmod +x deploy/macos/run_alas_mac.sh
```

ONNX Runtime and conversion dependencies stay isolated in `deploy/macos/packages/`. The installation does not replace Alas's NumPy, Pillow, or ImageIO. `deploy/macos/constraints.txt` documents the verified GIF-decoder versions; the OCR install does not reinstall those base dependencies.

## Check and launch

Run the offline check first:

```sh
./deploy/macos/run_alas_mac.sh --check
```

It checks ten synthetic text samples, all five original OCR models, whitelist and batch behavior, child-process startup, and grayscale map GIF decoding. It does not read account configuration or connect to the emulator. After it passes, launch Alas with:

```sh
./deploy/macos/run_alas_mac.sh
```

Set `ALAS_PYTHON` if Alas uses a different interpreter:

```sh
ALAS_PYTHON="/path/to/alas/bin/python" ./deploy/macos/run_alas_mac.sh
```

The launcher prefers `ALAS_PYTHON`, then the checkout's `.venv/bin/python`, then `python3` on `PATH`. Use the same interpreter for installation and startup. If `config/alas.json` does not exist yet, create a profile and configure the emulator serial in the GUI.

Run the check after installing or changing Python, ONNX Runtime, ImageIO, or Pillow. `sitecustomize.py` activates the OCR adapter only in processes started by this launcher; do not start `gui.py` directly.

## Regenerate models

After updating the OCR weights in the repository, regenerate the ONNX files from the repository root:

```sh
PYTHONPATH=deploy/macos/packages "$PYTHON" deploy/macos/convert_models.py
./deploy/macos/run_alas_mac.sh --check
```

At model load, the adapter verifies the original-weight fingerprint stored in each converted model. Generated ONNX files live in the Git-ignored `deploy/macos/models/` directory and should not be committed.

If the check reports `GIF decoder regression`, restore compatible image decoders in the same Python environment, then rerun the check:

```sh
"$PYTHON" -m pip install -c deploy/macos/constraints.txt imageio pillow
./deploy/macos/run_alas_mac.sh --check
```

This adapter uses Alas's existing emulator and input methods. Game tasks, maps, fleets, resource limits, and scheduling continue to follow the normal Alas configuration. Check your task settings and emulator connection in the Alas UI before the first run or after changing game/emulator settings.

## Validation and maintenance

On an Apple Silicon Mac with Python 3.10 and MuMu Pro 1.4.11, the CN client completed one automatic 16-4 safe-mode clear: four mob fights and the boss, all five with S results. That live test used the same inference module before packaging; conversion and offline checks were repeated for this deployment path. Intel Macs, live tasks in other languages, and first-clear behavior remain unverified.

Dependency and model directories are generated locally. Do not commit account configuration, run logs, full game screenshots, virtual environments, `packages/`, or `models/`. Offline fixtures are synthetic text and contain no account information.

Continue using this launcher after repository updates. Set `InstallDependencies` to `false` in the deployment configuration so the generic dependency installer does not reinstall incompatible MXNet packages; other update preferences are up to the user. If a source-weight fingerprint changes, regenerate the models and rerun the check.
