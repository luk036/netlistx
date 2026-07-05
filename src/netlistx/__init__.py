from collections.abc import MutableMapping
from importlib.metadata import PackageNotFoundError, version
from typing import Any, Iterator

try:
    # Change here if project is renamed and does not equal the package name
    dist_name = __name__
    __version__ = version(dist_name)
except PackageNotFoundError:  # pragma: no cover
    __version__ = "unknown"
finally:
    del version, PackageNotFoundError


class GapDict(MutableMapping):
    """Memory-efficient mutable view over a base weight mapping.

    Only stores *deltas* from the base values, avoiding a full copy of
    the weight dictionary.  Unmodified keys fall back to the base
    mapping with zero overhead.

    Typical usage replaces ``gap = copy.copy(weight)`` with
    ``gap = GapDict(weight)`` in primal-dual algorithms.
    """

    __slots__ = ("_base", "_delta")

    def __init__(self, base: MutableMapping) -> None:
        self._base = base
        self._delta: dict = {}

    def __getitem__(self, key: Any) -> Any:
        if key in self._delta:
            return self._delta[key]
        return self._base[key]

    def __setitem__(self, key: Any, value: Any) -> None:
        self._delta[key] = value

    def __delitem__(self, key: Any) -> None:
        del self._delta[key]

    def __iter__(self) -> Iterator:
        raise NotImplementedError("GapDict does not support iteration")

    def __len__(self) -> int:
        raise NotImplementedError("GapDict does not support len()")

    def __contains__(self, key: object) -> bool:
        return key in self._delta or key in self._base
