import json
from fastapi import APIRouter, HTTPException, Request, Depends
from sqlalchemy.orm import Session

from app.config import settings
from app.db import get_db
from app.deps import get_queue
from app.models import Job
from app.pipeline.worker import translate_epub
from app.logger import get_logger

logger = get_logger(__name__)

router = APIRouter()


# Stripe webhooks disabled - using PayPal only
# PayPal webhooks are handled in the PayPal router