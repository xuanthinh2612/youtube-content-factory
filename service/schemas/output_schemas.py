STORY_DIRECTOR_OUTPUT_FORMAT = {
    "format": {
        "type": "json_schema",
        "name": "story_director_plan",
        "strict": True,
        "schema": {
            "type": "object",
            "properties": {
                "title": {
                    "type": "string"
                },
                "premise": {
                    "type": "string"
                },
                "setting": {
                    "type": "string"
                },
                "emotional_core": {
                    "type": "string"
                },
                "central_conflict": {
                    "type": "string"
                },
                "hook": {
                    "type": "string"
                },
                "characters": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "name": {"type": "string"},
                            "role": {"type": "string"},
                            "personality": {"type": "string"},
                            "motivation": {"type": "string"},
                            "emotional_arc": {"type": "string"}
                        },
                        "required": [
                            "name",
                            "role",
                            "personality",
                            "motivation",
                            "emotional_arc"
                        ],
                        "additionalProperties": False
                    }
                },
                "chapters": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "chapter": {"type": "integer"},
                            "title": {"type": "string"},
                            "purpose": {"type": "string"},
                            "key_events": {
                                "type": "array",
                                "items": {"type": "string"}
                            },
                            "emotional_progression": {"type": "string"},
                            "character_changes": {
                                "type": "array",
                                "items": {"type": "string"}
                            },
                            "conflict_or_tension": {"type": "string"},
                            "turning_point": {"type": "string"},
                            "transition": {"type": "string"}
                        },
                        "required": [
                            "chapter",
                            "title",
                            "purpose",
                            "key_events",
                            "emotional_progression",
                            "character_changes",
                            "conflict_or_tension",
                            "turning_point",
                            "transition"
                        ],
                        "additionalProperties": False
                    }
                },
                "ending_plan": {
                    "type": "string"
                }
            },
            "required": [
                "title",
                "premise",
                "setting",
                "emotional_core",
                "central_conflict",
                "hook",
                "characters",
                "chapters",
                "ending_plan"
            ],
            "additionalProperties": False
        }
    }
}


FACT_DIRECTOR_OUTPUT_FORMAT = {
    "format": {
        "type": "json_schema",
        "name": "fact_director_plan",
        "strict": True,
        "schema": {
            "type": "object",
            "properties": {
                "title": {
                    "type": "string"
                },
                "angle": {
                    "type": "string"
                },
                "central_question": {
                    "type": "string"
                },
                "hook": {
                    "type": "string"
                },
                "audience_promise": {
                    "type": "string"
                },
                "sections": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "section": {"type": "integer"},
                            "title": {"type": "string"},
                            "purpose": {"type": "string"},
                            "key_facts": {
                                "type": "array",
                                "items": {"type": "string"}
                            },
                            "explanation_points": {
                                "type": "array",
                                "items": {"type": "string"}
                            },
                            "interesting_insights": {
                                "type": "array",
                                "items": {"type": "string"}
                            },
                            "narrative_direction": {"type": "string"},
                            "transition": {"type": "string"}
                        },
                        "required": [
                            "section",
                            "title",
                            "purpose",
                            "key_facts",
                            "explanation_points",
                            "interesting_insights",
                            "narrative_direction",
                            "transition"
                        ],
                        "additionalProperties": False
                    }
                },
                "factual_requirements": {
                    "type": "array",
                    "items": {"type": "string"}
                },
                "ending_takeaway": {
                    "type": "string"
                }
            },
            "required": [
                "title",
                "angle",
                "central_question",
                "hook",
                "audience_promise",
                "sections",
                "factual_requirements",
                "ending_takeaway"
            ],
            "additionalProperties": False
        }
    }
}


NEWS_DIRECTOR_OUTPUT_FORMAT = {
    "format": {
        "type": "json_schema",
        "name": "news_director_plan",
        "strict": True,
        "schema": {
            "type": "object",
            "properties": {
                "title": {
                    "type": "string"
                },
                "news_angle": {
                    "type": "string"
                },
                "central_event": {
                    "type": "string"
                },
                "hook": {
                    "type": "string"
                },
                "why_it_matters": {
                    "type": "string"
                },
                "timeline": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "order": {"type": "integer"},
                            "time": {"type": "string"},
                            "event": {"type": "string"},
                            "significance": {"type": "string"}
                        },
                        "required": [
                            "order",
                            "time",
                            "event",
                            "significance"
                        ],
                        "additionalProperties": False
                    }
                },
                "sections": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "section": {"type": "integer"},
                            "title": {"type": "string"},
                            "purpose": {"type": "string"},
                            "key_information": {
                                "type": "array",
                                "items": {"type": "string"}
                            },
                            "context": {
                                "type": "array",
                                "items": {"type": "string"}
                            },
                            "attribution_needed": {
                                "type": "array",
                                "items": {"type": "string"}
                            },
                            "narrative_direction": {"type": "string"},
                            "transition": {"type": "string"}
                        },
                        "required": [
                            "section",
                            "title",
                            "purpose",
                            "key_information",
                            "context",
                            "attribution_needed",
                            "narrative_direction",
                            "transition"
                        ],
                        "additionalProperties": False
                    }
                },
                "latest_development": {
                    "type": "string"
                },
                "ending": {
                    "type": "string"
                }
            },
            "required": [
                "title",
                "news_angle",
                "central_event",
                "hook",
                "why_it_matters",
                "timeline",
                "sections",
                "latest_development",
                "ending"
            ],
            "additionalProperties": False
        }
    }
}


