"""Pydantic metrics model for Sit-to-Stand results."""

from pydantic import BaseModel, Field


class ModuleAMetrics(BaseModel):
    rep_count: int
    target_rep_count: int
    completion_time_sec: float | None = None
    rep_durations_sec: list[float] = Field(default_factory=list)
    avg_rep_time_sec: float | None = None
    fastest_rep_time_sec: float | None = None
    slowest_rep_time_sec: float | None = None
    knee_rom_deg: float | None = None
    avg_trunk_lean_deg: float | None = None
    max_trunk_lean_deg: float | None = None
    wobble_count: int
    session_duration_sec: float
    stopped_early: bool
    tracked_leg: str | None = None
    client_attempted_reps: int | None = None
