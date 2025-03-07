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
import collections

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

ACCOUNT_ID = None


def get_bearer_token_msal(credfile, login_type):
    global ACCOUNT_ID

    authority_host_url = "https://login.microsoftonline.com/"
    # the Application ID of  AzureDatabricks
    scopes = [ '2ff814a6-3304-4ab8-85cb-cd0e6f879c1d/.default' ]

    with open(credfile) as json_data:
        user_parameters = json.load(json_data)
        json_data.close()

    for key in user_parameters : 
        if key == "accountId" :
            ACCOUNT_ID = user_parameters["accountId"] 
        if key == "tenant" :
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
            result = app.acquire_token_by_username_password(username = user_parameters['username'], password = user_parameters['password'], scopes=scopes)

    if login_type == "sp":
        app = msal.ConfidentialClientApplication(client_id=user_parameters['client_id'], authority=authority_url, client_credential=user_parameters['client_secret'])

        result = app.acquire_token_silent(scopes=scopes, account=None)

        if not result:
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
            flow = app.initiate_device_flow(scopes=scopes)
            print(flow['message'])
            result = app.acquire_token_by_device_flow(flow)

    if login_type == "external":
        AzureAccessToken = os.environ["BEARER_TOKEN"]
        return(AzureAccessToken)

    if login_type == "browser":
        ## https://learn.microsoft.com/en-us/entra/msal/python/#basic-usage
        return(0)

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

