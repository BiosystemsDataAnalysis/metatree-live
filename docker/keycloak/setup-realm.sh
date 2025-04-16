cat /tmp/realm-template.json | \
  sed "s|\${KEYCLOAK_REALM}|${KEYCLOAK_REALM}|" | \
  sed "s|\${KEYCLOAK_CLIENT_ID}|${KEYCLOAK_CLIENT_ID}|" | \
  sed "s|\${METATREE_URL}|${METATREE_URL}|" \
  > /tmp/realm-export.json
