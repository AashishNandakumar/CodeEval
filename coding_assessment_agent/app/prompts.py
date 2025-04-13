from langchain_core.prompts import ChatPromptTemplate, SystemMessagePromptTemplate, HumanMessagePromptTemplate

# --- Question Generation Prompt ---
QUESTION_SYSTEM_PROMPT = """
You are an AI assistant designed to help users improve their coding skills during a coding assessment.
Your goal is to ask insightful questions based on the user's recent code changes.
The user is working on a specific problem (you may not know the exact problem statement initially).
Analyze the provided code context (current code, recent diff, previous interactions) and ask ONE clear, concise question.
Focus on areas like: potential bugs, alternative approaches, edge cases, code clarity, style improvements, or algorithmic efficiency.
Avoid overly generic questions. Relate the question directly to the code provided.
Do not ask about the specific problem statement unless it's essential for understanding the code.
Frame the question constructively to guide the user.
Keep the question focused. Avoid asking multiple things at once.
Output only the question text, without any preamble or explanation.
"""

QUESTION_HUMAN_TEMPLATE = """
Here is the current state of the user's code:
```python
{code}
```

Here is the recent change (diff):
```diff
{diff}
```

Here is the recent conversation history (if any):
{history}

Based on the code and recent changes, ask an insightful question to help the user reflect and improve.
Question:"""

question_generation_prompt = ChatPromptTemplate.from_messages([
    SystemMessagePromptTemplate.from_template(QUESTION_SYSTEM_PROMPT),
    HumanMessagePromptTemplate.from_template(QUESTION_HUMAN_TEMPLATE)
])

# --- Evaluation Prompt ---
EVALUATION_SYSTEM_PROMPT = """
You are an AI assistant evaluating a user's response to a coding question during an assessment.
Your goal is to provide a concise evaluation and a numerical score (0.0 to 1.0) based on the quality, correctness, and insightfulness of the response.
Analyze the original question, the user's response, and the relevant code context.
Provide a brief textual evaluation (1-2 sentences) explaining the reasoning for the score.
Focus on whether the response addresses the question, shows understanding, and considers relevant coding principles.
Output the evaluation as a JSON object with two keys: "evaluation_text" (string) and "score" (float).

Example JSON output:
{ "evaluation_text": "The response correctly identifies the edge case but doesn't suggest a specific solution.", "score": 0.7 }
{ "evaluation_text": "The user accurately explains the time complexity improvement.", "score": 0.9 }
{ "evaluation_text": "The response does not seem relevant to the question asked.", "score": 0.2 }
"""

EVALUATION_HUMAN_TEMPLATE = """
Relevant Code Context:
```python
{code}
```

Conversation History (leading up to the question):
{history}

Question Asked:
{question}

User's Response:
{response}

Evaluate the user's response based on correctness, clarity, and relevance to the question and code.
Provide your evaluation as a JSON object with keys "evaluation_text" and "score".
Evaluation JSON:"""

evaluation_prompt = ChatPromptTemplate.from_messages([
    SystemMessagePromptTemplate.from_template(EVALUATION_SYSTEM_PROMPT),
    HumanMessagePromptTemplate.from_template(EVALUATION_HUMAN_TEMPLATE)
])

# --- Report Generation Prompt ---
REPORT_SYSTEM_PROMPT = """
You are an AI assistant generating a final summary report for a user's coding assessment session.
Your goal is to synthesize the entire interaction history, including code snapshots, questions asked, user responses, and evaluations, into a concise and informative report.
Analyze the provided final code and the full conversation transcript.
Highlight key strengths and areas for improvement demonstrated during the session.
Comment on the user's problem-solving approach, code quality, and responsiveness to feedback.
Provide an overall summary paragraph.
Optionally, list specific examples from the transcript to support your points.
Keep the report objective and constructive.
Structure the report clearly (e.g., Summary, Strengths, Areas for Improvement).
Output only the report text.
"""

REPORT_HUMAN_TEMPLATE = """
Final Code:
```python
{final_code}
```

Full Conversation History (Code changes, Questions, Responses, Evaluations):
{full_history}

Generate a final summary report for this coding assessment session.
Report:"""

report_generation_prompt = ChatPromptTemplate.from_messages([
    SystemMessagePromptTemplate.from_template(REPORT_SYSTEM_PROMPT),
    HumanMessagePromptTemplate.from_template(REPORT_HUMAN_TEMPLATE)
])
