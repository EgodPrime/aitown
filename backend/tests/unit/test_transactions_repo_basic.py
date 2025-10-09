from aitown.helpers.init_db import init_db
from aitown.repos import transactions_repo
import datetime


def test_transactions_append_and_list():
    conn = init_db(":memory:")
    Repo = transactions_repo.TransactionsRepository
    repo = Repo(conn)

    now = datetime.datetime.now().isoformat()
    # create referenced npc and item to satisfy FK constraints
    cur = conn.cursor()
    cur.execute("INSERT INTO npc (id) VALUES (?)", ("npc:1",))
    cur.execute("INSERT INTO item (id, name) VALUES (?,?)", ("item:1", "It"))
    conn.commit()

    tid = repo.append(npc_id="npc:1", item_id="item:1", amount=10, reason="test", created_at=now)
    assert isinstance(tid, int)

    rows = repo.list_by_npc("npc:1", limit=10)
    assert any(r.id == tid for r in rows)

    conn.close()


def test_transactions_list_empty_additional():
    conn = init_db(":memory:")
    Repo = transactions_repo.TransactionsRepository
    repo = Repo(conn)
    rows = repo.list_by_npc("nope", limit=5)
    assert rows == []
    conn.close()
