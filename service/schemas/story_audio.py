"""Responses API JSON mode for Story Audio output."""


# Speaker IDs are chosen from the story and therefore make `voices` a dynamic
# object map. JSON mode guarantees valid JSON; the full schema contract is
# specified in the prompt and enforced by the application validator.
STORY_AUDIO_OUTPUT_FORMAT = {
    "format": {
        "type": "json_object",
    }
}
