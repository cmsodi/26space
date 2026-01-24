#!/usr/bin/env python3
"""
Output Converter - Converts Markdown to docx/pptx/pdf via pandoc
For use with Claude Code (local execution)

Requirements:
    - pandoc installed (https://pandoc.org/installing.html)
    - For PDF: pdflatex or xelatex

Usage:
    python convert_output.py input.md --format docx
    python convert_output.py input.md --format pptx
    python convert_output.py input.md --format pdf
    python convert_output.py input.md --format all
"""

import subprocess
import sys
import shutil
from pathlib import Path


def check_pandoc():
    """Verify pandoc is installed."""
    if not shutil.which('pandoc'):
        print("ERROR: pandoc not found.")
        print("Install it:")
        print("  macOS:   brew install pandoc")
        print("  Ubuntu:  sudo apt install pandoc")
        print("  Windows: choco install pandoc")
        sys.exit(1)
    return True


def convert_to_docx(input_path: Path, output_path: Path = None):
    """Convert Markdown to Word docx."""
    if output_path is None:
        output_path = input_path.with_suffix('.docx')
    
    cmd = [
        'pandoc',
        str(input_path),
        '-o', str(output_path),
        '--from', 'markdown',
        '--to', 'docx',
        '--toc',                    # Table of contents
        '--toc-depth=3',
        '--highlight-style=tango',
    ]
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    if result.returncode == 0:
        print(f"✓ Created: {output_path}")
        return output_path
    else:
        print(f"✗ Error: {result.stderr}")
        return None


def convert_to_pptx(input_path: Path, output_path: Path = None):
    """
    Convert Markdown to PowerPoint pptx.
    
    Note: Pandoc creates slides from headers:
    - # H1 → Title slide
    - ## H2 → New slide with title
    - ### H3 → Bullet point
    """
    if output_path is None:
        output_path = input_path.with_suffix('.pptx')
    
    cmd = [
        'pandoc',
        str(input_path),
        '-o', str(output_path),
        '--from', 'markdown',
        '--to', 'pptx',
        '--slide-level=2',          # ## creates new slides
    ]
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    if result.returncode == 0:
        print(f"✓ Created: {output_path}")
        return output_path
    else:
        print(f"✗ Error: {result.stderr}")
        return None


def convert_to_pdf(input_path: Path, output_path: Path = None):
    """Convert Markdown to PDF (requires LaTeX)."""
    if output_path is None:
        output_path = input_path.with_suffix('.pdf')
    
    # Check for LaTeX
    if not shutil.which('pdflatex') and not shutil.which('xelatex'):
        print("WARNING: LaTeX not found. Trying with wkhtmltopdf...")
        cmd = [
            'pandoc',
            str(input_path),
            '-o', str(output_path),
            '--from', 'markdown',
            '--to', 'html',
            '--pdf-engine=wkhtmltopdf',
        ]
    else:
        cmd = [
            'pandoc',
            str(input_path),
            '-o', str(output_path),
            '--from', 'markdown',
            '--pdf-engine=xelatex',
            '--toc',
            '--toc-depth=3',
            '-V', 'geometry:margin=1in',
            '-V', 'fontsize=11pt',
        ]
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    if result.returncode == 0:
        print(f"✓ Created: {output_path}")
        return output_path
    else:
        print(f"✗ Error: {result.stderr}")
        return None


def convert_to_html(input_path: Path, output_path: Path = None):
    """Convert Markdown to standalone HTML."""
    if output_path is None:
        output_path = input_path.with_suffix('.html')
    
    cmd = [
        'pandoc',
        str(input_path),
        '-o', str(output_path),
        '--from', 'markdown',
        '--to', 'html5',
        '--standalone',
        '--toc',
        '--toc-depth=3',
        '--metadata', f'title={input_path.stem}',
    ]
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    if result.returncode == 0:
        print(f"✓ Created: {output_path}")
        return output_path
    else:
        print(f"✗ Error: {result.stderr}")
        return None


def main():
    if len(sys.argv) < 2:
        print("Usage: python convert_output.py <input.md> [--format docx|pptx|pdf|html|all]")
        sys.exit(1)
    
    input_path = Path(sys.argv[1])
    
    if not input_path.exists():
        print(f"ERROR: File not found: {input_path}")
        sys.exit(1)
    
    # Parse format argument
    output_format = 'docx'  # default
    if '--format' in sys.argv:
        idx = sys.argv.index('--format')
        if idx + 1 < len(sys.argv):
            output_format = sys.argv[idx + 1].lower()
    
    # Check pandoc
    check_pandoc()
    
    print(f"Converting: {input_path}")
    print(f"Format: {output_format}")
    print("-" * 40)
    
    # Execute conversion
    if output_format == 'all':
        convert_to_docx(input_path)
        convert_to_pptx(input_path)
        convert_to_html(input_path)
        convert_to_pdf(input_path)
    elif output_format == 'docx':
        convert_to_docx(input_path)
    elif output_format == 'pptx':
        convert_to_pptx(input_path)
    elif output_format == 'pdf':
        convert_to_pdf(input_path)
    elif output_format == 'html':
        convert_to_html(input_path)
    else:
        print(f"Unknown format: {output_format}")
        print("Supported: docx, pptx, pdf, html, all")
        sys.exit(1)


if __name__ == "__main__":
    main()
