from fastapi import APIRouter, UploadFile, File, HTTPException, Form, Depends
from typing import Optional
from functools import lru_cache

from app.models.schemas import DocumentResponse

router = APIRouter(prefix="/api/documents", tags=["documents"])


@lru_cache()
def get_document_service():
    from app.services.document_service import DocumentService
    return DocumentService()


@router.post("/upload", response_model=DocumentResponse)
async def upload_document(
    file: UploadFile = File(...),
    document_service = Depends(get_document_service),
):
    try:
        content = await file.read()
        text_content = content.decode("utf-8")
        
        result = document_service.ingest_document(
            filename=file.filename or "unknown",
            content=text_content
        )
        
        return result
    except UnicodeDecodeError:
        raise HTTPException(
            status_code=400,
            detail="File must be a valid text file (UTF-8 encoded)"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/upload-text", response_model=DocumentResponse)
async def upload_text(
    filename: str = Form(...),
    content: str = Form(...),
    document_service = Depends(get_document_service),
):
    try:
        result = document_service.ingest_document(
            filename=filename,
            content=content
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("", response_model=list[DocumentResponse])
async def list_documents(document_service = Depends(get_document_service)):
    try:
        return document_service.get_all_documents()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{document_id}", response_model=DocumentResponse)
async def get_document(document_id: str, document_service = Depends(get_document_service)):
    try:
        doc = document_service._get_document(document_id)
        return DocumentResponse(
            id=doc.id,
            filename=doc.filename,
            chunk_count=doc.chunk_count,
            raptor_indexed=doc.raptor_indexed,
            graphrag_indexed=doc.graphrag_indexed,
            created_at=doc.created_at
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{document_id}")
async def delete_document(document_id: str, document_service = Depends(get_document_service)):
    try:
        document_service.delete_document(document_id)
        return {"status": "success", "message": f"Document {document_id} deleted"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
