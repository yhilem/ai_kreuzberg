from __future__ import annotations

from functools import partial
from typing import TYPE_CHECKING, TypeVar, cast

from anyio.to_thread import run_sync as any_io_run_sync
from typing_extensions import ParamSpec

if TYPE_CHECKING:  # pragma: no cover
    from collections.abc import Callable

T = TypeVar("T")
P = ParamSpec("P")


async def run_sync(sync_fn: Callable[P, T], *args: P.args, **kwargs: P.kwargs) -> T:
    """Run a synchronous function in an asynchronous context.

    Args:
        sync_fn: The synchronous function to run.
        *args: The positional arguments to pass to the function.
        **kwargs: The keyword arguments to pass to the function.

    Returns:
        The result of the synchronous function.
    """
    handler = partial(sync_fn, **kwargs)
    return cast(T, await any_io_run_sync(handler, *args))  # pyright: ignore [reportCallIssue]
