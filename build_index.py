"""
Build script to pre-generate the index locally for faster Streamlit Cloud deployment.
Run this script before deploying to Streamlit Cloud.

Usage:
    python build_index.py
    python build_index.py --verbose  # Show detailed filtering stats
"""
import sys
from pathlib import Path
import pickle
import logging
import argparse
import time

# Add parent directory to path
sys.path.append(str(Path(__file__).parent))

from app import ingest

def build_and_save_index(verbose=False):
    """
    Build index from Microsoft AI Agents for Beginners repository
    and save it to the data directory for deployment
    
    Args:
        verbose (bool): If True, show detailed debug logs
    """
    # Set logging level based on verbose flag
    if verbose:
        logging.basicConfig(
            level=logging.DEBUG,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
    else:
        logging.basicConfig(
            level=logging.INFO,
            format='%(levelname)s - %(message)s'
        )
    
    logger = logging.getLogger(__name__)
    
    repo_owner = "microsoft"
    repo_name = "ai-agents-for-beginners"
    
    print("=" * 70)
    print("🔄 Building index from GitHub repository...")
    print(f"   Repository: {repo_owner}/{repo_name}")
    print(f"   Filters: English-only markdown files (.md, .mdx)")
    if verbose:
        print(f"   Verbose mode: ON")
    print("=" * 70)
    
    # Start timer
    start_time = time.time()
    
    try:
        # Build the index
        print("\n⏳ Step 1/5: Downloading repository...")
        step_start = time.time()
        
        index = ingest.index_data(
            repo_owner, 
            repo_name,
            filter=None,
            chunk=True,
            chunking_params={'size': 2000, 'step': 1000},
            use_cache=False  # Force fresh build
        )
        
        build_time = time.time() - step_start
        print(f"✅ Index built in {build_time:.1f} seconds")
        
        # Create data directory if it doesn't exist
        print("\n⏳ Step 2/5: Preparing data directory...")
        data_dir = Path(__file__).parent / "data"
        data_dir.mkdir(exist_ok=True)
        
        # Save the index
        cache_file = data_dir / "ms_ai_agents_index.pkl"
        
        print(f"\n⏳ Step 3/5: Serializing index to {cache_file}...")
        save_start = time.time()
        
        with open(cache_file, 'wb') as f:
            pickle.dump(index, f)
        
        save_time = time.time() - save_start
        print(f"✅ Saved in {save_time:.1f} seconds")
        
        # Get file size
        file_size_mb = cache_file.stat().st_size / (1024 * 1024)
        
        # Calculate total elapsed time
        elapsed_time = time.time() - start_time
        
        print("\n" + "=" * 70)
        print("✅ Index built and saved successfully!")
        print(f"   File: {cache_file}")
        print(f"   Size: {file_size_mb:.2f} MB")
        print(f"   Language: English only")
        print(f"   File types: .md, .mdx")
        print(f"   ⏱️  Total build time: {elapsed_time:.1f} seconds")
        print("=" * 70)
        
        # Check GitHub file size limits
        print("\n⏳ Step 4/5: Checking file size limits...")
        if file_size_mb > 100:
            print("\n⚠️  WARNING: File size exceeds GitHub's 100MB limit!")
            print("   Consider using Git LFS or Azure Blob Storage")
            print("   See: https://git-lfs.github.com/")
        elif file_size_mb > 50:
            print("\n⚠️  File is large (>50MB). Consider:")
            print("   1. Using Git LFS for better performance")
            print("   2. Adding to .gitattributes for LFS tracking")
            print("   3. Or use Azure Blob Storage for cloud caching")
        else:
            print("\n✅ File size is within GitHub limits")
        
        print("\n⏳ Step 5/5: Next steps...")
        print("\n📋 Deployment steps:")
        print("   1. Commit the generated file:")
        print("      git add data/ms_ai_agents_index.pkl")
        print("      git commit -m 'Add pre-built index for instant loading'")
        print("   2. Push to GitHub:")
        print("      git push")
        print("   3. Deploy to Streamlit Cloud")
        print("   4. Enjoy instant loading! ⚡ (1-2 seconds vs 60-90 seconds)")
        
        # Performance summary
        print("\n📊 Performance Summary:")
        print(f"   Build time: {build_time:.1f}s")
        print(f"   Save time: {save_time:.1f}s")
        print(f"   Total time: {elapsed_time:.1f}s")
        print(f"   Expected Streamlit load time: 1-2 seconds")
        
        return True
        
    except Exception as e:
        elapsed_time = time.time() - start_time
        logger.error(f"❌ Failed to build index after {elapsed_time:.1f}s: {e}", exc_info=True)
        print(f"\n❌ Error: {e}")
        print(f"   Time elapsed before error: {elapsed_time:.1f} seconds")
        return False

def main():
    """Main entry point with argument parsing"""
    parser = argparse.ArgumentParser(
        description="Build search index for AI Hero Streamlit app",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python build_index.py              # Normal build with progress info
  python build_index.py --verbose    # Detailed debug logs
  python build_index.py -v           # Short form of verbose

This script caches the GitHub repository index locally to avoid
60-90 second download/processing times on every Streamlit Cloud restart.
        """
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Show detailed debug logs including file filtering"
    )
    
    args = parser.parse_args()
    
    print("\n🚀 AI Hero Index Builder")
    print("=" * 70)
    
    success = build_and_save_index(verbose=args.verbose)
    
    if success:
        print("\n" + "=" * 70)
        print("🎉 Success! Index is ready for deployment.")
        print("=" * 70)
        sys.exit(0)
    else:
        print("\n" + "=" * 70)
        print("❌ Build failed. Check the error messages above.")
        print("=" * 70)
        sys.exit(1)

if __name__ == "__main__":
    main()