#!/usr/bin/env bash

root=$(realpath $(dirname "${0}"))

# check for existence of server keys and pem files, create for localhost if non-existent

if [ -d "${root}/ssl" ] 
then 
    crux=1
    _files=("${root}/ssl/server.pem" "${root}/ssl/server.key")    
    for str in ${_files[@]};do
        if [ ! -f ${str} ]
        then 
            crux=0
        fi
    done
        
    if [ ! -f "${root}/ssl/extra_certs.pem" ]
    then
        if [ ${crux} -eq "1" ]
        then
            echo "Creating extra certs file"
            ln -s ${root}/server.pem ${root}/ssl/extra_certs.pem
        fi
    fi    
else 
    crux=0
fi

if [ ${crux} -eq "0" ] 
then
    echo "Creating folder ssl"
    mkdir -p "${root}/ssl" 

    openssl req -new -newkey rsa:4096 -x509 -sha256 -days 365 -nodes \
         -out ${root}/ssl/server.pem -keyout ${root}/ssl/server.key \
         -subj "/C=NL/ST=Amsterdam/L=NH/O=UvA/CN=localhost" \
         -addext "subjectAltName=DNS:keycloak,DNS:metatree"
    
    ln -sf ${root}/ssl/server.pem ${root}/ssl/extra_certs.pem
    
fi


pushd "${root}"
docker compose -f docker-compose.yml -f keycloak-docker-compose.yml -f ssl-proxy-docker-compose.yml up -d
popd
