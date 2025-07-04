# Keycloak Upgrade Guide: 16.1.1 → 26.2.5

This document outlines the complete process for upgrading Keycloak from version 16.1.1 to 26.2.5 in a Docker Compose environment.

## Overview

Keycloak 26.x introduces significant architectural changes compared to 16.x:
- **Runtime**: Moved from WildFly to Quarkus-based runtime
- **Configuration**: New environment variable format (KC_* prefix)
- **Commands**: New startup commands (`start-dev`, `start`)
- **Import**: Improved realm import mechanism
- **Security**: Enhanced security defaults

## Prerequisites

- Docker and Docker Compose installed
- Existing Keycloak 16.x setup with Docker Compose
- Backup of existing configuration and data (recommended)

## Step-by-Step Upgrade Process

### 1. Update the Keycloak Image Version

**File**: `.env`

```bash
# Change from:
KEYCLOAK_IMAGE=frnzdock/keycloak:16.1.1_fix

# To:
KEYCLOAK_IMAGE=keycloak/keycloak:26.2.5
```

### 2. Create New Realm Initialization Script

**File**: `keycloak/init-realm.sh`

```bash
#!/bin/bash

# Process the realm template with environment variables
cat /tmp/realm-template.json | \
  sed "s|\${KEYCLOAK_REALM}|${KEYCLOAK_REALM}|" | \
  sed "s|\${KEYCLOAK_CLIENT_ID}|${KEYCLOAK_CLIENT_ID}|" | \
  sed "s|\${METATREE_URL}|${METATREE_URL}|" \
  > /opt/keycloak/data/import/realm.json

echo "Realm configuration processed and saved to /opt/keycloak/data/import/realm.json"
```

**Make it executable:**
```bash
chmod +x keycloak/init-realm.sh
```

### 3. Update Docker Compose Configuration

**File**: `keycloak-docker-compose.yml`

Replace the existing `metatree-keycloak` service with:

```yaml
services:
  metatree-keycloak-postgres:
    image: postgres:13-alpine
    container_name: metatree-keycloak-database
    environment:
      POSTGRES_DB: keycloak
      POSTGRES_USER: keycloak
      POSTGRES_PASSWORD: keycloak
    volumes:
      - metatree-keycloak-postgres-data:/var/lib/postgresql/data
    networks:
      - metatree-keycloak-db-network
    restart: unless-stopped
    logging:
      driver: ${DOCKER_LOGGING_DRIVER:-journald}
      options:
        labels: application
        tag: metatree-keycloak-postgres

  metatree-keycloak-init:
    image: alpine:latest
    container_name: metatree-keycloak-init
    environment:
      KEYCLOAK_REALM: ${KEYCLOAK_REALM:?Please configure KEYCLOAK_REALM}
      KEYCLOAK_CLIENT_ID: ${KEYCLOAK_CLIENT_ID:?Please configure KEYCLOAK_CLIENT_ID}
      KEYCLOAK_CLIENT_SECRET: ${KEYCLOAK_CLIENT_SECRET:?Please configure KEYCLOAK_CLIENT_SECRET}
      METATREE_URL: ${METATREE_URL:?Please configure METATREE_URL.}
    volumes:
      - ./keycloak/realm-template.json:/tmp/realm-template.json
      - keycloak-import-data:/opt/keycloak/data/import
      - ./keycloak/init-realm.sh:/init-realm.sh
    command: sh /init-realm.sh
    networks:
      - metatree-keycloak-db-network

  metatree-keycloak:    
    image: ${KEYCLOAK_IMAGE}
    container_name: metatree-keycloak
    command: start-dev --import-realm
    environment:
      KC_DB: postgres
      KC_DB_URL: jdbc:postgresql://metatree-keycloak-postgres:5432/keycloak
      KC_DB_USERNAME: keycloak
      KC_DB_PASSWORD: keycloak
      KC_HOSTNAME: ${KEYCLOAK_HOSTNAME:?Please configure KEYCLOAK_HOSTNAME.}
      KC_HOSTNAME_URL: https://${KEYCLOAK_HOSTNAME:?Please configure KEYCLOAK_HOSTNAME.}
      KC_HTTP_PORT: 8080
      KC_HTTPS_PORT: 8443
      KC_PROXY: edge
      KC_BOOTSTRAP_ADMIN_USERNAME: admin
      KC_BOOTSTRAP_ADMIN_PASSWORD: admin      
      KC_HTTP_RELATIVE_PATH: /auth
    ports:
      - ${KEYCLOAK_PORT:-8080}:8080
    depends_on:
      - metatree-keycloak-postgres
      - metatree-keycloak-init
    networks:
      - metatree-keycloak-db-network
    volumes:
      - keycloak-import-data:/opt/keycloak/data/import
    restart: unless-stopped
    logging:
      driver: ${DOCKER_LOGGING_DRIVER:-journald}
      options:
        labels: application
        tag: metatree-keycloak

volumes:
  metatree-keycloak-postgres-data:
  keycloak-import-data:

networks:
  metatree-keycloak-db-network:
    driver: bridge
```

