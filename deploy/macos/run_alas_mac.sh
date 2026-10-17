#!/bin/zsh
set -euo pipefail

SCRIPT_DIR="${0:A:h}"
ROOT_DIR="${SCRIPT_DIR:h:h}"
if [[ -n "${ALAS_PYTHON:-}" ]]; then
  PYTHON="${ALAS_PYTHON}"
elif [[ -x "${ROOT_DIR}/.venv/bin/python" ]]; then
  PYTHON="${ROOT_DIR}/.venv/bin/python"
else
  PYTHON="$(command -v python3 || true)"
fi
ADB="${ADB:-$(command -v adb || true)}"

if [[ ! -x "${PYTHON}" ]]; then
  print -u2 "Missing Alas Python: ${PYTHON}"
  print -u2 "Set ALAS_PYTHON to the Python executable used by this installation."
  exit 1
fi

cd "${ROOT_DIR}"
export ALAS_MAC_OCR=onnx
export PYTHONPATH="${SCRIPT_DIR}${PYTHONPATH:+:${PYTHONPATH}}"

if [[ "${1:-}" == "--check" ]]; then
  exec "${PYTHON}" "${SCRIPT_DIR}/check_runtime.py"
fi

DEVICE="$("${PYTHON}" -c 'import json; from pathlib import Path; p=Path("config/alas.json"); print(json.loads(p.read_text())["Alas"]["Emulator"]["Serial"] if p.exists() else "auto")')"

if [[ -z "${ADB}" || ! -x "${ADB}" ]]; then
  print -u2 "ADB was not found. Install Android platform-tools or set ADB to its executable path."
  exit 1
fi

"${ADB}" start-server >/dev/null
if [[ "${DEVICE}" == *:* ]]; then
  "${ADB}" connect "${DEVICE}"
fi
if [[ "${DEVICE}" != "auto" ]] && [[ "$("${ADB}" -s "${DEVICE}" get-state 2>/dev/null)" != "device" ]]; then
  print -u2 "MuMu ADB device is unavailable: ${DEVICE}. Start the Android instance and check config/alas.json."
  exit 1
fi

exec "${PYTHON}" gui.py "$@"
