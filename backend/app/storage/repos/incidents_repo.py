from sqlalchemy.orm import Session
from ..models_sql import IncidentSQL

class IncidentsRepo:
    @staticmethod
    def list_open(db: Session):
        return db.query(IncidentSQL).filter(IncidentSQL.status != "CLOSED").all()

    @staticmethod
    def create(db: Session, inc: IncidentSQL):
        db.add(inc)
        db.commit()
        db.refresh(inc)
        return inc

    @staticmethod
    def assign(db: Session, incident_id: str, vehicle_id: str):
        inc = db.query(IncidentSQL).filter(IncidentSQL.id == incident_id).first()
        if not inc:
            return None
        inc.assigned_vehicle_id = vehicle_id
        inc.status = "ASSIGNED"
        db.commit()
        db.refresh(inc)
        return inc
