from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import Interview
from app.schemas import ReportResponse
from app.services.report_service import ReportService

router = APIRouter()


@router.get("/{interview_id}", response_model=ReportResponse)
async def get_report(interview_id: int, db: Session = Depends(get_db)):
    interview = db.query(Interview).filter(Interview.id == interview_id).first()
    if not interview:
        raise HTTPException(status_code=404, detail="面试不存在")

    service = ReportService(db)
    try:
        return await service.generate(interview_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
