"""
Content Cleaner - Removes duplicates and cleans document content

Handles:
- Exact duplicate detection and removal
- Near-duplicate detection using fuzzy matching
- Content normalization (whitespace, special characters)
- Boilerplate removal (headers, footers, common templates)
"""

import hashlib
import re
from typing import List, Set, Dict, Tuple
from collections import Counter
from langchain.schema import Document
from difflib import SequenceMatcher


class ContentCleaner:
    """Cleans and deduplicates document content"""

    def __init__(self,
                 similarity_threshold: float = 0.95,
                 min_content_length: int = 50):
        """
        Args:
            similarity_threshold: Threshold for near-duplicate detection (0-1)
            min_content_length: Minimum length to keep a chunk
        """
        self.similarity_threshold = similarity_threshold
        self.min_content_length = min_content_length

        self.stats = {
            'total_input_chunks': 0,
            'exact_duplicates_removed': 0,
            'near_duplicates_removed': 0,
            'too_small_removed': 0,
            'boilerplate_removed': 0,
            'total_output_chunks': 0,
        }

    def clean_and_deduplicate(self,
                              chunks: List[Document],
                              remove_near_duplicates: bool = True,
                              remove_boilerplate: bool = True) -> List[Document]:
        """
        Clean and deduplicate chunks

        Args:
            chunks: List of document chunks
            remove_near_duplicates: Whether to detect and remove near-duplicates
            remove_boilerplate: Whether to remove common boilerplate text

        Returns:
            List of cleaned, deduplicated chunks
        """
        self.stats['total_input_chunks'] += len(chunks)

        if not chunks:
            return []

        # Step 1: Remove exact duplicates
        chunks = self._remove_exact_duplicates(chunks)

        # Step 2: Remove near-duplicates (optional)
        if remove_near_duplicates:
            chunks = self._remove_near_duplicates(chunks)

        # Step 3: Remove boilerplate patterns (optional)
        if remove_boilerplate:
            chunks = self._remove_boilerplate(chunks)

        # Step 4: Remove chunks that are too small
        chunks = self._filter_small_chunks(chunks)

        # Step 5: Normalize content
        chunks = self._normalize_chunks(chunks)

        self.stats['total_output_chunks'] = len(chunks)

        return chunks

    def _remove_exact_duplicates(self, chunks: List[Document]) -> List[Document]:
        """Remove chunks with identical content"""

        seen_hashes: Set[str] = set()
        unique_chunks = []

        for chunk in chunks:
            # Create hash of content
            content_hash = hashlib.md5(chunk.page_content.encode()).hexdigest()

            if content_hash not in seen_hashes:
                seen_hashes.add(content_hash)
                unique_chunks.append(chunk)
            else:
                self.stats['exact_duplicates_removed'] += 1

        return unique_chunks

    def _remove_near_duplicates(self, chunks: List[Document]) -> List[Document]:
        """Remove chunks that are very similar (near-duplicates)"""

        if len(chunks) <= 1:
            return chunks

        unique_chunks = []
        seen_contents = []

        for chunk in chunks:
            is_duplicate = False

            # Compare with previously seen chunks
            for seen_content in seen_contents:
                similarity = self._calculate_similarity(
                    chunk.page_content,
                    seen_content
                )

                if similarity >= self.similarity_threshold:
                    is_duplicate = True
                    self.stats['near_duplicates_removed'] += 1
                    break

            if not is_duplicate:
                unique_chunks.append(chunk)
                seen_contents.append(chunk.page_content)

        return unique_chunks

    def _remove_boilerplate(self, chunks: List[Document]) -> List[Document]:
        """Remove common boilerplate patterns"""

        # Identify boilerplate: text that appears too frequently
        content_counter = Counter(chunk.page_content for chunk in chunks)

        # If a chunk appears in > 20% of documents, it's likely boilerplate
        threshold = max(3, len(chunks) * 0.2)
        boilerplate_content = {
            content for content, count in content_counter.items()
            if count >= threshold
        }

        if not boilerplate_content:
            return chunks

        # Remove boilerplate chunks
        cleaned_chunks = []
        for chunk in chunks:
            if chunk.page_content not in boilerplate_content:
                cleaned_chunks.append(chunk)
            else:
                self.stats['boilerplate_removed'] += 1

        return cleaned_chunks

    def _filter_small_chunks(self, chunks: List[Document]) -> List[Document]:
        """Remove chunks that are too small to be useful"""

        filtered_chunks = []

        for chunk in chunks:
            content_length = len(chunk.page_content.strip())

            if content_length >= self.min_content_length:
                filtered_chunks.append(chunk)
            else:
                self.stats['too_small_removed'] += 1

        return filtered_chunks

    def _normalize_chunks(self, chunks: List[Document]) -> List[Document]:
        """Normalize whitespace and formatting in chunks"""

        for chunk in chunks:
            # Normalize whitespace
            content = chunk.page_content
            content = re.sub(r'\s+', ' ', content)  # Multiple spaces to single
            content = re.sub(r'\n\s*\n\s*\n+', '\n\n', content)  # Multiple newlines to double
            content = content.strip()

            chunk.page_content = content

        return chunks

    def _calculate_similarity(self, text1: str, text2: str) -> float:
        """Calculate similarity between two texts using sequence matching"""

        # Quick length check
        len1, len2 = len(text1), len(text2)
        if len1 == 0 or len2 == 0:
            return 0.0

        # If lengths are very different, they're probably not duplicates
        length_ratio = min(len1, len2) / max(len1, len2)
        if length_ratio < 0.5:
            return 0.0

        # Use SequenceMatcher for fuzzy matching
        return SequenceMatcher(None, text1, text2).ratio()

    def detect_common_patterns(self, chunks: List[Document]) -> Dict[str, int]:
        """Detect common patterns in chunks (for debugging)"""

        # Common patterns to detect
        patterns = {
            'japanese_header': r'^\d+\.\s*書誌情報',
            'researchgate': r'researchgate\.net',
            'doi': r'doi\.org',
            'arxiv': r'arxiv\.org',
            'citations': r'(References|参考文献|Bibliography)',
            'copyright': r'©|Copyright',
            'page_numbers': r'^\d+$',
            'urls': r'https?://',
        }

        pattern_counts = {name: 0 for name in patterns.keys()}

        for chunk in chunks:
            content = chunk.page_content
            for name, pattern in patterns.items():
                if re.search(pattern, content, re.IGNORECASE):
                    pattern_counts[name] += 1

        return pattern_counts

    def get_stats(self) -> Dict:
        """Get cleaning statistics"""
        stats = self.stats.copy()

        if stats['total_input_chunks'] > 0:
            stats['removal_rate'] = (
                (stats['total_input_chunks'] - stats['total_output_chunks'])
                / stats['total_input_chunks']
            )
        else:
            stats['removal_rate'] = 0.0

        return stats

    def print_stats(self):
        """Print cleaning statistics"""
        print("\n" + "="*80)
        print("CONTENT CLEANING STATISTICS")
        print("="*80)

        stats = self.get_stats()

        print(f"\nInput chunks: {stats['total_input_chunks']}")
        print(f"Output chunks: {stats['total_output_chunks']}")
        print(f"Total removed: {stats['total_input_chunks'] - stats['total_output_chunks']}")
        print(f"Removal rate: {stats['removal_rate']:.1%}")

        print(f"\nRemoval breakdown:")
        print(f"  Exact duplicates: {stats['exact_duplicates_removed']}")
        print(f"  Near duplicates: {stats['near_duplicates_removed']}")
        print(f"  Boilerplate: {stats['boilerplate_removed']}")
        print(f"  Too small: {stats['too_small_removed']}")

        print("="*80)


def clean_documents(chunks: List[Document],
                   min_length: int = 100,
                   similarity_threshold: float = 0.95,
                   remove_near_duplicates: bool = True) -> List[Document]:
    """
    Convenience function to clean and deduplicate documents

    Args:
        chunks: List of document chunks
        min_length: Minimum chunk length to keep
        similarity_threshold: Threshold for near-duplicate detection
        remove_near_duplicates: Whether to remove near-duplicates

    Returns:
        Cleaned and deduplicated chunks
    """
    cleaner = ContentCleaner(
        similarity_threshold=similarity_threshold,
        min_content_length=min_length
    )

    return cleaner.clean_and_deduplicate(
        chunks,
        remove_near_duplicates=remove_near_duplicates
    )
