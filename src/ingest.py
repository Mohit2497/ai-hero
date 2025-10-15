"""
ingest.py
Module for ingesting and processing markdown files from a GitHub repository,
extracting frontmatter metadata, chunking documents, and creating a search index.
"""

import io
import logging
import zipfile
import pickle
from pathlib import Path

import frontmatter
import requests
from minsearch import Index

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Suppress verbose logs from external libraries
logging.getLogger("google_genai.models").setLevel(logging.WARNING)
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("google.generativeai").setLevel(logging.WARNING)

def read_repo_data(repo_owner: str, repo_name: str) -> list[dict]:
    """
    Reads markdown files from a GitHub repository, extracts frontmatter metadata,
    and returns a list of dictionaries containing the metadata and filename.

    Args:
        repo_owner (str): GitHub repository owner.
        repo_name (str): GitHub repository name.

    Returns:
        list[dict]: List of dictionaries with frontmatter metadata and filename.
    """
    prefix = "https://github.com"
    url = f"{prefix}/{repo_owner}/{repo_name}/archive/refs/heads/master.zip"

    logger.info(f"Reading data from repository: {url}")

    resp = requests.get(url)

    if resp.status_code != 200:
        raise Exception(f"Failed to download repository: {resp.status_code}")
    else:
        logger.info("Repository downloaded successfully.")

    repository_data = []

    zf = zipfile.ZipFile(io.BytesIO(resp.content))

    for file_info in zf.infolist():
        filename = file_info.filename.lower()
        filename_lower = filename.lower()

        if not (filename.endswith(".md") or (filename.endswith(".mdx"))):
            continue

        if '/translations/' in filename and '/en/' not in filename:
            continue

        if any(skip in filename_lower for skip in ['/locale/', '/i18n/', '/.github/']):
            if '/en/' not in filename_lower and '/english/' not in filename_lower:
                continue

        with zf.open(file_info) as f_in:
            content = f_in.read().decode("utf-8", errors="ignore")
            post = frontmatter.loads(content)
            data = post.to_dict()

            _, filename_repo = file_info.filename.split("/", maxsplit=1)
            data["filename"] = filename_repo

            repository_data.append(data)

    zf.close()

    logger.info(f"Extracted {len(repository_data)} documents from the repository.")

    return repository_data


def sliding_window(seq: list, size: int, step: int) -> list[dict]:
    """
    Splits a sequence into overlapping chunks using a sliding window approach.
    Args:
        seq (list): The input sequence to be chunked.
        size (int): The size of each chunk.
        step (int): The step size for the sliding window.

    Returns:
        list of dict: A list of dictionaries, each containing the start index and the chunk content.
    """
    if size <= 0 or step <= 0:
        raise ValueError("size and step must be positive")

    n = len(seq)
    result = []
    for i in range(0, n, step):
        batch = seq[i : i + size]
        result.append({"start": i, "content": batch})
        if i + size > n:
            break

    return result


def chunk_documents(docs, size=2000, step=1000):
    """
    Chunks the "content" field of each document in the list using a sliding window approach.
    Each chunk retains the original document"s metadata.

    Args:
        docs (list of dict): List of documents, each containing a "content" field.
        size (int): The size of each chunk.
        step (int): The step size for the sliding window.

    Returns:
        list of dict: A list of chunked documents with metadata.
    """
    logger.info(f"Chunking {len(docs)} documents with size {size} and step {step}")

    chunks = []

    for doc in docs:
        doc_copy = doc.copy()
        doc_content = doc_copy.pop("content")
        doc_chunks = sliding_window(doc_content, size=size, step=step)
        for chunk in doc_chunks:
            chunk.update(doc_copy)
        chunks.extend(doc_chunks)

    logger.info(f"Generated {len(chunks)} chunks from {len(docs)} documents")

    return chunks


def load_cached_index(cache_filepath: str = "data/ms_ai_agents_index.pkl") -> Index | None:
    """
    Load pre-built index from disk cache.
    
    Args:
        cache_filepath (str): Path to the cached index file
        
    Returns:
        Index | None: The cached index or None if not found
    """
    cache_path = Path(cache_filepath)
    
    if not cache_path.exists():
        logger.info(f"No cached index found at {cache_filepath}")
        return None
    
    try:
        logger.info(f"Loading cached index from {cache_filepath}")
        with open(cache_path, 'rb') as f:
            index = pickle.load(f)
        
        file_size_mb = cache_path.stat().st_size / (1024 * 1024)
        logger.info(f"✅ Successfully loaded cached index ({file_size_mb:.2f} MB)")
        return index
        
    except Exception as e:
        logger.error(f"Failed to load cached index: {e}")
        return None


def index_data(
    repo_owner: str,
    repo_name: str,
    filter=None,
    chunk=True,
    chunking_params=None,
    use_cache=True,
    cache_filepath="data/ms_ai_agents_index.pkl"
):
    """
    Reads data from a GitHub repository, optionally filters and chunks the documents,
    and creates a search index. Supports loading from pre-built cache.

    Args:
        repo_owner (str): GitHub repository owner.
        repo_name (str): GitHub repository name.
        filter (callable, optional): A function to filter documents. Defaults to None.
        chunk (bool, optional): Whether to chunk documents. Defaults to True.
        chunking_params (dict, optional): Parameters for chunking. Defaults to None.
        use_cache (bool, optional): Whether to try loading from cache first. Defaults to True.
        cache_filepath (str, optional): Path to cache file. Defaults to "data/ms_ai_agents_index.pkl".

    Returns:
        Index: A search index created from the documents.
    """
    # Try loading from cache first
    if use_cache:
        cached_index = load_cached_index(cache_filepath)
        if cached_index is not None:
            logger.info("Using cached index - skipping repository download")
            return cached_index
    
    # If no cache, build fresh index
    logger.info("Building fresh index from repository...")
    docs = read_repo_data(repo_owner, repo_name)

    if filter is not None:
        docs = [doc for doc in docs if filter(doc)]

    if chunk:
        if chunking_params is None:
            chunking_params = {"size": 2000, "step": 1000}
        docs = chunk_documents(docs, **chunking_params)

    index = Index(
        text_fields=["content", "filename", "title", "author", "status", "type"],
    )

    index.fit(docs)
    logger.info("Fitting index completed.")

    return index