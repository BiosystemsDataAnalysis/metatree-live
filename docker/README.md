# Configure metatree for running on localhost with docker and no proxy

This guide will walk you through the complete setup process for running the metatree application locally using Docker containers without a reverse proxy.

## Prerequisites

- Docker and Docker Compose installed on your system
- Root/sudo privileges to modify the hosts file
- Python 3 with pip for database initialization

## Step 1: Adjust hosts file

Before starting the containers, you need to add entries to your system's hosts file to allow access to the metatree and keycloak services via their hostnames:

```bash
sudo bash -c 'cat >> /etc/hosts <<EOF
127.0.0.1 metatree keycloak
EOF'
```

This enables you to access the services at `https://metatree` and `https://keycloak` instead of using IP addresses.

## Step 2: Start Docker containers

Navigate to the docker directory and run the startup script:

```bash
cd docker
./start_all.sh
```

This script will:
- Create self-signed SSL certificates for nginx
- Download required Docker images
- Start all containers (metatree, keycloak, database, nginx)

## Step 3: Initialize Keycloak

After the containers start, you need to configure Keycloak:

1. **Access Keycloak**: Navigate to `https://keycloak` in your browser
2. **Accept SSL warning**: Since we're using self-signed certificates, accept the security warning
3. **Login**: Use the default credentials:
   - Username: `keycloak`
   - Password: `keycloak`

## Step 4: Update .env file to reflect changes in keycloak

1. **Navigate to Clients**: In Keycloak admin console, go to Clients → metatree-client
2. **Regenerate Secret**: Go to the Credentials tab and click "Regenerate Secret"
3. **Copy the new secret**: Save the generated secret
4. **Update .env file**: Replace the `KEYCLOAK_CLIENT_SECRET` value in the docker/.env file:

```bash
sed -i "s/^KEYCLOAK_CLIENT_SECRET=.*/KEYCLOAK_CLIENT_SECRET=your_new_secret/" .env
```

## Step 5: Configure user access (Optional)

To limit write access to specific folders for users:

1. Go to Users → View all users in Keycloak
2. Select a user (e.g., "organisation-admin")
3. Go to Attributes tab
4. Add attribute "accessRoot" with desired folder paths:
   - For global access: `/`
   - For specific folders: `/test` or `/test,/test2`

## Step 6: Restart Docker containers

Apply the configuration changes by restarting the containers:

```bash
./stop_all.sh
./start_all.sh
```

## Step 7: Initialize database

Navigate to the init directory and run the database initialization script:

```bash
cd ../init
python3 initialize_db.py --env ./env
```

**Note**: Ensure you have the required Python packages installed:
```bash
pip install typed-argument-parser python-dotenv
```

This script populates the database with ontology options according to the schema defined in the vocabulary file.

## Step 8: Run metatree

Once all steps are complete, you can access the metatree application:

1. **Access metatree**: Navigate to `https://metatree` in your browser
2. **Accept SSL warning**: Accept the self-signed certificate warning
3. **Login**: Use the default credentials:
   - Username: `organisation-admin`
   - Password: `fairspace123`

## Troubleshooting

- If containers fail to start, check Docker logs: `docker-compose logs`
- Ensure ports 80, 443, 8080 are not in use by other services
- Verify the hosts file entries are correct
- Make sure the .env file has the updated Keycloak client secret

## Next Steps

- Upload sample data from the `uploading_data` directory
- Create departments and organize your data structure
- Refer to the main README.md for detailed configuration options
