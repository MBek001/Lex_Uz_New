#!/bin/bash
# Simple database check script using psql

echo "================================"
echo "DATABASE STATUS CHECK"
echo "================================"
echo ""

# Database connection details
DB_HOST="localhost"
DB_PORT="5432"
DB_NAME="lex_uz_db"
DB_USER="postgres"
PGPASSWORD="2005"

export PGPASSWORD

echo "Connecting to database: $DB_NAME"
echo ""

# Check if psql is available
if ! command -v psql &> /dev/null; then
    echo "❌ psql not found. Install PostgreSQL client:"
    echo "   sudo apt-get install postgresql-client"
    echo ""
    echo "OR use docker exec instead:"
    echo "   docker exec lex_uz_postgres psql -U postgres -d lex_uz_db -c 'SELECT COUNT(*) FROM document_metadata;'"
    exit 1
fi

# Check metadata count
echo "📋 Checking document_metadata table..."
METADATA_COUNT=$(psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME -t -c "SELECT COUNT(*) FROM document_metadata;" 2>/dev/null | xargs)

if [ $? -eq 0 ]; then
    echo "   ✅ document_metadata: $METADATA_COUNT records"
else
    echo "   ❌ Error accessing document_metadata table"
fi

# Check Russian documents
echo "📄 Checking ru_documents table..."
RU_COUNT=$(psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME -t -c "SELECT COUNT(*) FROM ru_documents;" 2>/dev/null | xargs)

if [ $? -eq 0 ]; then
    echo "   ✅ ru_documents: $RU_COUNT records"
else
    echo "   ❌ Error accessing ru_documents table"
fi

# Check Uzbek documents
echo "📄 Checking uz_documents table..."
UZ_COUNT=$(psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME -t -c "SELECT COUNT(*) FROM uz_documents;" 2>/dev/null | xargs)

if [ $? -eq 0 ]; then
    echo "   ✅ uz_documents: $UZ_COUNT records"
else
    echo "   ❌ Error accessing uz_documents table"
fi

echo ""
echo "================================"
echo "SUMMARY"
echo "================================"

TOTAL=$((${METADATA_COUNT:-0} + ${RU_COUNT:-0} + ${UZ_COUNT:-0}))
echo "Total records: $TOTAL"
echo ""

if [ "$TOTAL" -eq 0 ]; then
    echo "⚠️  DATABASE IS EMPTY!"
    echo ""
    echo "To upload data, use these API endpoints:"
    echo "  1. Upload metadata Excel: POST http://localhost:8000/api/metadata/upload/excel"
    echo "  2. Upload Russian docs:   POST http://localhost:8000/api/upload/russian"
    echo "  3. Upload Uzbek docs:     POST http://localhost:8000/api/upload/uzbek"
    echo ""
    echo "Example:"
    echo "  curl -X POST 'http://localhost:8000/api/metadata/upload/excel' \\"
    echo "    -F 'file=@your_metadata.xlsx'"
else
    echo "✅ Database contains data. System ready for searches."
fi

echo ""