VIDEO_DIRECTOR_OUTPUT_FORMAT = {
    "format": {
        "type": "json_schema",
        "name": "video_director_plan",
        "strict": True,
        "schema": {
            "type": "object",
            "properties": {
                "title": {
                    "type": "string"
                },
                "concept": {
                    "type": "string"
                },
                "audience_promise": {
                    "type": "string"
                },
                "hook": {
                    "type": "string"
                },
                "format": {
                    "type": "string"
                },
                "sections": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "section": {"type": "integer"},
                            "title": {"type": "string"},
                            "purpose": {"type": "string"},
                            "narrative_content": {
                                "type": "array",
                                "items": {"type": "string"}
                            },
                            "visual_direction": {
                                "type": "array",
                                "items": {"type": "string"}
                            },
                            "pacing": {"type": "string"},
                            "transition": {"type": "string"}
                        },
                        "required": [
                            "section",
                            "title",
                            "purpose",
                            "narrative_content",
                            "visual_direction",
                            "pacing",
                            "transition"
                        ],
                        "additionalProperties": False
                    }
                },
                "narration_strategy": {
                    "type": "string"
                },
                "visual_strategy": {
                    "type": "string"
                },
                "ending": {
                    "type": "string"
                }
            },
            "required": [
                "title",
                "concept",
                "audience_promise",
                "hook",
                "format",
                "sections",
                "narration_strategy",
                "visual_strategy",
                "ending"
            ],
            "additionalProperties": False
        }
    }
}


MUSIC_DIRECTOR_OUTPUT_FORMAT = {
    "format": {
        "type": "json_schema",
        "name": "music_director_plan",
        "strict": True,
        "schema": {
            "type": "object",
            "properties": {
                "title": {
                    "type": "string"
                },
                "concept": {
                    "type": "string"
                },
                "theme": {
                    "type": "string"
                },
                "emotional_core": {
                    "type": "string"
                },
                "narrative_perspective": {
                    "type": "string"
                },
                "genre_direction": {
                    "type": "string"
                },
                "mood": {
                    "type": "string"
                },
                "lyrical_direction": {
                    "type": "string"
                },
                "song_structure": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "section": {"type": "integer"},
                            "name": {"type": "string"},
                            "purpose": {"type": "string"},
                            "emotional_state": {"type": "string"},
                            "key_ideas": {
                                "type": "array",
                                "items": {"type": "string"}
                            },
                            "energy": {"type": "string"},
                            "transition": {"type": "string"}
                        },
                        "required": [
                            "section",
                            "name",
                            "purpose",
                            "emotional_state",
                            "key_ideas",
                            "energy",
                            "transition"
                        ],
                        "additionalProperties": False
                    }
                },
                "chorus_strategy": {
                    "type": "string"
                },
                "ending_direction": {
                    "type": "string"
                }
            },
            "required": [
                "title",
                "concept",
                "theme",
                "emotional_core",
                "narrative_perspective",
                "genre_direction",
                "mood",
                "lyrical_direction",
                "song_structure",
                "chorus_strategy",
                "ending_direction"
            ],
            "additionalProperties": False
        }
    }
}


DIRECTOR_OUTLINE_OUTPUT_FORMATS = {
    "story": STORY_DIRECTOR_OUTPUT_FORMAT,
    "fact": FACT_DIRECTOR_OUTPUT_FORMAT,
    "news": NEWS_DIRECTOR_OUTPUT_FORMAT,
    "video": VIDEO_DIRECTOR_OUTPUT_FORMAT,
    "music": MUSIC_DIRECTOR_OUTPUT_FORMAT,
}


# STORY_FINAL_JSON_FORMAT = {
#     "format": {
#         "type": "json_schema",
#         "name": "story_final",
#         "strict": True,
#         "schema": {
#             "type": "object",
#             "properties": {
#                 "story_metadata": {
#                     "type": "object",
#                     "properties": {
#                         "title": {
#                             "type": "string"
#                         },
#                         "language": {
#                             "type": "string"
#                         },
#                         "model_id": {
#                             "type": "string"
#                         },
#                         "total_segments": {
#                             "type": "integer"
#                         }
#                     },
#                     "required": [
#                         "title",
#                         "language",
#                         "model_id",
#                         "total_segments"
#                     ],
#                     "additionalProperties": False
#                 },

#                 "voice_mapping": {
#                     "type": "object",
#                     "additionalProperties": {
#                         "type": "string"
#                     }
#                 },

#                 "segments": {
#                     "type": "array",
#                     "items": {
#                         "type": "object",
#                         "properties": {
#                             "segment_id": {
#                                 "type": "integer"
#                             },
#                             "character": {
#                                 "type": "string"
#                             },
#                             "voice_id": {
#                                 "type": "string"
#                             },
#                             "text": {
#                                 "type": "string"
#                             },
#                             "emotion_intent": {
#                                 "type": "string"
#                             },
#                             "voice_settings": {
#                                 "type": "object",
#                                 "properties": {
#                                     "stability": {
#                                         "type": "number"
#                                     },
#                                     "similarity_boost": {
#                                         "type": "number"
#                                     },
#                                     "style": {
#                                         "type": "number"
#                                     },
#                                     "use_speaker_boost": {
#                                         "type": "boolean"
#                                     }
#                                 },
#                                 "required": [
#                                     "stability",
#                                     "similarity_boost",
#                                     "style",
#                                     "use_speaker_boost"
#                                 ],
#                                 "additionalProperties": False
#                             }
#                         },
#                         "required": [
#                             "segment_id",
#                             "character",
#                             "voice_id",
#                             "text",
#                             "emotion_intent",
#                             "voice_settings"
#                         ],
#                         "additionalProperties": False
#                     },
#                     "minItems": 1
#                 }
#             },

#             "required": [
#                 "story_metadata",
#                 "voice_mapping",
#                 "segments"
#             ],

#             "additionalProperties": False
#         }
#     }
# }