### 4. Environment Variable Migration

#### Old Format (Keycloak 16.x):
```bash
DB_VENDOR: POSTGRES
DB_ADDR: metatree-keycloak-postgres
DB_DATABASE: keycloak
DB_USER: keycloak
DB_PASSWORD: keycloak
KEYCLOAK_IMPORT: /tmp/realm-export.json
PROXY_ADDRESS_FORWARDING: 'true'
```

#### New Format (Keycloak 26.x):
```bash
KC_DB: postgres
KC_DB_URL: jdbc:postgresql://metatree-keycloak-postgres:5432/keycloak
KC_DB_USERNAME: keycloak
KC_DB_PASSWORD: keycloak
KC_PROXY: edge
KEYCLOAK_ADMIN: admin
KEYCLOAK_ADMIN_PASSWORD: admin
KC_HTTP_RELATIVE_PATH: /auth
```

### 5. Upgrade Process Commands

#### Stop existing containers:
```bash
docker compose -f keycloak-docker-compose.yml down
```

#### Pull new images:
```bash
docker compose -f keycloak-docker-compose.yml pull
```

#### Start with fresh volumes (if needed):
```bash
docker compose -f keycloak-docker-compose.yml down -v
```

#### Start the upgraded setup:
```bash
docker compose -f keycloak-docker-compose.yml up -d
```

#### Monitor the startup:
```bash
docker compose -f keycloak-docker-compose.yml logs -f metatree-keycloak
```

### 6. User Data Migration (Critical Step)

**Important**: The realm import process only imports realm configuration, not user data. Users need to be migrated separately.

#### Option A: Export/Import Users from Old Keycloak

1. **Export users from old Keycloak 16.x** (before upgrade):
```bash
# Export users from the old Keycloak instance
docker compose -f keycloak-docker-compose.yml exec metatree-keycloak \
  /opt/jboss/keycloak/bin/standalone.sh \
  -Djboss.socket.binding.port-offset=100 \
  -Dkeycloak.migration.action=export \
  -Dkeycloak.migration.provider=singleFile \
  -Dkeycloak.migration.file=/tmp/users-export.json \
  -Dkeycloak.migration.usersExportStrategy=REALM_FILE \
  -Dkeycloak.migration.realmName=metatree
```

2. **Copy the export file**:
```bash
docker cp metatree-keycloak:/tmp/users-export.json ./keycloak/users-export.json
```

