import os

from sqlalchemy import select

from app.core.security import hash_password
from app.db.database import SessionLocal
from app.db.models import ExerciseCatalog, User, UserProfile

EXERCISES = [
    {
        "code": "sit_to_stand",
        "name": "Sit-to-Stand",
        "mode": "functional",
        "description": "Functional check for repeated sit-to-stand movement.",
        "view_guidance": "side_view",
    },
    {
        "code": "supported_single_leg_stance",
        "name": "Supported Single-Leg Stance",
        "mode": "functional",
        "description": "Functional balance check with support allowed.",
        "view_guidance": "front_view",
    },
    {
        "code": "weight_bearing_lunge_test",
        "name": "Weight-Bearing Lunge Test",
        "mode": "functional",
        "description": "Functional ankle mobility check.",
        "view_guidance": "side_view",
    },
    {
        "code": "module_b_placeholder_exercise",
        "name": "Module B Placeholder Exercise",
        "mode": "rehab",
        "description": "Configurable rehab grading exercise for Module B.",
        "view_guidance": "front_view",
    },
]


def seed_exercises() -> int:
    created = 0
    with SessionLocal() as db:
        for item in EXERCISES:
            exists = db.scalar(
                select(ExerciseCatalog).where(ExerciseCatalog.code == item["code"])
            )
            if exists:
                continue
            db.add(ExerciseCatalog(**item))
            created += 1
        db.commit()
    return created


def seed_demo_user() -> bool:
    email = os.getenv("DEMO_USER_EMAIL")
    password = os.getenv("DEMO_USER_PASSWORD")
    if not email or not password:
        return False

    with SessionLocal() as db:
        exists = db.scalar(select(User).where(User.email == email.lower()))
        if exists:
            return False
        user = User(
            email=email.lower(),
            password_hash=hash_password(password),
            full_name=os.getenv("DEMO_USER_FULL_NAME", "Demo User"),
        )
        user.profile = UserProfile(user_type="patient", focus_area="general")
        db.add(user)
        db.commit()
    return True


def main() -> None:
    exercise_count = seed_exercises()
    demo_created = seed_demo_user()
    print(f"Seeded {exercise_count} exercise(s). Demo user created: {demo_created}.")


if __name__ == "__main__":
    main()
