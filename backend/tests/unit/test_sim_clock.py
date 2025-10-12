import time

import pytest

from aitown.kernel.event_bus import EventType
from aitown.kernel.sim_clock import ClockError, SimClock
from aitown.repos.event_repo import Event
from aitown.helpers.db_helper import init_db
from aitown.repos.town_repo import TownRepository


def test_tick_phases_and_event_flow():
    clock = SimClock()
    bus = clock.event_bus

    processed = []

    # subscriber to action_processed to record processing
    def on_action_processed(evt):
        processed.append(("processed", evt))

    bus.subscribe(EventType.NPC_ACTION, on_action_processed)

    # subscriber to post_tick to publish an action for next pre_tick
    def on_post(evt):
        # simulate an NPC decision producing an action event
        bus.publish(
            Event(
                event_type=EventType.NPC_ACTION,
                payload={"action": "do_something"},
                created_at=time.time(),
            )
        )

    bus.subscribe(EventType.NPC_DECISION, on_post)

    # run 3 steps synchronously
    clock.step(3)

    # After three steps, we should have processed at least some actions
    # There should be processed entries for actions created in previous post_tick
    assert any(p[0] == "processed" for p in processed)


def test_step_emits_ticks():
    clock = SimClock()
    bus = clock.event_bus
    assert clock.tick_count == 0
    clock.step(3)
    assert clock.tick_count == 3


def test_start_and_step_and_running_flag():
    clock = SimClock()
    assert not clock.running
    clock.start()
    assert clock.running
    clock.step(1)
    assert clock.tick_count == 1
    clock.stop()
    assert not clock.running


def test_subscriber_callback_called():
    clock = SimClock()
    bus = clock.event_bus
    called = []

    def cb(payload):
        called.append(payload)

    bus.subscribe(EventType.NPC_DECISION, cb)

    clock.step(2)
    assert len(called) == 2


def test_start_already_running():
    clock = SimClock()
    clock.start()
    assert clock.running
    # start again should do nothing
    clock.start()
    assert clock.running


def test_start_negative_tick_interval(monkeypatch):
    monkeypatch.setattr("aitown.kernel.sim_clock.cfg_kernel", {"tick_interval_seconds": -10})
    clock = SimClock()
    with pytest.raises(ClockError, match="tick_interval_seconds must be non-negative"):
        clock.start()


def test_step_negative_steps():
    clock = SimClock()
    with pytest.raises(ClockError, match="steps must be non-negative"):
        clock.step(-1)


def test_get_town_time_from_timestamp_returns_formatted():
    # prepare an in-memory DB and set town start time so the static method can compute
    conn = init_db(":memory:")
    repo = TownRepository(conn)
    # insert town row directly via SQL to populate created_at column used by get_by_id
    cur = conn.cursor()
    cur.execute("INSERT INTO town (id, name, description, sim_start_time) VALUES (?,?,?,?)", ("town:001", "X", "d", 0.0))
    conn.commit()

    # monkeypatch TownRepository used inside SimClock.get_town_time_from_timestamp
    import aitown.kernel.sim_clock as scmod
    monkey_repo = lambda *args, **kwargs: repo
    setattr(scmod, "TownRepository", lambda *a, **k: repo)

    # now timestamp at tick interval 90 * (24*1 + 5) -> 1 day and 5 hours
    ts = (24 + 5) * 90.0
    s = SimClock.get_town_time_from_timestamp(ts)
    assert "第1天05点" in s
