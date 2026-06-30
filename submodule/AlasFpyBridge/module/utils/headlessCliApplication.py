import os
import shlex
import sys
from subprocess import PIPE, STDOUT, Popen, TimeoutExpired
from threading import Thread


class HeadlessCliApplication:
    """Wrap a cli application to provide programmable interactive access"""

    def __init__(self, launch):
        self.pipe = Popen([launch], stdin=PIPE, stdout=PIPE, stderr=STDOUT, encoding="utf-8", text=True)

        def f():
            while True:
                line = self.pipe.stdout.readline()
                if not line:
                    break
                self.callback(line[:-1])
            if hasattr(self, "orphan_slayer"):
                self.orphan_slayer.kill()
            self.pipe.kill()
            self.callback("exited")

        self.logger = Thread(target=f, daemon=True)
        self.logger.start()

    def callback(self, line):
        print(line)

    def start_orphan_slayer(self, pid, cmd):
        self.orphan_slayer = Popen([
            sys.executable,
            os.path.join(os.path.dirname(__file__), "orphanSlayer.py"),
            str(os.getpid()),
            pid,
            "" if cmd is None else cmd,
        ])

    def feed(self, cmd):
        self.pipe.stdin.write(cmd.strip() + "\n")
        self.pipe.stdin.flush()
