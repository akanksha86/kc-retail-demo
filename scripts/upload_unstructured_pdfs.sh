#!/bin/bash

# Ensure we are in the correct directory
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
BASE_DIR="$(dirname "$DIR")"

cd "$BASE_DIR"

echo "================================================="
echo "Uploading Unstructured PDFs to GCS"
echo "================================================="

if [ ! -d "data/unstructured" ]; then
    echo "Error: data/unstructured directory not found. Please run scripts/generate_unstructured.py first."
    exit 1
fi

echo "Uploading files from data/unstructured to gs://kc-retail-demo-warehouse/unstructured/"
gcloud storage cp -r data/unstructured/* gs://kc-retail-demo-warehouse/unstructured/

echo "Done!"
