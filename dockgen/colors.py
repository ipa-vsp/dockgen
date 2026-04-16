"""
Terminal color helpers using ANSI escape codes.
Colors are automatically disabled when stdout/stderr is not a TTY.
"""
import sys

_RESET  = "\033[0m"
_BOLD   = "\033[1m"
_DIM    = "\033[2m"

_RED    = "\033[31m"
_GREEN  = "\033[32m"
_YELLOW = "\033[33m"
_CYAN   = "\033[36m"
_WHITE  = "\033[37m"


def _tty(stream=None):
    return (stream or sys.stdout).isatty()


def _c(code, text, stream=None):
    if not _tty(stream):
        return text
    return f"{code}{text}{_RESET}"


def bold(text):    return _c(_BOLD,           text)
def dim(text):     return _c(_DIM,            text)
def green(text):   return _c(_GREEN,          text)
def yellow(text):  return _c(_YELLOW,         text)
def cyan(text):    return _c(_CYAN,           text)
def red(text):     return _c(_RED,            text, sys.stderr)
def header(text):  return _c(_BOLD + _CYAN,   text)
def success(text): return _c(_BOLD + _GREEN,  text)
def warn(text):    return _c(_YELLOW,         text, sys.stderr)
def error(text):   return _c(_BOLD + _RED,    text, sys.stderr)
