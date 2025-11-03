"""
Test script to diagnose metadata search issues
"""
import os
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.models.metadata import DocumentMetadata

load_dotenv()

# Database connection
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT")
DB_NAME = os.getenv("DB_NAME")

DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)

def search_by_number(number: str):
    """Search metadata by exact number"""
    db = SessionLocal()
    try:
        print(f"\n🔍 Searching for number: {number}")
        print("=" * 80)

        # Search for exact match
        results = db.query(DocumentMetadata)\
            .filter(DocumentMetadata.number.ilike(f"%{number}%"))\
            .limit(10)\
            .all()

        if not results:
            print(f"❌ No documents found with number containing '{number}'")
            return

        print(f"✅ Found {len(results)} documents:\n")

        for idx, doc in enumerate(results, 1):
            print(f"\n📄 Document {idx}:")
            print(f"   Number: {doc.number}")
            print(f"   Title: {doc.title[:80]}...")
            print(f"   Type: {doc.doc_type}")
            print(f"   Date: {doc.registration_date}")
            print(f"   Status: {doc.status}")
            print(f"   Link RU: {doc.link_rus}")
            print(f"   Link UZ: {doc.link_uz_latin}")

    finally:
        db.close()

def search_all_with_234():
    """Find all documents containing 234"""
    db = SessionLocal()
    try:
        print(f"\n🔍 Finding ALL documents with '234' in any field")
        print("=" * 80)

        from sqlalchemy import or_

        results = db.query(DocumentMetadata)\
            .filter(or_(
                DocumentMetadata.number.ilike('%234%'),
                DocumentMetadata.title.ilike('%234%'),
                DocumentMetadata.doc_type.ilike('%234%')
            ))\
            .limit(20)\
            .all()

        print(f"✅ Found {len(results)} documents:\n")

        for idx, doc in enumerate(results, 1):
            print(f"\n📄 Document {idx}:")
            print(f"   Number: {doc.number}")
            print(f"   Title: {doc.title[:80]}...")
            print(f"   Where '234' appears:")
            if '234' in (doc.number or ''):
                print(f"      ✓ In NUMBER field: {doc.number}")
            if '234' in doc.title.lower():
                print(f"      ✓ In TITLE")
            if '234' in doc.doc_type.lower():
                print(f"      ✓ In DOC_TYPE")

    finally:
        db.close()

def show_sample_numbers():
    """Show sample document numbers to understand the format"""
    db = SessionLocal()
    try:
        print(f"\n📋 Sample document numbers in database:")
        print("=" * 80)

        results = db.query(DocumentMetadata)\
            .filter(DocumentMetadata.number != '')\
            .filter(DocumentMetadata.number != None)\
            .limit(50)\
            .all()

        numbers = [doc.number for doc in results if doc.number]
        unique_numbers = sorted(set(numbers))[:30]

        print("First 30 unique document numbers:")
        for num in unique_numbers:
            print(f"   {num}")

    finally:
        db.close()

if __name__ == "__main__":
    print("\n" + "=" * 80)
    print("METADATA SEARCH DIAGNOSTIC TOOL")
    print("=" * 80)

    # Test 1: Show sample numbers
    show_sample_numbers()

    # Test 2: Search for exact "234"
    search_by_number("234")

    # Test 3: Search for "N 234"
    search_by_number("N 234")

    # Test 4: Show all documents with 234 anywhere
    search_all_with_234()

    print("\n" + "=" * 80)
    print("DIAGNOSTIC COMPLETE")
    print("=" * 80 + "\n")
