import re
from typing import List
from app.core.config import settings

def chunk_text(text: str, chunk_size: int = None, chunk_overlap: int = None) -> List[str]:
    """
    Splits text into meaningful chunks while preserving paragraph/sentence boundaries.
    """
    if not text:
        return []

    size = chunk_size or settings.DOCUMENT_CHUNK_SIZE
    overlap = chunk_overlap or settings.DOCUMENT_CHUNK_OVERLAP

    # Basic normalization (if not already done)
    text = text.strip()

    # Split by paragraphs first
    paragraphs = re.split(r'\n{2,}', text)
    
    chunks = []
    current_chunk = ""

    for para in paragraphs:
        para = para.strip()
        if not para:
            continue
            
        # If adding this paragraph exceeds chunk size and we already have content
        if len(current_chunk) + len(para) + 2 > size and current_chunk:
            chunks.append(current_chunk.strip())
            
            # Start new chunk with overlap if possible
            if overlap > 0 and len(current_chunk) > overlap:
                # Find a good breaking point in the overlap region (e.g. sentence boundary)
                overlap_text = current_chunk[-overlap:]
                # Try to break at a sentence or word
                match = re.search(r'[.!?]\s+', overlap_text)
                if match:
                    current_chunk = overlap_text[match.end():] + " " + para
                else:
                    # Fallback to just taking the last `overlap` characters (adjust to nearest word)
                    space_idx = overlap_text.find(" ")
                    if space_idx != -1:
                        current_chunk = overlap_text[space_idx+1:] + " " + para
                    else:
                        current_chunk = overlap_text + " " + para
            else:
                current_chunk = para
        else:
            if current_chunk:
                current_chunk += "\n\n" + para
            else:
                current_chunk = para
                
        # If a single paragraph is larger than size, we should split it by sentences
        while len(current_chunk) > size:
            # Find the last sentence end within the size limit
            split_point = current_chunk.rfind(". ", 0, size)
            if split_point == -1:
                # Fallback to space
                split_point = current_chunk.rfind(" ", 0, size)
            
            if split_point == -1:
                # Absolute worst case, split exactly at size
                split_point = size
            else:
                split_point += 1 # Include the period or space
                
            chunks.append(current_chunk[:split_point].strip())
            
            if overlap > 0:
                progress_idx = max(split_point - overlap, 1)
                # Ensure we make some progress to avoid infinite loop
                if progress_idx >= split_point:
                    progress_idx = split_point
                current_chunk = current_chunk[progress_idx:].strip()
            else:
                current_chunk = current_chunk[split_point:].strip()

    if current_chunk:
        chunks.append(current_chunk.strip())

    # Filter out empty chunks
    return [c for c in chunks if c]