3. **Import users to new Keycloak 26.x** (after upgrade):
```bash
# Copy users file to new container
docker cp ./keycloak/users-export.json metatree-keycloak:/tmp/users-export.json

# Import users using kcadm
docker compose -f keycloak-docker-compose.yml exec metatree-keycloak \
  /opt/keycloak/bin/kcadm.sh config credentials \
  --server http://localhost:8080 --realm master --user admin --password admin

docker compose -f keycloak-docker-compose.yml exec metatree-keycloak \
  /opt/keycloak/bin/kcadm.sh create partialImport \
  -r metatree -s ifResourceExists=OVERWRITE -o -f /tmp/users-export.json
```

#### Option B: Database Migration (Recommended)

1. **Export database from old Keycloak**:
```bash
# Backup old database
docker compose -f keycloak-docker-compose.yml exec metatree-keycloak-postgres \
  pg_dump -U keycloak keycloak > keycloak-16-backup.sql
```

2. **Stop new containers and restore database**:
```bash
# Stop new setup
docker compose -f keycloak-docker-compose.yml down

# Remove new database volume
docker volume rm docker_metatree-keycloak-postgres-data

# Start only database
docker compose -f keycloak-docker-compose.yml up -d metatree-keycloak-postgres

# Wait for database to be ready
sleep 10

# Restore old database
docker compose -f keycloak-docker-compose.yml exec -T metatree-keycloak-postgres \
  psql -U keycloak -d keycloak < keycloak-16-backup.sql

# Start all services
docker compose -f keycloak-docker-compose.yml up -d
```

#### Option C: Manual User Recreation

If you have a small number of users, you can recreate them manually through the admin console:

1. Access admin console: `http://localhost:8080/admin`
2. Switch to your realm (e.g., "metatree")
3. Go to Users → Add User
4. Recreate each user with their original usernames and details
5. Set temporary passwords and require password reset on first login

### 7. Verification Steps

#### Check container status:
```bash
docker compose -f keycloak-docker-compose.yml ps
```

#### Test HTTP response:
```bash
curl -s -o /dev/null -w "%{http_code}" http://localhost:8080
```
*Expected: 302 (redirect to login page)*

#### Check initialization logs:
```bash
docker compose -f keycloak-docker-compose.yml logs metatree-keycloak-init
```
*Expected: "Realm configuration processed and saved..."*

#### Verify Keycloak startup:
```bash
docker compose -f keycloak-docker-compose.yml logs --tail=20 metatree-keycloak
```
*Look for: "Keycloak 26.2.5 on JVM started" and "Realm 'metatree' imported"*

#### Verify user data migration:
```bash
# Check if users exist in the realm
docker compose -f keycloak-docker-compose.yml exec metatree-keycloak \
  /opt/keycloak/bin/kcadm.sh config credentials \
  --server http://localhost:8080 --realm master --user admin --password admin

docker compose -f keycloak-docker-compose.yml exec metatree-keycloak \
  /opt/keycloak/bin/kcadm.sh get users -r metatree --fields username,email,enabled
```
*Expected: List of your migrated users*

## Key Changes Summary

### Architecture Changes:
- **Runtime**: WildFly → Quarkus (faster startup, lower memory)
- **Commands**: `start-dev` for development, `start` for production
- **Import**: Native `--import-realm` flag replaces startup scripts

### Configuration Changes:
- **Environment Variables**: `DB_*` → `KC_DB_*`
- **Proxy Configuration**: `PROXY_ADDRESS_FORWARDING` → `KC_PROXY: edge`
- **Admin Setup**: `KEYCLOAK_ADMIN` and `KEYCLOAK_ADMIN_PASSWORD`

### Volume Changes:
- **Import Path**: `/opt/jboss/startup-scripts/` → `/opt/keycloak/data/import/`
- **Init Container**: Separate container for realm template processing

## Troubleshooting

### Common Issues:

1. **HTTPS Configuration Error**:
   ```
   Key material not provided to setup HTTPS
   ```
   **Solution**: Use `start-dev` command for development or configure proper SSL certificates

2. **Database Connection Issues**:
   - Verify PostgreSQL container is running
   - Check `KC_DB_URL` format: `jdbc:postgresql://host:port/database`

