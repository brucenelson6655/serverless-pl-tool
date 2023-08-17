# serverless-pl-tool

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


### Options and Commands
__ServerlessPL tool usage:__
          

    options :
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
    commands : (use with -C or --command) 
        get_workspace_ncc :  Gets the NCC ID for a given workspace
        attach_workspace  :  Attach a NCC (network config) to a workspace
        get_stable_ep :  Gets the stable service endpoints for a given workspace
            to be used for stoarage firewall
        get_ncc : Gets details about a NCC, also used to "lock in" the PE info
            to a NCC after the PE is approved approved.
        create_ncc :  Created a blank NCC (network config) object and
            returns its NCC id
        get_ncc_list :  Gets a list of NCCs in the account (tenant)
        get_workspace :  Gets details about a given workspace including
            the NCC id if its attached
        delete_ncc :  deletes a NCC (network config) object (Note: may not be
            able to delete NCCs with active private endpoints)
        create_serverless_pe :  Main command to use. Creates a private endpoint
            for a storage or SQL and ataches to, or updates a workspace. If you
            include an existing NCC id it will update that NCC and add it to the
            workspace or replace an existing NCC.
