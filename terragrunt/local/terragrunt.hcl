include "root" {
  path = find_in_parent_folders()
  expose = true # Needed to read locals from root config
}

include "localstack" {
  path = "localstack.hcl"
  expose = true
}


terraform {
  source = include.root.locals.source_base_url

  before_hook "configurable_after_hook" {
    commands = ["init"]
    execute  = include.localstack.locals.after_hook_execute
  }
}
