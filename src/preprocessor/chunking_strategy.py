"""
Chunking Strategy Selector - Intelligently selects chunking strategy

Different document types benefit from different chunking approaches:
- Markdown: Header-based semantic chunking
- PDF: Fixed-size with custom separators
- Code: Code-aware splitting
- Academic papers: Section-based chunking
"""

from typing import List, Dict, Optional
from dataclasses import dataclass
from enum import Enum
from langchain_text_splitters import (
    RecursiveCharacterTextSplitter,
    MarkdownHeaderTextSplitter,
    CharacterTextSplitter
)
from langchain.schema import Document


class ChunkingMethod(Enum):
    """Available chunking methods"""
    RECURSIVE = "recursive"
    MARKDOWN_HEADERS = "markdown_headers"
    FIXED_SIZE = "fixed_size"
    SEMANTIC = "semantic"
    HYBRID = "hybrid"
    CODE_AWARE = "code_aware"


@dataclass
class ChunkingConfig:
    """Configuration for chunking"""
    method: ChunkingMethod
    chunk_size: int
    chunk_overlap: int
    min_chunk_size: int = 100  # Minimum chunk size to keep
    separators: Optional[List[str]] = None
    headers_to_split_on: Optional[List[tuple]] = None
    metadata: Dict = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


class ChunkingStrategy:
    """Selects and applies appropriate chunking strategy"""

    # Default configurations for different document types
    DEFAULT_CONFIGS = {
        'markdown': ChunkingConfig(
            method=ChunkingMethod.MARKDOWN_HEADERS,
            chunk_size=1500,
            chunk_overlap=300,
            min_chunk_size=100,
            headers_to_split_on=[
                ("#", "h1"),
                ("##", "h2"),
                ("###", "h3"),
            ]
        ),
        'pdf': ChunkingConfig(
            method=ChunkingMethod.RECURSIVE,
            chunk_size=1200,
            chunk_overlap=200,
            min_chunk_size=150,
            separators=["\n\n", "\n", ". ", " ", ""]
        ),
        'plain_text': ChunkingConfig(
            method=ChunkingMethod.RECURSIVE,
            chunk_size=1000,
            chunk_overlap=200,
            min_chunk_size=100,
        ),
        'academic_paper': ChunkingConfig(
            method=ChunkingMethod.HYBRID,
            chunk_size=1500,
            chunk_overlap=300,
            min_chunk_size=200,
            headers_to_split_on=[
                ("Abstract", "section"),
                ("Introduction", "section"),
                ("Methods", "section"),
                ("Results", "section"),
                ("Discussion", "section"),
                ("Conclusion", "section"),
                ("References", "section"),
            ]
        ),
        'code': ChunkingConfig(
            method=ChunkingMethod.CODE_AWARE,
            chunk_size=1500,
            chunk_overlap=200,
            min_chunk_size=50,  # Code can have smaller meaningful chunks
        )
    }

    # Language-specific separators for code-aware chunking
    CODE_SEPARATORS = {
        'python': [
            "\n\nclass ",      # Class definitions
            "\n\ndef ",        # Function definitions
            "\n\nasync def ",  # Async functions
            "\n\n@",           # Decorators
            "\n\n",            # Double newlines
            "\n",              # Single newlines
            " ",
            ""
        ],
        'javascript': [
            "\n\nclass ",
            "\n\nfunction ",
            "\n\nexport ",
            "\n\nconst ",
            "\n\nlet ",
            "\n\nvar ",
            "\n\n",
            "\n",
            " ",
            ""
        ],
        'typescript': [
            "\n\nclass ",
            "\n\ninterface ",
            "\n\ntype ",
            "\n\nfunction ",
            "\n\nexport ",
            "\n\nconst ",
            "\n\n",
            "\n",
            " ",
            ""
        ],
        'java': [
            "\n\npublic class ",
            "\n\nprivate class ",
            "\n\nclass ",
            "\n\npublic ",
            "\n\nprivate ",
            "\n\nprotected ",
            "\n\n",
            "\n",
            " ",
            ""
        ],
        'golang': [
            "\n\nfunc ",
            "\n\ntype ",
            "\n\nvar ",
            "\n\nconst ",
            "\n\n",
            "\n",
            " ",
            ""
        ],
        'rust': [
            "\n\npub fn ",
            "\n\nfn ",
            "\n\npub struct ",
            "\n\nstruct ",
            "\n\nimpl ",
            "\n\npub enum ",
            "\n\nenum ",
            "\n\n",
            "\n",
            " ",
            ""
        ],
        'default': [
            "\n\n",
            "\n",
            " ",
            ""
        ]
    }

    def __init__(self):
        self.stats = {
            'total_documents': 0,
            'total_chunks': 0,
            'chunks_by_method': {},
            'filtered_small_chunks': 0,
        }

    def select_config(self,
                     structure_type: str,
                     file_size: int,
                     language: str = 'english',
                     has_complex_structure: bool = False,
                     programming_language: str = None) -> ChunkingConfig:
        """Select appropriate chunking configuration"""

        # Start with base config for structure type
        if structure_type in self.DEFAULT_CONFIGS:
            config = self.DEFAULT_CONFIGS[structure_type]
        else:
            config = self.DEFAULT_CONFIGS['plain_text']

        # Handle code files with language-specific separators
        if structure_type == 'code' and programming_language:
            separators = self.CODE_SEPARATORS.get(
                programming_language,
                self.CODE_SEPARATORS['default']
            )
            config = ChunkingConfig(
                method=ChunkingMethod.CODE_AWARE,
                chunk_size=config.chunk_size,
                chunk_overlap=config.chunk_overlap,
                min_chunk_size=config.min_chunk_size,
                separators=separators,
                metadata={'programming_language': programming_language}
            )

        # Adjust for Japanese content (typically needs larger chunks)
        if language in ('japanese', 'mixed'):
            config = ChunkingConfig(
                method=config.method,
                chunk_size=int(config.chunk_size * 1.2),  # 20% larger for Japanese
                chunk_overlap=config.chunk_overlap,
                min_chunk_size=config.min_chunk_size,
                separators=config.separators,
                headers_to_split_on=config.headers_to_split_on,
            )

        # Adjust for very large files
        if file_size > 1024 * 1024:  # > 1MB
            config = ChunkingConfig(
                method=config.method,
                chunk_size=min(2000, int(config.chunk_size * 1.3)),
                chunk_overlap=config.chunk_overlap,
                min_chunk_size=config.min_chunk_size,
                separators=config.separators,
                headers_to_split_on=config.headers_to_split_on,
                metadata={'large_file': True}
            )

        # Use simpler strategy for simple documents
        if structure_type == 'plain_text' or not has_complex_structure:
            if config.method == ChunkingMethod.MARKDOWN_HEADERS:
                config = ChunkingConfig(
                    method=ChunkingMethod.RECURSIVE,
                    chunk_size=config.chunk_size,
                    chunk_overlap=config.chunk_overlap,
                    min_chunk_size=config.min_chunk_size,
                )

        return config

    def chunk_documents(self,
                       documents: List[Document],
                       config: ChunkingConfig,
                       source: str = "") -> List[Document]:
        """Apply chunking strategy to documents"""

        if not documents:
            return []

        self.stats['total_documents'] += len(documents)

        # Select and create text splitter based on method
        if config.method == ChunkingMethod.MARKDOWN_HEADERS:
            chunks = self._chunk_with_markdown_headers(documents, config)
        elif config.method == ChunkingMethod.HYBRID:
            chunks = self._chunk_hybrid(documents, config)
        elif config.method == ChunkingMethod.CODE_AWARE:
            chunks = self._chunk_code_aware(documents, config)
        else:
            # Use recursive for most cases
            text_splitter = RecursiveCharacterTextSplitter(
                chunk_size=config.chunk_size,
                chunk_overlap=config.chunk_overlap,
                separators=config.separators if config.separators else ["\n\n", "\n", " ", ""],
                length_function=len,
            )
            chunks = text_splitter.split_documents(documents)

        # Filter out very small chunks
        original_count = len(chunks)
        chunks = [
            chunk for chunk in chunks
            if len(chunk.page_content) >= config.min_chunk_size
        ]
        filtered = original_count - len(chunks)

        if filtered > 0:
            self.stats['filtered_small_chunks'] += filtered

        # Update statistics
        self.stats['total_chunks'] += len(chunks)
        method_name = config.method.value
        self.stats['chunks_by_method'][method_name] = \
            self.stats['chunks_by_method'].get(method_name, 0) + len(chunks)

        # Add metadata
        for chunk in chunks:
            chunk.metadata.update({
                'chunking_method': config.method.value,
                'chunk_size_config': config.chunk_size,
                'source': source
            })

        return chunks

    def _chunk_with_markdown_headers(self,
                                    documents: List[Document],
                                    config: ChunkingConfig) -> List[Document]:
        """Chunk using markdown headers then recursively split large chunks"""

        if not config.headers_to_split_on:
            # Fall back to recursive
            return self._chunk_recursive(documents, config)

        # First, split by headers
        markdown_splitter = MarkdownHeaderTextSplitter(
            headers_to_split_on=config.headers_to_split_on
        )

        header_chunks = []
        for doc in documents:
            try:
                splits = markdown_splitter.split_text(doc.page_content)
                # Preserve original metadata
                for split in splits:
                    split.metadata.update(doc.metadata)
                header_chunks.extend(splits)
            except Exception:
                # If header splitting fails, add original document
                header_chunks.append(doc)

        # Then recursively split large chunks
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=config.chunk_size,
            chunk_overlap=config.chunk_overlap,
            length_function=len,
        )

        final_chunks = []
        for chunk in header_chunks:
            if len(chunk.page_content) > config.chunk_size:
                # Split large chunks further
                splits = text_splitter.split_documents([chunk])
                final_chunks.extend(splits)
            else:
                final_chunks.append(chunk)

        return final_chunks

    def _chunk_hybrid(self,
                     documents: List[Document],
                     config: ChunkingConfig) -> List[Document]:
        """Hybrid approach: try header splitting, fall back to recursive"""

        try:
            return self._chunk_with_markdown_headers(documents, config)
        except Exception:
            return self._chunk_recursive(documents, config)

    def _chunk_code_aware(self,
                         documents: List[Document],
                         config: ChunkingConfig) -> List[Document]:
        """Code-aware chunking that respects code structure"""

        # Use language-specific separators or defaults
        separators = config.separators if config.separators else self.CODE_SEPARATORS['default']

        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=config.chunk_size,
            chunk_overlap=config.chunk_overlap,
            separators=separators,
            length_function=len,
            keep_separator=True,  # Keep the separator at the start of chunks
        )

        chunks = text_splitter.split_documents(documents)

        # Add programming language to metadata if available
        if config.metadata and 'programming_language' in config.metadata:
            for chunk in chunks:
                chunk.metadata['programming_language'] = config.metadata['programming_language']

        return chunks

    def _chunk_recursive(self,
                        documents: List[Document],
                        config: ChunkingConfig) -> List[Document]:
        """Standard recursive chunking"""

        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=config.chunk_size,
            chunk_overlap=config.chunk_overlap,
            length_function=len,
        )

        return text_splitter.split_documents(documents)

    def get_stats(self) -> Dict:
        """Get chunking statistics"""
        return self.stats.copy()

    def print_stats(self):
        """Print chunking statistics"""
        print("\n" + "="*80)
        print("CHUNKING STATISTICS")
        print("="*80)

        print(f"\nDocuments processed: {self.stats['total_documents']}")
        print(f"Total chunks created: {self.stats['total_chunks']}")
        print(f"Small chunks filtered: {self.stats['filtered_small_chunks']}")

        if self.stats['chunks_by_method']:
            print(f"\nChunks by method:")
            for method, count in self.stats['chunks_by_method'].items():
                percentage = (count / self.stats['total_chunks'] * 100) if self.stats['total_chunks'] > 0 else 0
                print(f"  {method}: {count} ({percentage:.1f}%)")

        avg_chunks = self.stats['total_chunks'] / self.stats['total_documents'] if self.stats['total_documents'] > 0 else 0
        print(f"\nAverage chunks per document: {avg_chunks:.1f}")

        print("="*80)