3. **Realm Import Failed**:
   - Check init container logs
   - Verify realm template file exists and is valid JSON
   - Ensure environment variables are properly substituted

4. **Container Restart Loop**:
   - Remove volumes with `-v` flag and restart
   - Check for conflicting environment variables

5. **Users Not Imported**:
   ```
   Realm imported successfully but no users found
   ```
   **Cause**: Keycloak 26.x `--import-realm` only imports realm configuration, not user data
   
   **Solutions**:
   - Use database migration (Option B above) - **Recommended**
   - Export/import users separately using kcadm (Option A above)
   - Manually recreate users through admin console
   
   **Verification**:
   ```bash
   # Check user count in realm
   docker compose -f keycloak-docker-compose.yml exec metatree-keycloak \
     /opt/keycloak/bin/kcadm.sh config credentials \
     --server http://localhost:8080 --realm master --user admin --password admin
   
   docker compose -f keycloak-docker-compose.yml exec metatree-keycloak \
     /opt/keycloak/bin/kcadm.sh get users -r metatree --format csv --fields username | wc -l
   ```

5. **Cannot Login to Admin Console**:
   ```
   LOGIN_ERROR: user_not_found
   ```
   **Common Causes & Solutions**:
   
   a) **Wrong Username**: 
   - Use `admin` (not `keycloak` or other usernames)
   - Default admin credentials: `admin` / `admin`
   
   b) **Wrong Realm**:
   - Admin access requires **Master realm**, not your custom realm
   - Make sure realm dropdown shows "Master"
   
   c) **Deprecated Environment Variables**:
   - Update from `KEYCLOAK_ADMIN` to `KC_BOOTSTRAP_ADMIN_USERNAME`
   - Update from `KEYCLOAK_ADMIN_PASSWORD` to `KC_BOOTSTRAP_ADMIN_PASSWORD`
   
   **Fix**: Update your `keycloak-docker-compose.yml`:
   ```yaml
   environment:
     # Change from:
     KEYCLOAK_ADMIN: admin
     KEYCLOAK_ADMIN_PASSWORD: admin
     
     # To:
     KC_BOOTSTRAP_ADMIN_USERNAME: admin
     KC_BOOTSTRAP_ADMIN_PASSWORD: admin
   ```
   
   Then restart the container:
   ```bash
   docker compose -f keycloak-docker-compose.yml restart metatree-keycloak
   ```
   
   d) **Browser Cache Issues**:
   - Clear browser cache and cookies
   - Use incognito/private browsing mode
   - Try different browser

   **Verification Steps**:
   ```bash
   # Test admin user exists and can authenticate
   docker compose -f keycloak-docker-compose.yml exec metatree-keycloak \
     /opt/keycloak/bin/kcadm.sh config credentials \
     --server http://localhost:8080 --realm master --user admin --password admin
   
   # List users in master realm
   docker compose -f keycloak-docker-compose.yml exec metatree-keycloak \
     /opt/keycloak/bin/kcadm.sh get users -r master
   
   # List users in custom realm
   docker compose -f keycloak-docker-compose.yml exec metatree-keycloak \
     /opt/keycloak/bin/kcadm.sh get users -r metatree
   ```

### Useful Commands:

```bash
# View all logs
docker compose -f keycloak-docker-compose.yml logs

# Restart specific service
docker compose -f keycloak-docker-compose.yml restart metatree-keycloak

# Execute into container for debugging
docker compose -f keycloak-docker-compose.yml exec metatree-keycloak bash

# View environment variables
docker compose -f keycloak-docker-compose.yml exec metatree-keycloak env | grep KC_
```

## Access Information

After successful upgrade:
- **Admin Console**: `http://localhost:8080` (or your configured domain)
- **Default Admin Credentials**: `admin` / `admin`
- **Realm**: Your existing realm name (e.g., `metatree`)

### Post-Upgrade Login Instructions

