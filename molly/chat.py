from __future__ import annotations

import logging

from molly.adapters import ChatMessage, DummyAdapter, LMStudioAdapter, ModelAdapter
from molly.config import load_settings
from molly.db import DbConnInfo, create_db_engine
from molly.log import setup_logging
from molly.session import make_session_factory, session_scope
from molly.repos import ConversationRepo, MessageRepo
from molly.prompts import TITLE_SYSTEM, SUMMARY_SYSTEM, make_title_prompt, make_summary_prompt


def get_adapter(settings) -> ModelAdapter:
    if settings.model_adapter == "dummy":
        return DummyAdapter()
    if settings.model_adapter == "lmstudio":
        return LMStudioAdapter(settings)
    raise ValueError(f"Unknown adapter: {settings.model_adapter}")


def run_chat(conversation_id: str | None = None) -> int:
    settings = load_settings()
    setup_logging(settings.log_level)
    log = logging.getLogger("molly.chat")

    adapter = get_adapter(settings)  # create once per chat session
    print(f"Adapter: {adapter.name}")
    limit = settings.model_context_messages

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

    # Fetch system prompt once per session
    with session_scope(sf) as s:
        convo = ConversationRepo(s).get(conversation_id)
        if convo is None:
            print(f"Conversation not found ❌ ({conversation_id})")
            return 2
        system_prompt = convo.system_prompt

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

            # Fetch recent history (tail)
            with session_scope(sf) as s:
                tail = MessageRepo(s).tail_for_conversation(conversation_id=conversation_id, limit=limit)
                convo = ConversationRepo(s).get(conversation_id)
                convo_summary = None if convo is None else convo.summary

            # Build model context:
            # system prompt + (optional) summary + last N messages
            history = [ChatMessage(role="system", content=system_prompt)]
            if convo_summary:
                history.append(
                    ChatMessage(role="system", content=f"Conversation summary:\n{convo_summary}")
                )
            history += [ChatMessage(role=m.role, content=m.content) for m in tail]

            assistant_text = adapter.generate(history)

            # Save assistant message
            with session_scope(sf) as s:
                MessageRepo(s).add(conversation_id=conversation_id, role="assistant", content=assistant_text)

            print(f"Molly> {assistant_text}")

            # ---- Step 11: auto-title + rolling summary (AFTER saving assistant message) ----
            with session_scope(sf) as s:
                convo_repo = ConversationRepo(s)
                msg_repo = MessageRepo(s)
                convo = convo_repo.get(conversation_id)
                if convo is None:
                    continue  # extremely unlikely

                # Auto-title once (only if empty)
                if not convo.title:
                    recent = msg_repo.tail_for_conversation(conversation_id, limit=6)
                    title_input = [f"{m.role}: {m.content}" for m in recent]
                    title_msgs = [
                        ChatMessage(role="system", content=TITLE_SYSTEM),
                        ChatMessage(role="user", content=make_title_prompt(title_input)),
                    ]
                    try:
                        new_title = adapter.generate(title_msgs).strip().strip('"').strip()
                        if new_title:
                            convo_repo.set_title(conversation_id, new_title)
                    except Exception:
                        log.exception("Auto-title failed")

                # Rolling summary (update every turn, v1 simple & reliable)
                recent = msg_repo.tail_for_conversation(conversation_id, limit=12)
                summary_input = [f"{m.role}: {m.content}" for m in recent]
                summary_msgs = [
                    ChatMessage(role="system", content=SUMMARY_SYSTEM),
                    ChatMessage(role="user", content=make_summary_prompt(convo.summary, summary_input)),
                ]
                try:
                    new_summary = adapter.generate(summary_msgs).strip()
                    if new_summary:
                        convo_repo.set_summary(conversation_id, new_summary)
                except Exception:
                    log.exception("Summary update failed")

    except KeyboardInterrupt:
        print("\nMolly> Bye.")
        log.info("Chat exited via KeyboardInterrupt")
        return 0