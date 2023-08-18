# serverless-pl-tool

Converted using https://alldocs.app/convert-word-docx-to-markdown

The Serverless Secure Connectivity feature enables you to securely connect your
Serverless clusters with backend resources such as Azure Data Lake Storage (ADLS)
accounts and external Hive Metadata Store.
With this feature you can:

1. Configure Azure Storage firewall to constrain access to Databricks Serverless
runtime based on a set of stable subnet IDs (Service Endpoints) associated
with your Workspace.
2. Configure dedicated and private connectivity using Azure Private Link to
cloud backends such as:

    1. Azure Storage
    2. Azure SQL (external Hive Metadata Store)

The serverless-pl tool helps with handling the REST-API and process to create serverless private and points and also generating service endpints (stable end point) for storage firewall if private end points are not needed. 

##  Setup : 
1. Python packages : You will need to install the MSAL for python package for Python version 3 (pip install MSAL), all other packages should be built in. 
2. Credentials : Access to the accounts API is done through getting a bearer token for the Databricks service. Since we are using MSAL, you have 3 options for authenticating to Databricks : 
   1. Service Principal (*default*)
   2. User device code 
   3. Username and Password
   4. *Device Code and Username / Password cache and use a refresh token to prevent constant re-authentication*
   
### Credential files
Each option for authentication uses a JSON file. By default the appplication uses a file called credential.json, but you can use a different file or files for different authentication methds or users using the -l or --login_type option for the mode (sp, device or user) and the -f or --config option for the filename. A sample credential file is in the repo, edit it accordinly and rename to credential.json. 

## Definitions 
__NCC or Network Connectivity Config__ : 

__Stable Endpoint__ :

__Private Endpoint__ : 

__Serverless Compute__ : 

## Process : 


Examples: 
__Service Principal (sp)__

            {
                "tenant" : "your tenant id",
                "client_id" : "sp client id",
                "client_secret" : "sp secret"
            }
__Device Code (device)__

            {
                "tenant" : "your tenant id",
                "client_id" : "application / sp client id",
                "username" : "username"
            }
__User / Password (user)__

            {
                "tenant" : "your tenant id",
                "client_id" : "application / sp client id",
                "username" : "username"
                "password" : "password"
            }

*Please follow the Microsoft doc (https://learn.microsoft.com/en-us/azure/databricks/dev-tools/app-aad-token) for instructions on setting up user auth in Azure.*


### Options and Commands
__ServerlessPL tool usage:__
          
__options :__

__-h or --help :__ this page

__--logout :__ Removes cached login and refresh token for use and device (see README)

__-v :__ verbose output - expands some command outputs from lists to whole json docs

__-C or --command :__ See commands below - each command performs a distinct action for serverless private link

__-w or --workspaceId :__ The workspace ID

__-a or --accountId :__ The Account ID from UC account console

__-n or --nccId :__ THe ID of the NCC (network config) object

__-l or --login_type :__ Default service principal. Choose between Device code login (device), Username / Password (user), or Service Principal (sp) See README

__-f or --config :__ Default credential.json, JSON file for holding user / sp

credentials (See README)

__--nccname :__ Unique name for the NCC object

__--region :__ Azure region, example: eastus, westus, westus2

__-r or --resourceId :__ The resource ID of the storage account/sql db you wish to create a private end point to

__-t or --type :__ The type of resource, dfs or blob or SqlServer

__commands :__ (use with -C or --command)

__get_workspace_ncc :__ Gets the NCC ID for a given workspace

__ensure_workspace_ncc :__ Gets the NCC ID for a given workspace if the workspace does not have an NCC, create and attach a new NCC. Can be used for stable endpoints if no private endpoint is desired.

__attach_workspace :__ Attach a NCC (network config) to a workspace

__get_stable_ep :__ Gets the stable service endpoints for a given workspace to be used for storage firewall

__get_ncc :__ Gets details about a NCC, also used to "lock in" the PE
info to a NCC after the PE is approved.

__create_ncc :__ Creates a blank NCC (network config) object and returns its NCC id

__create_pe :__ Creates a new private endpoint in a NCC (network config)
object

__get_ncc_list :__ Gets a list of NCCs in the account (tenant)

__get_workspace :__ Gets details about a given workspace including the NCC id if its attached

__delete_ncc :__ deletes a NCC (network config) object (Note: may not be able to delete NCCs with active private endpoints)

__create_serverless_private_link :__ <u>Main command to use</u>. Creates
a private endpoint for storage or SQL and attaches to, or updates a workspace. If you include an existing NCC id it will update that NCC and add it to the workspace or replace an existing NCC.
