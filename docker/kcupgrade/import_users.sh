#!/bin/bash

# Enable debugging options
set -e  # Exit on error
set -u  # Exit on undefined variable
set -o pipefail  # Exit if any command in pipeline fails

# Add debug mode
DEBUG=${DEBUG:-false}
SKIP_EXISTING=${SKIP_EXISTING:-false}  # Option to skip existing users
DRY_RUN=${DRY_RUN:-false}             # Option to run without actual import

if [ "$DEBUG" = "true" ]; then
    set -x  # Enable trace mode
fi

# Function for debug logging
debug_log() {
    if [ "$DEBUG" = "true" ]; then
        echo "DEBUG: $1" >&2
    fi
}

# Function for error logging
error_log() {
    echo "ERROR: $1" >&2
}

# Function for info logging
info_log() {
    echo "INFO: $1"
}

# Function for warning logging
warn_log() {
    echo "WARN: $1"
}

# Function for dry run logging
dry_run_log() {
    if [ "$DRY_RUN" = "true" ]; then
        echo "DRY_RUN: $1"
    fi
}

# Configuration
KEYCLOAK_URL="http://localhost:8080"  # Change this to your Keycloak URL
ADMIN_USERNAME="admin"               # Change this to your admin username
ADMIN_PASSWORD="admin"               # Change this to your admin password
REALM="metatree"
IMPORT_FILE="./keycloak_users_import_formatted.json"
#IMPORT_FILE="../keycloak/keycloak-add-user.json"

# Get access token
info_log "Getting access token..."
debug_log "Keycloak URL: $KEYCLOAK_URL"
debug_log "Admin username: $ADMIN_USERNAME"
debug_log "Realm: $REALM"

ACCESS_TOKEN=$(curl -s -X POST "$KEYCLOAK_URL/auth/realms/master/protocol/openid-connect/token" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=$ADMIN_USERNAME" \
  -d "password=$ADMIN_PASSWORD" \
  -d "grant_type=password" \
  -d "client_id=admin-cli" | jq -r .access_token)

if [ "$ACCESS_TOKEN" == "null" ] || [ -z "$ACCESS_TOKEN" ]; then
  error_log "Failed to get access token. Please check your credentials."
  exit 1
fi

info_log "Access token obtained successfully."
debug_log "Access token: ${ACCESS_TOKEN:0:20}..."

# Create temporary files for each user
info_log "Extracting users from JSON file..."
debug_log "Import file: $IMPORT_FILE"

if [ ! -f "$IMPORT_FILE" ]; then
  error_log "Import file not found: $IMPORT_FILE"
  exit 1
fi

jq -c '.[]' "$IMPORT_FILE" > /tmp/users.json
debug_log "Users extracted to /tmp/users.json"

# Import each user
counter=1
total_users=$(wc -l < /tmp/users.json)
successful_imports=0
failed_imports=0

info_log "Starting import of $total_users users..."

while IFS= read -r user; do
  username=$(echo "$user" | jq -r '.username')
  info_log "Processing user $counter/$total_users: $username"
  debug_log "User data: $user"
  
  # Check if user already exists
  if [ "$SKIP_EXISTING" = "true" ]; then
    existing_user=$(curl -s -X GET "$KEYCLOAK_URL/auth/admin/realms/$REALM/users?username=$username" \
      -H "Authorization: Bearer $ACCESS_TOKEN" | jq -r '.[0]')
    
    if [ "$existing_user" != "null" ]; then
      warn_log "User $username already exists, skipping..."
      counter=$((counter + 1))
      continue
    fi
  fi
  
  # Perform dry run
  if [ "$DRY_RUN" = "true" ]; then
    dry_run_log "Would import user: $username"
    successful_imports=$((successful_imports + 1))
  else
    # Import user
    response=$(curl -s -X POST "$KEYCLOAK_URL/auth/admin/realms/$REALM/users" \
      -H "Authorization: Bearer $ACCESS_TOKEN" \
      -H "Content-Type: application/json" \
      -d "$user")
    
    if [ -z "$response" ]; then
      info_log "✓ User $username imported successfully"
      successful_imports=$((successful_imports + 1))
    else
      if echo "$response" | grep -q "User exists with same username"; then
        warn_log "⚠ User $username already exists"
        failed_imports=$((failed_imports + 1))
      else
        error_log "✗ Failed to import user $username: $response"
        failed_imports=$((failed_imports + 1))
      fi
    fi
  fi
  
  counter=$((counter + 1))
done < /tmp/users.json

# Summary
info_log "Import Summary:"
info_log "- Total users processed: $total_users"
info_log "- Successful imports: $successful_imports"
info_log "- Failed imports: $failed_imports"
if [ "$DRY_RUN" = "true" ]; then
  info_log "- Mode: DRY RUN (no actual imports performed)"
fi

# Clean up
rm -f /tmp/users.json
debug_log "Temporary files cleaned up"

info_log "Import process completed!"
