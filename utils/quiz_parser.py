import re

def parse_quiz_markdown(markdown_text: str) -> list[dict]:
    """
    Parses strictly formatted Quiz Agent markdown into structured dictionaries.
    
    Expected format per question:
    ---
    **Q[N]. [Question text]**

    - a) [Option A]
    - b) [Option B]
    - c) [Option C]
    - d) [Option D]

    ✅ **Answer: [letter]) [Correct option text]**

    💬 **Explanation:** [Text]
    ---
    """
    # Regex designed to capture the core components of each question block
    pattern = re.compile(
        r"\*\*Q\d+\.\s*(.*?)\*\*\s*"           # Group 1: Question text
        r"-\s*a\)\s*(.*?)\s*"                  # Group 2: Option a
        r"-\s*b\)\s*(.*?)\s*"                  # Group 3: Option b
        r"-\s*c\)\s*(.*?)\s*"                  # Group 4: Option c
        r"-\s*d\)\s*(.*?)\s*"                  # Group 5: Option d
        r"✅\s*\*\*Answer:\s*([a-d])\)\s*(.*?)\*\*\s*"  # Group 6: Correct letter, Group 7: Correct text
        r"💬\s*\*\*Explanation:\*\*\s*(.*?)(?:\n---|---|\Z)",  # Group 8: Explanation
        re.IGNORECASE | re.DOTALL
    )

    questions = []
    matches = pattern.finditer(markdown_text)

    for match in matches:
        q_text = match.group(1).strip()
        opts = {
            "a": match.group(2).strip(),
            "b": match.group(3).strip(),
            "c": match.group(4).strip(),
            "d": match.group(5).strip(),
        }
        correct_letter = match.group(6).strip().lower()
        explanation = match.group(8).strip()
        
        questions.append({
            "question": q_text,
            "options": opts,
            "answer_key": correct_letter,
            "explanation": explanation
        })
        
    return questions

if __name__ == "__main__":
    # Test block
    sample = """
---
**Q1. What is the main purpose of ML?**

- a) Magic
- b) Data analysis
- c) Networking
- d) Hardware

✅ **Answer: b) Data analysis**

💬 **Explanation:** Because it fits the description.
---
"""
    print(parse_quiz_markdown(sample))
