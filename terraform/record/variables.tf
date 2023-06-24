variable "dnsName" {
  type = string
}
variable "records" {
  type = list(any)
}

# AWS
variable "region" {
  default = "us-east-1"
}
