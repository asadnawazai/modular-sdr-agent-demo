# Data Processing Script for LLM Fine-tuning

This script processes PDF and JSON data files to extract and combine text content into a clean, structured format suitable for LLM fine-tuning.

## Features

- **PDF Processing**: Extract text from PDF files with multi-page support
- **JSON Processing**: Recursively extract text content from nested JSON structures
- **Text Cleaning**: Remove extra whitespace, normalize formatting, and clean control characters
- **Duplicate Detection**: Automatically detect and remove duplicate content using content hashing
- **JSONL Output**: Generate JSON Lines format suitable for LLM training
- **Batch Processing**: Process multiple files with progress tracking
- **Error Handling**: Robust error handling for corrupted or invalid files
- **Logging**: Comprehensive logging with configurable log levels
- **CLI Interface**: Easy-to-use command-line interface

## Installation

1. Install the required dependencies:
```bash
pip install -r requirements.txt
```

## Usage

### Basic Usage

Process files in a directory:
```bash
python data_processor.py --input ./data --output extracted_data.jsonl
```

Process specific files:
```bash
python data_processor.py --input file1.pdf file2.json --output output.jsonl
```

Process multiple directories:
```bash
python data_processor.py --input ./pdfs ./jsons --output combined.jsonl
```

### Advanced Usage

Enable debug logging:
```bash
python data_processor.py --input ./data --output output.jsonl --log-level DEBUG
```

Process with different log levels:
```bash
python data_processor.py --input ./data --output output.jsonl --log-level WARNING
```

### Command-line Options

- `--input, -i`: Input file paths or directories (required, accepts multiple values)
- `--output, -o`: Output file path in JSONL format (required)
- `--log-level`: Logging level (DEBUG, INFO, WARNING, ERROR, default: INFO)

## Output Format

The script generates output in JSON Lines (JSONL) format, where each line contains a JSON object with the following structure:

```json
{
  "text": "Extracted and cleaned text content from the source file",
  "metadata": {
    "source_file": "path/to/source/file.pdf",
    "file_type": ".pdf",
    "extraction_timestamp": "2024-01-15T10:30:45.123456",
    "text_length": 1234,
    "text_hash": "md5_hash_of_content"
  }
}
```

## Supported File Types

- **PDF**: `.pdf` files (using pdfplumber and PyPDF2)
- **JSON**: `.json` files with recursive text extraction

## Features in Detail

### PDF Text Extraction

- Uses `pdfplumber` as the primary extraction library for better accuracy
- Falls back to `PyPDF2` if pdfplumber fails
- Handles multi-page PDFs
- Extracts text page by page with page markers
- Cleans extracted text to remove formatting artifacts

### JSON Text Extraction

- Recursively traverses nested JSON structures
- Extracts all string values, including keys and values
- Handles arrays and nested objects
- Preserves context by including field names

### Text Cleaning

- Removes excessive whitespace and control characters
- Normalizes line breaks and spacing
- Preserves meaningful structure while cleaning formatting
- Handles various text encodings

### Duplicate Detection

- Uses MD5 hashing to identify duplicate content
- Compares cleaned text content, not file names
- Logs duplicate detection for transparency
- Helps reduce redundant training data

### Error Handling

- Continues processing even when individual files fail
- Logs specific error messages for debugging
- Provides comprehensive statistics at completion
- Handles corrupted PDFs and invalid JSON gracefully

## Logging

The script provides detailed logging with multiple levels:

- **DEBUG**: Detailed extraction information and processing steps
- **INFO**: General processing information and statistics (default)
- **WARNING**: Non-critical issues like duplicate files or extraction warnings
- **ERROR**: Critical errors that prevent file processing

Logs are written to both the console and a `data_processor.log` file.

## Examples

### Example 1: Process a directory of mixed files
```bash
python data_processor.py --input ./training_data --output llm_training.jsonl
```

### Example 2: Process specific files with debug output
```bash
python data_processor.py \
  --input document1.pdf document2.json research.pdf \
  --output processed_docs.jsonl \
  --log-level DEBUG
```

### Example 3: Process multiple directories
```bash
python data_processor.py \
  --input ./pdf_documents ./json_data ./additional_files \
  --output combined_training_data.jsonl
```

## Output Statistics

After processing, the script provides comprehensive statistics:

- Total files processed
- Number of PDF and JSON files
- Processing errors encountered
- Total characters extracted
- Number of duplicates removed
- Processing time and performance metrics

## Troubleshooting

### Common Issues

1. **PDF extraction fails**: The script will try both pdfplumber and PyPDF2. Some PDFs may be scanned images without extractable text.

2. **JSON parsing errors**: Invalid JSON files will be logged and skipped. Check the log output for specific error details.

3. **Memory usage**: For very large files or datasets, monitor memory usage. Consider processing in smaller batches if needed.

4. **Permission errors**: Ensure the script has read access to input files and write access to the output directory.

### Dependencies

If you encounter import errors, ensure all dependencies are installed:

```bash
pip install pdfplumber PyPDF2 tqdm jsonschema
```

## Performance Considerations

- Processing speed depends on file sizes and complexity
- PDF extraction is generally slower than JSON processing
- Progress bars show real-time processing status
- Large datasets can be processed in chunks if memory is limited

## Integration with LLM Training

The JSONL output format is compatible with most LLM training frameworks:

- Each line is a complete JSON record
- Text content is pre-cleaned and normalized
- Metadata allows for data provenance tracking
- Content deduplication reduces training data redundancy

## License

This script is part of the modular-sdr-agent-demo project. See the main project README for license information.