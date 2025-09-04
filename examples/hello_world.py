#!/usr/bin/env python3

from persishell import PersiShell

sh = PersiShell()

sh.export("MYVAR", "123")
sh.run("echo $MYVAR")  # prints: 123

sh.unset("MYVAR")
sh.run("echo $MYVAR")  # prints nothing
