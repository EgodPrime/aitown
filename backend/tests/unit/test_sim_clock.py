import time
import pytest

from aitown.kernel.sim_clock import SimClock, InMemoryEventBus, ClockError
from aitown.kernel.event_bus import InMemoryEventBus, EventType
from aitown.repos.event_repo import Event


def test_tick_phases_and_event_flow():
    clock = SimClock()
    bus = clock.event_bus

    processed = []

    # subscriber to action_processed to record processing
    def on_action_processed(evt):
        processed.append(('processed', evt))

    bus.subscribe(EventType.NPC_ACTION, on_action_processed)

    # subscriber to post_tick to publish an action for next pre_tick
    def on_post(evt):
        # simulate an NPC decision producing an action event
        bus.publish(Event(event_type=EventType.NPC_ACTION, payload={"action": "do_something"}, created_at=time.strftime("%Y-%m-%dT%H:%M:%S")))

    bus.subscribe(EventType.NPC_DECISION, on_post)

    # run 3 steps synchronously
    clock.step(3)

    # After three steps, we should have processed at least some actions
    # There should be processed entries for actions created in previous post_tick
    assert any(p[0] == 'processed' for p in processed)


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
    def mock_get_config(section):
        if section == 'kernel':
            return {'tick_interval_seconds': -1.0}
        raise KeyError(section)
    
    monkeypatch.setattr('aitown.kernel.sim_clock.get_config', mock_get_config)
    clock = SimClock()
    with pytest.raises(ClockError, match="tick_interval_seconds must be non-negative"):
        clock.start()


def test_step_negative_steps():
    clock = SimClock()
    with pytest.raises(ClockError, match="steps must be non-negative"):
        clock.step(-1)
