import pytest

from src.conversation import answer_question
from src.demo_data import load_demo_data


@pytest.mark.parametrize("question,fragment,chart", [
    ("What is the latest reported U.S. GDP?", "latest GDP", False),
    ("How has U.S. GDP changed over the past 10 years?", "GDP changed", False),
    ("What is the current Core CPI inflation rate?", "latest Core CPI", False),
    ("How has Core CPI inflation changed over the past five years?", "Available window", False),
    ("What is the relationship between GDP growth and Core CPI inflation?", "correlation", True),
    ("Generate a visualization comparing GDP growth and Core CPI inflation over time.", "chart", True),
    ("Summarize the key economic trends observed in both datasets.", "Nominal GDP growth", True),
])
def test_assignment_questions(question, fragment, chart):
    result = answer_question(question, load_demo_data(), "Synthetic demo")
    assert fragment in result["answer"]
    assert result["chart"] is chart
