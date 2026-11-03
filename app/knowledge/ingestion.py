import re

import pymupdf

from multiprocessing import Value
from pathlib import Path

from app.knowledge.embeddings import EmbeddingModel
from app.knowledge.vector_store import ChromaVectorStore


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
    Split the content extracted from PDF into chunks (per section).
    Identifies numeric titles
    Args:
        extracted_pages: List of pages.
        chunk_size: Maximum size of each chunk.
        overlap: 
    Returns:
        list of chunks with ID, page, section and content.
    """

    if chunk_size <= overlap:
        raise ValueError("chunk_size should be greater than overlap.")

    sections = []
    current_section = None

    section_pattern = re.compile(r"^\s*(\d+(?:\.\d+)*)(?:[.)])?\s+([A-ZÁÉÍÓÚÂÊÔÃÕÇ].*?)\s*$")

    for page_data in extracted_pages:
        page_number = page_data["page"]
        lines = page_data["content"].splitlines()

        for line in lines:
            line = line.strip()

            if not line:
                continue

            match = section_pattern.match(line)

            if match:
                if current_section:
                    sections.append(current_section)

                section_number = match.group(1)
                section_title = match.group(2)

                current_section = {
                    "section": section_number,
                    "title": section_title,
                    "page": page_number,
                    "content": []
                }

            elif current_section:
                current_section["content"].append(line)

    if current_section:
        sections.append(current_section)

    chunks = []

    for section in sections:
        header = (f"Seção {section['section']}: {section['title']}")

        section_text = "\n".join(section["content"]).strip()

        if not section_text:
            continue

        full_text = f"{header}\n\n{section_text}"

        if len(full_text) <= chunk_size:
            chunks.append({
                "id": f"section-{section['section']}-chunk-1",
                "page": section["page"],
                "section": section["section"],
                "content": full_text
            })
            continue

        start = 0
        chunk_number = 1

        while start < len(section_text):
            end = start + chunk_size - len(header) - 2

            fragment = section_text[start:end]

            chunks.append({
                "id": (f"section-{section['section']}"f"-chunk-{chunk_number}"),
                "page": section["page"],
                "section": section["section"],
                "content": f"{header}\n\n{fragment}"
            })

            chunk_number += 1
            start = end - overlap

    ids = [chunk["id"] for chunk in chunks]
    assert len(ids) == len(set(ids)), "Existem IDs duplicados!"

    return chunks


def ingest_pdf(pdf_path: Path,embedding_model: EmbeddingModel,vector_store: ChromaVectorStore):
    """
    Extract, chunk, embed and store PDF content.
    Returns:
        int: Number of chunks stored.
    """

    extracted_pages = extract_pdf_pages(pdf_path)

    if not extracted_pages:
        raise ValueError("No text was extracted from the PDF.")

    chunks = chunk_pages(extracted_pages)

    if not chunks:
        raise ValueError("No chunks were generated from the PDF.")

    texts = [chunk["content"] for chunk in chunks]

    embeddings = embedding_model.encode(texts)
    vector_store.reset()
    vector_store.add_chunks(chunks, embeddings)

    return len(chunks)
