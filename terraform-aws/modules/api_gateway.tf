// modules/api_gateway/main.tf
resource "aws_api_gateway_rest_api" "example" {
  name        = "example-api"
  description = "Example API Gateway"
  
  // Define API Gateway resources, methods, integrations, etc.
}
