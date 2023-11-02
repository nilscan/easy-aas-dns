package easyaas.dnsrecord

test_valid_name {
  record := {
    "request": {
      "operation": "CREATE",
      "object": {
        "kind": "DnsRecord",
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
      "operation": "CREATE",
      "object": {
        "kind": "DnsRecord",
        "spec": {
          "dnsName": "invalid_name"
        }
      }
    }
  }

  res := deny with input as record
  count(res) > 0
}
