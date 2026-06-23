# async worker
# find pending job
# mark as processing
# process document
    # run generate chunks
    # run extract occurrences
# mark as completed

from scripts.process_document_chunks import generate_chunks_for_document
from scripts.process_keyword_occurrences import extract_occurrences_for_document
