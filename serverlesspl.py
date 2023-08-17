import requests
import msal
import getopt
import json
import sys
import os
import atexit
import pprint
import string
import random

# parameters
    # login file
    # account id
    # workspace id
    # ncc id
    # resource id
    # resource type
    # command
    # azure region
    # NCC name

# constants 
ACCOUNT_URL = "https://accounts.azuredatabricks.net/api/2.0/accounts/"


def get_bearer_token_msal(credfile, login_type):
    authority_host_url = "https://login.microsoftonline.com/"
    # the Application ID of  AzureDatabricks
    scopes = [ '2ff814a6-3304-4ab8-85cb-cd0e6f879c1d/.default' ]

    with open(credfile) as json_data:
        user_parameters = json.load(json_data)
        json_data.close()

    authority_url = authority_host_url + user_parameters['tenant']


    cache = msal.SerializableTokenCache()

    if os.path.exists("my_cache.bin"):
        cache.deserialize(open("my_cache.bin", "r").read())
    atexit.register(lambda:
        open("my_cache.bin", "w").write(cache.serialize())
        # Hint: The following optional line persists only when state changed
        if cache.has_state_changed else None
        )

    # print(cache.serialize())

    if login_type == "user":
        app = msal.PublicClientApplication(client_id=user_parameters['client_id'], client_credential=None, authority=authority_url, token_cache=cache)
        result = None
        # Get an account
        accounts = app.get_accounts(username=user_parameters['username'])
        if accounts :
            account = accounts[0]  # Simulate user selection
        else :
            account=None
        
        # result = None
        result = app.acquire_token_silent(scopes=scopes, account=account)

        if not result:
            print("user not silent\n")
            result = app.acquire_token_by_username_password(username = user_parameters['username'], password = user_parameters['password'], scopes=scopes)

    if login_type == "sp":
        app = msal.ConfidentialClientApplication(client_id=user_parameters['client_id'], authority=authority_url, client_credential=user_parameters['client_secret'])

        result = app.acquire_token_silent(scopes=scopes, account=None)

        if not result:
            print("sp not silent\n")
            result = app.acquire_token_for_client(scopes)

    if login_type == "device":
        app = msal.PublicClientApplication(client_id=user_parameters['client_id'], client_credential=None, authority=authority_url, token_cache=cache)
        result = None
        # Get an account
        accounts = None
        for key in user_parameters :
            if key == "username" :
                accounts = app.get_accounts(username=user_parameters['username'])
        if accounts :
            account = accounts[0]  # Simulate user selection
        else :
            account=None
            print("cache miss")
       
        result = app.acquire_token_silent(scopes=scopes, account=account)

        if not result:
            print("user not silent\n")
            flow = app.initiate_device_flow(scopes=scopes)
            print(flow['message'])
            result = app.acquire_token_by_device_flow(flow)


    if "access_token" in result:
        AzureAccessToken = result["access_token"]
        return(AzureAccessToken)
    else :
        return(0)


def create_nas(bearertoken, accountId, nccname, azregion) :

    url = ACCOUNT_URL+accountId+"/network-connectivity-configs"

    payload = json.dumps({
        "name": f"{nccname}",
        "region": f"{azregion}"
    })
    headers = {
        'Content-Type': 'application/json',
        'Authorization': 'Bearer '+bearertoken
    }
    try : 
        response = requests.request("POST", url, headers=headers, data=payload)
        response.raise_for_status()
    except requests.exceptions.HTTPError as errh:
        print("HTTP Error")
        print(errh.args[0]) 

    return(response.json())

def update_workspace (bearertoken, accountId, nccId, workspaceId) : 
    url = ACCOUNT_URL+accountId+"/workspaces/"+workspaceId

    payload = json.dumps({
    "network_connectivity_config_id": f"{nccId}"
    })
    headers = {
    'Content-Type': 'application/json',
    'Authorization': 'Bearer '+bearertoken
    }
    try : 
        response = requests.request("PATCH", url, headers=headers, data=payload)
        response.raise_for_status()
    except requests.exceptions.HTTPError as errh:
        print("HTTP Error")
        print(errh.args[0]) 

    return(response.json())

