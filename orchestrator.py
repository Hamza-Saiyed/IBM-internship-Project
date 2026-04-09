import time
from agents.research import research_agent
from agents.summarizer import summarizer_agent
from agents.quiz_maker import quiz_agent


def run_study_assistant(topic: str, difficulty: str = "Medium", status_callback=None):
    """
    Orchestrator — coordinates all three agents sequentially and streams
    live status updates via an optional callback function.

    Error handling (API rate limits, key rotation, retries) is managed
    exclusively inside gemini_client.py. This function simply calls each
    agent in order and propagates any exceptions to the caller.

    Args:
        topic:           The study topic provided by the user.
        difficulty:      Quiz difficulty level — 'Easy', 'Medium', or 'Hard'.
        status_callback: Optional callable(message: str) for live UI updates.

    Returns:
        dict with keys: topic, research, notes, quiz, elapsed_time

    Raises:
        ValueError:   If topic is empty.
        RuntimeError: If any agent fails (propagated from gemini_client.py).
    """
    if not topic or not topic.strip():
        raise ValueError("Topic cannot be empty.")

    def _notify(msg: str):
        if status_callback:
            try:
                status_callback(msg)
            except Exception:
                pass  # Never let a UI callback crash the pipeline

    start_time = time.perf_counter()

    # ── Step 1: Research ──────────────────────────────────────────────────────
    _notify("🔍 Research Agent is scanning knowledge bases...")
    research_output = research_agent(topic)

    # ── Step 2: Summarizer ────────────────────────────────────────────────────
    _notify("📝 Summarizer Agent is distilling key insights...")
    notes_output = summarizer_agent(research_output)

    # ── Step 3: Quiz ──────────────────────────────────────────────────────────
    _notify(f"🧠 Quiz Agent is crafting {difficulty} questions...")
    quiz_output = quiz_agent(notes_output, difficulty=difficulty)

    elapsed = round(time.perf_counter() - start_time, 2)
    _notify(f"✅ All agents completed in {elapsed}s — packaging results...")

    return {
        "topic": topic,
        "research": research_output,
        "notes": notes_output,
        "quiz": quiz_output,
        "elapsed_time": elapsed,
    }


if __name__ == "__main__":
    topic = "What is Agentic AI?"

    def console_status(msg):
        print(f"  ▶ {msg}")

    result = run_study_assistant(topic, difficulty="Hard", status_callback=console_status)

    print("\n\n📦 FINAL STUDY PACKAGE")
    print("=" * 60)
    print(f"⏱  Completed in {result['elapsed_time']}s")
    print("\n📚 RESEARCH:\n", result["research"])
    print("\n📝 STUDY NOTES:\n", result["notes"])
    print("\n🧪 QUIZ:\n", result["quiz"])