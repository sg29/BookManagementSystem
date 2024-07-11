// main.tf
module "api_gateway" {
  source = "./modules/api_gateway"
  // Specify module variables if needed
}

module "rds_postgres" {
  source = "./modules/rds_postgres"
  // Specify module variables if needed
}

module "kafka" {
  source = "./modules/kafka"
  // Specify module variables if needed
}

module "elasticache" {
  source = "./modules/elasticache"
  // Specify module variables if needed
}

module "sagemaker" {
  source = "./modules/sagemaker"
  // Specify module variables if needed
}
