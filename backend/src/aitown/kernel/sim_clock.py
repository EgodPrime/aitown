"""Simple simulation clock that emits ticks via a pluggable event bus.

This implementation is synchronous and test-friendly. It supports start(), stop(),
step(), and set_scale(). By default it uses a minimal in-memory event bus interface
that expects a `publish(event_name, payload)` method.
"""
from __future__ import annotations

import time
from typing import Callable, Optional
from aitown.repos.event_repo import Event
from aitown.kernel.event_bus import InMemoryEventBus, EventType
from aitown.helpers.config_helper import get_config

class ClockError(Exception):
    pass


class SimClock:
    def __init__(self):
        # load configuration
        cfg = get_config("kernel")
        self.tick_interval_seconds: float = cfg.get("tick_interval_seconds", 90.0)
        self.event_bus: InMemoryEventBus = InMemoryEventBus()

        self._running: bool = False
        self._last_tick_ts: Optional[float] = None
        self._tick_count: int = 0

    def start(self) -> None:
        if self._running:
            return
        if self.tick_interval_seconds < 0:
            raise ClockError("tick_interval_seconds must be non-negative")
        self._running = True
        self._last_tick_ts = time.time()

    def stop(self) -> None:
        self._running = False

    def step(self, steps: int = 1) -> None:
        if steps < 0:
            raise ClockError("steps must be non-negative")
        for _ in range(steps):
            self._tick()
            # if a real-time delay is desired between steps, caller should sleep

    def _tick(self) -> None:
        """Run one tick cycle: pre_tick -> on_tick -> post_tick.
        """
        self.event_bus.pre_tick()
        self.event_bus.on_tick()
        self.event_bus.post_tick()

        # update internal state
        self._tick_count += 1
        self._last_tick_ts = time.time()

    @property
    def running(self) -> bool:
        return self._running

    @property
    def tick_count(self) -> int:
        return self._tick_count