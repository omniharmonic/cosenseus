from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional

import sys
import os
from pydantic import BaseModel
import uuid

# Add the backend directory to the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), '../..'))

from core.database_local import get_local_db
from shared.models.database import EventTemplate, OutputTemplate

router = APIRouter()

# Pydantic Schemas for Event Templates
class EventTemplateBase(BaseModel):
    name: str
    description: Optional[str] = None
    structure: Dict[str, Any]

class EventTemplateCreate(EventTemplateBase):
    pass

class EventTemplateResponse(EventTemplateBase):
    id: uuid.UUID

    class Config:
        from_attributes = True

# Pydantic Schemas for Output Templates
class OutputTemplateBase(BaseModel):
    name: str
    description: Optional[str] = None
    structure: Dict[str, Any]

class OutputTemplateCreate(OutputTemplateBase):
    pass

class OutputTemplateResponse(OutputTemplateBase):
    id: uuid.UUID

    class Config:
        from_attributes = True

# --- Event Template CRUD Endpoints ---

@router.post("/templates/events/", response_model=EventTemplateResponse, status_code=201)
def create_event_template(template: EventTemplateCreate, db: Session = Depends(get_local_db)):
    db_template = EventTemplate(**template.model_dump())
    db.add(db_template)
    db.commit()
    db.refresh(db_template)
    return db_template

@router.get("/templates/events/", response_model=List[EventTemplateResponse])
def read_event_templates(skip: int = 0, limit: int = 100, db: Session = Depends(get_local_db)):
    templates = db.query(EventTemplate).offset(skip).limit(limit).all()
    return templates

@router.get("/templates/events/{template_id}", response_model=EventTemplateResponse)
def read_event_template(template_id: uuid.UUID, db: Session = Depends(get_local_db)):
    db_template = db.query(EventTemplate).filter(EventTemplate.id == template_id).first()
    if db_template is None:
        raise HTTPException(status_code=404, detail="Event template not found")
    return db_template

@router.put("/templates/events/{template_id}", response_model=EventTemplateResponse)
def update_event_template(template_id: uuid.UUID, template: EventTemplateCreate, db: Session = Depends(get_local_db)):
    db_template = db.query(EventTemplate).filter(EventTemplate.id == template_id).first()
    if db_template is None:
        raise HTTPException(status_code=404, detail="Event template not found")
    
    for key, value in template.model_dump().items():
        setattr(db_template, key, value)
        
    db.commit()
    db.refresh(db_template)
    return db_template

@router.delete("/templates/events/{template_id}", status_code=204)
def delete_event_template(template_id: uuid.UUID, db: Session = Depends(get_local_db)):
    db_template = db.query(EventTemplate).filter(EventTemplate.id == template_id).first()
    if db_template is None:
        raise HTTPException(status_code=404, detail="Event template not found")
    db.delete(db_template)
    db.commit()
    return

# --- Output Template CRUD Endpoints ---

@router.post("/templates/outputs/", response_model=OutputTemplateResponse, status_code=201)
def create_output_template(template: OutputTemplateCreate, db: Session = Depends(get_local_db)):
    db_template = OutputTemplate(**template.model_dump())
    db.add(db_template)
    db.commit()
    db.refresh(db_template)
    return db_template

@router.get("/templates/outputs/", response_model=List[OutputTemplateResponse])
def read_output_templates(skip: int = 0, limit: int = 100, db: Session = Depends(get_local_db)):
    templates = db.query(OutputTemplate).offset(skip).limit(limit).all()
    return templates

@router.get("/templates/outputs/{template_id}", response_model=OutputTemplateResponse)
def read_output_template(template_id: uuid.UUID, db: Session = Depends(get_local_db)):
    db_template = db.query(OutputTemplate).filter(OutputTemplate.id == template_id).first()
    if db_template is None:
        raise HTTPException(status_code=404, detail="Output template not found")
    return db_template

@router.put("/templates/outputs/{template_id}", response_model=OutputTemplateResponse)
def update_output_template(template_id: uuid.UUID, template: OutputTemplateCreate, db: Session = Depends(get_local_db)):
    db_template = db.query(OutputTemplate).filter(OutputTemplate.id == template_id).first()
    if db_template is None:
        raise HTTPException(status_code=404, detail="Output template not found")
        
    for key, value in template.model_dump().items():
        setattr(db_template, key, value)
        
    db.commit()
    db.refresh(db_template)
    return db_template

@router.delete("/templates/outputs/{template_id}", status_code=204)
def delete_output_template(template_id: uuid.UUID, db: Session = Depends(get_local_db)):
    db_template = db.query(OutputTemplate).filter(OutputTemplate.id == template_id).first()
    if db_template is None:
        raise HTTPException(status_code=404, detail="Output template not found")
    db.delete(db_template)
    db.commit()
    return 