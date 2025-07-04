# Keycloak User Export with Hashed Passwords

This guide explains how to export Keycloak users with their hashed passwords by accessing the underlying PostgreSQL database directly.

## Overview

Keycloak's admin CLI (`kcadm.sh`) does not export password hashes for security reasons. To export users with their hashed passwords, we need to query the database directly.

## Prerequisites

- Docker or Podman with Keycloak container running
- PostgreSQL database container for Keycloak
- Access to the database container

## Steps

### 1. Verify Keycloak Setup

First, check if your Keycloak containers are running:

```bash
docker ps | grep keycloak
```

Expected output should show:
- Keycloak application container
- PostgreSQL database container

### 2. Identify Database Schema

Examine the credential table structure:

```bash
docker exec <database-container> psql -U keycloak -d keycloak -c "\d credential"
```

Key columns:
- `secret_data`: Contains the password hash and salt (JSON format)
- `credential_data`: Contains hashing algorithm and iterations (JSON format)
- `user_id`: Links to the user_entity table

### 3. Export Users with Password Hashes

#### Option A: JSON Format

```bash
docker exec <database-container> psql -U keycloak -d keycloak -c "
SELECT json_agg(row_to_json(t)) FROM (
    SELECT 
        u.username, 
        u.email, 
        u.first_name, 
        u.last_name, 
        c.secret_data::json as secret_data, 
        c.credential_data::json as credential_data 
    FROM user_entity u 
    JOIN credential c ON u.id = c.user_id 
    WHERE c.type = 'password' 
    AND u.realm_id = (SELECT id FROM realm WHERE name = '<realm-name>')
) t;" > keycloak_users_with_passwords.json
```

#### Option B: Import-Ready JSON Format

```bash
docker exec <database-container> psql -U keycloak -d keycloak -c "
SELECT json_agg(
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
    'realmRoles', json_build_array('default-roles-<realm-name>'),
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
AND u.realm_id = (SELECT id FROM realm WHERE name = '<realm-name>');
" > keycloak_users_import_ready.json
```

### 4. Using the Provided Script

A convenient script `export_keycloak_users.sh` is provided that automates the export process:

```bash
./export_keycloak_users.sh
```

## Output Format

### JSON Export
Contains an array of user objects with:
- `username`: User's login name
- `email`: User's email address
- `first_name`: User's first name
- `last_name`: User's last name
- `secret_data`: JSON object containing:
  - `value`: Base64-encoded password hash
  - `salt`: Base64-encoded salt
- `credential_data`: JSON object containing:
  - `algorithm`: Hashing algorithm (e.g., "pbkdf2-sha256")
  - `hashIterations`: Number of iterations used

### Import-Ready JSON Export
Contains an array of user objects formatted for Keycloak import with:
- `username`: User's login name
- `email`: User's email address
- `firstName`: User's first name
- `lastName`: User's last name
- `enabled`: Whether the user account is enabled
- `createdTimestamp`: When the user was created (Unix timestamp)
- `credentials`: Array containing password credential object:
  - `type`: "password"
  - `hashedSaltedValue`: Base64-encoded password hash
  - `salt`: Base64-encoded salt
  - `hashIterations`: Number of iterations used
  - `algorithm`: Hashing algorithm
  - `config`: Empty configuration object
  - `temporary`: false
- `realmRoles`: Array of realm roles (includes default role)
- `clientRoles`: Object for client-specific roles
- `groups`: Array of user groups
- `attributes`: Object for user attributes
- `requiredActions`: Array of required actions
- `federatedIdentities`: Array of federated identities
- `socialLinks`: Array of social links

## Password Hash Details

Keycloak typically uses:
- **Algorithm**: PBKDF2-SHA256
- **Iterations**: Usually 100,000 (may vary)
- **Salt**: Random salt for each password
- **Encoding**: Base64 encoding for hash and salt

## Security Considerations

⚠️ **Important Security Notes:**

1. **Handle with Care**: Password hashes are sensitive data
2. **Secure Storage**: Store export files securely
3. **Clean Up**: Delete export files when no longer needed
4. **Access Control**: Limit access to database containers
5. **Audit Trail**: Log who exports password data

## Troubleshooting

### Common Issues

1. **Database Connection Failed**
   - Verify container names
   - Check if containers are running
   - Ensure database credentials are correct

2. **Permission Denied**
   - Ensure you have access to Docker containers
   - Check if the database user has required permissions

3. **Realm Not Found**
   - Verify the realm name is correct
   - List available realms: `docker exec <keycloak-container> /opt/jboss/keycloak/bin/kcadm.sh get realms`

## Alternative Methods

### Using Keycloak Admin CLI (Without Passwords)
```bash
docker exec <keycloak-container> /opt/jboss/keycloak/bin/kcadm.sh get users -r <realm-name>
```

### Full Realm Export
```bash
docker exec <keycloak-container> /opt/jboss/keycloak/bin/standalone.sh \
  -Djboss.socket.binding.port-offset=100 \
  -Dkeycloak.migration.action=export \
  -Dkeycloak.migration.provider=singleFile \
  -Dkeycloak.migration.file=/tmp/realm-export.json \
  -Dkeycloak.migration.usersExportStrategy=REALM_FILE
```

## Script Configuration

The provided script uses these variables (modify as needed):
- `db_container`: Database container name
- `realm_name`: Keycloak realm to export
- `output_json`: JSON output filename
- `output_csv`: CSV output filename

## Example Usage

```bash
# Make script executable
chmod +x export_keycloak_users.sh

# Run the export
./export_keycloak_users.sh

# Verify output files
ls -la keycloak_users_*.json keycloak_users_*.csv
```

## Conclusion

This method provides a complete export of Keycloak users with their hashed passwords, suitable for:
- Data migration
- Backup purposes
- Security auditing
- Password hash analysis

Remember to handle the exported data securely and in compliance with your organization's security policies.
