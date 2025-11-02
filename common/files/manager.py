"""
File and directory management utilities
"""

import os
import shutil
import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


class FileManager:
    """Handles file and directory operations for the translation pipeline."""
    
    def __init__(self):
        pass
    
    def ensure_output_directory(
        self, 
        base_dir: Path,
        subdirs: List[str]
    ) -> Dict[str, Path]:
        """
        Create and return output directory structure.
        
        Args:
            base_dir: Base directory path
            subdirs: List of subdirectory names to create
            
        Returns:
            Dictionary mapping subdir names to their paths
        """
        
        directory_paths = {}
        
        # Ensure base directory exists
        base_dir.mkdir(parents=True, exist_ok=True)
        
        # Create subdirectories
        for subdir in subdirs:
            subdir_path = base_dir / subdir
            subdir_path.mkdir(parents=True, exist_ok=True)
            directory_paths[subdir] = subdir_path
            logger.debug(f"Created directory: {subdir_path}")
        
        return directory_paths
    
    def get_file_size_formatted(self, path: Path) -> str:
        """
        Get formatted file size (KB, MB, etc).
        
        Args:
            path: Path to file
            
        Returns:
            Formatted size string
        """
        
        if not path.exists():
            return "File not found"
        
        try:
            size_bytes = path.stat().st_size
            
            # Determine appropriate unit
            if size_bytes >= 1024 * 1024:  # MB
                size = size_bytes / (1024 * 1024)
                unit = "MB"
            elif size_bytes >= 1024:  # KB
                size = size_bytes / 1024
                unit = "KB"
            else:  # Bytes
                size = size_bytes
                unit = "B"
            
            return f"{size:.1f} {unit}"
            
        except Exception as e:
            logger.error(f"Error getting file size for {path}: {e}")
            return "Size unknown"
    
    def copy_with_metadata_preservation(
        self,
        source: Path,
        destination: Path,
        preserve_timestamps: bool = True
    ) -> bool:
        """
        Copy files preserving metadata.
        
        Args:
            source: Source file path
            destination: Destination file path
            preserve_timestamps: Whether to preserve file timestamps
            
        Returns:
            True if copy successful, False otherwise
        """
        
        try:
            # Ensure destination directory exists
            destination.parent.mkdir(parents=True, exist_ok=True)
            
            # Copy file
            if preserve_timestamps:
                shutil.copy2(source, destination)  # Preserves metadata
            else:
                shutil.copy(source, destination)   # Just copies content
            
            logger.debug(f"Copied {source} to {destination}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to copy {source} to {destination}: {e}")
            return False
    
    def cleanup_temp_files(
        self,
        directory: Path,
        patterns: List[str] = None
    ) -> int:
        """
        Clean up temporary files in directory.
        
        Args:
            directory: Directory to clean
            patterns: List of glob patterns to match (default: common temp patterns)
            
        Returns:
            Number of files cleaned up
        """
        
        if patterns is None:
            patterns = [
                "*.tmp",
                "*.temp",
                "*~",
                ".DS_Store",
                "Thumbs.db"
            ]
        
        cleaned_count = 0
        
        try:
            for pattern in patterns:
                for file_path in directory.glob(pattern):
                    if file_path.is_file():
                        file_path.unlink()
                        cleaned_count += 1
                        logger.debug(f"Cleaned up temp file: {file_path}")
            
            logger.info(f"Cleaned up {cleaned_count} temporary files from {directory}")
            return cleaned_count
            
        except Exception as e:
            logger.error(f"Error during cleanup in {directory}: {e}")
            return cleaned_count
    
    def get_directory_summary(self, directory: Path) -> Dict[str, any]:
        """
        Get summary information about a directory.
        
        Args:
            directory: Directory to analyze
            
        Returns:
            Dictionary with directory summary information
        """
        
        summary = {
            "path": str(directory),
            "exists": directory.exists(),
            "is_directory": directory.is_dir() if directory.exists() else False,
            "file_count": 0,
            "total_size": 0,
            "files": {}
        }
        
        if not summary["exists"] or not summary["is_directory"]:
            return summary
        
        try:
            for file_path in directory.iterdir():
                if file_path.is_file():
                    file_size = file_path.stat().st_size
                    summary["file_count"] += 1
                    summary["total_size"] += file_size
                    summary["files"][file_path.name] = {
                        "size_bytes": file_size,
                        "size_formatted": self.get_file_size_formatted(file_path)
                    }
            
            summary["total_size_formatted"] = self.get_file_size_formatted(
                Path("/tmp/dummy")  # Dummy path, we'll override the size
            )
            
            # Calculate total size manually for formatting
            if summary["total_size"] >= 1024 * 1024:
                summary["total_size_formatted"] = f"{summary['total_size'] / (1024 * 1024):.1f} MB"
            elif summary["total_size"] >= 1024:
                summary["total_size_formatted"] = f"{summary['total_size'] / 1024:.1f} KB"
            else:
                summary["total_size_formatted"] = f"{summary['total_size']} B"
            
        except Exception as e:
            logger.error(f"Error analyzing directory {directory}: {e}")
            summary["error"] = str(e)
        
        return summary
    
    def generate_original_formats(
        self,
        source_epub: Path,
        output_dir: Path,
        pdf_converter_func = None,
        txt_generator_func = None
    ) -> Dict[str, Optional[Path]]:
        """
        Generate original formats (PDF, TXT) from source EPUB for comparison.
        
        Args:
            source_epub: Path to source EPUB file
            output_dir: Output directory for generated files
            pdf_converter_func: Function to convert EPUB to PDF
            txt_generator_func: Function to convert EPUB to TXT
            
        Returns:
            Dictionary mapping format names to generated file paths
        """
        
        results = {
            "epub": None,
            "pdf": None,
            "txt": None
        }
        
        # Ensure output directory exists
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Copy original EPUB
        try:
            original_epub = output_dir / "original.epub"
            if self.copy_with_metadata_preservation(source_epub, original_epub):
                results["epub"] = original_epub
                logger.info(f"✅ EPUB: {original_epub} ({self.get_file_size_formatted(original_epub)})")
        except Exception as e:
            logger.error(f"Failed to copy original EPUB: {e}")
        
        # Generate PDF if converter available
        if pdf_converter_func and results["epub"]:
            try:
                logger.info("🔄 Converting original EPUB to PDF...")
                pdf_path = pdf_converter_func(str(results["epub"]), str(output_dir))
                
                if pdf_path and Path(pdf_path).exists():
                    results["pdf"] = Path(pdf_path)
                    logger.info(f"✅ PDF: {pdf_path} ({self.get_file_size_formatted(Path(pdf_path))})")
                else:
                    logger.error("❌ PDF generation failed - no output file")
                    
            except Exception as e:
                logger.error(f"❌ PDF generation failed: {e}")
        
        # Generate TXT if generator available
        if txt_generator_func and results["epub"]:
            try:
                logger.info("🔄 Converting original EPUB to TXT...")
                txt_path = output_dir / "original.txt"
                
                # This would need to be implemented based on the txt_generator_func interface
                txt_content = txt_generator_func(results["epub"])
                
                if txt_content:
                    with open(txt_path, 'w', encoding='utf-8') as f:
                        f.write(txt_content)
                    
                    results["txt"] = txt_path
                    logger.info(f"✅ TXT: {txt_path} ({self.get_file_size_formatted(txt_path)})")
                    
            except Exception as e:
                logger.error(f"❌ TXT generation failed: {e}")
        
        # Log summary
        logger.info(f"\n📁 Original formats ready in: {output_dir}")
        
        return results
    
    def list_directory_contents(
        self,
        directory: Path,
        include_sizes: bool = True
    ) -> List[Dict[str, any]]:
        """
        List directory contents with optional size information.
        
        Args:
            directory: Directory to list
            include_sizes: Whether to include file size information
            
        Returns:
            List of file information dictionaries
        """
        
        contents = []
        
        if not directory.exists() or not directory.is_dir():
            return contents
        
        try:
            for item in directory.iterdir():
                item_info = {
                    "name": item.name,
                    "path": str(item),
                    "is_file": item.is_file(),
                    "is_directory": item.is_dir()
                }
                
                if include_sizes and item.is_file():
                    item_info["size_bytes"] = item.stat().st_size
                    item_info["size_formatted"] = self.get_file_size_formatted(item)
                
                contents.append(item_info)
            
            # Sort by name
            contents.sort(key=lambda x: x["name"])
            
        except Exception as e:
            logger.error(f"Error listing directory contents for {directory}: {e}")
        
        return contents