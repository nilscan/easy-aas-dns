locals {
  source_base_url = "http://localhost:8080/terraform/record.zip"
}

inputs = {
  dnsName = "test.easyaas.dev"
  records = ["1.2.3.4"]
}