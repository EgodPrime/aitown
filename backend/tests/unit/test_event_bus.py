from aitown.kernel.event_bus import EventType, InMemoryEventBus
from aitown.repos.event_repo import Event


def test_publish_sets_created_at_if_none():
    bus = InMemoryEventBus()
    event = Event(event_type=EventType.NPC_DECISION, payload={})
    assert event.created_at is None
    bus.publish(event)
    assert event.created_at is not None


def test_subscribe_and_publish_calls_callback():
    bus = InMemoryEventBus()
    called = []

    def cb(evt):
        called.append(evt)

    bus.subscribe(EventType.NPC_DECISION, cb)
    bus.post_tick()
    assert len(called) == 1


def test_drain():
    bus = InMemoryEventBus()
    event1 = Event(event_type=EventType.NPC_DECISION, payload={})
    event2 = Event(event_type=EventType.NPC_ACTION, payload={})
    bus.events = [event1, event2]
    drained = bus.drain(EventType.NPC_DECISION)
    assert len(drained) == 1
    assert drained[0] is event1


def test_pre_tick_processes_actions():
    bus = InMemoryEventBus()
    action_called = []

    def action_cb(evt):
        action_called.append(evt)

    bus.subscribe(EventType.NPC_ACTION, action_cb)

    action_event = Event(event_type=EventType.NPC_ACTION, payload={})
    bus.events = [action_event]

    bus.pre_tick()
    assert len(action_called) == 1


def test_on_tick_marks_processed_events():
    bus = InMemoryEventBus()
    # Mock event_repo.mark_processed
    marked = []
    bus.event_repo.mark_processed = lambda id, ts: marked.append((id, ts))

    event1 = Event(event_type=EventType.NPC_DECISION, payload={}, processed=0)
    event2 = Event(event_type=EventType.NPC_ACTION, payload={}, processed=1, id=2)
    bus.events = [event1, event2]

    bus.on_tick()
    assert len(marked) == 1
    assert marked[0][0] == 2
    assert len(bus.events) == 1
    assert bus.events[0] is event1


def test_post_tick_creates_decision_event_and_calls_subscribers():
    bus = InMemoryEventBus()
    called = []

    def cb(evt):
        called.append(evt)

    bus.subscribe(EventType.NPC_DECISION, cb)

    initial_len = len(bus.events)
    bus.post_tick()
    assert len(bus.events) == initial_len  # since removed
    assert len(called) == 1
    assert called[0].event_type == EventType.NPC_DECISION


def test_drainI_iterator_yields_expected():
    bus = InMemoryEventBus()
    e1 = Event(event_type=EventType.NPC_DECISION, payload={})
    e2 = Event(event_type=EventType.NPC_ACTION, payload={})
    bus.events = [e1, e2]

    got = list(bus.drainI(EventType.NPC_DECISION))
    assert len(got) == 1
    assert got[0] is e1


def test_post_tick_calls_npc_memory_subscribers():
    bus = InMemoryEventBus()
    called = []

    def cb(evt):
        called.append(evt)

    bus.subscribe(EventType.NPC_MEMORY, cb)
    bus.post_tick()
    assert len(called) == 1
    assert called[0].event_type == EventType.NPC_MEMORY
