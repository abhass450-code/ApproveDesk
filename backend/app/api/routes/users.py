from fastapi import APIRouter, Depends
from pydantic import BaseModel, ConfigDict, EmailStr
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.security import require_roles
from app.db.session import get_db
from app.models.user import User
from app.schemas.common import UserRole

router = APIRouter(prefix="/users", tags=["Users"])


class OfficerOut(BaseModel):
    id: int
    full_name: str
    email: EmailStr
    model_config = ConfigDict(from_attributes=True)


@router.get("/officers", response_model=list[OfficerOut])
def list_officers(user: User = Depends(require_roles(UserRole.ADMIN)),
                  db: Session = Depends(get_db)) -> list[OfficerOut]:
    officers = db.scalars(select(User).where(User.role == UserRole.OFFICER.value, User.is_active.is_(True))
                          .order_by(User.full_name.asc())).all()
    return [OfficerOut.model_validate(officer) for officer in officers]
