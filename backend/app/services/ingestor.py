import os
import io
from typing import List
from pypdf import PdfReader
from langchain_text_splitters import RecursiveCharacterTextSplitter

class DocumentIngestor:
    def __init__(self, chunk_size: int = 1000, chunk_overlap: int = 200):
        """
        Initializes the text splitter. 
        It will break big documents down into smaller, readable pieces.
        """
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            length_function=len,
            is_separator_regex=False,
        )

    def extract_text_from_pdf(self, file_source) -> str:
        """
        Extracts raw text strings from either a local file path OR a raw binary bytes stream.
        """
        # If the input is raw binary bytes from the network, wrap it in a stream object
        if isinstance(file_source, bytes):
            pdf_file = io.BytesIO(file_source)
        else:
            # Fallback wrapper in case a local string path is passed
            pdf_file = open(file_source, "rb")

        reader = PdfReader(pdf_file)
        extracted_text = ""
        
        for page in reader.pages:
            text = page.extract_text()
            if text:
                extracted_text += text + "\n"
                
        # If we opened a local file, make sure to close it cleanly
        if not isinstance(file_source, bytes):
            pdf_file.close()
            
        return extracted_text

    def create_chunks(self, text: str) -> List[str]:
        """Splits raw text into manageable, overlapping text blocks."""
        return self.text_splitter.split_text(text)