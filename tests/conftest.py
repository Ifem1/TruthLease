"""Windows-only compatibility for gltest's stdin temporary-file injection.

gltest v0.29 unlinks the file immediately after dup2(). Windows keeps that file
open through fd 0, so the unlink raises WinError 32 before a contract is loaded.
The deferred unlink is test-only and happens after pytest has released the VM.
"""

import os
import sys


_deferred_unlinks: list[str] = []
_original_unlink = os.unlink


def pytest_configure() -> None:
    if sys.platform != "win32":
        return
    def defer_open_stdin_unlink(path: str, *args, **kwargs) -> None:
        try:
            _original_unlink(path, *args, **kwargs)
        except PermissionError:
            _deferred_unlinks.append(path)

    # loader imports os inside _inject_message_to_fd0, so patch the process
    # module only for the pytest session and restore it in sessionfinish.
    os.unlink = defer_open_stdin_unlink


def pytest_sessionfinish(session, exitstatus) -> None:
    for path in _deferred_unlinks:
        try:
            os.unlink(path)
        except OSError:
            pass
    os.unlink = _original_unlink
