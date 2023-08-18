**options :**

**-h or --help :** this page

**--logout :** Removes cached login and refresh token for use

and device (see README)

**-v :** verbose output - expands some command outputs from lists to

whole json docs

**-C or --command :** See commands below - each command performs a
distinct

action for serverless private link

**-w or --workspaceId :** The workspace ID

**-a or --accountId :** The Account ID from UC account console

**-n or --nccId :** THe ID of the NCC (network config) object

**-l or --login_type :** Default service principal. Choose between

Device code login (device), Username / Password (user),

or Service Principal (sp) See README

**-f or --config :** Default credential.json, JSON file for holding user
/ sp

credentials (See README)

**--nccname :** Unique name for the NCC object

**--region :** Azure region, example: eastus, westus, westus2

**-r or --resourceId :** The resource ID of the storage account/sql db
you

wish to create a private end point to

**-t or --type :** The type of resource, dfs or blob or SqlServer

**commands :** (use with -C or --command)

**get_workspace_ncc :** Gets the NCC ID for a given workspace

**ensure_workspace_ncc :** Gets the NCC ID for a given workspace

if the workspace does not have an NCC, create and attach a new NCC.

Can be used for stable endpoints if no private endpoint is desired.

**attach_workspace :** Attach a NCC (network config) to a workspace

**get_stable_ep :** Gets the stable service endpoints for a given
workspace

to be used for storage firewall

**get_ncc :** Gets details about a NCC, also used to "lock in" the PE
info

to a NCC after the PE is approved.

**create_ncc :** Creates a blank NCC (network config) object and

returns its NCC id

**create_pe :** Creates a new private endpoint in a NCC (network config)
object

**get_ncc_list :** Gets a list of NCCs in the account (tenant)

**get_workspace :** Gets details about a given workspace including

the NCC id if its attached

**delete_ncc :** deletes a NCC (network config) object (Note: may not be

able to delete NCCs with active private endpoints)

**create_serverless_private_link :** <u>Main command to use</u>. Creates
a private

endpoint for storage or SQL and attaches to, or updates a workspace. If

you include an existing NCC id it will update that NCC and add it to the

workspace or replace an existing NCC.
