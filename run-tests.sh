set -e

CACHE_DIR=".oacensus"

echo "Removing cache at $CACHE_DIR"
rm -rf $CACHE_DIR

echo "Running tests with no cache..."
nosetests

echo "Running tests with cache..."
nosetests
