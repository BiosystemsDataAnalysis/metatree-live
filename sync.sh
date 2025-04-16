#!/usr/bin/env bash

# setting up metatree for running on local host, use this script only if you have original distribution of the metatree source

SOURCE=../metatree/docker
rm -rf docker
mkdir docker

# copy the docker compose configuration files
cp $SOURCE/docker-compose.yml docker 
cp $SOURCE/keycloak-docker-compose.yml docker 
cp $SOURCE/ssl-proxy-docker-compose.yml docker 
cp -R $SOURCE/keycloak docker
cp $SOURCE/start_all.sh docker
cp $SOURCE/stop_all.sh docker
cp $SOURCE/.env docker
cp -L $SOURCE/views.yaml docker
cp -L $SOURCE/vocabulary.ttl docker
cp $SOURCE/README_live.md docker/README.md

cp $SOURCE/.env docker/.env

# copy the database initialization scripts
rm -rf init
mkdir init

cp ../metatree/init_db/extra_plant_species.ttl init
cp ../metatree/init_db/{plant_species.ttl,other_species.ttl} init
cp ../metatree/init_db/{growth_facilities.ttl,plant_growth_medium.ttl} init
cp ../metatree/init_db/{plant_states_stages.ttl,ploidy.ttl,treatments.ttl} init
cp ../metatree/init_db/{apparatus.ttl,assay_types.ttl} init
cp ../metatree/init_db/{initialize_db.py,Metatree_functions_common.py} init

cp ../metatree/init_db/.env_local init/.env
# copy the demonstration files
rm -rf demo_files
rm -rf uploading_data
mkdir uploading_data
# copy the example input excel file
cp ../metatree/demo-files/PPH_example.xlsx uploading_data
cp ../metatree/distro/Uploading_Metadata.pdf uploading_data


root=$(realpath $(dirname "${0}"))
# copy the version number from the VERSION file
echo $(awk '$1=="\"version\":" {gsub(/"/, "");gsub(/,/, ""); print $2}'  ${root}/../metatree/projects/mercury/package.json) > ${root}/../VERSION
VERSION=$(cat "${root}/../VERSION")

# replace the version in the environment file
sed -i "s/^VERSION=.*/VERSION=${VERSION}/" docker/.env
# replace the keycloak secret in the environment file
sed -i 's/^KEYCLOAK_CLIENT_SECRET=.*/KEYCLOAK_CLIENT_SECRET=********/' docker/.env
sed -i 's/^KEYCLOAK_CLIENT_SECRET=.*/KEYCLOAK_CLIENT_SECRET=********/' init/.env