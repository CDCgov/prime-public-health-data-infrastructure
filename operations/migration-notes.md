# Migrating reportstream terraform

Modules deleted:

This includes deleting the modules themselves as well as the references from
`vars/test/*`:

* `container_registry`
* `database`
* `front_door`
* `metabase`
* `sftp_container`

Capabilities deleted:

* `application_insights`
    * Removed all alerts and PagerDuty reference
* `storage`
    * Removed references to web container and public site
    * Removed references to partner account
    * Removed references to candidate slot
    * Removed 30 day retention limit

