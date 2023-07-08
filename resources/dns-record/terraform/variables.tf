variable "dnsName" {
  type = string
}

variable "type" {
  type = string
}

variable "records" {
  type = list(string)
}

# AWS
variable "region" {
  default = "us-east-1"
}
