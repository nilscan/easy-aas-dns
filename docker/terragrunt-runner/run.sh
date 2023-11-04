#!/bin/sh

echo "Terragrunt info: "
terragrunt --version
echo
echo -n "Tfswitch info: "
tfswitch --version
echo

echo "Running terraform module in $TERRAFORM_ROOT_DIR/$TERRAFORM_DIR"
cd $TERRAFORM_ROOT_DIR/$TERRAFORM_DIR

TERRAGRUNT_ACTION=${1:-apply}

# Run terragrunt
terragrunt $TERRAGRUNT_ACTION --terragrunt-non-interactive -auto-approve
