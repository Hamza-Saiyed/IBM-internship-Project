import streamlit as st
import time


def _set_quiz_tab():
    """Callback: marks the Quiz tab as the active tab in session state."""
    st.session_state.active_tab = 1


def render_interactive_quiz(quiz_data: list[dict], difficulty: str):
    """
    Renders an interactive quiz component from the parsed data dictionary list.
    Handles session state for reveal toggles and score calculation.
    """
    st.markdown(
        f'<div style="font-size:11px;letter-spacing:0.10em;text-transform:uppercase;'
        f'color:var(--text-muted);font-weight:700;margin-bottom:var(--sp-4,16px);'
        f'font-family:var(--font-body,sans-serif);">'
        f'{difficulty.upper()} DIFFICULTY &nbsp;·&nbsp; INTERACTIVE QUIZ</div>',
        unsafe_allow_html=True,
    )
    
    if "quiz_score" not in st.session_state:
        st.session_state.quiz_score = 0
    if "answered_questions" not in st.session_state:
        st.session_state.answered_questions = set()
    if "revealed_questions" not in st.session_state:
        st.session_state.revealed_questions = set()

    for idx, q_dict in enumerate(quiz_data):
        q_id = f"q_{idx}"
        is_revealed = q_id in st.session_state.revealed_questions
        
        with st.container():
            st.markdown(f'<div class="q-card-title">Q{idx+1}. {q_dict["question"]}</div>', unsafe_allow_html=True)
            
            # Use columns to lay out the radio buttons nicely or just a standard radio
            # Using st.radio inside a styled form-like approach
            user_choice = st.radio(
                f"Options for Q{idx+1}",
                options=['a', 'b', 'c', 'd'],
                format_func=lambda x: f"{x}) {q_dict['options'][x]}",
                key=f"radio_{q_id}",
                label_visibility="collapsed",
                disabled=is_revealed,
                on_change=_set_quiz_tab,
            )
            
            col1, col2 = st.columns([1, 4])
            with col1:
                if not is_revealed:
                    if st.button("Reveal", key=f"btn_{q_id}", on_click=_set_quiz_tab):
                        st.session_state.revealed_questions.add(q_id)
                        if user_choice == q_dict["answer_key"]:
                            st.session_state.quiz_score += 1
                        st.rerun()
            
            # Answer Review Block
            if is_revealed:
                is_correct = user_choice == q_dict["answer_key"]
                feedback_color = "#10b981" if is_correct else "#ef4444"
                icon = "✅" if is_correct else "❌"
                
                _fb_class = "quiz-feedback-correct" if is_correct else "quiz-feedback-wrong"
                _fb_color = "var(--accent-secondary,#2DD4BF)" if is_correct else "var(--accent-danger,#F87171)"
                st.markdown(
                    f'<div class="{_fb_class}">'
                    f'<div class="quiz-feedback-label" style="color:{_fb_color};">'
                    f'{icon} Correct Answer: {q_dict["answer_key"].upper()}) '
                    f'{q_dict["options"][q_dict["answer_key"]]}</div>'
                    f'<div class="quiz-feedback-exp">{q_dict["explanation"]}</div>'
                    f'</div>',
                    unsafe_allow_html=True,
                )
            
            st.markdown("<hr style='border-color: rgba(31,41,55,0.6); margin: 1.5rem 0;'>", unsafe_allow_html=True)
            
    # Final Score Block if all revealed
    if len(st.session_state.revealed_questions) == len(quiz_data) and len(quiz_data) > 0:
        score_pct = (st.session_state.quiz_score / len(quiz_data)) * 100
        st.markdown(
            f'<div style="text-align:center;padding:2.5rem;'
            f'background:rgba(13,20,35,0.75);'
            f'backdrop-filter:blur(24px) saturate(160%);'
            f'border:1px solid rgba(56,189,248,0.18);'
            f'border-radius:18px;'
            f'box-shadow:0 0 32px rgba(56,189,248,0.10),0 8px 32px rgba(0,0,0,0.55);">'
            f'<div style="font-family:var(--font-display,Manrope,sans-serif);'
            f'font-size:13px;font-weight:700;letter-spacing:0.10em;text-transform:uppercase;'
            f'color:var(--text-muted,#4A5870);margin-bottom:12px;">Quiz Complete</div>'
            f'<div style="font-family:var(--font-display,Manrope,sans-serif);'
            f'font-size:3rem;font-weight:800;'
            f'background:linear-gradient(135deg,#38BDF8,#A78BFA);'
            f'-webkit-background-clip:text;-webkit-text-fill-color:transparent;'
            f'line-height:1.1;">'
            f'{st.session_state.quiz_score} / {len(quiz_data)}</div>'
            f'<div style="font-size:13px;color:var(--text-secondary,#8899BB);'
            f'font-weight:600;margin-top:6px;font-family:var(--font-mono,monospace);">'
            f'Score: {score_pct:.0f}%</div>'
            f'</div>',
            unsafe_allow_html=True,
        )


import re
import html

def format_study_notes(notes: str) -> str:
    """
    Formats the raw study notes with custom CSS classes for definitions, key terms, etc.
    Calculates reading time and injects a Clipboard HTML component.
    """
    # Defensive processing
    if not notes:
        return ""
        
    word_count = len(notes.split())
    read_time = max(1, round(word_count / 200))

    # Basic markdown header replacements for styling anchors
    formatted = notes.replace("## 📌 Quick Overview", '<div class="note-section-title">📌 Quick Overview</div>')
    formatted = formatted.replace("## 🔑 Key Concepts", '<div class="note-section-title">🔑 Key Concepts</div>')
    formatted = formatted.replace("## 📖 Glossary of Terms", '<div class="note-section-title">📖 Glossary of Terms</div>')
    formatted = formatted.replace("## 💡 Must-Remember Facts", '<div class="note-section-title">💡 Must-Remember Facts</div>')
    formatted = formatted.replace("## ⚠️ Common Pitfalls", '<div class="note-section-title">⚠️ Common Pitfalls</div>')
    
    # Auto-detect `**Key Term**:` and wrap it in a <kbd> or badge-like style
    # Regex looks for `**term**:` pattern and injects span tags
    pattern = re.compile(r"\*\*(.*?)\*\*\:")
    formatted = pattern.sub(r'<span class="k-term">\1:</span>', formatted)
    
    # Simple copy to clipboard component logic 
    # Use HTML templating attached to the div wrapper
    escaped_notes = html.escape(notes).replace("\n", "\\n").replace("'", "\\'")
    
    # Streamlit prevents arbitrary script exec without components.v1.html, so we use a visual wrapper 
    # and rely on the users browser for standard text selection unless we build a dedicated iframe.
    # We will build a small header block.
    
    header_block = (
        f'<div style="display:flex;justify-content:space-between;align-items:center;'
        f'margin-bottom:1rem;border-bottom:1px solid rgba(56,189,248,0.12);padding-bottom:10px;">'
        f'<span style="font-size:11px;color:var(--accent-primary,#38BDF8);'
        f'font-weight:700;letter-spacing:0.10em;text-transform:uppercase;'
        f'font-family:var(--font-mono,monospace);">'
        f'⏱ Approx. {read_time} min read</span>'
        f'</div>'
    )
    
    return f'<div class="study-notes-container">{header_block}{formatted}</div>'
    
