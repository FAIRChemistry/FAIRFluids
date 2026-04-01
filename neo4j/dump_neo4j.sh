#!/bin/bash

echo "🗄️  Neo4j Database Dump"
echo "======================"

# Container name
CONTAINER_NAME="fairfluids-neo4j"
DUMP_FILE="neo4j_dump_$(date +%Y%m%d_%H%M%S).dump"
SCRIPT_DIR="$(dirname "$0")"
OUTPUT_DIR="$SCRIPT_DIR/../Workflows/paper_outputs"

# Ensure output directory exists
mkdir -p "$OUTPUT_DIR"

# Check if container is running
if ! docker ps | grep -q "$CONTAINER_NAME"; then
    echo "❌ Container $CONTAINER_NAME is not running."
    echo "   Start it with: ./setup_neo4j.sh"
    exit 1
fi

echo "📦 Creating database dump..."
echo "   Container: $CONTAINER_NAME"
echo "   Output file: $OUTPUT_DIR/$DUMP_FILE"

# Stop container (Neo4j runs as main process, so we need to stop the container)
echo "⏸️  Stopping Neo4j container..."
docker stop "$CONTAINER_NAME"

# Wait a moment for container to stop
sleep 5

# Ensure dumps directory exists and clean up old dump files
echo "📁 Ensuring dumps directory exists and cleaning old dumps..."
docker start "$CONTAINER_NAME" 2>/dev/null || true
sleep 3
docker exec "$CONTAINER_NAME" mkdir -p /data/dumps 2>/dev/null || true
# Remove old dump files to avoid "Archive already exists" error
docker exec "$CONTAINER_NAME" rm -f /data/dumps/neo4j.dump 2>/dev/null || true
docker stop "$CONTAINER_NAME" 2>/dev/null || true
sleep 2

# Also clean up in the volume/filesystem using temporary container
echo "🧹 Cleaning old dump files..."
docker run --rm \
    --volumes-from "$CONTAINER_NAME" \
    neo4j:5.15 \
    sh -c "rm -f /data/dumps/neo4j.dump" 2>/dev/null || true

# Create dump using a temporary container with access to the same volumes/filesystem
echo "💾 Creating dump file using temporary container..."
DUMP_OUTPUT=$(docker run --rm \
    --volumes-from "$CONTAINER_NAME" \
    neo4j:5.15 \
    neo4j-admin database dump neo4j --to-path=/data/dumps/ 2>&1)
DUMP_EXIT_CODE=$?

# Check output for errors
if [ $DUMP_EXIT_CODE -eq 0 ] && ! echo "$DUMP_OUTPUT" | grep -qi "error\|failed"; then
    echo "✅ Dump created successfully!"
    echo "$DUMP_OUTPUT" | grep -v "^$" | tail -3
else
    echo "❌ Failed to create dump file."
    echo "Error output:"
    echo "$DUMP_OUTPUT" | grep -i "error\|failed" || echo "$DUMP_OUTPUT"
    echo ""
    echo "   Starting Neo4j container..."
    docker start "$CONTAINER_NAME"
    exit 1
fi

# Start Neo4j container again
echo "▶️  Starting Neo4j container..."
docker start "$CONTAINER_NAME"
sleep 10

# Find the dump file in the container
# neo4j-admin creates a file named "neo4j.dump" by default
DUMP_FILE_IN_CONTAINER=$(docker exec "$CONTAINER_NAME" sh -c "ls -t /data/dumps/*.dump 2>/dev/null | head -1" || echo "")

# If not found with wildcard, try the default name
if [ -z "$DUMP_FILE_IN_CONTAINER" ]; then
    if docker exec "$CONTAINER_NAME" test -f /data/dumps/neo4j.dump 2>/dev/null; then
        DUMP_FILE_IN_CONTAINER="/data/dumps/neo4j.dump"
    else
        echo "❌ Dump file not found in container."
        echo "   Listing /data/dumps directory:"
        docker exec "$CONTAINER_NAME" ls -la /data/dumps/ 2>/dev/null || echo "   Directory does not exist or is not accessible"
        exit 1
    fi
fi

# Extract just the filename
DUMP_FILENAME=$(basename "$DUMP_FILE_IN_CONTAINER")

# Create a timestamped filename for the host
TIMESTAMPED_FILENAME="neo4j_dump_$(date +%Y%m%d_%H%M%S).dump"

# Copy dump file from container to host with timestamped name
echo "📥 Copying dump file to host..."
if docker cp "$CONTAINER_NAME:$DUMP_FILE_IN_CONTAINER" "$OUTPUT_DIR/$TIMESTAMPED_FILENAME"; then
    ABSOLUTE_PATH="$(cd "$OUTPUT_DIR" && pwd)/$TIMESTAMPED_FILENAME"
    echo "✅ Dump created and copied successfully!"
    echo "   File: $ABSOLUTE_PATH"
    echo "   Relative path: $OUTPUT_DIR/$TIMESTAMPED_FILENAME"
    echo "   Original name in container: $DUMP_FILENAME"
    echo ""
    echo "💡 To restore this dump later, use:"
    echo "   ./restore_neo4j.sh $TIMESTAMPED_FILENAME"
else
    echo "❌ Failed to copy dump file."
    exit 1
fi
