"""Registry for Module B exercise plugins."""

from fastapi import HTTPException, status

from app.module_b.core.exercise import ModuleBExercise

_EXERCISES: dict[str, ModuleBExercise] = {}


def register_exercise(exercise: ModuleBExercise) -> None:
    """Registers one unique, non-empty exercise code."""
    code = exercise.code.strip().lower()
    if not code:
        raise ValueError("Module B exercise code cannot be empty")
    if code in _EXERCISES:
        raise ValueError(f"Module B exercise already registered: {code}")
    _EXERCISES[code] = exercise


def get_exercise(code: str) -> ModuleBExercise:
    """Returns a plugin or a clear 404; there is never a default exercise."""
    exercise = _EXERCISES.get(code.strip().lower())
    if exercise is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Unknown Module B exercise: {code}",
        )
    return exercise


def registered_exercise_codes() -> tuple[str, ...]:
    """Stable registry snapshot for diagnostics and tests."""
    return tuple(sorted(_EXERCISES))


# Built-in plugins are registered here so importing the registry is sufficient.
from app.module_b.lunge.exercise import LungeExercise  # noqa: E402
from app.module_b.squat.exercise import SquatExercise  # noqa: E402

register_exercise(SquatExercise())
register_exercise(LungeExercise())
