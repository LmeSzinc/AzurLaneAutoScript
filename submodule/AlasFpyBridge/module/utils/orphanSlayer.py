import os
import platform
import time

if platform.system() == "Windows":
    def isProcessExist(pid):
        with os.popen(f'tasklist /NH /FI "PID eq {pid}"') as p:
            return p.read()[0] == "\n"
else:
    def isProcessExist(pid):
        try:
            os.kill(pid, 0)
        except OSError:
            return False
        else:
            return True


def orphanSlayer(ppid, spid, kill = ""):
    """
    module.webui.process_manager.ProcessManager.stop() uses kill() to stop subprocess
    and to a large extent it cannot be changed to terminate(), see #883

    In *nix systems, process created by subprosecc.Popen does not exit with the parent process,
    and there are no options of daemon=True, etc.
    So there need to be some way to ensure sub-subprocess to be killed other than capturing SIGTERM,
    such as:

    1. Set subprocess to a new process group and killpg() in ProcessManager.stop()
    2. Try to terminate() or send other signals before kill()
    3. Make sub-subprocess end itself when it does not receive a heartbeat

    All of these seemingly elegant solutions require invasive changes,
    therefore, I choose to open another process, once the father dead, kill the son as well
    So called orphanSlayer

    Lme曰：「你可以通过经常拉屎，来结交朋友（」
    """
    while isProcessExist(ppid):
        if not isProcessExist(spid):
            return
        time.sleep(1)
    if kill:
        os.system(f"{kill} {spid}")
    else:
        os.kill(spid, 9)


if __name__ == "__main__":
    # python orphanSlayer.py 114 514 "docker stop ..."
    import sys

    orphanSlayer(int(sys.argv[1]), int(sys.argv[2]), sys.argv[3])
