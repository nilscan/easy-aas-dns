#!/bin/sh

echo "Terragrunt info: "
terragrunt --version
echo
echo -n "Tfswitch info: "
tfswitch --version
echo

echo "Running terraform module in $TERRAFORM_ROOT_DIR/$TERRAFORM_DIR"
cd $TERRAFORM_ROOT_DIR/$TERRAFORM_DIR

TERRAGRUNT_ACTION=${1:-${$TERRAGRUNT_ACTION:-apply}}

# Switch to the proper version of terraform
tfswitch --default=$(tfswitch --show-latest)

# Run terragrunt
terragrunt $TERRAGRUNT_ACTION --terragrunt-non-interactive -auto-approve
