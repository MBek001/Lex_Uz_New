#!/usr/bin/env python3
"""
Test script for uploading documents to the API.
"""
import requests
import sys
import os
from pathlib import Path


def test_upload(file_path: str, language: str = "russian"):
    """
    Test document upload.

    Args:
        file_path: Path to ZIP file
        language: 'russian' or 'uzbek'
    """
    if not os.path.exists(file_path):
        print(f"❌ File not found: {file_path}")
        return False

    url = f"http://localhost:8000/api/upload/{language}"

    print(f"📤 Uploading {file_path} to {url}...")
    print(f"   File size: {os.path.getsize(file_path) / 1024 / 1024:.2f} MB")

    try:
        with open(file_path, 'rb') as f:
            files = {'file': (Path(file_path).name, f, 'application/zip')}
            response = requests.post(url, files=files, timeout=3600)

        if response.status_code == 200:
            result = response.json()
            print("\n✅ Upload successful!")
            print(f"   Status: {result.get('status')}")
            print(f"   Filename: {result.get('filename')}")

            processing = result.get('processing', {})
            print(f"\n📊 Processing Stats:")
            print(f"   Processed: {processing.get('processed', 0)}")
            print(f"   Errors: {processing.get('errors', 0)}")

            database = result.get('database', {})
            print(f"\n💾 Database Stats:")
            print(f"   Total: {database.get('total', 0)}")
            print(f"   Inserted: {database.get('inserted', 0)}")
            print(f"   Errors: {database.get('errors', 0)}")
            print(f"   Total in DB: {result.get('total_records_in_db', 0)}")

            return True
        else:
            print(f"\n❌ Upload failed!")
            print(f"   Status code: {response.status_code}")
            print(f"   Response: {response.text}")
            return False

    except requests.exceptions.ConnectionError:
        print("\n❌ Connection error!")
        print("   Make sure the API is running at http://localhost:8000")
        return False
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        return False


def get_stats(language: str = "russian"):
    """Get statistics for language"""
    url = f"http://localhost:8000/api/stats/{language}"

    try:
        response = requests.get(url)
        if response.status_code == 200:
            stats = response.json()
            print(f"\n📊 {language.title()} Documents Statistics:")
            print(f"   Total documents: {stats.get('total_documents', 0)}")

            latest = stats.get('latest_documents', [])
            if latest:
                print(f"   Latest uploads:")
                for doc in latest[:5]:
                    print(f"      - {doc['title']} ({doc['file_size']} bytes)")
        else:
            print(f"❌ Failed to get stats: {response.status_code}")
    except Exception as e:
        print(f"❌ Error getting stats: {str(e)}")


def main():
    """Main function"""
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python test_upload.py <zip_file_path> [russian|uzbek]")
        print("\nExamples:")
        print("  python test_upload.py russian_docs.zip russian")
        print("  python test_upload.py uzbek_docs.zip uzbek")
        print("\nOr to get statistics:")
        print("  python test_upload.py stats [russian|uzbek]")
        sys.exit(1)

    command = sys.argv[1]

    if command == "stats":
        language = sys.argv[2] if len(sys.argv) > 2 else "russian"
        get_stats(language)
    else:
        file_path = command
        language = sys.argv[2] if len(sys.argv) > 2 else "russian"

        if language not in ["russian", "uzbek"]:
            print(f"❌ Invalid language: {language}")
            print("   Must be 'russian' or 'uzbek'")
            sys.exit(1)

        success = test_upload(file_path, language)
        sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
