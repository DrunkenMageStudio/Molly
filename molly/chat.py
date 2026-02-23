from __future__ import annotations

import logging
from molly.adapters import ChatMessage, DummyAdapter, ModelAdapter

from molly.config import load_settings
from molly.db import DbConnInfo, create_db_engine
from molly.log import setup_logging
from molly.session import make_session_factory, session_scope
from molly.repos import ConversationRepo, MessageRepo

def get_adapter(name: str) -> ModelAdapter:
    if name == "dummy":
        return DummyAdapter()
    raise ValueError(f"Unknown adapter: {name}")

def run_chat(conversation_id: str | None = None) -> int:
    settings = load_settings()
    setup_logging(settings.log_level)
    log = logging.getLogger("molly.chat")

    cfg = DbConnInfo(
        host=settings.db.host,
        port=settings.db.port,
        name=settings.db.name,
        user=settings.db.user,
        password=settings.db.password,
    )
    engine = create_db_engine(cfg)
    sf = make_session_factory(engine)

    # Create or load a conversation
    with session_scope(sf) as s:
        convo_repo = ConversationRepo(s)
        if conversation_id:
            convo = convo_repo.get(conversation_id)
            if convo is None:
                print(f"Conversation not found ❌ ({conversation_id})")
                return 2
        else:
            convo = convo_repo.create(title=None)
            conversation_id = convo.id

    print(f"Conversation: {conversation_id}")
    print("Type 'exit' or 'quit' to leave.\n")

    try:
        while True:
            user_text = input("You> ").strip()
            if not user_text:
                continue
            if user_text.lower() in {"exit", "quit"}:
                print("Molly> Bye.")
                return 0

            # Save user message
            with session_scope(sf) as s:
                MessageRepo(s).add(conversation_id=conversation_id, role="user", content=user_text)

            adapter = get_adapter(settings.model_adapter)
            limit = settings.model_context_messages

            with session_scope(sf) as s:
                tail = MessageRepo(s).tail_for_conversation(conversation_id=conversation_id, limit=limit)

            history = [ChatMessage(role=m.role, content=m.content) for m in tail]
            assistant_text = adapter.generate(history)

            # Save assistant message
            with session_scope(sf) as s:
                MessageRepo(s).add(conversation_id=conversation_id, role="assistant", content=assistant_text)

            print(f"Molly> {assistant_text}")

    except KeyboardInterrupt:
        print("\nMolly> Bye.")
        log.info("Chat exited via KeyboardInterrupt")
        return 0