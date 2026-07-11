from app.api.deps import get_current_user
from app.db.database import get_db
from app.db.models import User, UserProfile
from app.db.schemas import ProfileRead, ProfileUpdate
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

router = APIRouter(prefix="/api/users", tags=["users"])


def _profile_response(user: User, profile: UserProfile) -> ProfileRead:
    return ProfileRead(
        id=profile.id,
        user_id=profile.user_id,
        full_name=user.full_name,
        avatar_image=user.avatar_image,
        age_group=profile.age_group,
        gender=profile.gender,
        height_cm=float(profile.height_cm) if profile.height_cm is not None else None,
        weight_kg=float(profile.weight_kg) if profile.weight_kg is not None else None,
        user_type=profile.user_type,
        focus_area=profile.focus_area,
        self_reported_note=profile.self_reported_note,
        created_at=profile.created_at,
        updated_at=profile.updated_at,
    )


def _ensure_profile(db: Session, user: User) -> UserProfile:
    if user.profile is not None:
        return user.profile
    profile = UserProfile(user_id=user.id)
    db.add(profile)
    db.commit()
    db.refresh(profile)
    return profile


@router.get("/me/profile", response_model=ProfileRead)
def get_profile(
    db: Session = Depends(get_db), current_user: User = Depends(get_current_user)
) -> ProfileRead:
    profile = _ensure_profile(db, current_user)
    return _profile_response(current_user, profile)


@router.put("/me/profile", response_model=ProfileRead)
def update_profile(
    payload: ProfileUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ProfileRead:
    profile = _ensure_profile(db, current_user)
    updates = payload.model_dump(exclude_unset=True)

    # full_name and avatar_image live on User, not UserProfile — pop them off
    # before the generic loop below applies everything else to the profile row.
    if "full_name" in updates:
        current_user.full_name = updates.pop("full_name")
    if "avatar_image" in updates:
        current_user.avatar_image = updates.pop("avatar_image")
    for field, value in updates.items():
        setattr(profile, field, value)

    db.add(current_user)
    db.add(profile)
    db.commit()
    db.refresh(current_user)
    db.refresh(profile)
    return _profile_response(current_user, profile)
