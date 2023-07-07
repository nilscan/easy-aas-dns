include "root" {
  path = find_in_parent_folders()
  expose = true # Needed to read locals from root config
}

include "localstack" {
  path = "localstack.hcl"
  expose = true
}

terraform {
  source = "../../resources/dns-record/terraform"
  # source = include.root.locals.source_base_url

  before_hook "install_terraform" {
    commands = ["init"]
    execute  = ["tfswitch", "--default", "$(tfswitch --show-latest)"]
  }

  before_hook "render_localstack_provider" {
    commands = ["init"]
    execute  = include.localstack.locals.after_hook_execute
  }
}
