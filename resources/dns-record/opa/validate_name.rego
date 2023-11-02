package easyaas.dnsrecord

operations := {"CREATE", "UPDATE"}

deny[msg] {
	input.request.object.kind == "DnsRecord"
	operations[input.request.operation]
	host := input.request.object.spec.dnsName

  not regex.match("^([a-z0-9-.]{1,63})$", host)

	msg := sprintf("invalid ingress host %q", [host])
}
