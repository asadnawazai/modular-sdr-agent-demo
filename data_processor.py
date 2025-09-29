#!/usr/bin/env python3
"""
Data Processing Script for LLM Fine-tuning
==========================================

This script processes PDF and JSON data files to extract and combine text content
into a clean, structured format suitable for LLM fine-tuning.

Features:
- PDF text extraction with multi-page support
- JSON recursive text extraction
- Text cleaning and normalization
- JSONL output format for LLM training
- Batch processing with progress tracking
- Comprehensive error handling and logging

Author: AI Assistant
"""

import os
import sys
import json
import logging
import argparse
import hashlib
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional, Iterator
import re

# PDF processing libraries
try:
    import pdfplumber
    import PyPDF2
    PDF_LIBRARIES_AVAILABLE = True
except ImportError:
    PDF_LIBRARIES_AVAILABLE = False

# Progress tracking
try:
    from tqdm import tqdm
    TQDM_AVAILABLE = True
except ImportError:
    TQDM_AVAILABLE = False


class DataProcessor:
    """Main class for processing PDF and JSON files for LLM fine-tuning."""
    
    def __init__(self, log_level: str = "INFO"):
        """Initialize the DataProcessor with logging configuration."""
        self.setup_logging(log_level)
        self.logger = logging.getLogger(__name__)
        
        # Check dependencies
        if not PDF_LIBRARIES_AVAILABLE:
            self.logger.warning("PDF libraries not available. PDF processing will be disabled.")
        
        # Statistics tracking
        self.stats = {
            'files_processed': 0,
            'pdf_files': 0,
            'json_files': 0,
            'errors': 0,
            'total_text_length': 0,
            'duplicates_removed': 0
        }
        
    def setup_logging(self, log_level: str) -> None:
        """Setup logging configuration."""
        log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        logging.basicConfig(
            level=getattr(logging, log_level.upper()),
            format=log_format,
            handlers=[
                logging.StreamHandler(sys.stdout),
                logging.FileHandler('data_processor.log', mode='a')
            ]
        )
    
    def clean_text(self, text: str) -> str:
        """Clean and normalize extracted text."""
        if not text or not isinstance(text, str):
            return ""
        
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text)
        
        # Remove control characters except newlines and tabs
        text = re.sub(r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]', '', text)
        
        # Normalize line breaks
        text = re.sub(r'\r\n|\r', '\n', text)
        
        # Remove excessive newlines
        text = re.sub(r'\n{3,}', '\n\n', text)
        
        # Strip leading/trailing whitespace
        text = text.strip()
        
        return text
    
    def extract_pdf_text(self, pdf_path: Path) -> Optional[str]:
        """Extract text from PDF file using pdfplumber as primary, PyPDF2 as fallback."""
        if not PDF_LIBRARIES_AVAILABLE:
            self.logger.error("PDF libraries not available")
            return None
            
        try:
            # Try pdfplumber first (better for text extraction)
            text_content = []
            with pdfplumber.open(pdf_path) as pdf:
                for page_num, page in enumerate(pdf.pages, 1):
                    try:
                        page_text = page.extract_text()
                        if page_text:
                            text_content.append(f"=== Page {page_num} ===\n{page_text}")
                    except Exception as e:
                        self.logger.warning(f"Error extracting page {page_num} from {pdf_path}: {e}")
                        continue
            
            if text_content:
                full_text = "\n\n".join(text_content)
                self.logger.debug(f"Successfully extracted {len(full_text)} characters from {pdf_path}")
                return self.clean_text(full_text)
        
        except Exception as e:
            self.logger.warning(f"pdfplumber failed for {pdf_path}: {e}. Trying PyPDF2...")
            
            # Fallback to PyPDF2
            try:
                text_content = []
                with open(pdf_path, 'rb') as file:
                    reader = PyPDF2.PdfReader(file)
                    for page_num, page in enumerate(reader.pages, 1):
                        try:
                            page_text = page.extract_text()
                            if page_text:
                                text_content.append(f"=== Page {page_num} ===\n{page_text}")
                        except Exception as e:
                            self.logger.warning(f"Error extracting page {page_num} from {pdf_path}: {e}")
                            continue
                
                if text_content:
                    full_text = "\n\n".join(text_content)
                    self.logger.debug(f"Successfully extracted {len(full_text)} characters from {pdf_path} using PyPDF2")
                    return self.clean_text(full_text)
                        
            except Exception as e:
                self.logger.error(f"PyPDF2 also failed for {pdf_path}: {e}")
        
        return None
    
    def extract_json_text(self, json_path: Path) -> Optional[str]:
        """Extract text content from JSON file recursively."""
        try:
            with open(json_path, 'r', encoding='utf-8') as file:
                data = json.load(file)
            
            text_parts = []
            self._extract_text_recursive(data, text_parts)
            
            if text_parts:
                full_text = "\n".join(text_parts)
                self.logger.debug(f"Successfully extracted {len(full_text)} characters from {json_path}")
                return self.clean_text(full_text)
                
        except json.JSONDecodeError as e:
            self.logger.error(f"Invalid JSON in {json_path}: {e}")
        except Exception as e:
            self.logger.error(f"Error processing {json_path}: {e}")
        
        return None
    
    def _extract_text_recursive(self, data: Any, text_parts: List[str]) -> None:
        """Recursively extract text from nested JSON structures."""
        if isinstance(data, dict):
            for key, value in data.items():
                if isinstance(value, str) and value.strip():
                    text_parts.append(f"{key}: {value}")
                elif isinstance(value, (dict, list)):
                    self._extract_text_recursive(value, text_parts)
                    
        elif isinstance(data, list):
            for item in data:
                self._extract_text_recursive(item, text_parts)
                
        elif isinstance(data, str) and data.strip():
            text_parts.append(data)
    
    def generate_text_hash(self, text: str) -> str:
        """Generate a hash for text to detect duplicates."""
        return hashlib.md5(text.encode('utf-8')).hexdigest()
    
    def process_files(self, input_paths: List[Path], output_path: Path) -> Dict[str, Any]:
        """Process multiple files and combine into structured output."""
        self.logger.info(f"Starting processing of {len(input_paths)} files")
        
        # Collect all text content
        extracted_texts = []
        seen_hashes = set()
        
        # Setup progress bar if tqdm is available
        if TQDM_AVAILABLE:
            pbar = tqdm(input_paths, desc="Processing files")
        else:
            pbar = input_paths
        
        for file_path in pbar:
            try:
                self.stats['files_processed'] += 1
                
                text_content = None
                file_extension = file_path.suffix.lower()
                
                if file_extension == '.pdf':
                    text_content = self.extract_pdf_text(file_path)
                    self.stats['pdf_files'] += 1
                    
                elif file_extension == '.json':
                    text_content = self.extract_json_text(file_path)
                    self.stats['json_files'] += 1
                    
                else:
                    self.logger.warning(f"Unsupported file type: {file_path}")
                    continue
                
                if text_content:
                    # Check for duplicates
                    text_hash = self.generate_text_hash(text_content)
                    if text_hash in seen_hashes:
                        self.logger.info(f"Duplicate content found in {file_path}, skipping")
                        self.stats['duplicates_removed'] += 1
                        continue
                    
                    seen_hashes.add(text_hash)
                    self.stats['total_text_length'] += len(text_content)
                    
                    # Create structured record
                    record = {
                        'text': text_content,
                        'metadata': {
                            'source_file': str(file_path),
                            'file_type': file_extension,
                            'extraction_timestamp': datetime.now().isoformat(),
                            'text_length': len(text_content),
                            'text_hash': text_hash
                        }
                    }
                    extracted_texts.append(record)
                    
                else:
                    self.logger.warning(f"No text extracted from {file_path}")
                    
            except Exception as e:
                self.logger.error(f"Error processing {file_path}: {e}")
                self.stats['errors'] += 1
                continue
        
        # Write output in JSONL format
        self._write_jsonl_output(extracted_texts, output_path)
        
        # Log final statistics
        self._log_statistics()
        
        return self.stats
    
    def _write_jsonl_output(self, records: List[Dict[str, Any]], output_path: Path) -> None:
        """Write records to JSONL format file."""
        try:
            with open(output_path, 'w', encoding='utf-8') as file:
                for record in records:
                    json.dump(record, file, ensure_ascii=False)
                    file.write('\n')
            
            self.logger.info(f"Successfully wrote {len(records)} records to {output_path}")
            
        except Exception as e:
            self.logger.error(f"Error writing output file {output_path}: {e}")
            raise
    
    def _log_statistics(self) -> None:
        """Log processing statistics."""
        self.logger.info("Processing Statistics:")
        self.logger.info(f"  Files processed: {self.stats['files_processed']}")
        self.logger.info(f"  PDF files: {self.stats['pdf_files']}")
        self.logger.info(f"  JSON files: {self.stats['json_files']}")
        self.logger.info(f"  Errors: {self.stats['errors']}")
        self.logger.info(f"  Total text length: {self.stats['total_text_length']:,} characters")
        self.logger.info(f"  Duplicates removed: {self.stats['duplicates_removed']}")


