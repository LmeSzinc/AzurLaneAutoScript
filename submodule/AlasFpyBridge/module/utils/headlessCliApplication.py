import os
import shlex
from subprocess import PIPE, STDOUT, Popen, TimeoutExpired
from threading import Thread


class HeadlessCliApplication:
    """Wrap a cli application to provide programmable interactive access"""

    def __init__(self, cmd):
        self.pipe = Popen(
            shlex.split(cmd, posix=os.name=="posix"),
            stdin=PIPE, stdout=PIPE, stderr=STDOUT, text=True
        )

        def f():
            while True:
                line = self.pipe.stdout.readline()
                if not line:
                    break
                self.callback(line[:-1])
            try:
                self.pipe.wait(10)
            except TimeoutExpired:
                self.pipe.kill()
            finally:
                self.callback("exited")

        Thread(target=f, daemon=True).start()

    def callback(self, line):
        print(line)

    def feed(self, cmd):
        self.pipe.stdin.write(cmd.strip() + "\n")
        self.pipe.stdin.flush()
