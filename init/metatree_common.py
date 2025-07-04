#%%
import requests
import logging
from xml.etree.ElementTree import fromstring
from typing import Dict
import re
import json
import time

from requests.models import Response

logging.basicConfig(level=logging.ERROR, format='%(asctime)s [%(levelname)s] %(message)s')
log = logging.getLogger('logs')


import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

session = None



config_file = ""
config = None
METATREE_USER, METATREE_PASSWORD,KEYCLOAK_REALM = "","",""
KEYCLOAK_CLIENT_ID,KEYCLOAK_CLIENT_SECRET,KEYCLOAK_SERVER_URL= "","",""
VERIFY=False
server_url:str=""
from dotenv import dotenv_values
from os.path import expandvars

# make endpoint dictionary for faster access
dict_endpoints = {}


def importConfiguration(fileName):
    global config_file,config
    global METATREE_USER, METATREE_PASSWORD,KEYCLOAK_REALM
    global KEYCLOAK_CLIENT_ID,KEYCLOAK_CLIENT_SECRET,KEYCLOAK_SERVER_URL,server_url
    config_file = fileName
    # Load .env file and expand environment variables
    raw_config = dotenv_values(config_file)

    # Expand environment variables in the configuration values
    config = {k: expandvars(v) if (isinstance(v, str) and v.startswith('$')) else v for k, v in raw_config.items()}

    server_url = config['METATREE_URL']

    METATREE_USER = config['METATREE_USER']
    METATREE_PASSWORD = config['METATREE_PASSWORD']
    KEYCLOAK_REALM = config['KEYCLOAK_REALM']
    KEYCLOAK_CLIENT_ID = config['KEYCLOAK_CLIENT_ID']
    KEYCLOAK_CLIENT_SECRET = config['KEYCLOAK_CLIENT_SECRET']
    KEYCLOAK_SERVER_URL = config['KEYCLOAK_SERVER_URL']


    print("imported settings from {0}".format(config_file))


def getSession():
    global session
    if session is None:
        session = requests.Session()
    return session

def isNaN(string):
    return string != string

tfdict = {0:'false',1:'true'}

def dict_to_string(adict):
    rstr = ""
    for kx in adict:
        rstr += "{0} {1};\n".format(kx,adict[kx])
    
    rstr = rstr.strip(';\n')+" .\n"
    return rstr


def add_info(field:str=None,value=None,literal=True):
    dict_ = {}
    if literal:
        dict_[field]="\"{0}\"".format(value)
    else:
        dict_[field]=value

    return dict_
    

METADATA_ENDPOINT='/api/metadata/'
WEBDAV_ENDPOINT='/api/webdav/'



def fetch_access_token() -> str:
    """
    Obtain access token from Keycloak
    :return: the access token as string.
    """
    s = int(round(time.time()))

    keycloak_url: str = KEYCLOAK_SERVER_URL
    realm: str = KEYCLOAK_REALM
    client_id: str = KEYCLOAK_CLIENT_ID
    client_secret: str = KEYCLOAK_CLIENT_SECRET
    username: str = METATREE_USER 
    password: str = METATREE_PASSWORD

    params = {
        'client_id': client_id,
        'client_secret': client_secret,
        'username': username,
        'password': password,
        'grant_type': 'password'
    }

    headers = {
        'Content-type': 'application/x-www-form-urlencoded',
        'Accept': 'application/json'
    }
    log.info(f'Fetch authentication token from {keycloak_url}/auth/realms/{realm}/protocol/openid-connect/token ...')
    response = requests.post(f'{keycloak_url}/auth/realms/{realm}/protocol/openid-connect/token',
                             data=params,
                             headers=headers,verify=VERIFY)
    if not response.ok:
        log.error('Error fetching token!')
        log.error(f'{response.status_code} {response.reason} {response.json()}')
        raise Exception('Error fetching token.')
    data = response.json()
    token = data['access_token']
    log.info(f"Token obtained successfully. It will expire in {data['expires_in']} seconds.")
    
    texp = s + data['expires_in']
    return token, texp

texp = -1
token = ""
def auth():
    global texp, token
    s = int(round(time.time()))
    if s >= texp:    
        token, texp = fetch_access_token()        
    return f'Bearer {token}'

def exists(path):
    """ Check if a path exists
    """
    headers = {
        'Depth': '0',
        'Authorization': auth()
    }
    session = getSession()
    req = requests.Request('PROPFIND', f'{server_url}/api/webdav/{path}/', headers=headers, cookies=session.cookies)
    response: Response = session.send(req.prepare(),verify=VERIFY)
    return response.ok


# def getProperties(iri:str):
#     headers = {
#         'Accept' : ' application/ld+json' \
#         ''
#     }
#     curl -G -H "Accept: application/ld+json" \
# --data-urlencode "subject=a" \
# --data-urlencode "predicate=b" \
# --data-urlencode "object=c" \
# --data-urlencode "withValueProperties=true" \
# "http://localhost:8080/api/metadata/"

