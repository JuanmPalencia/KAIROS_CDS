from sqlalchemy.orm import Session
from sqlalchemy import select
from ..models_sql import Vehicle

class VehicleRepo:
    @staticmethod
    def list_enabled(db: Session) -> list[Vehicle]:
        return db.scalars(select(Vehicle).where(Vehicle.enabled == True)).all()

    @staticmethod
    def upsert(db: Session, vehicle: Vehicle) -> None:
        db.merge(vehicle)
        db.commit()
