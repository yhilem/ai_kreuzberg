from __future__ import annotations

import sys
from functools import partial
from typing import TYPE_CHECKING, TypeVar, cast

from anyio import create_task_group
from anyio.to_thread import run_sync as any_io_run_sync

if TYPE_CHECKING:  # pragma: no cover
    from collections.abc import Callable, Coroutine

if sys.version_info >= (3, 10):
    from typing import ParamSpec
else:  # pragma: no cover
    from typing_extensions import ParamSpec

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
    return cast(T, await any_io_run_sync(handler, *args, abandon_on_cancel=True))  # pyright: ignore [reportCallIssue]


async def run_taskgroup(*async_tasks: Callable[[], Coroutine[None, None, T]]) -> list[T]:
    """Run a list of coroutines concurrently.

    Args:
        *async_tasks: The list of coroutines to run.

    Returns:
        The results of the coroutines.
    """
    results = cast(list[T], [None] * len(async_tasks))

    async def run_task(index: int, task: Callable[[], Coroutine[None, None, T]]) -> None:
        results[index] = await task()

    async with create_task_group() as tg:
        for i, t in enumerate(async_tasks):
            tg.start_soon(run_task, i, t)

    return results


async def run_taskgroup_batched(*async_tasks: Callable[[], Coroutine[None, None, T]], batch_size: int) -> list[T]:
    """Run a list of coroutines concurrently in batches.

    Args:
        *async_tasks: The list of coroutines to run.
        batch_size: The size of each batch.

    Returns:
        The results of the coroutines.
    """
    results: list[T] = []

    for i in range(0, len(async_tasks), batch_size):
        batch = async_tasks[i : i + batch_size]
        results.extend(await run_taskgroup(*batch))

    return results