def ls(path: str):
    """ List contents of path
    """

    data = "<propfind><allprop /></propfind>"
    headers = {
        'Depth': '0',
        'Authorization': auth()
    }
    session = getSession()
    req = requests.Request('PROPFIND', f'{server_url}/api/webdav/{path}', data=data,headers=headers, cookies=session.cookies)
    response: Response = session.send(req.prepare(),verify=VERIFY)
    if not response.ok:
        raise Exception(f"Error fetching directory '{path}': {response.status_code} {response.reason}")
    tree = fromstring(response.content.decode())
    for item in tree.findall('{DAV:}response'):
        print(item.find('{DAV:}href').text)
    return response

def mkdir(path: str, entity_type: str=None):
    # Create directory    
    headers={'Entity-Type': f'https://sils.uva.nl/ontology#{entity_type}', 'Authorization': auth()}
    session = getSession()
    try:
        req = requests.Request('MKCOL', f'{server_url}{WEBDAV_ENDPOINT}{path}', headers=headers, cookies=session.cookies)
        # response: Response = requests.Session().send(req.prepare(),verify=False)
        response = requests.Session().send(req.prepare(),verify=VERIFY)
    except:
        if not response.ok:
            log.error(f'{response.status_code} {response.reason} {response.json()}')        
            #raise Exception(f"Error creating directory '{path}': {response.status_code} {response.reason}")



def getProperties(path:str):
    """ List contents of path
    """
    data = "<propfind><allprop /></propfind>"
    headers = {
        'Depth': '0',
        'Authorization': auth()
    }
    session = getSession()
    req = requests.Request('PROPFIND', f'{server_url}{WEBDAV_ENDPOINT}{path}', data=data,headers=headers, cookies=session.cookies)
    response: Response = session.send(req.prepare(),verify=VERIFY)
    if not response.ok:
        raise Exception(f"Error fetching directory '{path}': {response.status_code} {response.reason}")
        
    return response.text

def getIRIs(path:str):
    """ List contents of path
    """
    data = "<propfind><allprop /></propfind>"
    headers = {
        'Depth': '0',
        'Authorization': auth()
    }
    session = getSession()
    req = requests.Request('PROPFIND', f'{server_url}{WEBDAV_ENDPOINT}{path}', data=data,headers=headers, cookies=session.cookies)
    response: Response = session.send(req.prepare(),verify=VERIFY)
    if not response.ok:
        return None
        #raise Exception(f"Error fetching directory '{path}': {response.status_code} {response.reason}")
    
    rtext = response.text
    pattern = re.compile(r"<ns1[^<>]+>")
    patterns = pattern.findall(rtext)

    links = {}
    for pat in patterns:
        pat_end = pat.replace("<","</")
        links[pat] = re.search(f'{pat}(.*?){pat_end}',rtext).group(1)
        
    return links



def upload_metadata(filename,verbose=False):
    metatree_url: str = config['METATREE_URL']
    headers={'Content-type': 'text/turtle',
             'Authorization': auth()}

    with open(filename) as testdata:
        response = requests.put(f"{metatree_url}{METADATA_ENDPOINT}", data=testdata.read(), headers=headers,verify=VERIFY)

    if not response.ok:
        log.error('Error uploading data!')
        log.error(f'{response.status_code} {response.reason} {response.json()}')
        raise Exception('Error uploading data.')
    if verbose:
        print(f'Response code: {response.status_code}')



def upload_files(path: str, files: Dict[str, any]):
    # Upload files
    response =  getSession().post(f'{server_url}/api/webdav/{path}/',
            headers={'Authorization': auth()},
            data={'action': 'upload_files'},
            files=files,verify=VERIFY)
    if not response.ok:
        raise Exception(f"Error uploading files into '{path}': {response.status_code} {response.reason}")

def _load_block(data:str):
    blocks = []
    st = ""
    pf = ""
    for line in data:        
        if line.startswith('@prefix'):
           pf = pf+line
        elif (line.startswith('#')):
            continue                
        elif line.strip():
            st = st + line
            if line.strip().endswith('.'):
                #print(st)
                blocks.append(st)
                st = ""
    blocks = [pf] + blocks
    return blocks   


def put_meta_data(fileName:str):
    with open(fileName) as testdata:
        blks = _load_block(testdata)
        for blk in blks[1:]:
            #print(blks[0]+blk)            
            response = getSession().put(f"{server_url}/api/metadata/",
                data=blks[0]+blk,
                headers={
                    'Authorization': auth(),
                    'Content-type': 'text/turtle'
                },
                verify=VERIFY)
            if not response.ok:
                log.error(f'{response.status_code} {response.reason} {response.json()}')
                raise Exception(f"Error uploading metadata block: {blk} {response.status_code} {response.reason}")
    return response


