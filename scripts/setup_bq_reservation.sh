#!/usr/bin/env bash
set -e

PROJECT_ID="kc-retail-demo"
REGION="EU"
RESERVATION_NAME="ml_inference_reservation"

echo "================================================="
echo "Setting up BigQuery Enterprise Reservation for ML"
echo "================================================="
echo "Note: BigQuery ML inference on Object Tables requires an Enterprise Edition reservation."
echo "This script creates a Pay-As-You-Go (Autoscaling) reservation with 0 baseline slots,"
echo "meaning you only pay for slots when queries are actively running."
echo ""

echo "1. Enabling BigQuery Reservation API..."
gcloud services enable bigqueryreservation.googleapis.com --project="$PROJECT_ID"

echo "2. Creating Enterprise Reservation ($RESERVATION_NAME)..."
# Check if reservation exists
if bq show --reservation --project_id="$PROJECT_ID" --location="$REGION" "$RESERVATION_NAME" >/dev/null 2>&1; then
    echo "Reservation already exists."
else
    bq mk --reservation \
        --project_id="$PROJECT_ID" \
        --location="$REGION" \
        --slots=0 \
        --autoscale_max_slots=100 \
        --edition=ENTERPRISE \
        "$RESERVATION_NAME"
    echo "Reservation created."
fi

echo "3. Assigning project to the reservation for QUERY jobs..."
# Note: Assignee ID is the project ID
ASSIGNMENT_ID=$(bq ls --reservation_assignment --project_id="$PROJECT_ID" --location="$REGION" | grep "$RESERVATION_NAME" | grep "QUERY" | awk '{print $1}' || true)

if [ -z "$ASSIGNMENT_ID" ]; then
    bq mk --reservation_assignment \
        --project_id="$PROJECT_ID" \
        --location="$REGION" \
        --reservation_id="${PROJECT_ID}:${REGION}.${RESERVATION_NAME}" \
        --job_type=QUERY \
        --assignee_id="$PROJECT_ID" \
        --assignee_type=PROJECT
    echo "Assignment created successfully."
else
    echo "Project is already assigned to the reservation."
fi

echo "================================================="
echo "Reservation Setup Complete! You can now run the ML query."
echo "================================================="
