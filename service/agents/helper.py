"""Builders for the role-specific task instructions sent to agents."""


def build_director_role_task(language):
    return (
        "Analyze the user's request and create the most suitable content plan and outline. "
        f"Write the plan in {language}. "
        "Return only the required JSON structure."
    )


def build_writer_role_task(language, director_outline):
    return (
        f"DIRECTOR OUTLINE:\n{director_outline}\n\n"
        "Use the Director plan to create the complete content as a finished, high-quality content. "
        "Do not merely expand or restate the outline. "
        f"Write the content in {language}. "
        "Return only the complete content."
    )


def build_reviewer_role_task(director_outline, writer_draft):
    return (
        f"DIRECTOR PLAN:\n{director_outline}\n\n"
        f"WRITER OUTPUT:\n{writer_draft}\n\n"
        "Evaluate the Writer output as a final product against the user's requirements and the Director plan. "
        "Assess its overall quality and identify every important weakness, missing element, or issue that should be improved. "
        "Provide clear, concrete, and prioritized feedback for the Editor. "
        "Do not rewrite the content. "
        "Return the required JSON structure."
    )


def build_editor_role_task(language, writer_draft, reviewer_feedback=""):
    return (
        f"WRITER OUTPUT:\n{writer_draft}\n\n"
        f"REVIEWER FEEDBACK:\n{reviewer_feedback or 'No separate review provided.'}\n\n"
        "Rewrite the entire Writer output into the final version. "
        "Use the Director plan to preserve the intended concept and use the Reviewer feedback to fix all important weaknesses. "
        "Do not merely patch individual issues; produce one cohesive, polished final version. "
        f"Start with exactly one Markdown H1 title on the first line, written in {language}, "
        "using the exact title from the Director plan. "
        "Then add one blank line and the complete final content. "
        "Return only the final content."
    )
