resource "aws_route53_zone" "easyaas-dev" {
  name = "easyaas.dev"
}

resource "aws_route53_record" "record" {
  name = var.dnsName

  zone_id = aws_route53_zone.easyaas-dev.zone_id
  type    = "A"
  ttl     = "300"
  records = var.records
}
