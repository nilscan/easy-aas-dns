locals {
  resource_params = jsondecode(file("${get_terragrunt_dir()}/easyaas_resource_params.json"))
}

generate "tfvars_from_spec" {
  path      = "terraform.tfvars.json"
  if_exists = "skip"
  contents = file("${get_terragrunt_dir()}/resource_spec.json")
  disable_signature = true
}

terraform {
  source = local.resource_params["source"]

  before_hook "install_terraform" {
    commands = ["init"]
    execute  = ["tfswitch", "--default", "$(tfswitch --show-latest)"]
  }
}

# TODO: inject backend config
