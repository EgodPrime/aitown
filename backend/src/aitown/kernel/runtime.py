"""Kernel runtime wrapper that composes the existing SimClock and exposes
a stable runtime interface for services (npc_service, player_service).

This thin façade keeps existing `SimClock` behavior while providing a clear
API for emit_event, schedule_action, and lifecycle methods.
"""
from __future__ import annotations

import time
from typing import Optional, Callable
from loguru import logger

from aitown.kernel.sim_clock import SimClock, ClockError
from aitown.kernel.event_bus import InMemoryEventBus
from aitown.repos.event_repo import EventRepository, Event
import threading


class KernelRuntime:
    """A minimal runtime that owns a SimClock and exposes a runtime interface.
    """

    def __init__(self, sim_clock: Optional[SimClock] = None, event_bus: Optional[InMemoryEventBus] = None):
        self.sim_clock = sim_clock or SimClock()
        # allow injecting a preconfigured event bus
        if event_bus is not None:
            self.sim_clock.event_bus = event_bus
        self.worker_thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()

    # Lifecycle methods delegate to SimClock
    def start(self) -> None:
        self.sim_clock.start()
        self._stop_event.clear()
        self.worker_thread = threading.Thread(target=self.working, daemon=True)
        self.worker_thread.start()

    def stop(self) -> None:
        self._stop_event.set()
        if self.worker_thread is not None:
            self.worker_thread.join()
        self.sim_clock.stop()

    def working(self) -> None:
        while 1 :
            if self._stop_event.is_set():
                break
            try:
                self.sim_clock.step(1)
            except ClockError as e:
                logger.error(f"ClockError in working loop: {e}")
                break
            time.sleep(self.sim_clock.tick_interval_seconds)  # prevent tight loop

    def running(self) -> bool:
        return self.sim_clock.running

    def tick_count(self) -> int:
        return self.sim_clock.tick_count
    
    @property
    def event_bus(self) -> InMemoryEventBus:
        return self.sim_clock.event_bus

    def get_sim_time(self) -> int:
        return self.sim_clock.tick_count