def create_pe (bearertoken, accountId, nccId, resourceID, resourceType, domainList) : 
    url = ACCOUNT_URL+accountId+"/network-connectivity-configs/"+nccId+"/private-endpoint-rules"

    if not resourceType : 
        resourceType = ''

    if resourceType and domainList == None :
        payload = json.dumps({
        "resource_id": f"{resourceID}",
        "group_id": f"{resourceType}"
        })
    elif not domainList == None and not resourceType : 
        payload = json.dumps({
        "resource_id": f"{resourceID}",
        "domain_names": domainList
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

def get_ncc_by_resource (bearertoken, accountId, resourceID, resourceType, domainList) : 

    nccmatch = []

    if not resourceType : 
        resourceType = ''

    nccs = get_ncc_list(bearertoken,accountId)

    for ncc in nccs : 
        ncc_id = ncc["network_connectivity_config_id"]
        if "egress_config" in ncc : 
            if "target_rules" in ncc["egress_config"] :
                for res in ncc["egress_config"]["target_rules"]["azure_private_endpoint_rules"] :
                    if res["resource_id"] == resourceID and res["group_id"] == resourceType and res["connection_state"] == "ESTABLISHED" :
                        if "domain_names" in res : 
                            if collections.Counter(domainList) == collections.Counter(res["domain_names"]) :
                                nccmatch.append({"ncc" : ncc_id})
                        else : 
                            nccmatch.append({"ncc" : ncc_id})         
    return nccmatch

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

   ##  print(response.json())

    responsejson = json.loads(response.text)

    sortedresponse = sorted(responsejson["items"], key=lambda x: x['name'])


    return(sortedresponse)

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

def delete_pe(bearertoken, accountId, nccId, peId) : 
    url = ACCOUNT_URL+accountId+"/network-connectivity-configs/"+nccId+"/private-endpoint-rules/"+peId

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

def confirm(ignore, message):
    """
    Ask user to enter Y or N (case-insensitive).
    :return: True if the answer is Y.
    :rtype: bool
    """
    if ignore :
        return True
    
    answer = ""
    response = False
    print(message)
    while answer not in ["y", "n"]:
        answer = input("OK to continue [Y/N]? ").lower()
    if answer == "y" :
        response = True

    return response

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
    '''+color.BOLD+'''-h or --help :'''+color.END+''' this page
    '''+color.BOLD+'''--logout :'''+color.END+''' Removes cached login and refresh token for use
        and device (see README)
    '''+color.BOLD+'''-v :'''+color.END+''' verbose output - expands some command outputs from lists to
        whole json docs
    '''+color.BOLD+'''-C or --command :'''+color.END+''' See commands below - each command performs a distinct
        action for serverless private link
    '''+color.BOLD+'''-w or --workspaceId :'''+color.END+''' The workspace ID
    '''+color.BOLD+'''-a or --accountId :'''+color.END+''' The Account ID from UC account console
    '''+color.BOLD+'''-n or --nccId :'''+color.END+''' The ID of the NCC (network config) object
    '''+color.BOLD+'''-l or --login_type :'''+color.END+''' Default service principal. Choose between
        Device code login (device), Username / Password (user),
        Service Principal (sp), or ENV Var (external) See README
    '''+color.BOLD+'''-f or --config :'''+color.END+''' Default credential.json, JSON file for holding user / sp
        credentials (See README)
    '''+color.BOLD+'''-I or --noprompt :'''+color.END+''' Run in non-interactive mode, do not prompt. For scripts etc.
    '''+color.BOLD+'''-F or --force :'''+color.END+''' Override default behavior to stop on a config issue
    '''+color.BOLD+'''--nccname :'''+color.END+''' Unique name for the NCC object
    '''+color.BOLD+'''--region :'''+color.END+''' Azure region, example: eastus, westus, westus2
    '''+color.BOLD+'''-r or --resourceId :'''+color.END+''' The resource ID of the storage account/sql db you
        wish to create a private end point to
    '''+color.BOLD+'''-t or --type :'''+color.END+''' The type of resource, dfs or blob or SqlServer

    '''+color.BOLD+'''commands :'''+color.END+''' (use with -C or --command) '''+color.END+'''
    '''+color.BOLD+'''create_serverless_private_link : '''+color.END+''' '''+color.UNDERLINE+'''Main command to use'''+color.END+'''. Creates a private
        endpoint for storage or SQL and attaches to, or updates a workspace. If
        you include an existing NCC id it will update that NCC and add it to the
        workspace or replace an existing NCC.
    '''+color.BOLD+'''ensure_workspace_ncc : '''+color.END+''' Gets the NCC ID for a given workspace
        if the workspace does not have an NCC, create and attach a new NCC.
        Can be used for stable endpoints if no private endpoint is desired.
    
    '''+color.BOLD+'''utilities :'''+color.END+'''
    '''+color.BOLD+'''attach_workspace : '''+color.END+''' Attach a NCC (network config) to a workspace
    '''+color.BOLD+'''get_stable_ep : '''+color.END+''' Gets the stable service endpoints for a given workspace
        to be used for storage firewall
    '''+color.BOLD+'''get_ncc : '''+color.END+'''Gets details about a NCC, also used to "lock in" the PE info
        to a NCC after the PE is approved.
    '''+color.BOLD+'''get_workspace_ncc : '''+color.END+''' Gets the NCC ID for a given workspace
    '''+color.BOLD+'''get_ncc_by_resource : '''+color.END+''' Checks the resource if its part of a NCC
    '''+color.BOLD+'''create_ncc : '''+color.END+''' Creates a blank NCC (network config) object and
    returns its NCC id
    '''+color.BOLD+'''create_pe : '''+color.END+''' Creates a new private endpoint in a NCC (network config) object
    '''+color.BOLD+'''delete_pe : '''+color.END+''' deletes (deactivates) a private endpoint in a NCC (network config) object
    '''+color.BOLD+'''get_ncc_list : '''+color.END+''' Gets a list of NCCs in the account (tenant)
    '''+color.BOLD+'''get_workspace : '''+color.END+''' Gets details about a given workspace including
        the NCC id if its attached
    '''+color.BOLD+'''delete_ncc : '''+color.END+''' deletes a NCC (network config) object (Note: may not be
        able to delete NCCs with active private endpoints)
    ''')

def logout() :
    filename = "my_cache.bin"
    try:
        os.remove(filename)
    except OSError:
        pass


def main():
    global ACCOUNT_ID
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
    noprompt = False
    override = False
    pe_rule_id = None
    domain_list = None

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
        opts, args = getopt.getopt(sys.argv[1:], "hC:r:t:w:a:n:r:d:p:t:f:l:vIF", ["help", "command=", "resourceId=", "domain_list=", "type=", "workspaceId=", "PeRuleId=", "login_type=", "config=", "nccname=", "region=","logout","noprompt","force"])
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
        elif o in ("-p","--PeRuleId"):
            pe_rule_id = a
        elif o in ("-l","--login_type"):
            login_type = a
        elif o in ("-f","--config"):
            config_file = a
        elif o in ("-r","--resourceId"):
            resource_id = a
        elif o in ("-t","--type"):
            resource_type = a
        elif o in ("-d", "--domain_list"):
            domain_list = a.strip('[]').split(',')
        elif o in ("-I","--noprompt") :
            noprompt = True
        elif o in ("-F","--force") :
            override = True
        else:
            assert False, "unhandled option"
            sys.exit()
    
    if command is not None :
        bearer = get_bearer_token_msal(config_file, login_type)
        if verbose : 
            print(config_file, login_type)
            print(bearer)

        # pick up account id from global vars if needed 
        if account_id == None :
            account_id = ACCOUNT_ID
            

    if command == "get_workspace_ncc" :
        if account_id is None or workspace is None : 
            print("Missing Parameters : ")
            print(sys.argv[0],"-C",command,"[-a|--accountId ACCOUNT-ID] -w|--workspaceId WORKSPACE-ID [-v]")
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
            print(sys.argv[0],"-C",command,"[-a|--accountId ACCOUNT-ID] -n|--nccId NCC-ID -w|--workspace WORKSPACE-ID")
            sys.exit()
        if not confirm(noprompt,"You are about to attach a NCC to your workspace which could alter your serverless compute networking config.") :
                sys.exit()
        output = update_workspace (bearer, account_id, ncc_id, workspace) 
        pprint.pprint(output)
    elif command == "get_stable_ep" :
        if account_id is None or workspace is None : 
            print("Missing Parameters : ")
            print(sys.argv[0],"-C",command,"[-a|--accountId ACCOUNT-ID] -w|--workspaceId WORKSPACE-ID [-v]")
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
            print(sys.argv[0],"-C",command,"[-a|--accountId ACCOUNT-ID] -n|--nccId NCC-ID [-v]")
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
            print(sys.argv[0],"-C",command,"[-a|--accountId ACCOUNT-ID] --nccname NAME-OF-NCC --region AZURE-REGION [-I or --noprompt]")
            sys.exit()
        if not confirm(noprompt,"You are about to create a NCC in your serverless compute networking config.") :
                sys.exit()
        output = create_nas(bearer,account_id, ncname,regionname)
        ncc_id = output["network_connectivity_config_id"]
        print("NCC id",ncc_id,"\n\n",output)
    elif command == "create_pe" : 
        if account_id is None or ncc_id is None or resource_id is None or (resource_type or domain_list) is None : 
            print("Missing Parameters : ")
            print(sys.argv[0],"-C",command,"[-a|--accountId ACCOUNT-ID] -n|--nccId NCC-ID -r|--resourceId RESOURCE-ID [-t|--type RESOURCE-TYPE or -d | --domain_list DOAIN-LIST][-F or --force][-I or --noprompt]")
            sys.exit()
        
        nccmatchtest = get_ncc_by_resource(bearer, account_id, resource_id, resource_type, domain_list)
        
        if len(nccmatchtest) > 0 : 
            for nccmatch in nccmatchtest : 
                print("\n",resource_id,"was found in NCC", nccmatch["ncc"])
            if not override :
                print("\n\nThe resource id you are creating a private endpoint for is already attached to one or more NCC, if the workspace you are using in the command has an NCC already or you want to generate a new NCC - and you don't want to re-use one of NCC it found with the resource ID\n\nuse the -F or --force flag to override to create a new private end point and new NCC if needed,")
                print("\n... if not, either add or replace NCC above using the attach_workspace command" )
                sys.exit()
            else : 
                if not confirm(noprompt,"You are about to create an additional private endpoint for resource ID "+color.UNDERLINE+resource_id+ color.END+" in a new or current serverless compute networking config.") :
                    sys.exit()


        if not confirm(noprompt,"You are about to add a private endpoint to your serverless compute networking config.") :
                sys.exit()
        output = create_pe (bearer, account_id, ncc_id, resource_id, resource_type, domain_list) 
        pprint.pprint(output)
    elif command == "delete_pe" :
        if account_id is None or ncc_id is None or pe_rule_id is None : 
            print("Missing Parameters : ")
            print(sys.argv[0],"-C",command,"[-a|--accountId ACCOUNT-ID] -n|--nccId NCC-ID -p|-- PeRuleId [-I or --noprompt]")
            sys.exit()
        if not confirm(noprompt,"You are about to delete/deactivate a Private Endpoint from your serverless compute networking config.") :
                sys.exit()
        output = delete_pe(bearer, account_id, ncc_id, pe_rule_id)
        pprint.pprint(output)
    elif command == "delete_ncc" :
        if account_id is None or account_id is None or ncc_id is None : 
            print("Missing Parameters : ")
            print(sys.argv[0],"-C",command,"[-a|--accountId ACCOUNT-ID] -n|--nccId NCC-ID [-I or --noprompt]")
            sys.exit()
        if not confirm(noprompt,"You are about to delete a NCC from your serverless compute networking config.") :
                sys.exit()
        output = delete_ncc(bearer, account_id, ncc_id)
        pprint.pprint(output)
    elif command == "get_ncc_by_resource" :
        if account_id is None or resource_id is None or (resource_type or domain_list) is None: 
            print("Missing Parameters : ")
            print(sys.argv[0],"-C",command,"[-a|--accountId ACCOUNT-ID] -r|--resourceId RESOURCE-ID -t|--type RESOURCE-TYPE [--nccname NAME-OF-NCC]")
            sys.exit()
        
        output = get_ncc_by_resource(bearer,account_id, resource_id, resource_type, domain_list)
        for nccmatch in output : 
            print(resource_id,"was found in NCC", nccmatch["ncc"])
    
    elif command == "get_ncc_list" : 
        if account_id is None or account_id is None : 
            print("Missing Parameters : ")
            print(sys.argv[0],"-C",command,"[-a|--accountId ACCOUNT-ID] [-v]")
            sys.exit()
        output = get_ncc_list(bearer, account_id)
        if not verbose : 
            print("{:<30} {:<36} {:<15}".format("NCC Name", "NCC ID", "Region"))
            print("{:<30} {:<36} {:<15}".format("---------", "-------", "--------"))
        for ncc_json in output : 
            if verbose :
                print("\n-----------------------\n")
                pprint.pprint(ncc_json)
            else:
                print("{:<30} {:<36} {:<15}".format(ncc_json["name"],ncc_json["network_connectivity_config_id"],ncc_json["region"]))
    elif command == "get_workspace_list" :
        print("DEBUG")
        output = list_workspaces(bearer, account_id)
        print(output)
    elif command == "get_workspace" : 
        if account_id is None or workspace is None : 
            print("Missing Parameters : ")
            print(sys.argv[0],"-C",command,"[-a|--accountId ACCOUNT-ID] -w|--workspaceId WORKSPACE-ID [-v]")
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
            print(sys.argv[0],"-C",command,"[-a|--accountId ACCOUNT-ID] -w|--workspaceId WORKSPACE-ID -r|--resourceId RESOURCE-ID -t|--type RESOURCE-TYPE [--nccname NAME-OF-NCC][-F or --force][-I or --noprompt]")
            sys.exit()
        
        output = get_workspace(bearer, account_id, workspace)
        has_ncc = False
        regionname = output["location"]

        nccmatchtest = get_ncc_by_resource(bearer, account_id, resource_id, resource_type)
        
        if len(nccmatchtest) > 0 : 
            for nccmatch in nccmatchtest : 
                print("\n",resource_id,"was found in NCC", nccmatch["ncc"])
            if not override :
                print("\n\nThe resource id you are creating a private endpoint for is already attached to one or more NCC, if the workspace you are using in the command has an NCC already or you want to generate a new NCC - and you don't want to re-use one of NCC it found with the resource ID\n\nuse the -F or --force flag to override to create a new private end point and new NCC if needed,")
                print("\n... if not, either add or replace NCC above using the attach_workspace command" )
                sys.exit()
            else : 
                if not confirm(noprompt,"You are about to create an additional private endpoint for resource ID "+color.UNDERLINE+resource_id+ color.END+" in a new or current serverless compute networking config.") :
                    sys.exit()

        if "network_connectivity_config_id" in output : # has an NCC 
            ncc_id = output["network_connectivity_config_id"]
            print("Creating Private Endpoint")
            if not confirm(noprompt,"You are about to add a private endpoint to workspace "+output["workspace_name"]+" using NCC "+ncc_id+" serverless compute networking config.") :
                sys.exit()
            output = create_pe (bearer, account_id, ncc_id, resource_id, resource_type, domain_list) 
            pprint.pprint(output)
            print("Please Approve your private endpoint and run get_ncc command for NCC id ",ncc_id," once approved")
        else : 
            print("creating new NCC")
            if ncname is None :
                randname = ''.join(random.choices(string.ascii_lowercase + string.digits, k=7))
                ncname = "ncc_"+str(randname)+"_"+regionname
            if not confirm(noprompt,"You are about to add a new NCC " +color.UNDERLINE+ ncname + color.END+" and private endpoint to workspace "+color.UNDERLINE+output["workspace_name"]+ color.END+" serverless compute networking config.") :
                sys.exit()
            nccobj = create_nas(bearer,account_id, ncname,regionname)
            ncc_id = nccobj["network_connectivity_config_id"]
            print("Adding NCC to workspace")
            output = update_workspace(bearer, account_id, ncc_id, workspace)
            print("Creating Private Endpoint")
            output = create_pe (bearer, account_id, ncc_id, resource_id, resource_type, domain_list)
            pprint.pprint(output)
            print("Please Approve your private endpoint and run get_ncc command  for NCC id ",ncc_id," once approved")
    
    elif command == "ensure_workspace_ncc" :
        if account_id is None or workspace is None: 
            print("Missing Parameters : ")
            print(sys.argv[0],"-C",command,"[-a|--accountId ACCOUNT-ID] -w|--workspaceId WORKSPACE-ID")
            sys.exit()
        
        output = get_workspace(bearer, account_id, workspace)
        has_ncc = False
        regionname = output["location"]

        if "network_connectivity_config_id" in output : # has an NCC    
            ncc_id = output["network_connectivity_config_id"]
            print("NCC id :",ncc_id)
        else : 
            print("creating new NCC")
            randname = ''.join(random.choices(string.ascii_lowercase + string.digits, k=7))
            ncname = "ncc_"+str(randname)+"_"+regionname
            if not confirm(noprompt,"You are about to add a new NCC " +color.UNDERLINE+ ncname + color.END+" to workspace "+color.UNDERLINE+output["workspace_name"]+ color.END+" serverless compute networking config.") :
                sys.exit()
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
