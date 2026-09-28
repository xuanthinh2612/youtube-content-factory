"""Common output languages shown in the project creation form.

The country in each label is a representative audience market, so people can
identify the language without needing to know its local name.
"""


# A curated set of 30 languages associated with large YouTube audience
# markets. Each language appears once. Labels use familiar Vietnamese names.
OUTPUT_LANGUAGES = (
    ("hi", "Tiếng Hindi"),
    ("en", "Tiếng Anh"),
    ("pt", "Tiếng Bồ Đào Nha"),
    ("id", "Tiếng Indonesia"),
    ("es", "Tiếng Tây Ban Nha"),
    ("ja", "Tiếng Nhật"),
    ("de", "Tiếng Đức"),
    ("vi", "Tiếng Việt"),
    ("fil", "Tiếng Philippines"),
    ("tr", "Tiếng Thổ Nhĩ Kỳ"),
    ("ur", "Tiếng Urdu"),
    ("ar", "Tiếng Ả Rập"),
    ("fr", "Tiếng Pháp"),
    ("th", "Tiếng Thái"),
    ("bn", "Tiếng Bengali"),
    ("ko", "Tiếng Hàn"),
    ("it", "Tiếng Ý"),
    ("ru", "Tiếng Nga"),
    ("uk", "Tiếng Ukraina"),
    ("ms", "Tiếng Malaysia"),
    ("pl", "Tiếng Ba Lan"),
    ("zh", "Tiếng Trung"),
    ("fa", "Tiếng Ba Tư"),
    ("my", "Tiếng Myanmar"),
    ("ne", "Tiếng Nepal"),
    ("sw", "Tiếng Swahili"),
    ("ha", "Tiếng Hausa"),
    ("ro", "Tiếng Romania"),
    ("nl", "Tiếng Hà Lan"),
    ("el", "Tiếng Hy Lạp"),
)


LANGUAGE_NAMES = dict(OUTPUT_LANGUAGES)


def language_display_name(language_code):
    """Return a readable Vietnamese language name for a language code."""
    code = str(language_code or "").strip().lower()
    return LANGUAGE_NAMES.get(code, f"Ngôn ngữ ({code})" if code else "Ngôn ngữ chưa xác định")