def create_pe (bearertoken, accountId, nccId, resourceID, resourceType) : 
    url = ACCOUNT_URL+accountId+"/network-connectivity-configs/"+nccId+"/private-endpoint-rules"

    payload = json.dumps({
    "resource_id": f"{resourceID}",
    "group_id": f"{resourceType}"
    })
    headers = {
    'Content-Type': 'application/json',
    'Authorization': 'Bearer '+bearertoken
    }

    try : 
        response = requests.request("POST", url, headers=headers, data=payload)
        response.raise_for_status()
    except requests.exceptions.HTTPError as errh:
        print("HTTP Error")
        print(errh.args[0]) 

    return(response.json())

def get_ncc_list (bearertoken, accountId) :
    url = ACCOUNT_URL+accountId+"/network-connectivity-configs"
    payload = {}
    headers = {
        'Content-Type': 'application/json',
        'Authorization': 'Bearer '+bearertoken
    }

    try : 
        response = requests.request("GET", url, headers=headers, data=payload)
        response.raise_for_status()
    except requests.exceptions.HTTPError as errh:
        print("HTTP Error")
        print(errh.args[0]) 

    return(response.json())

def get_ncc (bearertoken, accountId, nccId) : 
    url = ACCOUNT_URL+accountId+"/network-connectivity-configs/"+nccId

    payload = {}
    headers = {
        'Content-Type': 'application/json',
        'Authorization': 'Bearer '+bearertoken
    }

    try : 
        response = requests.request("GET", url, headers=headers, data=payload)
        response.raise_for_status()
    except requests.exceptions.HTTPError as errh:
        print("HTTP Error")
        print(errh.args[0]) 

    return(response.json())

def get_workspace_ncc (bearertoken, accountId, workspaceId) :
    url = ACCOUNT_URL+accountId+"/workspaces/"+workspaceId+"/network-connectivity-configs"

    payload = {}
    headers = {
       'Authorization': 'Bearer '+bearertoken
    }

    try : 
        response = requests.request("GET", url, headers=headers, data=payload)
        response.raise_for_status()
    except requests.exceptions.HTTPError as errh:
        print("HTTP Error")
        print(errh.args[0]) 

    return(response.json())

def get_workspace(bearertoken, accountId, workspaceId) : 
    url = ACCOUNT_URL+accountId+"/workspaces/"+workspaceId
    
    payload = {}
    headers = {
       'Authorization': 'Bearer '+bearertoken
    }

    try : 
        response = requests.request("GET", url, headers=headers, data=payload)
        response.raise_for_status()
    except requests.exceptions.HTTPError as errh:
        print("HTTP Error")
        print(errh.args[0]) 

    return(response.json())

def list_workspaces(bearertoken, accountId) : 
    url = ACCOUNT_URL+accountId+"/workspaces"
    
    payload = {}
    headers = {
        'Content-Type': 'application/json',
       'Authorization': 'Bearer '+bearertoken
    }

    try :
        response = requests.request("GET", url, headers=headers, data=payload)
        response.raise_for_status()
    except requests.exceptions.HTTPError as errh:
        print("HTTP Error")
        print(errh.args[0]) 

    return(response.text)

def delete_ncc (bearertoken, accountId, nccId) : 
    url = ACCOUNT_URL+accountId+"/network-connectivity-configs/"+nccId

    payload = {}
    headers = {
        'Authorization': 'Bearer '+bearertoken
    }

    try : 
        response = requests.request("DELETE", url, headers=headers, data=payload)
        response.raise_for_status()
    except requests.exceptions.HTTPError as errh:
        print("HTTP Error")
        print(errh.args[0]) 

    print(response.text)

