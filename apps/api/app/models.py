from datetime import datetime
from typing import Optional

from sqlalchemy import Column, Integer, String, DateTime, Text

from app.db import Base


class Job(Base):
    """Job model for tracking translation tasks."""
    
    __tablename__ = "jobs"
    
    id = Column(String, primary_key=True)  # UUID
    created_at = Column(DateTime, default=datetime.utcnow)
    email = Column(String, nullable=True)
    source_key = Column(String, nullable=False)  # R2 upload key
    output_epub_key = Column(String, nullable=True)  # R2 EPUB output key
    output_pdf_key = Column(String, nullable=True)  # R2 PDF output key  
    output_txt_key = Column(String, nullable=True)  # R2 TXT output key
    target_lang = Column(String, nullable=False)
    source_lang = Column(String, nullable=True)  # Auto-detected
    output_format = Column(String, default="translation")  # 'translation' | 'bilingual'
    provider = Column(String, nullable=False)  # 'gemini' | 'groq'
    status = Column(String, default="queued")  # queued|processing|done|failed
    error = Column(Text, nullable=True)
    size_bytes = Column(Integer, nullable=False)
    tokens_est = Column(Integer, nullable=False)
    tokens_actual = Column(Integer, nullable=True)
    provider_cost_cents = Column(Integer, nullable=True)
    price_charged_cents = Column(Integer, nullable=False)
    stripe_payment_id = Column(String, unique=True, nullable=True)  # Idempotency
    progress_step = Column(String, default="queued")  # User-visible ETA
    progress_percent = Column(Integer, default=0)  # 0-100 for smooth progress bar
    failover_count = Column(Integer, default=0)  # Provider fallback tracking
    
    def __repr__(self):
        return f"<Job(id={self.id}, status={self.status}, provider={self.provider})>"