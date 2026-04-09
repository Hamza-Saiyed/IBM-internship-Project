from agents.gemini_client import call_gemini

# Difficulty-specific instructions injected into the prompt
_DIFFICULTY_INSTRUCTIONS = {
    "Easy": (
        "Create EASY questions: straightforward definitions and recall-level questions. "
        "Avoid tricky wording. All incorrect options should be obviously wrong."
    ),
    "Medium": (
        "Create MEDIUM difficulty questions: mix of comprehension and application. "
        "Distractors (wrong options) should be plausible but clearly wrong on reflection."
    ),
    "Hard": (
        "Create HARD questions: deep understanding, edge-case reasoning, and synthesis. "
        "All four options should seem plausible — only an expert will identify the correct answer."
    ),
}


def quiz_agent(study_notes: str, difficulty: str = "Medium", api_key: str = None) -> str:
    """
    Quiz Agent — generates MCQ questions from study notes at a given difficulty.

    Args:
        study_notes: The condensed study notes from the Summarizer Agent.
        difficulty: 'Easy', 'Medium', or 'Hard'. Defaults to 'Medium'.
        api_key: Optional override for the Gemini API key.

    Returns:
        A formatted string of quiz questions with answers.
    """
    diff_instruction = _DIFFICULTY_INSTRUCTIONS.get(difficulty, _DIFFICULTY_INSTRUCTIONS["Medium"])

    prompt = f"""You are an expert Quiz Creator and Educator.

Study Notes:
{study_notes}

DIFFICULTY LEVEL: {difficulty}
{diff_instruction}

Generate exactly 5 Multiple Choice Questions (MCQs) based ONLY on the study notes above.

Format each question EXACTLY like this (no deviations):

---
**Q[N]. [Question text]**

- a) [Option A]
- b) [Option B]
- c) [Option C]
- d) [Option D]

✅ **Answer: [letter]) [Correct option text]**

💬 **Explanation:** [One sentence explaining why this is correct]
---

Ensure:
- Questions cover different concepts from the notes
- No repeated concepts
- Grammar is perfect
- The explanation adds value and reinforces learning"""

    return call_gemini(prompt=prompt, agent_name="Quiz Agent", api_key=api_key)


if __name__ == "__main__":
    sample_notes = """
    Machine Learning is a subset of AI that learns from data.
    Three types: Supervised, Unsupervised, Reinforcement Learning.
    Supervised learning uses labeled data.
    Unsupervised learning finds hidden patterns.
    Reinforcement learning learns through rewards and penalties.
    Real world examples: Netflix, spam detection, self-driving cars.
    """
    output = quiz_agent(sample_notes, difficulty="Hard")
    print("\n📝 Quiz Questions:")
    print(output)