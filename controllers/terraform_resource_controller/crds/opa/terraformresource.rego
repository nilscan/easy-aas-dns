package easyaas.terraformresource

operations := {"CREATE", "UPDATE"}

isResourceRole(role) {
  input.request.object.metadata.annotation["easyaas.dev/terraformResource"] == input.request.object.metadata.name
}

deny[msg] {
	input.request.object.kind == "TerraformResource"
	operations[input.request.operation]
	role := input.request.object.spec.extraRoles[_]
  isResourceRole(role)

  msg := sprintf("only Roles with the easyaas.dev/terraformResource=%v annotation can be attached (role %v)", [input.request.object.metadata.name, role])
}