**For Admin Console Access:**
1. Navigate to: `http://localhost:8080/`
2. Click "Administration Console"
3. **Important**: Make sure you're logging into the **Master** realm (not your custom realm)
4. Enter credentials:
   - **Username**: `admin`
   - **Password**: `admin`
5. After login, you can switch to your custom realm (e.g., "metatree") from the realm dropdown

**Alternative Direct URL:**
- Direct admin URL: `http://localhost:8080/admin/master/console/`

**Realm Management:**
- **Master Realm**: For administrative tasks, user management, realm configuration
- **Custom Realm** (e.g., metatree): For your application's users and client configurations
- Switch between realms using the dropdown in the top-left corner of the admin console

## Final Verification Checklist

Before considering the upgrade complete, verify:

### ✅ System Health
- [ ] All containers are running: `docker compose -f keycloak-docker-compose.yml ps`
- [ ] Keycloak responds to HTTP requests: `curl -I http://localhost:8080`
- [ ] Database connection is stable: Check logs for connection errors

### ✅ Realm Configuration
- [ ] Realm exists and is accessible through admin console
- [ ] Client configurations are preserved
- [ ] Realm settings match previous configuration
- [ ] Authentication flows are working

### ✅ User Data
- [ ] **Critical**: All users are present in the realm
- [ ] User attributes and roles are preserved
- [ ] Test login with existing user credentials
- [ ] User sessions and tokens work correctly

### ✅ Application Integration
- [ ] Client applications can authenticate
- [ ] Token validation works
- [ ] User permissions and roles function correctly
- [ ] SSO flows work as expected

### ✅ Verification Commands
```bash
# Complete system check
./verify-keycloak-upgrade.sh
```

Create this verification script:
```bash
#!/bin/bash
# File: verify-keycloak-upgrade.sh

echo "=== Keycloak Upgrade Verification ==="

# Container status
echo "\n1. Container Status:"
docker compose -f keycloak-docker-compose.yml ps

# HTTP response
echo "\n2. HTTP Response:"
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8080)
echo "HTTP Status: $HTTP_CODE (Expected: 302)"

# User count
echo "\n3. User Count Check:"
docker compose -f keycloak-docker-compose.yml exec metatree-keycloak \
  /opt/keycloak/bin/kcadm.sh config credentials \
  --server http://localhost:8080 --realm master --user admin --password admin 2>/dev/null

USER_COUNT=$(docker compose -f keycloak-docker-compose.yml exec metatree-keycloak \
  /opt/keycloak/bin/kcadm.sh get users -r metatree --format csv --fields username 2>/dev/null | wc -l)
echo "Users in realm: $((USER_COUNT-1))"  # Subtract header line

# Realm status
echo "\n4. Realm Status:"
docker compose -f keycloak-docker-compose.yml exec metatree-keycloak \
  /opt/keycloak/bin/kcadm.sh get realms/metatree --fields realm,enabled 2>/dev/null

echo "\n=== Verification Complete ==="
```

```bash
chmod +x verify-keycloak-upgrade.sh
```

## Security Recommendations

1. **Change Admin Password**: Update default admin credentials immediately
2. **Review Realm Settings**: Verify all configurations are preserved
3. **Test Applications**: Ensure client applications can still authenticate
4. **SSL Configuration**: Configure proper SSL certificates for production
5. **User Data Backup**: Ensure user data migration was successful before decommissioning old instance

## Rollback Plan

To rollback to Keycloak 16.x:
1. Stop containers: `docker compose -f keycloak-docker-compose.yml down`
2. Restore `.env` file with old image version
3. Restore old `keycloak-docker-compose.yml` configuration
4. Restore database from backup if needed
5. Start containers: `docker compose -f keycloak-docker-compose.yml up -d`

---

**Version**: 1.0  
**Date**: 2025-07-02  
**Tested With**: Keycloak 16.1.1 → 26.2.5  
**Environment**: Docker Compose on AlmaLinux
