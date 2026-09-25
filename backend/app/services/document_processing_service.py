import os
import re
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from pypdf import PdfReader
from docx import Document as DocxDocument
from app.models.document import Document
from app.models.document_chunk import DocumentChunk
from app.services.document_chunking_service import chunk_text
from app.services.embedding_service import generate_embeddings

def clean_text(text: str) -> str:
    if not text:
        return ""
    
    # Normalize line endings
    text = text.replace('\r\n', '\n').replace('\r', '\n')
    
    # Remove excessive blank lines (more than 2 consecutive newlines become 2 newlines)
    text = re.sub(r'\n{3,}', '\n\n', text)
    
    # Remove excessive spaces (more than 2 consecutive spaces become 1 space)
    # but don't touch newlines
    text = re.sub(r'[ \t]{2,}', ' ', text)
    
    # Trim leading and trailing whitespace
    return text.strip()

def extract_text_from_pdf(file_path: str) -> str:
    text_content = []
    try:
        reader = PdfReader(file_path)
        for page in reader.pages:
            page_text = page.extract_text()
            if page_text:
                text_content.append(page_text)
        
        extracted = "\n\n".join(text_content)
        if not extracted.strip():
            raise ValueError("Could not extract readable text from this PDF.")
        return extracted
    except Exception as e:
        raise ValueError(f"PDF Extraction Error: {str(e)}")

def extract_text_from_docx(file_path: str) -> str:
    text_content = []
    try:
        doc = DocxDocument(file_path)
        for para in doc.paragraphs:
            if para.text.strip():
                text_content.append(para.text.strip())
        
        extracted = "\n\n".join(text_content)
        if not extracted.strip():
            raise ValueError("Could not extract readable text from this DOCX.")
        return extracted
    except Exception as e:
        raise ValueError(f"DOCX Extraction Error: {str(e)}")

def extract_text_from_txt(file_path: str) -> str:
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            extracted = f.read()
        if not extracted.strip():
            raise ValueError("TXT file is empty.")
        return extracted
    except Exception as e:
        raise ValueError(f"TXT Extraction Error: {str(e)}")

def process_document(db: Session, document_id: int, user_id: int) -> Document:
    # Fetch the document and verify ownership
    doc = db.query(Document).filter(Document.id == document_id).first()
    if not doc or doc.user_id != user_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")
    
    if not os.path.exists(doc.storage_path):
        doc.processing_status = "failed"
        doc.processing_error = "Physical file missing on server."
        db.commit()
        db.refresh(doc)
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Physical file missing.")

    # Mark as processing
    doc.processing_status = "processing"
    doc.processing_error = None
    db.commit()
    db.refresh(doc)

    try:
        # Extract text based on file_type
        raw_text = ""
        if doc.file_type == "pdf":
            raw_text = extract_text_from_pdf(doc.storage_path)
        elif doc.file_type == "docx":
            raw_text = extract_text_from_docx(doc.storage_path)
        elif doc.file_type == "txt":
            raw_text = extract_text_from_txt(doc.storage_path)
        else:
            raise ValueError("Unsupported file type for extraction.")
        
        # Clean text
        cleaned_text = clean_text(raw_text)
        
        # Chunk text
        chunks = chunk_text(cleaned_text)
        if not chunks:
            raise ValueError("No extractable chunks found in the document.")

        # Generate embeddings
        try:
            embeddings = generate_embeddings(chunks)
        except Exception as e:
            raise ValueError(f"Embedding generation failed: {str(e)}")
            
        if len(chunks) != len(embeddings):
            raise ValueError("Mismatch between chunks and embeddings.")

        # Remove existing chunks for this document if any (in case of reprocessing)
        db.query(DocumentChunk).filter(DocumentChunk.document_id == doc.id).delete()
        
        # Create new chunks
        for i, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
            doc_chunk = DocumentChunk(
                document_id=doc.id,
                user_id=doc.user_id,
                chunk_index=i,
                content=chunk,
                embedding=embedding
            )
            db.add(doc_chunk)
        
        # Store results
        doc.extracted_text = cleaned_text
        doc.processing_status = "ready"
        doc.processed_at = datetime.now(timezone.utc)
        db.commit()
        db.refresh(doc)
        
        return doc
        
    except ValueError as e:
        db.rollback()
        db.query(Document).filter(Document.id == document_id).update({
            "processing_status": "failed",
            "processing_error": str(e)
        })
        db.commit()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        db.rollback()
        db.query(Document).filter(Document.id == document_id).update({
            "processing_status": "failed",
            "processing_error": "An unexpected error occurred during processing."
        })
        db.commit()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Document processing failed.")
