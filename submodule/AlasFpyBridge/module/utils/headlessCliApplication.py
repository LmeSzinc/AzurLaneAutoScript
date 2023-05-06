import shlex
from subprocess import PIPE, STDOUT, Popen
from threading import Thread


class HeadlessCliApplication:
    """Wrap a cli application to provide programmable interactive access"""

    def __init__(self, cmd):
        self.pipe = Popen(shlex.split(cmd), stdin=PIPE, stdout=PIPE, stderr=STDOUT, text=True, encoding="UTF-8")

        def f():
            while self.pipe.poll() is None:
                self.callback(self.pipe.stdout.readline()[:-1])
            self.callback("exited")

        Thread(target=f, daemon=True).start()

    def callback(self, line):
        print(line)

    def feed(self, cmd):
        self.pipe.stdin.write(cmd.strip() + "\n")
        self.pipe.stdin.flush()
