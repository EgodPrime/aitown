import datetime
import time
import pytest

import aitown.repos.event_repo as event_mod


def test_event_repo_append_fetch_mark(db_conn):
    Repo = event_mod.EventRepository
    repo = Repo(db_conn)

    now = time.time()
    payload = {"foo": "bar"}
    evt = event_mod.Event(
        id=None, event_type="test_event", payload=payload, created_at=now
    )
    eid = repo.append_event(evt)
    assert isinstance(eid, int)

    events = repo.fetch_unprocessed(limit=10)
    assert any(e.id == eid for e in events)
    ev = next(e for e in events if e.id == eid)
    assert ev.payload == payload

    processed_time = time.time()
    repo.mark_processed(eid, processed_time)
    events2 = repo.fetch_unprocessed(limit=10)
    assert all(e.id != eid for e in events2)