def patch_meta_data(fileName:str,verbose=False):
    with open(fileName) as testdata:
        blks = _load_block(testdata)
        for blk in blks[1:]:
            if verbose:
                print(blk)
            response = getSession().patch(f"{server_url}/api/metadata/",
                data=blks[0]+blk, # testdata.read(),
                headers={
                    'Authorization': auth(),
                    'Content-type': 'text/turtle'
                },
                verify=VERIFY)
            if not response.ok:
                log.error(f'{response.status_code} {response.reason} {response.json()}')
                raise Exception(f"Error uploading metadata: {blk} {response.status_code} {response.reason}")


def delete_meta_data(fileName:str):
    with open(fileName) as testdata:       
        response = getSession().delete(f"{server_url}/api/metadata/",
            data=testdata.read(),
            headers={
                'Authorization': auth(),
                'Content-type': 'text/turtle'
            },verify=VERIFY)
        if not response.ok:
            raise Exception(f"Error uploading metadata: {response.status_code} {response.reason}")

def patch_bulk_meta_data(fileName:str): 
    with open(fileName) as testdata:
        response = getSession().patch(f"{server_url}/api/metadata/",
                data=testdata.read(),
                headers={
                    'Authorization': auth(),
                    'Content-type': 'text/turtle'
                },
                verify=VERIFY)
        if not response.ok:
            log.error(f'{response.status_code} {response.reason} {response.json()}')
            raise Exception(f"Error uploading metadata: {response.status_code} {response.reason}")

def upload_iri_metadata(iri,data,output_file=None,verbose=False):
    
    # mydata = f'''
    # @prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .
    # @prefix fs: <https://fairspace.nl/ontology#> .  
    # @prefix example: <https://example.com/ontology#> . 
    # @prefix sils: <https://sils.uva.nl/ontology#> . 
          
    # <{iri}>{data} 
    # '''
    mydata = \
f'''@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .
@prefix fs: <https://metatree.nl/ontology#> .      
@prefix sils: <https://sils.uva.nl/ontology#> . 
@prefix uniprot: <https://uniprot.org/taxonomy/> .
          
<{iri}>{data} 
'''
    if verbose:
        print(mydata)

    if output_file:
        print(mydata,file=output_file)
        return

    headers={'Content-type': 'text/turtle',
       'Authorization': auth()}

    respons = requests.patch(f"{server_url}{METADATA_ENDPOINT}", data=mydata, headers=headers,verify=VERIFY)
    if not respons.ok:
        log.error(f'{respons.status_code} {respons.reason} {respons.json()}')


def csv_upload(path:str=None,filename:str=None,verbose=False):
    entity_path=path    
    headers={'Authorization': auth()}
    data = {
        'action': 'upload_metadata',
    }
    files = {
        'file': open(filename, 'rb'),
    }

    if verbose:
        print(f"{server_url}{WEBDAV_ENDPOINT}{entity_path}")

    response = requests.request('POST', f"{server_url}{WEBDAV_ENDPOINT}{entity_path}", headers=headers, data=data, files=files,verify=VERIFY)

    if not response.ok:
        log.error('Error uploading data!')
        log.error(f'{response.status_code} {response.reason} {response.content.decode()}')
        
        return response
        #raise Exception('Error uploading data.')
    if verbose:
        print(f'Response code: {response.status_code}. {entity_path} updated.')



def getEndpoint(endpoint:str=None,resourceType:str=None, verbose=False):
        
    if (endpoint is None) or (resourceType is None):
        return None

    if endpoint in dict_endpoints:
        return dict_endpoints[endpoint]

    SEARCH_ENDPOINT = "/api/search/lookup"
    headers={'Authorization': auth(),
             'Content-Type': 'application/json',
             'Accept': 'application/json'}

    data = '{{ "query": "{0}","resourceType": "{1}" }}'.format(endpoint,resourceType)

    if verbose:
        print("looking for definition of {0} as {1}".format(endpoint,resourceType))

    response = requests.request('POST', f"{server_url}{SEARCH_ENDPOINT}", headers=headers, data=data,verify=VERIFY)
    if not response.ok:
        log.error('Error looking for endpoint {0}'.format(endpoint))
        log.error(f'{response.status_code} {response.reason} {response.content.decode()}')
    
    value = json.loads(response.content.decode())
    if len(value['results'])>1:
        print('not a unique query, only first hit is returned')
    
    value = value['results'][0]['id']
    value_id = value.replace('#','/').split('/')[-1]
    value_realm = value.replace("http://","https://").split('https://')[1].split('.')[0]
    return_val = '{0}:{1}'.format(value_realm,value_id)    
    dict_endpoints[endpoint]=return_val
    
    return return_val