def select_chunking_strategy(
    structure_type: str,
    file_size: int,
    language: str = 'english',
    has_complex_structure: bool = False,
    programming_language: str = None
) -> ChunkingConfig:
    """
    Convenience function to select chunking configuration

    Args:
        structure_type: Type of document ('markdown', 'pdf', 'plain_text', 'code')
        file_size: Size of file in bytes
        language: Detected language ('english', 'japanese', 'mixed')
        has_complex_structure: Whether document has complex structure
        programming_language: Programming language for code files ('python', 'javascript', etc.)

    Returns:
        ChunkingConfig with recommended settings
    """
    strategy = ChunkingStrategy()
    return strategy.select_config(
        structure_type=structure_type,
        file_size=file_size,
        language=language,
        has_complex_structure=has_complex_structure,
        programming_language=programming_language
    )


# Example usage configurations
EXAMPLE_CONFIGS = {
    'simple_markdown': {
        'description': 'Simple markdown files without complex headers',
        'config': ChunkingConfig(
            method=ChunkingMethod.RECURSIVE,
            chunk_size=1000,
            chunk_overlap=200,
            min_chunk_size=100,
        )
    },
    'academic_paper_pdf': {
        'description': 'Academic papers in PDF format',
        'config': ChunkingConfig(
            method=ChunkingMethod.RECURSIVE,
            chunk_size=1500,
            chunk_overlap=300,
            min_chunk_size=200,
            separators=["\n\n", "\n", ". ", " ", ""]
        )
    },
    'structured_markdown': {
        'description': 'Markdown with clear section headers',
        'config': ChunkingConfig(
            method=ChunkingMethod.MARKDOWN_HEADERS,
            chunk_size=1500,
            chunk_overlap=300,
            min_chunk_size=150,
            headers_to_split_on=[("#", "h1"), ("##", "h2"), ("###", "h3")]
        )
    },
    'mixed_language': {
        'description': 'Documents with English and Japanese',
        'config': ChunkingConfig(
            method=ChunkingMethod.RECURSIVE,
            chunk_size=1200,
            chunk_overlap=250,
            min_chunk_size=120,
        )
    }
}
