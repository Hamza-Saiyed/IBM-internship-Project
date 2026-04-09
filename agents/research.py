from agents.gemini_client import call_gemini

def research_agent(topic: str, api_key: str = None) -> str:
    """
    Research Agent — fetches comprehensive background information on a topic.

    Args:
        topic: The subject to research.
        api_key: Optional override for the Gemini API key.

    Returns:
        A detailed research summary string.
    """
    prompt = f"""You are an expert Research Agent specializing in academic and technical topics.
Your task is to produce comprehensive, well-structured research on the topic provided.

Topic: '{topic}'

Your research MUST include:
1. **Definition & Core Concepts** — precise, clear definitions
2. **Key Principles** — the foundational ideas that underpin this topic
3. **Historical Context / Origin** — where/when it emerged (if applicable)
4. **Real-World Applications** — concrete, modern examples
5. **Common Misconceptions** — things students often get wrong
6. **Related Topics** — adjacent concepts worth exploring

Format with clear headings and bullet points. Be factual and thorough."""

    return call_gemini(prompt=prompt, agent_name="Research Agent", api_key=api_key)


if __name__ == "__main__":
    topic = "What is Machine Learning?"
    output = research_agent(topic)
    print("\n📄 Research Output:")
    print(output)
