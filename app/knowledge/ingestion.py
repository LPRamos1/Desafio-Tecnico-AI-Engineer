from multiprocessing import Value
from pathlib import Path

import pymupdf


def extract_pdf_pages(pdf_path: Path):
    """
    Extract text from each page of a PDF document.
    Args:
        pdf_path (Path): path to the PDF document
    Returns:
        list[dict]: Extracted text and page number for each page.
    """
    if not pdf_path.exists():
        raise FileNotFoundError(f"PDF Document not found: {pdf_path}")

    extracted_pages = []

    with pymupdf.open(pdf_path) as document:
        for page_number, page in enumerate(document, start=1): # type: ignore
            text = page.get_text("text").strip()

            if text:
                extracted_pages.append({
                    "page": page_number,
                    "content": text
                })
    return extracted_pages


def chunk_pages(extracted_pages: list[dict], chunk_size: int = 1200, overlap: int = 150):
    """
    Split the extracted PDF pages into smaller text chunks.
    Args:
        extracted_pages (list[dict]): Extracted page contents and metadata.
        chunk_size (int): Maximum number of characters per chunk.
        overlap (int): Number of overlapping characters between chunks.
    Returns:
        list[dict]: Text chunks with their page numbers and identifiers.
    """
    if chunk_size <=0 :
        raise ValueError("Chunk size must be greater than zero.")

    if overlap < 0 or overlap >= chunk_size:
        raise ValueError("Overlap must be non-negative and smaller than chunk size")

    chunks = []

    for page_data in extracted_pages:
        page_number = page_data["page"]
        content = page_data["content"].strip()

        start = 0
        chunk_number = 1

        while start < len(content):
            end = min(start + chunk_size, len(content))

            # Prefer breaker at a line boundary
            if end < len(content):
                line_break = content.rfind("\n", start + chunk_size // 2, end)
                if line_break != -1:
                    end = line_break

            chunk_content = content[start:end].strip()

            if chunk_content:
                chunks.append({
                    "id": f"page-{page_number}-chunk-{chunk_number}",
                    "page": page_number,
                    "content": chunk_content
                })
                chunk_number += 1

            if end >= len(content):
                break

            start = end - overlap

    return chunks
