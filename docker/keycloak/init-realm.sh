#!/bin/bash

# Process the realm template with environment variables
cat /tmp/realm-template.json | \
  sed "s|\${KEYCLOAK_REALM}|${KEYCLOAK_REALM}|g" | \
  sed "s|\${KEYCLOAK_CLIENT_ID}|${KEYCLOAK_CLIENT_ID}|g" | \
  sed "s|\${KEYCLOAK_CLIENT_SECRET}|${KEYCLOAK_CLIENT_SECRET}|g" | \
  sed "s|\${METATREE_URL}|${METATREE_URL}|g" \
  > /opt/keycloak/data/import/realm.json

echo "Realm configuration processed and saved to /opt/keycloak/data/import/realm.json"
