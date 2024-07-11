// outputs.tf
output "api_gateway_endpoint" {
  value = module.api_gateway.endpoint_url
}

output "rds_postgres_endpoint" {
  value = module.rds_postgres.endpoint_address
}

// Define outputs for other resources as needed