def usage() : 
    class color:
        PURPLE = '\033[95m'
        CYAN = '\033[96m'
        DARKCYAN = '\033[36m'
        BLUE = '\033[94m'
        GREEN = '\033[92m'
        YELLOW = '\033[93m'
        RED = '\033[91m'
        BOLD = '\033[1m'
        UNDERLINE = '\033[4m'
        END = '\033[0m'

    print(color.BOLD+'''ServerlessPL tool usage: 
          

options : '''+color.END+'''
    -h or --help : this page
    --logout : Removes cached login and refresh token for use 
          and device (see README)
    -v : verbose output - expands some command outputs from lists to 
          whole json docs
    -C or --command : See commands below - each command performs a distict
          action for serverless private link
    -w or --workspaceId : The worksace ID 
    -a or --accountId : The Account ID from UC account console 
    -n or --nccId : THe ID of the NCC (network config) object
    -l or --login_type : Default service principal. Choose between
          Device code login (device), Username / Passowrd (user),
          or Service Principal (sp)  See README
    -f or --config : Default credential.json, JSON file for holding user / sp
          credentials (See README) 
    --nccname : Unique name for the NCC object 
    --region :  Azure region, examlpe: eastus, westus, westus2
    -r or --resourceId : The resource ID of the storage account/sql db you
          wish to create a private end point to
    -t or --type : The type of resource, dfs or blob or SqlServer
'''+color.BOLD+'''commands : (use with -C or --command) '''+color.END+'''
    '''+color.BOLD+'''get_workspace_ncc : '''+color.END+''' Gets the NCC ID for a given workspace
    '''+color.BOLD+'''ensure_workspace_ncc : '''+color.END+''' Gets the NCC ID for a given workspace
        if the workspave does not have an NCC, create and attach a new NCC. 
        Can be used for stable endpoints if no private endpoint is desired.
    '''+color.BOLD+'''attach_workspace  : '''+color.END+''' Attach a NCC (network config) to a workspace
    '''+color.BOLD+'''get_stable_ep : '''+color.END+''' Gets the stable service endpoints for a given workspace
          to be used for stoarage firewall
    '''+color.BOLD+'''get_ncc : '''+color.END+'''Gets details about a NCC, also used to "lock in" the PE info
          to a NCC after the PE is approved approved.
    '''+color.BOLD+'''create_ncc : '''+color.END+''' Creates a blank NCC (network config) object and
          returns its NCC id
    '''+color.BOLD+'''create_pe : '''+color.END+''' Creates a new private endpoint in a NCC (network config) object
    '''+color.BOLD+'''get_ncc_list : '''+color.END+''' Gets a list of NCCs in the account (tenant)
    '''+color.BOLD+'''get_workspace : '''+color.END+''' Gets details about a given workspace including
          the NCC id if its attached
    '''+color.BOLD+'''delete_ncc : '''+color.END+''' deletes a NCC (network config) object (Note: may not be
          able to delete NCCs with active private endpoints)
    '''+color.BOLD+'''create_serverless_private_link : '''+color.END+''' '''+color.UNDERLINE+'''Main command to use'''+color.END+'''. Creates a private endpoint
          for a storage or SQL and ataches to, or updates a workspace. If you
          include an existing NCC id it will update that NCC and add it to the
          workspace or replace an existing NCC.
          ''')

def logout() :
    filename = "my_cache.bin"
    try:
        os.remove(filename)
    except OSError:
        pass


