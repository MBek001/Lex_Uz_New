#!/usr/bin/env python3
"""
Database diagnostic script - Check actual record counts
"""
from app.config.database import get_db_context
from app.models.documents import RussianDocument, UzbekDocument
from sqlalchemy import func, text


def check_database():
    """Check actual database counts"""
    with get_db_context() as db:
        print("=" * 60)
        print("DATABASE DIAGNOSTIC REPORT")
        print("=" * 60)
        print()

        # Count Russian documents
        try:
            ru_count = db.query(RussianDocument).count()
            print(f"✅ Russian Documents (ru_documents): {ru_count:,}")

            # Get min and max IDs
            ru_min_id = db.query(func.min(RussianDocument.id)).scalar()
            ru_max_id = db.query(func.max(RussianDocument.id)).scalar()
            print(f"   Min ID: {ru_min_id}, Max ID: {ru_max_id}")

            # Get latest record
            latest_ru = db.query(RussianDocument)\
                .order_by(RussianDocument.created_at.desc())\
                .first()
            if latest_ru:
                print(f"   Latest: ID={latest_ru.id}, Title={latest_ru.title}, Created={latest_ru.created_at}")

        except Exception as e:
            print(f"❌ Error reading ru_documents: {str(e)}")

        print()

        # Count Uzbek documents
        try:
            uz_count = db.query(UzbekDocument).count()
            print(f"✅ Uzbek Documents (uz_documents): {uz_count:,}")

            # Get min and max IDs
            uz_min_id = db.query(func.min(UzbekDocument.id)).scalar()
            uz_max_id = db.query(func.max(UzbekDocument.id)).scalar()
            print(f"   Min ID: {uz_min_id}, Max ID: {uz_max_id}")

            # Get latest record
            latest_uz = db.query(UzbekDocument)\
                .order_by(UzbekDocument.created_at.desc())\
                .first()
            if latest_uz:
                print(f"   Latest: ID={latest_uz.id}, Title={latest_uz.title}, Created={latest_uz.created_at}")

        except Exception as e:
            print(f"❌ Error reading uz_documents: {str(e)}")

        print()

        # Total count
        total = (ru_count if 'ru_count' in locals() else 0) + (uz_count if 'uz_count' in locals() else 0)
        print(f"📊 TOTAL DOCUMENTS: {total:,}")
        print()

        # Check for gaps in IDs (might indicate deletions)
        try:
            if uz_count > 0 and uz_max_id and uz_min_id:
                expected_count = uz_max_id - uz_min_id + 1
                if expected_count != uz_count:
                    print(f"⚠️  Uzbek documents: ID gap detected!")
                    print(f"   Expected records (based on ID range): {expected_count:,}")
                    print(f"   Actual records: {uz_count:,}")
                    print(f"   Missing records: {expected_count - uz_count:,}")
                else:
                    print(f"✅ Uzbek documents: No ID gaps (continuous sequence)")
        except:
            pass

        try:
            if ru_count > 0 and ru_max_id and ru_min_id:
                expected_count = ru_max_id - ru_min_id + 1
                if expected_count != ru_count:
                    print(f"⚠️  Russian documents: ID gap detected!")
                    print(f"   Expected records (based on ID range): {expected_count:,}")
                    print(f"   Actual records: {ru_count:,}")
                    print(f"   Missing records: {expected_count - ru_count:,}")
                else:
                    print(f"✅ Russian documents: No ID gaps (continuous sequence)")
        except:
            pass

        print()

        # Raw SQL check (bypass ORM)
        print("Raw SQL verification:")
        try:
            result = db.execute(text("SELECT COUNT(*) FROM uz_documents")).scalar()
            print(f"   uz_documents (raw SQL): {result:,}")
        except Exception as e:
            print(f"   uz_documents error: {str(e)}")

        try:
            result = db.execute(text("SELECT COUNT(*) FROM ru_documents")).scalar()
            print(f"   ru_documents (raw SQL): {result:,}")
        except Exception as e:
            print(f"   ru_documents error: {str(e)}")

        print()
        print("=" * 60)


if __name__ == "__main__":
    check_database()
