#!/usr/bin/env python3
"""
Unified test runner for BookTranslator/Polytext
Runs comprehensive tests with multiple options
"""
import sys
import os
import argparse
import asyncio
from pathlib import Path

# Add API to path
root_dir = Path(__file__).parent
sys.path.insert(0, str(root_dir / "apps" / "api"))
os.chdir(root_dir)

def check_dependencies():
    """Check if all required dependencies are available."""
    print("🔍 Checking dependencies...")
    
    issues = []
    
    # Check API dependencies
    try:
        from app.config import settings
        print("   ✅ API configuration loaded")
    except Exception as e:
        issues.append(f"API config: {e}")
    
    # Check PDF converter
    try:
        from epub_to_pdf_with_images import convert_epub_to_pdf
        print("   ✅ Enhanced PDF converter available")
    except Exception as e:
        issues.append(f"PDF converter: {e}")
    
    # Check providers
    try:
        from app.providers.gemini import GeminiFlashProvider
        from app.providers.groq import GroqLlamaProvider
        print("   ✅ AI providers available")
    except Exception as e:
        issues.append(f"AI providers: {e}")
    
    # Check sample files
    sample_dir = root_dir / "sample_books"
    epub_files = list(sample_dir.glob("*.epub")) if sample_dir.exists() else []
    if epub_files:
        print(f"   ✅ Found {len(epub_files)} EPUB files for testing")
    else:
        issues.append("No EPUB test files found in sample_books/")
    
    if issues:
        print("\n⚠️  Issues found:")
        for issue in issues:
            print(f"   - {issue}")
        return False
    
    print("   ✅ All dependencies OK!")
    return True

async def run_dual_provider_test():
    """Run the comprehensive dual provider test."""
    print("\n🚀 Running Dual Provider Test...")
    
    # Import and run the test
    sys.path.insert(0, str(root_dir / "tests"))
    from test_dual_provider_complete import main as dual_test_main
    
    await dual_test_main()

async def run_pdf_test():
    """Run comprehensive PDF generation test."""
    print("\n🚀 Running PDF Generation Test...")
    
    try:
        sys.path.insert(0, str(root_dir / "tests"))
        from test_pdf_generation import main as pdf_test_main
        await pdf_test_main()
    except Exception as e:
        print(f"❌ PDF test failed: {e}")

def show_test_results():
    """Show available test results."""
    print("\n📊 Available Test Results:")
    
    output_dir = root_dir / "test_outputs"
    if not output_dir.exists():
        print("   No test results found. Run tests first.")
        return
    
    # Show provider outputs
    for provider in ["gemini", "groq"]:
        provider_dir = output_dir / provider
        if provider_dir.exists():
            files = list(provider_dir.glob("*"))
            print(f"\n   {provider.upper()} outputs ({len(files)} files):")
            for file in sorted(files):
                size = file.stat().st_size / 1024  # KB
                print(f"     - {file.name} ({size:.1f} KB)")
    
    # Show comparison results
    result_files = list(output_dir.glob("comparison_results_*.json"))
    if result_files:
        print(f"\n   Comparison Results ({len(result_files)} files):")
        for file in sorted(result_files, reverse=True):
            print(f"     - {file.name}")

def main():
    parser = argparse.ArgumentParser(description="BookTranslator Test Runner")
    parser.add_argument("--check", action="store_true", help="Check dependencies only")
    parser.add_argument("--dual", action="store_true", help="Run dual provider test")
    parser.add_argument("--pdf", action="store_true", help="Run PDF generation test")
    parser.add_argument("--results", action="store_true", help="Show test results")
    parser.add_argument("--all", action="store_true", help="Run all tests")
    
    args = parser.parse_args()
    
    print("📚 BookTranslator/Polytext Test Runner")
    print("=" * 50)
    
    # Always check dependencies first
    if not check_dependencies():
        print("\n❌ Dependency check failed. Please fix issues before running tests.")
        return
    
    if args.check:
        print("\n✅ Dependency check completed successfully!")
        return
    
    if args.results:
        show_test_results()
        return
    
    # Run tests
    async def run_tests():
        if args.dual or args.all:
            await run_dual_provider_test()
        
        if args.pdf or args.all:
            await run_pdf_test()
    
    if args.dual or args.pdf or args.all:
        asyncio.run(run_tests())
        print("\n✅ Test run completed!")
        show_test_results()
    else:
        parser.print_help()

if __name__ == "__main__":
    main()