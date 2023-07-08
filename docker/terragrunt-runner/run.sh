#!/bin/sh

echo "Terragrunt info: "
terragrunt --version
echo
echo -n "Tfswitch info: "
tfswitch --version
echo

print_file() {
  file=$1
  echo "$file:"
  cat $file
}

echo "Running terraform module in $TERRAFORM_ROOT_DIR/$TERRAFORM_DIR"
cd $TERRAFORM_ROOT_DIR/$TERRAFORM_DIR

print_file terragrunt.hcl

# Install terraform using version.tf or latest if not specified
tfswitch --default $(tfswitch --show-latest)

# Run terragrunt
terragrunt apply
