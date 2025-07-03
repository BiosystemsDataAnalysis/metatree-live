#!/bin/bash

# Configuration
KEYCLOAK_URL="http://localhost:8080"  # Change this to your Keycloak URL
ADMIN_USERNAME="admin"               # Change this to your admin username
ADMIN_PASSWORD="admin"               # Change this to your admin password
REALM="metatree"

# Get access token
echo "Getting access token..."
ACCESS_TOKEN=$(curl -s -X POST "$KEYCLOAK_URL/auth/realms/master/protocol/openid-connect/token" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=$ADMIN_USERNAME" \
  -d "password=$ADMIN_PASSWORD" \
  -d "grant_type=password" \
  -d "client_id=admin-cli" | jq -r .access_token)

if [ "$ACCESS_TOKEN" == "null" ] || [ -z "$ACCESS_TOKEN" ]; then
  echo "Failed to get access token. Please check your credentials."
  exit 1
fi

echo "Access token obtained successfully."

# Create temporary files for each user
echo "Extracting users from JSON file..."
jq -c '.[0].users[]' keycloak/keycloak-add-user.json > /tmp/users.json

# Import each user
counter=1
while IFS= read -r user; do
  username=$(echo "$user" | jq -r '.username')
  echo "Importing user $counter: $username"
  
  response=$(curl -s -X POST "$KEYCLOAK_URL/auth/admin/realms/$REALM/users" \
    -H "Authorization: Bearer $ACCESS_TOKEN" \
    -H "Content-Type: application/json" \
    -d "$user")
  
  if [ -z "$response" ]; then
    echo "✓ User $username imported successfully"
  else
    echo "✗ Failed to import user $username: $response"
  fi
  
  counter=$((counter + 1))
done < /tmp/users.json

# Clean up
rm /tmp/users.json

echo "Import process completed!"
