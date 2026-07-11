"""Shared age/sex -> McBride band-key resolver (blueprint §1.1, §3).

Single source of truth for turning a user's stored exact_age + gender into the
"ageband_sex" key used by WBLT_CONFIG["distance_bands"] / ["seed_distance_cm"].
Never inline these cutoffs elsewhere.
"""

# Upper bound of each band, ordered ascending. 999 stands in for "80+" (no upper
# bound). Matches the age bands used in WBLT_CONFIG's distance_bands/seed tables.
_AGE_BAND_UPPER_BOUNDS = [
    (29, "18-29"),
    (39, "30-39"),
    (49, "40-49"),
    (59, "50-59"),
    (69, "60-69"),
    (79, "70-79"),
    (999, "80+"),
]

_GENDER_TO_SEX = {"male": "male", "female": "female"}


def age_to_band(exact_age: int) -> str:
    """Resolves an exact age to a McBride age band.

    Ages below 18 are clamped to "18-29" -- the youngest band McBride (2026)
    publishes -- rather than left unbanded, since the app has no pediatric
    norms to fall back to and blocking every under-18 account is worse than a
    slightly conservative band.
    """
    clamped = max(exact_age, 18)
    for upper, band in _AGE_BAND_UPPER_BOUNDS:
        if clamped <= upper:
            return band
    return "80+"


def sex_from_gender(gender: str | None) -> str | None:
    """Maps the stored `gender` field to the "male"/"female" key McBride bands use.

    Returns None for "prefer_not_to_say", unset, or any other value -- callers
    must treat that as "banding blocked", never guess a sex (§13 edge case).
    """
    if gender is None:
        return None
    return _GENDER_TO_SEX.get(gender.lower())


def resolve_ageband_sex(exact_age: int | None, gender: str | None) -> str | None:
    """Resolves the full "ageband_sex" config key, or None if either input is missing/invalid."""
    if exact_age is None:
        return None
    sex = sex_from_gender(gender)
    if sex is None:
        return None
    return f"{age_to_band(exact_age)}_{sex}"
