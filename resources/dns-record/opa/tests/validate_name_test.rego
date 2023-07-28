package easyaas.dnsrecord

test_valid_name {
  record := {
    "request": {
      "kind": "DnsRecord",
      "operation": "CREATE",
      "object": {
        "spec": {
          "dnsName": "valid-name"
        }
      }
    }
  }

  res := deny with input as record
  count(res) == 0
}

test_invalid_name {
  record := {
    "request": {
      "kind": "DnsRecord",
      "operation": "CREATE",
      "object": {
        "spec": {
          "dnsName": "invalid_name"
        }
      }
    }
  }

  res := deny with input as record
  count(res) > 0
}
