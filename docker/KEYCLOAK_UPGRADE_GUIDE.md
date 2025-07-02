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

### 6. Verification Steps

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

## Security Recommendations

1. **Change Admin Password**: Update default admin credentials immediately
2. **Review Realm Settings**: Verify all configurations are preserved
3. **Test Applications**: Ensure client applications can still authenticate
4. **SSL Configuration**: Configure proper SSL certificates for production

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
