locals {
  resource_params = jsondecode(file("${get_terragrunt_dir()}/easyaas_resource_params.json"))
  terraform_source = local.resource_params["terraform"]["source"]

  resource = jsondecode(file("${get_terragrunt_dir()}/easyaas_resource.json"))
}

generate "tfvars_from_spec" {
  path      = "terraform.tfvars.json"
  if_exists = "skip"
  contents = file("${get_terragrunt_dir()}/easyaas_resource_spec.json")
  disable_signature = true
}

terraform {
  source = local.terraform_source
}

generate "backend" {
  path      = "backend.tf"
  if_exists = "skip"
  contents = <<END
    terraform {
      backend "kubernetes" {
        namespace = "${local.resource["metadata"]["namespace"]}"
        secret_suffix = "easyaas-${local.resource_params["crd"]}-${local.resource["metadata"]["name"]}"
      }
    }
  END
}
