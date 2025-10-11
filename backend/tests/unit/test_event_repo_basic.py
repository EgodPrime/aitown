import datetime

from aitown.helpers.db_helper import init_db
from aitown.repos import event_repo


def test_event_repo_append_fetch_mark():
    conn = init_db(":memory:")
    Repo = event_repo.EventRepository
    repo = Repo(conn)

    now = datetime.datetime.now().isoformat()
    payload = {"foo": "bar"}
    evt = event_repo.Event(
        id=None, event_type="test_event", payload=payload, created_at=now
    )
    eid = repo.append_event(evt)
    assert isinstance(eid, int)

    events = repo.fetch_unprocessed(limit=10)
    assert any(e.id == eid for e in events)
    ev = next(e for e in events if e.id == eid)
    assert ev.payload == payload

    processed_time = datetime.datetime.now().isoformat()
    repo.mark_processed(eid, processed_time)
    events2 = repo.fetch_unprocessed(limit=10)
    assert all(e.id != eid for e in events2)

    conn.close()
