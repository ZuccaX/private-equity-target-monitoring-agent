from sqlalchemy.orm import Session

from app.repositories.trigger_repository import TriggerRepository
from app.schemas.trigger import TriggerRead


class TriggerService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.trigger_repository = TriggerRepository(db)

    def list_triggers(
        self,
        company_id: int | None = None,
    ) -> list[TriggerRead]:
        if company_id is None:
            triggers = self.trigger_repository.list_all()
        else:
            triggers = self.trigger_repository.list_by_company_id(
                company_id
            )

        return [
            TriggerRead.model_validate(trigger)
            for trigger in triggers
        ]