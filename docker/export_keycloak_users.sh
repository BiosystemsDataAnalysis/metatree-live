#!/bin/bash

# Script to export Keycloak users with hashed passwords in importable format

# Set variables
db_container="metatree-keycloak-database"
realm_name="metatree"
output_json="keycloak_users_with_passwords.json"
output_import="keycloak_users_import_ready.json"

# Export users with passwords to JSON format (raw data)
docker exec $db_container psql -U keycloak -d keycloak \
-c "SELECT json_agg(row_to_json(t)) FROM (SELECT u.username, u.email, u.first_name, u.last_name, c.secret_data::json as secret_data, c.credential_data::json as credential_data FROM user_entity u JOIN credential c ON u.id = c.user_id WHERE c.type = 'password' AND u.realm_id = (SELECT id FROM realm WHERE name = '$realm_name')) t;" > $output_json

echo "Raw users exported to $output_json"

# Export users in Keycloak import format
docker exec $db_container psql -U keycloak -d keycloak \
-c "SELECT json_agg(
  json_build_object(
    'username', u.username,
    'email', u.email,
    'firstName', u.first_name,
    'lastName', u.last_name,
    'enabled', u.enabled,
    'createdTimestamp', u.created_timestamp,
    'credentials', json_build_array(
      json_build_object(
        'type', 'password',
        'hashedSaltedValue', (c.secret_data::json->>'value'),
        'salt', (c.secret_data::json->>'salt'),
        'hashIterations', (c.credential_data::json->>'hashIterations')::int,
        'algorithm', (c.credential_data::json->>'algorithm'),
        'config', json_build_object(),
        'temporary', false
      )
    ),
    'realmRoles', json_build_array('default-roles-$realm_name'),
    'clientRoles', json_build_object(),
    'groups', json_build_array(),
    'attributes', json_build_object(),
    'requiredActions', json_build_array(),
    'federatedIdentities', json_build_array(),
    'socialLinks', json_build_array()
  )
) FROM user_entity u 
JOIN credential c ON u.id = c.user_id 
WHERE c.type = 'password' 
AND u.realm_id = (SELECT id FROM realm WHERE name = '$realm_name');" > $output_import

echo "Import-ready users exported to $output_import"

# Clean and format the JSON for better readability and import compatibility
if command -v jq &> /dev/null; then
    formatted_output="keycloak_users_import_formatted.json"
    sed -n '3p' $output_import | jq '.' > $formatted_output
    echo "Formatted JSON exported to $formatted_output"
else
    echo "Note: Install 'jq' for formatted JSON output"
fi
