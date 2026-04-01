#!/bin/bash

echo "🗄️  Neo4j Database Restore"
echo "========================"

# Container name
CONTAINER_NAME="fairfluids-neo4j"
SCRIPT_DIR="$(dirname "$0")"
DUMP_DIR="$SCRIPT_DIR/../Workflows/paper_outputs"

# Check if dump file is provided
if [ -z "$1" ]; then
    echo "❌ Please provide a dump file name."
    echo "   Usage: ./restore_neo4j.sh <dump_file.dump>"
    echo ""
    echo "   Available dump files:"
    ls -lh "$DUMP_DIR"/*.dump 2>/dev/null | awk '{print "   - " $9}' || echo "   No dump files found in $DUMP_DIR"
    exit 1
fi

DUMP_FILE="$1"

# Check if dump file exists
if [ ! -f "$DUMP_FILE" ]; then
    # Try relative to dump directory (paper_outputs)
    if [ -f "$DUMP_DIR/$DUMP_FILE" ]; then
        DUMP_FILE="$DUMP_DIR/$DUMP_FILE"
    # Try relative to script directory (for backwards compatibility)
    elif [ -f "$SCRIPT_DIR/$DUMP_FILE" ]; then
        DUMP_FILE="$SCRIPT_DIR/$DUMP_FILE"
    else
        echo "❌ Dump file not found: $DUMP_FILE"
        echo "   Searched in:"
        echo "   - $DUMP_DIR/"
        echo "   - $SCRIPT_DIR/"
        exit 1
    fi
fi

DUMP_FILENAME=$(basename "$DUMP_FILE")

# Check if container is running
if ! docker ps | grep -q "$CONTAINER_NAME"; then
    echo "❌ Container $CONTAINER_NAME is not running."
    echo "   Start it with: ./setup_neo4j.sh"
    exit 1
fi

echo "⚠️  WARNING: This will DELETE all existing data in Neo4j!"
read -p "   Are you sure you want to continue? (yes/no): " confirm

if [ "$confirm" != "yes" ]; then
    echo "❌ Restore cancelled."
    exit 1
fi

echo "📦 Restoring database from dump..."
echo "   Container: $CONTAINER_NAME"
echo "   Dump file: $DUMP_FILE"

# Ensure dumps directory exists
docker exec "$CONTAINER_NAME" mkdir -p /data/dumps

# Stop Neo4j
echo "⏸️  Stopping Neo4j..."
docker exec "$CONTAINER_NAME" neo4j stop || true
sleep 5

# Check if container is still running
if ! docker ps | grep -q "$CONTAINER_NAME"; then
    echo "⚠️  Container stopped. Restarting..."
    docker start "$CONTAINER_NAME"
    sleep 10
fi

# Copy dump file to container
echo "📤 Copying dump file to container..."
if ! docker cp "$DUMP_FILE" "$CONTAINER_NAME:/data/dumps/$DUMP_FILENAME"; then
    echo "❌ Failed to copy dump file to container."
    exit 1
fi

# Load dump using neo4j-admin
echo "💾 Loading dump file..."
if ! docker exec "$CONTAINER_NAME" neo4j-admin database load neo4j --from-path=/data/dumps/ --overwrite-destination=true; then
    echo "❌ Failed to load dump file."
    echo "   Starting Neo4j..."
    docker exec "$CONTAINER_NAME" neo4j start 2>/dev/null || docker restart "$CONTAINER_NAME"
    exit 1
fi

# Start Neo4j again
echo "▶️  Starting Neo4j..."
if docker exec "$CONTAINER_NAME" neo4j start 2>&1; then
    echo "✅ Neo4j started successfully"
    sleep 10
else
    echo "⚠️  Could not start Neo4j via command. Restarting container..."
    docker restart "$CONTAINER_NAME"
    sleep 15
fi

echo "✅ Database restored successfully!"
echo ""
echo "💡 You can verify the restore by running:"
echo "   python create_neo4j_graph.py --queries"
