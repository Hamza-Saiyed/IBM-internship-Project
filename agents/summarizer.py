from agents.gemini_client import call_gemini

def summarizer_agent(research_text: str, api_key: str = None) -> str:
    """
    Summarizer Agent — converts raw research into clean, student-friendly notes.

    Args:
        research_text: The raw research text from the Research Agent.
        api_key: Optional override for the Gemini API key.

    Returns:
        Concise, well-structured study notes as a string.
    """
    prompt = f"""You are an expert Study Notes Creator who specializes in making complex topics
easy for students to understand and remember.

Research Content:
{research_text}

Transform the above into beautiful, structured study notes:

## 📌 Quick Overview
(3-4 sentence summary of the entire topic)

## 🔑 Key Concepts
(Bullet points — most important ideas, max 8 bullets)

## 📖 Glossary of Terms
(Important terms with their simple, plain-English definitions)

## 💡 Must-Remember Facts
(3-5 memorable takeaways a student should not forget)

## ⚠️ Common Pitfalls
(What students typically misunderstand about this topic)

Keep the language simple, engaging, and student-friendly. Use emojis sparingly to highlight sections."""

    return call_gemini(prompt=prompt, agent_name="Summarizer Agent", api_key=api_key)


if __name__ == "__main__":
    sample_research = """
    Machine Learning is a subset of Artificial Intelligence that empowers
    computer systems to learn from data, identify patterns, and make decisions
    with minimal human intervention. It includes supervised, unsupervised,
    and reinforcement learning. Real world examples include Netflix recommendations,
    spam detection, self driving cars and medical diagnosis.
    """
    output = summarizer_agent(sample_research)
    print("Study Notes:")
    print(output)