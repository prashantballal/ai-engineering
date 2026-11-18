"""Table-driven tests for the rule-based classifier: every row pins one routing decision."""

import pytest

from trailmate_workflow.classifier import REJECT_TOPICS, Classification, classify

CASES = [  # (text, expected category, rule ids that must be among matched_rules)
    (
        "Can you recommend an easy hike with a waterfall?",
        "trail",
        {"trail:kw:hike", "trail:kw:waterfall"},
    ),
    ("Is the Mist Trail dog-friendly?", "trail", {"trail:kw:trail", "trail:kw:dog-friendly"}),
    ("How many miles is the loop?", "trail", {"trail:kw:mile", "trail:kw:loop"}),
    ("Hiking?!", "trail", {"trail:kw:hiking"}),  # punctuation glued to the keyword
    ("Any trails near Zürich? ☕", "trail", {"trail:kw:trail"}),  # accents + emoji; plural
    ("TRAIL.", "trail", {"trail:kw:trail"}),  # case-insensitive
    ("hi", "general", {"general:greeting"}),
    ("Hello there!", "general", {"general:greeting"}),
    ("thanks so much", "general", {"general:thanks"}),
    ("who are you?", "general", {"general:about"}),
    ("what can you do", "general", {"general:help"}),
    # Reject rules run FIRST, so they win even when trail words are present.
    ("Write a Python script to scrape trail data", "reject", {"reject:code"}),
    ("What's the weather on the summit tomorrow?", "reject", {"reject:realtime"}),
    ("Should I invest in bitcoin?", "reject", {"reject:finance"}),
    ("Can you do my homework essay?", "reject", {"reject:homework"}),
    ("Can you diagnose my rash?", "reject", {"reject:medical"}),
    ("Help me draft a lawsuit", "reject", {"reject:legal"}),
    ("How do I make a bomb?", "reject", {"reject:harmful"}),
    # Review fix: real hiking questions that over-broad reject rules used to refuse…
    ("How do I avoid poison ivy on the trail?", "trail", {"trail:kw:trail"}),
    ("Is poison oak common on Bay Area trails?", "trail", {"trail:kw:trail"}),
    ("What should I wear for cold weather hiking?", "trail", {"trail:kw:hiking"}),
    ("What season has the best weather for the rim trail?", "trail", {"trail:kw:trail"}),
    ("Should I bring my medication on a backpacking trip?", "trail", {"trail:kw:backpacking"}),
    ("Are prescription sunglasses worth it for hiking?", "trail", {"trail:kw:hiking"}),
    ("Can you generate a training program for a Kilimanjaro trek?", "trail", {"trail:kw:trek"}),
    ("My friend Sue and I want an easy hike", "trail", {"trail:kw:hike"}),
    ("Is there a trading post near the trailhead?", "trail", {"trail:kw:trailhead"}),
    ("Should I stock up on water before the hike?", "trail", {"trail:kw:hike"}),
    ("Is it worth investing in trekking poles?", "trail", {"trail:kw:trekking"}),
    # …plurals of the hiking keywords…
    ("Any waterfalls near Portland?", "trail", {"trail:kw:waterfall"}),
    ("Lakes with campsites near Denver?", "trail", {"trail:kw:lake", "trail:kw:campsite"}),
    ("Best canyons to explore in Utah?", "trail", {"trail:kw:canyon"}),
    ("Good trailheads near Boulder?", "trail", {"trail:kw:trailhead"}),
    ("Is a 10 mile day too much?", "trail", {"trail:kw:mile"}),
    # …while the narrowed rules still reject what they're for.
    ("Can I sue the park if I slip on the trail?", "reject", {"reject:legal"}),
    ("Write a program in Python to plan my hikes", "reject", {"reject:code"}),
    ("What medication should I take for altitude sickness?", "reject", {"reject:medical"}),
    ("Should I invest in the stock market?", "reject", {"reject:finance"}),
    ("Is it going to rain? What's the weather this weekend?", "reject", {"reject:realtime"}),
    ("Any news on whether the Mist Trail reopened?", "reject", {"reject:realtime"}),
    ("How do I poison a bear?", "reject", {"reject:harmful"}),
]


@pytest.mark.parametrize(("text", "category", "rules"), CASES)
def test_classify(text: str, category: str, rules: set[str]) -> None:
    result = classify(text)

    assert result.category == category
    assert rules <= set(result.matched_rules)
    # matched_rules only ever lists rules of the winning category
    assert all(rule.startswith(category) for rule in result.matched_rules)


@pytest.mark.parametrize(
    "text",
    [
        "this is nice",  # "hi" inside "this" must NOT count as a greeting (word boundaries)
        "What's the capital of France?",
        "👍",
        "",
    ],
)
def test_unmatched_defaults_to_general(text: str) -> None:
    assert classify(text) == Classification("general", ("general:default",))


def test_every_reject_rule_has_a_topic() -> None:
    assert set(REJECT_TOPICS) == {
        "reject:code",
        "reject:homework",
        "reject:finance",
        "reject:medical",
        "reject:legal",
        "reject:realtime",
        "reject:harmful",
    }