def main():
    login_type = "sp"  # sp, device or user
    config_file = "credential.json"
    command = None
    account_id = None
    ncc_id = None
    workspace = None
    regionname = None
    ncname = None
    resource_id = None
    resource_type = None
    class color:
        PURPLE = '\033[95m'
        CYAN = '\033[96m'
        DARKCYAN = '\033[36m'
        BLUE = '\033[94m'
        GREEN = '\033[92m'
        YELLOW = '\033[93m'
        RED = '\033[91m'
        BOLD = '\033[1m'
        UNDERLINE = '\033[4m'
        END = '\033[0m'

    try:
        opts, args = getopt.getopt(sys.argv[1:], "hC:r:t:w:a:n:r:t:f:l:v", ["help", "command=", "resourceId=", "type=", "workspaceId=", "login_type=", "config=", "nccname=", "region=","logout"])
    except getopt.GetoptError as err:
        # print help information and exit:
        print(err)  # will print something like "option -a not recognized"
        usage()
        sys.exit(2)
    output = None
    verbose = False
    for o, a in opts:
        if o == "-v":
            verbose = True
        elif o in ("-h", "--help"):
            usage()
            sys.exit()
        elif o == "--logout":
            logout() # removes msal cache forced new login on nest run
            sys.exit()
        elif o == "--nccname":
            ncname = a
        elif o == "--region":
            regionname = a
        elif o in ("-C", "--command"):
            command = a
        elif o in ("-v"):
            verbose = True
        elif o in ("-w", "--workspaceId"):
            workspace = a
        elif o in ("-a", "--accountId"):
            account_id = a
        elif o in ("-n", "--nccId"):
            ncc_id = a
        elif o in ("-l","--login_type"):
            login_type = a
        elif o in ("-f","--config"):
            config_file = a
        elif o in ("-r","--resourceId"):
            resource_id = a
        elif o in ("-t","--type"):
            resource_type = a
        else:
            assert False, "unhandled option"
            sys.exit()
    
    if command is not None :
        bearer = get_bearer_token_msal(config_file, login_type)
    if command == "get_workspace_ncc" :
        if account_id is None or workspace is None : 
            print("Missing Parameters : ")
            print(sys.argv[0],"-C",command,"-a|--accountId ACCOUNT-ID -w|--workspaceId WORKSPACE-ID [-v]")
            sys.exit()
        ncc_body = get_workspace_ncc(bearer, account_id, workspace)
        for ncc_json in ncc_body : 
            if verbose :
                pprint.pprint(ncc_json)
            else :
                print("NCC ID : ",ncc_json["network_connectivity_config_id"])
    elif command == "attach_workspace" : 
        if account_id is None or ncc_id is None or workspace is None : 
            print("Missing Parameters : ")
            print(sys.argv[0],"-C",command,"-a|--accountId ACCOUNT-ID -n|--nccId NCC-ID -w|--workspace WORKSPACE-ID")
            sys.exit()
        output = update_workspace (bearer, account_id, ncc_id, workspace) 
        print(output)
    elif command == "get_stable_ep" :
        if account_id is None or workspace is None : 
            print("Missing Parameters : ")
            print(sys.argv[0],"-C",command,"-a|--accountId ACCOUNT-ID -w|--workspaceId WORKSPACE-ID [-v]")
            sys.exit()
        output = get_workspace_ncc(bearer, account_id, workspace)
        if verbose : 
            pprint.pprint(output)
        else :
            for ncc_json in output : 
                subnets = ncc_json["egress_config"]["default_rules"]["azure_service_endpoint_rule"]["subnets"]
                for sep in subnets :
                    print(sep)
    elif command == "get_ncc" :
        if account_id is None or ncc_id is None : 
            print("Missing Parameters : ")
            print(sys.argv[0],"-C",command,"-a|--accountId ACCOUNT-ID -n|--nccId NCC-ID [-v]")
            sys.exit()
        output = get_ncc(bearer, account_id, ncc_id)
        if verbose : 
            pprint.pprint(output)
        else :
            print("Name :",output["name"])
            print("Region :",output["region"])
            print("\nservice (stable) endpoints\n------------------------")
            subnets = output["egress_config"]["default_rules"]["azure_service_endpoint_rule"]["subnets"]
            for sep in subnets :
                print(sep)
            print("\nprivate endpoints\n------------------------")
            has_ep = False
            for tr in output["egress_config"] :
                if tr == "target_rules" :
                    has_ep = True
                    for ep in output["egress_config"]["target_rules"]["azure_private_endpoint_rules"] : 
                        for key in ep :
                            print(key,":",ep[key])
                        print("-----\n")
            if not has_ep : 
                print("None")
    elif command == "create_ncc" : # todo 
        if account_id is None or account_id is None or ncname is None or regionname is None: 
            print("Missing Parameters : ")
            print(sys.argv[0],"-C",command,"-a|--accountId ACCOUNT-ID --nccname NAME-OF-NCC --region AZURE-REGION")
            sys.exit()
        output = create_nas(bearer,account_id, ncname,regionname)
        ncc_id = output["network_connectivity_config_id"]
        print("NCC id",ncc_id,"\n\n",output)
    elif command == "create_pe" : 
        if account_id is None or workspace is None or ncc_id is None or resource_id is None or resource_type is None : 
            print("Missing Parameters : ")
            print(sys.argv[0],"-C",command,"-a|--accountId ACCOUNT-ID -n|--nccId NCC-ID -r|--resourceId RESOURCE-ID -t|--type RESOURCE-TYPE")
            sys.exit()
        output = create_pe (bearer, account_id, ncc_id, resource_id, resource_type) 
        print(output)
    elif command == "delete_ncc" :
        if account_id is None or account_id is None or ncc_id is None : 
            print("Missing Parameters : ")
            print(sys.argv[0],"-C",command,"-a|--accountId ACCOUNT-ID -n|--nccId NCC-ID")
            sys.exit()
        output = delete_ncc(bearer, account_id, ncc_id)
        pprint.pprint(output)
    elif command == "get_ncc_list" : 
        if account_id is None or account_id is None : 
            print("Missing Parameters : ")
            print(sys.argv[0],"-C",command,"-a|--accountId ACCOUNT-ID [-v]")
            sys.exit()
        output = get_ncc_list(bearer, account_id)
        for ncc_json in output : 
            if verbose :
                print("\n-----------------------\n")
                pprint.pprint(ncc_json)
            else:
                print(ncc_json["name"],ncc_json["network_connectivity_config_id"],ncc_json["region"])
    elif command == "get_workspace" : 
        if account_id is None or workspace is None : 
            print("Missing Parameters : ")
            print(sys.argv[0],"-C",command,"-a|--accountId ACCOUNT-ID -w|--workspaceId WORKSPACE-ID [-v]")
            sys.exit()
        output = get_workspace(bearer, account_id, workspace)

        if verbose : 
            pprint.pprint(output)
        else :
            print("Name:",output["workspace_name"])
            print("region:",output["location"])
            print("url:",output["deployment_name"])
            print("recource group:",output["azure_workspace_info"]["resource_group"])
            print("subscription:",output["azure_workspace_info"]["subscription_id"])
            has_ncc = False
            for key in output :
                if key == "network_connectivity_config_id" :
                    has_ncc = True
            if has_ncc :         
                print("NCC id:",output["network_connectivity_config_id"])
            else :
                print("NCC id: none")
    elif command == "create_serverless_private_link" :
        if account_id is None or workspace is None or resource_id is None or resource_type is None: 
            print("Missing Parameters : ")
            print(sys.argv[0],"-C",command,"-a|--accountId ACCOUNT-ID -w|--workspaceId WORKSPACE-ID -r|--resourceId RESOURCE-ID -t|--type RESOURCE-TYPE [--nccname NAME-OF-NCC]")
            sys.exit()
        
        output = get_workspace(bearer, account_id, workspace)
        has_ncc = False
        regionname = output["location"]
        for key in output :
            if key == "network_connectivity_config_id" :
                has_ncc = True
        if has_ncc :         
            ncc_id = output["network_connectivity_config_id"]
            print("Creating Private Endpoint")
            output = create_pe (bearer, account_id, ncc_id, resource_id, resource_type) 
            print(output)
            print("Please Approve your private endpoint and run get_ncc command for NCC id ",ncc_id," once approved")
        else : 
            print("creating new NCC")
            if ncname is None :
                randname = ''.join(random.choices(string.ascii_lowercase + string.digits, k=7))
                ncname = "ncc_"+str(randname)+"_"+regionname
            nccobj = create_nas(bearer,account_id, ncname,regionname)
            ncc_id = nccobj["network_connectivity_config_id"]
            print("Adding NCC to workspace")
            output = update_workspace(bearer, account_id, ncc_id, workspace)
            print("Creating Private Endpoint")
            output = create_pe (bearer, account_id, ncc_id, resource_id, resource_type)
            print(output)
            print("Please Approve your private endpoint and run get_ncc command  for NCC id ",ncc_id," once approved")
    elif command == "ensure_workspace_ncc" :
        if account_id is None or workspace is None: 
            print("Missing Parameters : ")
            print(sys.argv[0],"-C",command,"-a|--accountId ACCOUNT-ID -w|--workspaceId WORKSPACE-ID")
            sys.exit()
        
        output = get_workspace(bearer, account_id, workspace)
        has_ncc = False
        regionname = output["location"]
        for key in output :
            if key == "network_connectivity_config_id" :
                has_ncc = True
        if has_ncc :         
            ncc_id = output["network_connectivity_config_id"]
            print("Adding NCC to workspace")
            output = update_workspace(bearer, account_id, ncc_id, workspace)
            print("NCC id :",ncc_id)
        else : 
            print("creating new NCC")
            randname = ''.join(random.choices(string.ascii_lowercase + string.digits, k=7))
            ncname = "ncc_"+str(randname)+"_"+regionname
            output = create_nas(bearer,account_id, ncname,regionname)
            ncc_id = output["network_connectivity_config_id"]
            print("Adding NCC to workspace")
            output = update_workspace(bearer, account_id, ncc_id, workspace)
            print("NCC id :",ncc_id)

         
    else:
            print(command,"\n")
            usage()
            assert False, "unknown command"
            
if __name__ == '__main__':
    sys.exit(main())
