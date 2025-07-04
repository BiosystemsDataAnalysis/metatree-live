# Set your credentials (replace with your actual values)
KEYCLOAK_USER=${KEYCLOAK_USER:-keycloak}  # typically "admin" or your admin user
KEYCLOAK_PASSWORD=${KEYCLOAK_PASSWORD:-keycloak}  # typically "admin" or your admin password
REALM_NAME=metatree  # typically "master" or your custom realm name

# Export users
docker exec metatree-keycloak /opt/jboss/keycloak/bin/kcadm.sh config credentials --server http://localhost:8080/auth --realm master --user $KEYCLOAK_USER --password $KEYCLOAK_PASSWORD

docker exec metatree-keycloak /opt/jboss/keycloak/bin/kcadm.sh get users -r $REALM_NAME > keycloak_users_export.json 