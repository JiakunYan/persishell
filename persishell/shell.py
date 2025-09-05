import re
import subprocess
import os
import sys
import threading
import random
import fcntl
import time

def set_nonblocking(fd):
    """Set the file descriptor to non-blocking mode."""
    flags = fcntl.fcntl(fd, fcntl.F_GETFL)
    fcntl.fcntl(fd, fcntl.F_SETFL, flags | os.O_NONBLOCK)

class ThreadReadio(threading.Thread):
    def __init__(self, process, pipe, outfile, secret, command):
        super().__init__()
        self.ret = None
        self.returncode = None
        self.process = process
        self.pipe = pipe
        self.outfile = outfile
        self.secret = secret
        self.command = command
        self.terminator_pattern = re.compile(
            rf"\n__PERSISHELL_END__(\d+)__{self.secret}__\n"
        )

    def run(self):
        set_nonblocking(self.pipe.fileno())
        buffer = ""
        while self.process.poll() is None:
            try:
                chunk = self.pipe.read().decode("utf-8", errors="replace")
                if chunk:
                    buffer += chunk
                    match = self.terminator_pattern.search(buffer)
                    if match:
                        self.returncode = int(match.group(1))
                        buffer = self.terminator_pattern.sub("", buffer)
                        if len(chunk) < len(match.group(0)):
                            chunk = ""
                        else:
                            chunk = self.terminator_pattern.sub("", chunk)
                    if self.outfile:
                        print(chunk, file=self.outfile, end='', flush=True)
                    if match:
                        break;
            except AttributeError:
                pass
            time.sleep(0.5)
        self.ret = buffer


class PersiShell:
    class CompletedProcess:
        def __init__(self, args, returncode, stdout, stderr):
            self.args = args
            self.returncode = returncode
            self.stdout = stdout
            self.stderr = stderr

    def __init__(self):
        # We do not use 'with' here because the shell process is meant to
        # persist for the lifetime of this object.
        self.proc = subprocess.Popen(['bash'], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                     stderr=subprocess.PIPE, close_fds=False)

    def close(self):
        """Terminate the persistent shell process and clean up resources."""
        if self.proc and self.proc.poll() is None:
            self.proc.terminate()
            try:
                self.proc.wait(timeout=2)
            except subprocess.TimeoutExpired:
                self.proc.kill()
                self.proc.wait()

    def __del__(self):
        self.close()

    # Run a command in the persistent shell
    def run(self, command, print_command=True, print_output=True, timeout=None):
        if isinstance(command, (list, tuple)):
            command = " ".join(command)

        secret = random.randint(1, 1_000_000_000)
        term_format = "\n__PERSISHELL_END__%s__" + str(secret) + "__\n"

        cmd = (
            f"{command}; "
            f"printf \"{term_format}\" $?; "
            f">&2 printf \"{term_format}\" $?\n"
        )

        if print_command:
            print("PersiShell.run: " + command)
            sys.stdout.flush()
        self.proc.stdin.write(cmd.encode('UTF-8'))
        self.proc.stdin.flush()

        t1 = ThreadReadio(self.proc, self.proc.stdout, sys.stdout if print_output else None,
                          secret, command)
        t2 = ThreadReadio(self.proc, self.proc.stderr, sys.stderr if print_output else None,
                          secret, command)

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
                raise TimeoutError("Timeout")
        else:
            t1.join()
            t2.join()

        returncode = t1.returncode if t1.returncode is not None else t2.returncode or -1
        return self.CompletedProcess(command, returncode, t1.ret, t2.ret)

    # Convenience functions
    def export(self, key, val):
        ret = self.run(f"export {key}={val}")
        return ret.returncode

    def unset(self, key):
        ret = self.run(f"unset {key}")
        return ret.returncode
    