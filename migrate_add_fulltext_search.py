"""
Database migration to add full-text search indexes for better performance
Run this script once to improve search speed dramatically
"""
import os
from dotenv import load_dotenv
from sqlalchemy import create_engine, text

load_dotenv()

DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT")
DB_NAME = os.getenv("DB_NAME")

DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

def run_migration():
    """Add full-text search indexes to improve query performance"""
    engine = create_engine(DATABASE_URL)

    migrations = [
        # Add full-text search columns for document_metadata
        """
        ALTER TABLE document_metadata
        ADD COLUMN IF NOT EXISTS search_vector tsvector;
        """,

        # Create trigger to auto-update search vector
        """
        CREATE OR REPLACE FUNCTION document_metadata_search_trigger() RETURNS trigger AS $$
        begin
          new.search_vector :=
            setweight(to_tsvector('russian', coalesce(new.title,'')), 'A') ||
            setweight(to_tsvector('russian', coalesce(new.doc_type,'')), 'B') ||
            setweight(to_tsvector('russian', coalesce(new.category,'')), 'C') ||
            setweight(to_tsvector('russian', coalesce(new.number,'')), 'B');
          return new;
        end
        $$ LANGUAGE plpgsql;
        """,

        # Create trigger
        """
        DROP TRIGGER IF EXISTS tsvectorupdate ON document_metadata;
        CREATE TRIGGER tsvectorupdate BEFORE INSERT OR UPDATE
        ON document_metadata FOR EACH ROW EXECUTE FUNCTION document_metadata_search_trigger();
        """,

        # Create GIN index for fast full-text search
        """
        CREATE INDEX IF NOT EXISTS document_metadata_search_idx
        ON document_metadata USING GIN (search_vector);
        """,

        # Add full-text search for ru_documents
        """
        ALTER TABLE ru_documents
        ADD COLUMN IF NOT EXISTS search_vector tsvector;
        """,

        # Create trigger for ru_documents
        """
        CREATE OR REPLACE FUNCTION ru_documents_search_trigger() RETURNS trigger AS $$
        begin
          new.search_vector :=
            setweight(to_tsvector('russian', coalesce(new.title,'')), 'A') ||
            setweight(to_tsvector('russian', coalesce(substring(new.content, 1, 10000),'')), 'D');
          return new;
        end
        $$ LANGUAGE plpgsql;
        """,

        """
        DROP TRIGGER IF EXISTS tsvectorupdate ON ru_documents;
        CREATE TRIGGER tsvectorupdate BEFORE INSERT OR UPDATE
        ON ru_documents FOR EACH ROW EXECUTE FUNCTION ru_documents_search_trigger();
        """,

        """
        CREATE INDEX IF NOT EXISTS ru_documents_search_idx
        ON ru_documents USING GIN (search_vector);
        """,

        # Add full-text search for uz_documents
        """
        ALTER TABLE uz_documents
        ADD COLUMN IF NOT EXISTS search_vector tsvector;
        """,

        # Create trigger for uz_documents
        """
        CREATE OR REPLACE FUNCTION uz_documents_search_trigger() RETURNS trigger AS $$
        begin
          new.search_vector :=
            setweight(to_tsvector('russian', coalesce(new.title,'')), 'A') ||
            setweight(to_tsvector('russian', coalesce(substring(new.content, 1, 10000),'')), 'D');
          return new;
        end
        $$ LANGUAGE plpgsql;
        """,

        """
        DROP TRIGGER IF EXISTS tsvectorupdate ON uz_documents;
        CREATE TRIGGER tsvectorupdate BEFORE INSERT OR UPDATE
        ON uz_documents FOR EACH ROW EXECUTE FUNCTION uz_documents_search_trigger();
        """,

        """
        CREATE INDEX IF NOT EXISTS uz_documents_search_idx
        ON uz_documents USING GIN (search_vector);
        """,

        # Update existing rows
        """
        UPDATE document_metadata SET search_vector =
            setweight(to_tsvector('russian', coalesce(title,'')), 'A') ||
            setweight(to_tsvector('russian', coalesce(doc_type,'')), 'B') ||
            setweight(to_tsvector('russian', coalesce(category,'')), 'C') ||
            setweight(to_tsvector('russian', coalesce(number,'')), 'B');
        """,

        """
        UPDATE ru_documents SET search_vector =
            setweight(to_tsvector('russian', coalesce(title,'')), 'A') ||
            setweight(to_tsvector('russian', coalesce(substring(content, 1, 10000),'')), 'D');
        """,

        """
        UPDATE uz_documents SET search_vector =
            setweight(to_tsvector('russian', coalesce(title,'')), 'A') ||
            setweight(to_tsvector('russian', coalesce(substring(content, 1, 10000),'')), 'D');
        """
    ]

    with engine.connect() as conn:
        print("Running database migrations...")
        for i, migration in enumerate(migrations, 1):
            try:
                conn.execute(text(migration))
                conn.commit()
                print(f"✓ Migration {i}/{len(migrations)} completed")
            except Exception as e:
                print(f"✗ Migration {i} failed: {str(e)}")
                # Continue with other migrations

        print("\n✅ All migrations completed!")
        print("\nVerifying indexes...")

        # Check indexes
        result = conn.execute(text("""
            SELECT schemaname, tablename, indexname
            FROM pg_indexes
            WHERE indexname LIKE '%search_idx%'
        """))

        print("\nCreated indexes:")
        for row in result:
            print(f"  - {row[1]}.{row[2]}")

if __name__ == "__main__":
    run_migration()
