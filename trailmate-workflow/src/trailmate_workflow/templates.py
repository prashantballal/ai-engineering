"""Fixed (templated) replies. No model produces any of the text in this module."""

from collections.abc import Sequence

from trailmate_workflow.classifier import REJECT_TOPICS

# Day 2 these were the trail/general replies. From Day 3 a model writes those replies, and
# these templates are the deterministic FALLBACKS used when the model can't be reached.
TRAIL_FALLBACK_REPLY = (
    "I can't reach my trail model right now, sorry! In the meantime: tell me where you are, "
    "how far you'd like to walk, and how hard a hike you want, and try again in a moment."
)

GENERAL_FALLBACK_REPLY = (
    "Hi! I'm TrailMate. I help you find hiking trails that fit what you're after: "
    "distance, difficulty, scenery, or a dog-friendly loop. What are you looking for?"
)

REJECT_REPLY = (
    "Sorry, I can only help with hiking and trail questions, so I can't help with {topic}. "
    "Try asking me about a hike: distance, difficulty, or scenery."
)


# Day 5: replies for messages the INPUT guardrail blocked, by reason.
# Security reasons get a generic reply that reveals nothing about how detection works;
# UX reasons (empty, too long) get a specific, helpful one.
BLOCKED_REPLIES = {
    "empty": "Please type a message, for example: 'an easy hike near a lake'.",
    "too_long": "That message is a bit long for me. Please keep it under {max_chars} characters.",
    "prompt_injection": "I can't help with that. I'm here to help you find hiking trails.",
    "abusive_language": "Let's keep things friendly. I'm happy to help you find a trail.",
}

# Day 5: what the output guardrail shows instead of a reply it had to block.
OUTPUT_BLOCKED_REPLY = (
    "Sorry, I couldn't put together a good answer to that. Could you rephrase your trail question?"
)

EMPTY_REPLY_FALLBACK = (
    "Sorry, I didn't come up with an answer that time. Could you ask again, maybe with a "
    "bit more detail about the hike you want?"
)


def render_reject(matched_rules: Sequence[str]) -> str:
    """The reject reply, naming the topic of the first reject rule that matched."""
    return REJECT_REPLY.format(topic=REJECT_TOPICS[matched_rules[0]])
