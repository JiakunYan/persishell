# persishell

**Lightweight replacement for `os.system()` with a persistent environment.**

`persishell` is a simple Python library that wraps a persistent Bash subprocess, allowing you to run shell commands sequentially — with shared environment state across runs. It's useful when you need to maintain `export`ed variables, `cd` into directories, interact with `module load`, or configure shell settings once and use them across multiple commands.

I use it extensively on SLURM clusters to write all my experiment scripts (including the sbatch scripts) in Python.

## Installation

```bash
pip install persishell
```
Or for development:

```bash
pip install -e .
```

## Quick Start
```python
from persishell import PersiShell

sh = PersiShell()

# Set environment variables
sh.export("FOO", "bar")

# Commands use the persistent environment
sh.run("echo $FOO")  # prints: bar

# Change directories
sh.run("cd /tmp")
sh.run("pwd")  # prints: /tmp

# Unset environment variables
sh.unset("FOO")
sh.run("echo $FOO")  # prints an empty line
```

## API Summary
```python
PersiShell.run(command: str | list, optinal arguments)
```
Run a command inside the persistent shell. Accepts a string or a list of arguments.

```python
PersiShell.export(key: str, value: str)
```
Export a persistent environment variable.

```python
PersiShell.unset(key: str)
```
Unset a previously defined environment variable.

## Limitations
Currently designed for Unix-like systems (uses bash, fcntl). It has not been tested on Windows.

## License
MIT License