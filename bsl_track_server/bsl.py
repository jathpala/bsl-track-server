"""
Copyright (C) 2024 Jath Palasubramaniam
Licensed under the Affero General Public License version 3
"""

import datetime
from decimal import Decimal
from enum import Enum
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, ConfigDict, condecimal
from sqlalchemy import Integer, Enum as SaEnum, select, delete, DECIMAL, Date, Time, func
from sqlalchemy.orm import Session, Mapped, mapped_column

from bsl_track_server.database import OrmBase, get_db, DatabaseError
from bsl_track_server.logging import get_logger

logger = get_logger()

router = APIRouter(prefix="/bsl", tags=["bsl"])

class MeasurementTypes(Enum):
    """Allowed measurement types"""

    FASTING = "fasting"
    RANDOM = "random"

    def __repr__(self):
        return self.value


class BslMeasurementSchema(BaseModel):
    """Pydantic model for a BSL reading"""

    model_config = ConfigDict(from_attributes = True)

    id: int | None = None
    bsl: Annotated[Decimal, condecimal(ge=0, le=100, multiple_of=Decimal(0.1), decimal_places=1, allow_inf_nan=False)]
    type: MeasurementTypes = MeasurementTypes.FASTING
    date: datetime.date
    time: datetime.time

    def __repr__(self):
        return f"BSL(id={self.id!r}, bsl={self.bsl!r})"

    def __str__(self):
        return repr(self)


class BslMeasurementModel(OrmBase):
    """SQLAlchemy model for a BSL reading"""

    __tablename__ = "bsls"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    bsl: Mapped[Decimal] = mapped_column(DECIMAL(scale=1), nullable=False)
    type: Mapped[MeasurementTypes] = mapped_column(SaEnum(MeasurementTypes), nullable=False)
    date: Mapped[datetime.date] = mapped_column(Date, nullable=False, server_default=func.current_date())
    time: Mapped[datetime.time] = mapped_column(Time, nullable=False, server_default=func.current_time())

    @classmethod
    def list(cls, db: Session) -> list["BslMeasurementModel"]:
        """
        Obtain a list of all BSL readings within the database
        """

        stmt = select(cls)
        result = db.scalars(stmt).all()

        return result

    @classmethod
    def read(cls, db: Session, measurement_id: int) -> "BslMeasurementModel":
        """
        Read an existing BSL reading
        """

        stmt = select(cls).where(cls.id == measurement_id)
        record = db.scalar(stmt)

        if not record:
            raise DatabaseError(error = "MeasurementNotFound", message = f"No measurement with the given id: {measurement_id}")

        return record

    @classmethod
    def create(cls, db: Session, measurement: BslMeasurementSchema) -> "BslMeasurementModel":
        """
        Create a new BSL reading
        """

        if measurement.id is not None:
            raise DatabaseError(message = "ID should be null for new measurements")

        record = cls(**measurement.model_dump())
        logger.debug("Preparing to insert: %s", repr(record))

        db.add(record)
        db.commit()
        db.refresh(record)

        return record

    @classmethod
    def update(cls, db: Session, measurement: BslMeasurementSchema) -> "BslMeasurementModel":
        """
        Update an existing BSL reading
        """

        if measurement.id is None:
            raise DatabaseError(message = "ID should not be null for existing measurements")

        stmt = select(cls).where(cls.id == measurement.id)
        record = db.scalar(stmt)

        if not record:
            raise DatabaseError(message = "Measurement not found")

        for key, value in measurement.model_dump().items():
            setattr(record, key, value)

        db.commit()

        return record

    @classmethod
    def delete(cls, db: Session, measurement_id: int) -> None:
        """
        Delete a measurement (or do nothing if the measurement doesn't exist)
        """

        stmt = delete(cls).where(cls.id == measurement_id)
        db.execute(stmt)
        db.commit()

    def __repr__(self):
        return f"BSL(id={self.id!r}, name={self.bsl!r})"


#Duplicate route prevents redirects from trailing slash
@router.get("")
@router.get("/", include_in_schema = False)  # Show only one route in docs
def list_measurements(db: Annotated[Session, Depends(get_db)]) -> list[BslMeasurementSchema]:
    """Return a summary list of all BSL readings"""

    result = BslMeasurementModel.list(db)

    return result


@router.get("/{measurement_id}")
def get_measurement(measurement_id: int, db: Session = Depends(get_db)) -> BslMeasurementSchema:
    """Returns details for a single BSL reading"""

    logger.debug("get_measurement()")

    try:
        result = BslMeasurementModel.read(db, measurement_id)
    except DatabaseError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail="No measurement with that ID") from e

    return result


# Duplicate route prevents redirects from trailing slash
@router.post("", status_code = status.HTTP_201_CREATED)
@router.post("/", include_in_schema = False, status_code = status.HTTP_201_CREATED)
def create_measurement(measurement: BslMeasurementSchema, db: Session = Depends(get_db)) -> BslMeasurementSchema:
    """Create a new BSL reading"""

    logger.debug("create_measurement()")
    logger.debug("Received: %s", repr(measurement))

    result = BslMeasurementModel.create(db, measurement)

    return result


# Duplicate route prevents redirects from trailing slash
@router.put("", status_code = status.HTTP_201_CREATED)
@router.put("/", include_in_schema = False, status_code = status.HTTP_201_CREATED)
def update_measurement(measurement: BslMeasurementSchema, db: Session = Depends(get_db)) -> BslMeasurementSchema:
    """Modify an existing BSL reading"""

    logger.debug("update_measurement()")
    logger.debug("Updating: %s", measurement)

    try:
        result = BslMeasurementModel.update(db, measurement)
    except DatabaseError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail="No measurement with that ID") from e

    return result


@router.delete("/{measurement_id}")
def delete_measurement(measurement_id: int, db: Session = Depends(get_db)) -> None:
    """Delete an existing measurement"""

    logger.debug("delete_measurement()")

    BslMeasurementModel.delete(db, measurement_id)