def find_files(paths: List[Path], extensions: List[str] = ['.pdf', '.json']) -> List[Path]:
    """Find all files with specified extensions in given paths."""
    found_files = []
    
    for path in paths:
        if path.is_file():
            if path.suffix.lower() in extensions:
                found_files.append(path)
        elif path.is_dir():
            for ext in extensions:
                found_files.extend(path.glob(f"**/*{ext}"))
    
    return sorted(found_files)


def main():
    """Main entry point for the script."""
    parser = argparse.ArgumentParser(
        description="Process PDF and JSON files to extract text for LLM fine-tuning",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python data_processor.py --input ./data --output extracted_data.jsonl
  python data_processor.py --input file1.pdf file2.json --output output.jsonl --log-level DEBUG
  python data_processor.py --input ./pdfs ./jsons --output combined.jsonl
        """
    )
    
    parser.add_argument(
        '--input', '-i',
        nargs='+',
        required=True,
        help='Input file paths or directories containing PDF/JSON files'
    )
    
    parser.add_argument(
        '--output', '-o',
        required=True,
        help='Output file path (JSONL format)'
    )
    
    parser.add_argument(
        '--log-level',
        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'],
        default='INFO',
        help='Logging level (default: INFO)'
    )
    
    args = parser.parse_args()
    
    # Convert input paths to Path objects
    input_paths = [Path(p) for p in args.input]
    output_path = Path(args.output)
    
    # Validate input paths
    for path in input_paths:
        if not path.exists():
            print(f"Error: Input path does not exist: {path}")
            sys.exit(1)
    
    # Create output directory if needed
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Find all files to process
    files_to_process = find_files(input_paths)
    
    if not files_to_process:
        print("No PDF or JSON files found in the specified paths.")
        sys.exit(1)
    
    print(f"Found {len(files_to_process)} files to process:")
    for file_path in files_to_process[:10]:  # Show first 10
        print(f"  {file_path}")
    if len(files_to_process) > 10:
        print(f"  ... and {len(files_to_process) - 10} more files")
    
    # Process files
    processor = DataProcessor(log_level=args.log_level)
    stats = processor.process_files(files_to_process, output_path)
    
    print("\nProcessing completed!")
    print(f"Output written to: {output_path}")
    print(f"Records created: {stats['files_processed'] - stats['errors']}")


if __name__ == "__main__":
    main()