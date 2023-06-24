
locals {
  sed = get_platform() == "darwin" ? "gsed" : "sed" # Must use gsed on macos for the -i parameter
  provider_localstack = join("\\n", split("\n", file("localstack-providers.patch")))
  after_hook_execute = ["gsed", "-i", "s/provider \"aws\" {/${local.provider_localstack}/", "providers.tf"]
}

generate "variables-localstack" {
  path      = "variables-localstack.tf"
  if_exists = "skip"
  contents = file("localstack-variables.patch")
}