from __future__ import annotations

import argparse
import logging

from molly.config import load_settings
from molly.db import DbConnInfo, create_db_engine, ping_db
from molly.log import setup_logging

from molly.session import make_session_factory, session_scope
from molly.repos import AppMetaRepo

from molly.repos import ConversationRepo, MessageRepo

def run_doctor() -> int:
    settings = load_settings()
    setup_logging(settings.log_level)
    log = logging.getLogger("molly.doctor")

    log.info("Doctor check: starting")

    cfg = DbConnInfo(
        host=settings.db.host,
        port=settings.db.port,
        name=settings.db.name,
        user=settings.db.user,
        password=settings.db.password,
    )

    try:
        engine = create_db_engine(cfg)
        ping_db(engine)
        log.info("DB: OK (connected and ran SELECT 1)")
        print("Doctor: DB OK ✅")
        return 0
    except Exception as e:
        log.exception("DB: FAILED")
        print(f"Doctor: DB FAILED ❌ ({type(e).__name__}: {e})")
        return 2


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="molly")
    sub = parser.add_subparsers(dest="cmd", required=True)

    # ---- doctor ----
    sub.add_parser("doctor", help="Run health checks")
    chat = sub.add_parser("chat", help="Interactive console chat (persists to DB)")
    chat.add_argument("conversation_id", nargs="?", default=None)

    # ---- db command group ----
    db = sub.add_parser("db", help="Database commands")
    db_sub = db.add_subparsers(dest="db_cmd", required=True)

    db_sub.add_parser("upgrade", help="Apply migrations (upgrade to head)")
    db_sub.add_parser("seed", help="Seed basic app metadata")
    db_sub.add_parser("show", help="Show basic app metadata")

    # ---- memory command group ----
    mem = sub.add_parser("memory", help="Memory commands")
    mem_sub = mem.add_subparsers(dest="mem_cmd", required=True)

    mem_sub.add_parser("new", help="Create a new conversation")

    add = mem_sub.add_parser("add", help="Add a message to a conversation")
    add.add_argument("conversation_id")
    add.add_argument("role")
    add.add_argument("content")

    show = mem_sub.add_parser("show", help="Show messages for a conversation")
    show.add_argument("conversation_id")

    args = parser.parse_args(argv)

    # ---- doctor ----
    if args.cmd == "doctor":
        return run_doctor()
    
    if args.cmd == "chat":
        from molly.chat import run_chat
        return run_chat(args.conversation_id)
    
    # ---- db upgrade ----
    if args.cmd == "db" and args.db_cmd == "upgrade":
        from molly.migrate import upgrade_head
        upgrade_head()
        print("DB upgraded to head ✅")
        return 0

    # ---- db seed ----
    if args.cmd == "db" and args.db_cmd == "seed":
        settings = load_settings()
        setup_logging(settings.log_level)

        cfg = DbConnInfo(
            host=settings.db.host,
            port=settings.db.port,
            name=settings.db.name,
            user=settings.db.user,
            password=settings.db.password,
        )

        engine = create_db_engine(cfg)
        sf = make_session_factory(engine)

        with session_scope(sf) as s:
            repo = AppMetaRepo(s)
            repo.upsert("schema", "v1")
            repo.upsert("app", "molly")

        print("DB seeded ✅")
        return 0

    # ---- db show ----
    if args.cmd == "db" and args.db_cmd == "show":
        settings = load_settings()
        setup_logging(settings.log_level)

        cfg = DbConnInfo(
            host=settings.db.host,
            port=settings.db.port,
            name=settings.db.name,
            user=settings.db.user,
            password=settings.db.password,
        )

        engine = create_db_engine(cfg)
        sf = make_session_factory(engine)

        with session_scope(sf) as s:
            repo = AppMetaRepo(s)
            schema = repo.get("schema")
            app = repo.get("app")

        print(f"app={app!r} schema={schema!r}")
        return 0

    # ---- memory new ----
    if args.cmd == "memory" and args.mem_cmd == "new":
        settings = load_settings()
        setup_logging(settings.log_level)

        cfg = DbConnInfo(
            host=settings.db.host,
            port=settings.db.port,
            name=settings.db.name,
            user=settings.db.user,
            password=settings.db.password,
        )

        engine = create_db_engine(cfg)
        sf = make_session_factory(engine)

        with session_scope(sf) as s:
            convo = ConversationRepo(s).create(title=None)
            convo_id = convo.id  # capture while still attached to session

        print(convo_id)
        return 0

    # ---- memory add ----
    if args.cmd == "memory" and args.mem_cmd == "add":
        settings = load_settings()
        setup_logging(settings.log_level)

        cfg = DbConnInfo(
            host=settings.db.host,
            port=settings.db.port,
            name=settings.db.name,
            user=settings.db.user,
            password=settings.db.password,
        )

        engine = create_db_engine(cfg)
        sf = make_session_factory(engine)

        with session_scope(sf) as s:
            convo = ConversationRepo(s).get(args.conversation_id)
            if convo is None:
                print(f"Conversation not found ❌ ({args.conversation_id})")
                return 2

            MessageRepo(s).add(
                conversation_id=args.conversation_id,
                role=args.role,
                content=args.content,
            )

        print("Message added ✅")
        return 0

    # ---- memory show ----
    if args.cmd == "memory" and args.mem_cmd == "show":
        settings = load_settings()
        setup_logging(settings.log_level)

        cfg = DbConnInfo(
            host=settings.db.host,
            port=settings.db.port,
            name=settings.db.name,
            user=settings.db.user,
            password=settings.db.password,
        )

        engine = create_db_engine(cfg)
        sf = make_session_factory(engine)

        with session_scope(sf) as s:
            convo = ConversationRepo(s).get(args.conversation_id)
            if convo is None:
                print(f"Conversation not found ❌ ({args.conversation_id})")
                return 2

            msgs = MessageRepo(s).list_for_conversation(args.conversation_id)

        for m in msgs:
            print(f"[{m.created_at}] {m.role}: {m.content}")

        return 0

    return 1