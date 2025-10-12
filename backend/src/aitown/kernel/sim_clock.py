"""Simple simulation clock that emits ticks via a pluggable event bus.

This implementation is synchronous and test-friendly. It supports start(), stop(),
step(), and set_scale(). By default it uses a minimal in-memory event bus interface
that expects a `publish(event_name, payload)` method.
"""

from __future__ import annotations

import time
from typing import Optional
from loguru import logger

from aitown.helpers.config_helper import get_config
from aitown.kernel.event_bus import EventType, InMemoryEventBus
from aitown.kernel.npc_actions import ActionExecutor
from aitown.repos.town_repo import TownRepository


class ClockError(Exception):
    pass

cfg_town = get_config("town")
cfg_kernel = get_config("kernel")


class SimClock:
    def __init__(self):
        # load configuration
        self.town_id: str = cfg_town.get("town_id", "town:001")
        self.town_repo = TownRepository(None)
        self.tick_interval_seconds: float = cfg_kernel.get("tick_interval_seconds", 90.0)
        self.event_bus: InMemoryEventBus = InMemoryEventBus()
        self.event_bus.subscribe(EventType.NPC_ACTION, ActionExecutor.event_listener)

        self._running: bool = False
        self._last_tick_ts: Optional[float] = None
        self._tick_count: int = 0 # sim hour

    def start(self) -> None:
        if self._running:
            return
        if self.tick_interval_seconds < 0:
            raise ClockError("tick_interval_seconds must be non-negative")
        self._running = True
        self._last_tick_ts = time.time()
        self.town_repo.set_sim_start_time(self.town_id, self._last_tick_ts)

    def stop(self) -> None:
        self._running = False

    def step(self, steps: int = 1) -> None:
        if steps < 0:
            raise ClockError("steps must be non-negative")
        for _ in range(steps):
            self._tick()
            # if a real-time delay is desired between steps, caller should sleep

    def _tick(self) -> None:
        """Run one tick cycle: pre_tick -> on_tick -> post_tick."""
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
    
    @staticmethod
    def get_town_time_from_timestamp(timestamp: float) -> str:
        """Convert a real-world timestamp to in-simulation time as 'DD-HH'."""
        town_id = cfg_town.get("town_id", "town:001")
        tick_interval_seconds = cfg_kernel.get("tick_interval_seconds", 90.0)
        town_start_time = TownRepository().get_sim_start_time(town_id)
        elapsed = timestamp - town_start_time
        total_ticks = int(elapsed / tick_interval_seconds)
        days = total_ticks // 24
        hours = total_ticks % 24
        return f"第{days}天{hours:02d}点"
