output "ecr_repository_url" {
  description = "ECR repository URL"
  value       = aws_ecr_repository.superset.repository_url
}

output "cloudfront_domain_name" {
  description = "CloudFront distribution domain name"
  value       = aws_cloudfront_distribution.main.domain_name
}

output "certificate_arn" {
  description = "ACM certificate ARN"
  value       = aws_acm_certificate_validation.main.certificate_arn
}

output "iam_role_arn" {
  description = "IAM role ARN for EC2/ECS"
  value       = aws_iam_role.superset_role.arn
}

output "hosted_zone_id" {
  description = "Route 53 hosted zone ID"
  value       = data.aws_route53_zone.main.zone_id
}

output "ec2_public_ip" {
  description = "EC2 instance public IP"
  value       = aws_instance.web.public_ip
}

output "alb_dns_name" {
  description = "Application Load Balancer DNS name"
  value       = aws_lb.main.dns_name
}

output "website_url" {
  description = "Website URL"
  value       = "https://4edu.co.kr"
}

output "ssh_command" {
  description = "SSH command to connect to EC2"
  value       = "ssh -i superset-hackathon-key.pem ec2-user@${aws_instance.web.public_ip}"
}

output "private_key_path" {
  description = "Path to private key file"
  value       = "${path.module}/superset-hackathon-key.pem"
}

output "rds_endpoint" {
  description = "RDS PostgreSQL endpoint"
  value       = aws_db_instance.postgres.endpoint
}

output "rds_connection_string" {
  description = "PostgreSQL connection string for Superset"
  value       = "postgresql://supersetuser:SupersetHackathon2024!@${aws_db_instance.postgres.endpoint}/superset"
  sensitive   = true
}