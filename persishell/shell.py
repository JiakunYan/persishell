import re
from subprocess import Popen, PIPE
import os, sys
import threading
import random
import fcntl
import time

def set_nonblocking(fd):
    """Set the file descriptor to non-blocking mode."""
    flags = fcntl.fcntl(fd, fcntl.F_GETFL)
    fcntl.fcntl(fd, fcntl.F_SETFL, flags | os.O_NONBLOCK)

class ThreadReadio(threading.Thread):
    def __init__(self, process, pipe, outfile, term_words, command):
        threading.Thread.__init__(self)
        self.ret = None
        self.returncode = 0
        self.process = process
        self.pipe = pipe
        self.outfile = outfile
        self.term_words = term_words
        self.command = command

    def run(self):
        set_nonblocking(self.pipe.fileno())
        content = ""
        while self.process.poll() is None:  # Keep running while process is active
            try:
                text = self.pipe.read().decode("utf-8", errors="replace")
                if text:
                    content = content + text                        
                    to_break = False
                    if content.endswith(self.term_words):
                        to_break = True
                        content = content[:-len(self.term_words)]
                        text = text[:-len(self.term_words)]
                    if self.outfile:
                        print(text, file=self.outfile, end='', flush=True)
                    if to_break:
                        break
            except Exception:
                pass
            time.sleep(0.5)
        self.ret = content


class PersiShell:
    class CompletedProcess:
        def __init__(self, args, returncode, stdout, stderr):
            self.args = args
            self.returncode = returncode
            self.stdout = stdout
            self.stderr = stderr

    def __init__(self):
        self.proc = Popen(['bash'], stdin=PIPE, stdout=PIPE, stderr=PIPE, close_fds=False)

    # Run a command in the persistent shell
    def run(self, command, print_output=True, timeout=None):
        if type(command) is list or type(command) is tuple:
            command = " ".join(command)
        secret = random.random()
        term_words = f"\n__PERSISHELL_END__{secret}__\n"
        # cmd = command + "; printf \"{}\"; >&2 printf \"{}\"\n".format(term_words, term_words)
        # cmd = f"{command}; RETVAL=$?; printf \"{term_words}$RETVAL\"; >&2 printf \"{term_words}\"\n"
        cmd = (
            f"{command}; "
            f"printf \"{term_words}\"; "
            f">&2 printf \"{term_words}\"\n"
        )
        print("PersiShell.run: " + command)
        sys.stdout.flush()
        self.proc.stdin.write(cmd.encode('UTF-8'))
        self.proc.stdin.flush()

        if print_output:
            t1 = ThreadReadio(self.proc, self.proc.stdout, sys.stdout, term_words, command)
            t2 = ThreadReadio(self.proc, self.proc.stderr, sys.stderr, term_words, command)
        else:
            t1 = ThreadReadio(self.proc, self.proc.stdout, None, term_words, command)
            t2 = ThreadReadio(self.proc, self.proc.stderr, None, term_words, command)
        t1.start()
        t2.start()
        # timeout
        if timeout:
            t1.join(timeout)
            t2.join(timeout)
            if t1.is_alive() or t2.is_alive():
                print("PersiShell.run: killing process")
                self.proc.kill()
                self.proc.wait()
                raise Exception("Timeout")
        else:
            t1.join()
            t2.join()
        
        return self.CompletedProcess(command, t1.returncode, t1.ret, t2.ret)
    
    # Convenience functions
    def export(self, key, val):
        ret = self.run("export {}={}".format(key, val))
        return ret.returncode

    def unset(self, key):
        ret = self.run("unset {}".format(key))
        return ret.returncode