"""PROBE: temporary instrumentation to diagnose whole-machine stutter during
heavy OCR (Commission, Event etc.).

Every line is tagged `[PROBE]` so it can be grepped from the per-instance log
file (log/<name>/*.log) or the WebUI log panel after the next run:

    grep PROBE log/alas/*.log

What it measures:
  - per-call OCR latency (predict = onnxruntime inference only, ocr = full
    ocr_for_single_lines including preprocess/decode) with batch size and
    input image shape; slow calls (>250ms) are logged immediately
  - 5-second summaries of call counts, avg/max latency and CPU usage of the
    bot process and the whole system (psutil)

This file and its call sites are a single throwaway commit: after collecting
data, revert it with `git revert <probe commit>` and it disappears cleanly.
"""

from __future__ import annotations

import threading
import time
from collections import deque

from module.logger import logger

try:
    import psutil
except ImportError:  # pragma: no cover - psutil is a hard dependency
    psutil = None

FLUSH_INTERVAL = 5.0  # seconds between summary lines
SLOW_MS = 250.0  # log single calls slower than this immediately
MAX_HISTORY = 1000  # keep at most this many recent samples per kind


class OcrProbe:
    """Process-wide latency/cpu sampler. A daemon thread is lazily started on
    the first OCR call and exits with the (bot) process, so plain CLI runs
    pay nothing until an OCR call actually happens. Every failure is swallowed:
    the probe must never break the automation."""

    _lock = threading.Lock()
    _samples: dict[str, deque[float]] = {
        "predict": deque(maxlen=MAX_HISTORY),
        "ocr": deque(maxlen=MAX_HISTORY),
    }
    _batch_sizes: deque[int] = deque(maxlen=MAX_HISTORY)
    _shapes: deque[tuple] = deque(maxlen=MAX_HISTORY)
    _thread: threading.Thread | None = None
    _last_sys_cpu = 0.0
    _last_proc_cpu = 0.0

    # ------------------------------------------------------------------ api

    @classmethod
    def record(cls, kind: str, elapsed: float, batch: int, shape) -> None:
        """Record one OCR call. kind: 'predict' or 'ocr'. Never raises."""
        try:
            cls._ensure_thread()
            ms = elapsed * 1000.0
            with cls._lock:
                cls._samples[kind].append(ms)
                cls._batch_sizes.append(batch)
                cls._shapes.append(tuple(shape))
            if ms >= SLOW_MS:
                logger.warning(f"[PROBE][OCR-SLOW] {kind} {ms:.0f}ms batch={batch} img={'x'.join(map(str, shape))}")
        except Exception:
            pass

    # ------------------------------------------------------------- sampling

    @classmethod
    def _ensure_thread(cls) -> None:
        thread = cls._thread
        if thread is not None and thread.is_alive():
            return
        thread = threading.Thread(target=cls._run, name="ocr-probe", daemon=True)
        cls._thread = thread
        thread.start()

    @classmethod
    def _run(cls) -> None:
        proc = psutil.Process() if psutil is not None else None
        while True:
            time.sleep(FLUSH_INTERVAL)
            try:
                sys_cpu = psutil.cpu_percent(interval=None) if psutil is not None else -1.0
                proc_cpu = proc.cpu_percent(interval=None) if proc is not None else -1.0
                threads = len(proc.threads()) if proc is not None else -1
                # First call of cpu_percent() returns 0.0 (no interval yet);
                # keep the previous reading in that case.
                cls._last_sys_cpu = sys_cpu if sys_cpu else cls._last_sys_cpu
                cls._last_proc_cpu = proc_cpu if proc_cpu else cls._last_proc_cpu
                cls.flush(sys_cpu=cls._last_sys_cpu, proc_cpu=cls._last_proc_cpu, threads=threads)
            except Exception:
                pass

    @classmethod
    def flush(cls, sys_cpu: float = -1.0, proc_cpu: float = -1.0, threads: int = -1) -> None:
        """Emit one CPU line (when cpu data is available) and one summary
        line per OCR kind with pending samples. Each line stays short so
        terminal/WebUI wrapping cannot split a line in half."""
        try:
            # CPU line is emitted even when no OCR call happened, so the
            # sampler keeps a continuous per-5s CPU timeline between bursts.
            if sys_cpu >= 0 or proc_cpu >= 0:
                parts = []
                if sys_cpu >= 0:
                    parts.append(f"sys_cpu={sys_cpu:.0f}%")
                if proc_cpu >= 0:
                    parts.append(f"proc_cpu={proc_cpu:.0f}%")
                if threads >= 0:
                    parts.append(f"threads={threads}")
                logger.info(f"[PROBE][CPU] {' '.join(parts)}")
            with cls._lock:
                if not any(cls._samples.values()):
                    return
                if cls._batch_sizes:
                    batch_avg = sum(cls._batch_sizes) / len(cls._batch_sizes)
                    cls._batch_sizes.clear()
                    batch = f" batch_avg={batch_avg:.1f}"
                else:
                    batch = ""
                cls._shapes.clear()
                for kind in ("predict", "ocr"):
                    samples = cls._samples[kind]
                    if not samples:
                        continue
                    n = len(samples)
                    avg = sum(samples) / n
                    mx = max(samples)
                    logger.info(f"[PROBE][OCR][{kind}] n={n} avg={avg:.0f}ms max={mx:.0f}ms{batch}")
                    samples.clear()
        except Exception:
            pass
