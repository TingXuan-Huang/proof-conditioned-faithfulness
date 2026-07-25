"""Internal process launcher applying the trusted-checker OS sandbox."""

from __future__ import annotations

import ctypes
import errno
import math
import os
import platform
import resource
import sys

_PR_SET_NO_NEW_PRIVS = 38
_PR_SET_SECCOMP = 22
_SECCOMP_MODE_FILTER = 2
_SECCOMP_RET_ALLOW = 0x7FFF0000
_SECCOMP_RET_ERRNO = 0x00050000
_BPF_LOAD_SYSCALL = 0x20
_BPF_JUMP_EQUAL = 0x15
_BPF_RETURN = 0x06
_SOCKET_SYSCALLS = {
    "x86_64": (
        41,
        42,
        43,
        44,
        45,
        46,
        47,
        48,
        49,
        50,
        51,
        52,
        53,
        54,
        55,
        288,
        299,
        307,
    ),
    "aarch64": (
        198,
        199,
        200,
        201,
        202,
        203,
        204,
        205,
        206,
        207,
        208,
        209,
        210,
        211,
        212,
        242,
        243,
        269,
    ),
}


class _SockFilter(ctypes.Structure):
    _fields_ = [
        ("code", ctypes.c_ushort),
        ("jt", ctypes.c_ubyte),
        ("jf", ctypes.c_ubyte),
        ("k", ctypes.c_uint32),
    ]


class _SockFprog(ctypes.Structure):
    _fields_ = [
        ("length", ctypes.c_ushort),
        ("filters", ctypes.POINTER(_SockFilter)),
    ]


_LIBC = ctypes.CDLL(None, use_errno=True)


def main(arguments: list[str] | None = None) -> int:
    """Apply limits and replace this launcher with the requested command."""
    values = sys.argv[1:] if arguments is None else arguments
    if len(values) < 4 or values[2] != "--":
        print("PF_SANDBOX_SETUP_ERROR:invalid launcher arguments", file=sys.stderr)
        return 126
    try:
        timeout_seconds = float(values[0])
        memory_limit_mb = int(values[1])
        if not math.isfinite(timeout_seconds) or timeout_seconds <= 0:
            raise ValueError("timeout must be finite and positive")
        if memory_limit_mb <= 0:
            raise ValueError("memory limit must be positive")
        _apply_limits(timeout_seconds=timeout_seconds, memory_limit_mb=memory_limit_mb)
        _install_socket_seccomp_filter()
        os.execvpe(values[3], values[3:], os.environ)
    except (OSError, ValueError) as error:
        print(f"PF_SANDBOX_SETUP_ERROR:{type(error).__name__}:{error}", file=sys.stderr)
        return 126
    return 126


def _apply_limits(*, timeout_seconds: float, memory_limit_mb: int) -> None:
    memory_bytes = memory_limit_mb * 1024 * 1024
    resource.setrlimit(resource.RLIMIT_AS, (memory_bytes, memory_bytes))
    cpu_seconds = max(1, math.ceil(timeout_seconds))
    resource.setrlimit(resource.RLIMIT_CPU, (cpu_seconds, cpu_seconds + 1))
    resource.setrlimit(resource.RLIMIT_FSIZE, (8 * 1024 * 1024, 8 * 1024 * 1024))
    resource.setrlimit(resource.RLIMIT_NOFILE, (128, 128))


def _install_socket_seccomp_filter() -> None:
    architecture = platform.machine().lower()
    syscalls = _SOCKET_SYSCALLS.get(architecture)
    if syscalls is None:
        raise OSError(errno.ENOTSUP, f"Unsupported seccomp architecture: {architecture}")
    instructions: list[_SockFilter] = [_SockFilter(_BPF_LOAD_SYSCALL, 0, 0, 0)]
    for syscall_number in syscalls:
        instructions.append(_SockFilter(_BPF_JUMP_EQUAL, 0, 1, syscall_number))
        instructions.append(_SockFilter(_BPF_RETURN, 0, 0, _SECCOMP_RET_ERRNO | errno.EPERM))
    instructions.append(_SockFilter(_BPF_RETURN, 0, 0, _SECCOMP_RET_ALLOW))
    filter_array = (_SockFilter * len(instructions))(*instructions)
    program = _SockFprog(len(instructions), filter_array)
    if _LIBC.prctl(_PR_SET_NO_NEW_PRIVS, 1, 0, 0, 0) != 0:
        error_number = ctypes.get_errno()
        raise OSError(error_number, os.strerror(error_number))
    if _LIBC.prctl(_PR_SET_SECCOMP, _SECCOMP_MODE_FILTER, ctypes.byref(program)) != 0:
        error_number = ctypes.get_errno()
        raise OSError(error_number, os.strerror(error_number))


if __name__ == "__main__":
    raise SystemExit(main())
