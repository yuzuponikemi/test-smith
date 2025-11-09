"""
Document Analyzer - Evaluates document quality and characteristics

Analyzes documents to determine:
- File type and format
- Content characteristics (length, language, structure)
- Quality issues (too small, corrupted, low content)
- Recommended processing strategy
"""

import os
import re
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from pathlib import Path
import hashlib


@dataclass
class DocumentAnalysis:
    """Results of document analysis"""
    filepath: str
    filename: str
    file_size: int
    file_type: str
    estimated_content_length: int
    language: str
    structure_type: str  # 'markdown', 'pdf', 'plain_text', 'structured'
    quality_score: float  # 0-1, higher is better
    issues: List[str]
    recommendations: List[str]
    metadata: Dict


class DocumentAnalyzer:
    """Analyzes documents before ingestion"""

    # Quality thresholds
    MIN_FILE_SIZE = 50  # bytes
    MIN_CONTENT_LENGTH = 100  # characters
    TINY_FILE_THRESHOLD = 200  # bytes

    # File type detection
    TEXT_EXTENSIONS = {'.txt', '.md', '.markdown'}
    PDF_EXTENSIONS = {'.pdf'}
    SUPPORTED_EXTENSIONS = TEXT_EXTENSIONS | PDF_EXTENSIONS

    def __init__(self):
        self.analyzed_documents: List[DocumentAnalysis] = []

    def analyze_file(self, filepath: str) -> DocumentAnalysis:
        """Analyze a single document file"""

        filename = os.path.basename(filepath)
        file_size = os.path.getsize(filepath)
        file_ext = Path(filepath).suffix.lower()

        issues = []
        recommendations = []
        quality_score = 1.0

        # Check file size
        if file_size < self.MIN_FILE_SIZE:
            issues.append(f"File too small ({file_size} bytes)")
            quality_score -= 0.5
            recommendations.append("Consider removing this file or combining with related content")

        if file_size < self.TINY_FILE_THRESHOLD:
            issues.append(f"Very small file ({file_size} bytes) - may create useless chunks")
            quality_score -= 0.3

        # Detect file type
        file_type = self._detect_file_type(filepath, file_ext)

        # Read and analyze content (for small files)
        content = ""
        if file_size < 10 * 1024 * 1024:  # < 10MB
            try:
                content = self._read_file_content(filepath, file_type)
            except Exception as e:
                issues.append(f"Failed to read file: {e}")
                quality_score -= 0.4

        # Analyze content characteristics
        estimated_length = len(content) if content else file_size  # Rough estimate for PDFs
        language = self._detect_language(content[:1000] if content else "")
        structure_type = self._detect_structure(content, file_ext)

        # Content quality checks
        if estimated_length < self.MIN_CONTENT_LENGTH:
            issues.append(f"Very little content ({estimated_length} chars)")
            quality_score -= 0.3
            recommendations.append("File may not provide useful semantic information")

        # Check for common issues
        if filename.startswith('.'):
            issues.append("Hidden file (starts with .)")
            recommendations.append("Consider excluding hidden files")

        if 'placeholder' in filename.lower() or 'test' in filename.lower():
            issues.append("Appears to be a placeholder or test file")
            quality_score -= 0.4
            recommendations.append("Remove placeholder files before production ingestion")

        # Detect potential encoding issues
        if content and self._has_encoding_issues(content):
            issues.append("Possible encoding/character issues detected")
            quality_score -= 0.2
            recommendations.append("Check file encoding (should be UTF-8)")

        # Structure-specific recommendations
        if structure_type == 'markdown':
            if self._has_complex_structure(content):
                recommendations.append("Use MarkdownHeaderTextSplitter for better semantic chunking")
            else:
                recommendations.append("Simple markdown - RecursiveCharacterTextSplitter is fine")

        elif structure_type == 'pdf':
            if file_size > 1024 * 1024:  # > 1MB
                recommendations.append("Large PDF - use batch processing to avoid memory issues")
            recommendations.append("PDFs may have headers/footers - consider custom cleaning")

        # Ensure quality score is in [0, 1]
        quality_score = max(0.0, min(1.0, quality_score))

        metadata = {
            'has_japanese': language == 'japanese' or 'mixed',
            'has_code_blocks': bool(re.search(r'```', content)) if content else False,
            'has_tables': bool(re.search(r'\|.*\|', content)) if content else False,
            'line_count': content.count('\n') if content else 0,
        }

        analysis = DocumentAnalysis(
            filepath=filepath,
            filename=filename,
            file_size=file_size,
            file_type=file_type,
            estimated_content_length=estimated_length,
            language=language,
            structure_type=structure_type,
            quality_score=quality_score,
            issues=issues,
            recommendations=recommendations,
            metadata=metadata
        )

        self.analyzed_documents.append(analysis)
        return analysis

    def analyze_directory(self, directory: str) -> List[DocumentAnalysis]:
        """Analyze all documents in a directory"""

        analyses = []

        if not os.path.exists(directory):
            raise ValueError(f"Directory not found: {directory}")

        for filename in sorted(os.listdir(directory)):
            filepath = os.path.join(directory, filename)

            if os.path.isfile(filepath):
                file_ext = Path(filepath).suffix.lower()

                # Skip unsupported files
                if file_ext not in self.SUPPORTED_EXTENSIONS:
                    continue

                analysis = self.analyze_file(filepath)
                analyses.append(analysis)

        return analyses

    def get_summary(self) -> Dict:
        """Get summary statistics of analyzed documents"""

        if not self.analyzed_documents:
            return {
                'total_files': 0,
                'message': 'No documents analyzed yet'
            }

        total = len(self.analyzed_documents)
        high_quality = sum(1 for d in self.analyzed_documents if d.quality_score >= 0.7)
        medium_quality = sum(1 for d in self.analyzed_documents if 0.4 <= d.quality_score < 0.7)
        low_quality = sum(1 for d in self.analyzed_documents if d.quality_score < 0.4)

        total_size = sum(d.file_size for d in self.analyzed_documents)
        total_content = sum(d.estimated_content_length for d in self.analyzed_documents)

        issues_by_type = {}
        for doc in self.analyzed_documents:
            for issue in doc.issues:
                issues_by_type[issue] = issues_by_type.get(issue, 0) + 1

        return {
            'total_files': total,
            'high_quality': high_quality,
            'medium_quality': medium_quality,
            'low_quality': low_quality,
            'total_size_bytes': total_size,
            'total_content_chars': total_content,
            'avg_quality_score': sum(d.quality_score for d in self.analyzed_documents) / total,
            'files_with_issues': sum(1 for d in self.analyzed_documents if d.issues),
            'common_issues': dict(sorted(issues_by_type.items(), key=lambda x: x[1], reverse=True)[:5]),
            'file_types': self._count_by_attribute('file_type'),
            'languages': self._count_by_attribute('language'),
            'structure_types': self._count_by_attribute('structure_type'),
        }

    def get_problematic_files(self, threshold: float = 0.5) -> List[DocumentAnalysis]:
        """Get files with quality score below threshold"""
        return [d for d in self.analyzed_documents if d.quality_score < threshold]

    def _detect_file_type(self, filepath: str, file_ext: str) -> str:
        """Detect file type"""
        if file_ext in self.PDF_EXTENSIONS:
            return 'pdf'
        elif file_ext in self.TEXT_EXTENSIONS:
            return 'text'
        else:
            return 'unknown'

    def _read_file_content(self, filepath: str, file_type: str) -> str:
        """Read file content based on type"""
        if file_type == 'pdf':
            # For PDF, just return empty - we'll analyze after UnstructuredLoader
            return ""
        else:
            # Text files
            with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                return f.read()

    def _detect_language(self, sample: str) -> str:
        """Detect primary language (simple heuristic)"""
        if not sample:
            return 'unknown'

        # Count Japanese characters (hiragana, katakana, kanji)
        japanese_chars = len(re.findall(r'[\u3040-\u309F\u30A0-\u30FF\u4E00-\u9FFF]', sample))
        total_chars = len(sample.strip())

        if total_chars == 0:
            return 'unknown'

        japanese_ratio = japanese_chars / total_chars

        if japanese_ratio > 0.3:
            return 'japanese' if japanese_ratio > 0.7 else 'mixed'
        else:
            return 'english'

    def _detect_structure(self, content: str, file_ext: str) -> str:
        """Detect document structure type"""
        if file_ext == '.pdf':
            return 'pdf'

        if not content:
            return 'unknown'

        # Check for markdown
        if file_ext in {'.md', '.markdown'}:
            return 'markdown'

        # Check for structured patterns
        if re.search(r'^#{1,6}\s', content, re.MULTILINE):
            return 'markdown'

        return 'plain_text'

    def _has_complex_structure(self, content: str) -> bool:
        """Check if markdown has complex structure (multiple header levels)"""
        if not content:
            return False

        headers = re.findall(r'^(#{1,6})\s', content, re.MULTILINE)
        unique_levels = set(len(h) for h in headers)

        return len(unique_levels) >= 2 and len(headers) >= 3

    def _has_encoding_issues(self, content: str) -> bool:
        """Detect potential encoding issues"""
        # Look for replacement characters or mojibake patterns
        suspicious_patterns = [
            '\ufffd',  # Replacement character
            '�',  # Question mark replacement
        ]

        return any(pattern in content for pattern in suspicious_patterns)

    def _count_by_attribute(self, attr: str) -> Dict[str, int]:
        """Count documents by a specific attribute"""
        counts = {}
        for doc in self.analyzed_documents:
            value = getattr(doc, attr)
            counts[value] = counts.get(value, 0) + 1
        return counts

    def print_report(self):
        """Print a detailed analysis report"""
        print("="*80)
        print("DOCUMENT ANALYSIS REPORT")
        print("="*80)

        summary = self.get_summary()

        print(f"\nTotal Files Analyzed: {summary['total_files']}")
        print(f"\nQuality Distribution:")
        print(f"  High Quality (≥0.7):   {summary['high_quality']} files")
        print(f"  Medium Quality (0.4-0.7): {summary['medium_quality']} files")
        print(f"  Low Quality (<0.4):    {summary['low_quality']} files")
        print(f"  Average Quality Score: {summary['avg_quality_score']:.2f}")

        print(f"\nContent Statistics:")
        print(f"  Total Size: {summary['total_size_bytes']:,} bytes ({summary['total_size_bytes']/1024/1024:.2f} MB)")
        print(f"  Estimated Content: {summary['total_content_chars']:,} characters")

        print(f"\nFile Types:")
        for ftype, count in summary['file_types'].items():
            print(f"  {ftype}: {count}")

        print(f"\nLanguages Detected:")
        for lang, count in summary['languages'].items():
            print(f"  {lang}: {count}")

        if summary['common_issues']:
            print(f"\nMost Common Issues:")
            for issue, count in summary['common_issues'].items():
                print(f"  {issue}: {count} files")

        # Show problematic files
        problematic = self.get_problematic_files(threshold=0.5)
        if problematic:
            print(f"\n⚠️  Files Needing Attention ({len(problematic)}):")
            for doc in problematic:
                print(f"\n  {doc.filename} (Quality: {doc.quality_score:.2f})")
                for issue in doc.issues:
                    print(f"    ❌ {issue}")
                if doc.recommendations:
                    print(f"    💡 Recommendations:")
                    for rec in doc.recommendations:
                        print(f"       - {rec}")

        print("\n" + "="*80)
