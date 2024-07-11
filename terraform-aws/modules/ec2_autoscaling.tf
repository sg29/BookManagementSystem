// modules/ec2_autoscaling/main.tf

// Variables
variable "service_name" {
  description = "Name of the service"
}

variable "ami_id" {
  description = "AMI ID for the EC2 instance"
}

variable "instance_type" {
  description = "EC2 instance type"
}

variable "subnet_ids" {
  description = "List of subnet IDs in different AZs"
  type        = list(string)
}

variable "min_instances" {
  description = "Minimum number of instances"
  default     = 2
}

variable "desired_capacity" {
  description = "Desired number of instances"
  default     = 2
}

variable "max_instances" {
  description = "Maximum number of instances"
  default     = 10
}

variable "scale_out_threshold" {
  description = "Scale out threshold in percentage"
  default     = 70
}

variable "scale_in_threshold" {
  description = "Scale in threshold in percentage"
  default     = 30
}

// Launch Configuration
resource "aws_launch_configuration" "example" {
  name_prefix          = "${var.service_name}-lc"
  image_id             = var.ami_id
  instance_type        = var.instance_type
  security_groups      = [aws_security_group.instance.id]
  key_name             = "your_key_name"
  user_data            = <<EOF
    #!/bin/bash
    # Custom user data script for your service (optional)
    echo "This instance is serving ${var.service_name}"
    EOF

  lifecycle {
    create_before_destroy = true
  }
}

// Auto Scaling Group
resource "aws_autoscaling_group" "example" {
  name                      = "${var.service_name}-asg"
  launch_configuration      = aws_launch_configuration.example.id
  min_size                  = var.min_instances
  desired_capacity          = var.desired_capacity
  max_size                  = var.max_instances
  vpc_zone_identifier       = var.subnet_ids
  health_check_type         = "EC2"
  health_check_grace_period = 300
  force_delete              = true

  // Scaling Policies
  scaling_policy {
    name                   = "scale-out"
    adjustment_type        = "ChangeInCapacity"
    scaling_adjustment     = 1
    cooldown               = 300
    policy_type            = "SimpleScaling"
    estimated_instance_warmup = 300
  }

  scaling_policy {
    name                   = "scale-in"
    adjustment_type        = "ChangeInCapacity"
    scaling_adjustment     = -1
    cooldown               = 300
    policy_type            = "SimpleScaling"
    estimated_instance_warmup = 300
  }

  // Target Tracking Scaling Policy
  dynamic "scaling_policy" {
    for_each = {
      name  = "target-tracking-scaling-policy"
      scale_out_threshold = var.scale_out_threshold
      scale_in_threshold  = var.scale_in_threshold
    }
    content {
      name                     = scaling_policy.value["name"]
      target_tracking_configuration {
        predefined_metric_specification {
          predefined_metric_type = "ASGAverageCPUUtilization"
        }
        target_value             = scaling_policy.value["scale_out_threshold"] == var.scale_out_threshold ? 70.0 : 30.0
        disable_scale_in         = scaling_policy.value["scale_in_threshold"] == var.scale_in_threshold ? false : true
      }
    }
  }

  lifecycle {
    create_before_destroy = true
  }
}

// IAM Policy for Auto Scaling Group
resource "aws_iam_role_policy_attachment" "example" {
  role       = aws_iam_role.instance_role.name
  policy_arn = aws_iam_policy.example.arn
}

// Security Group
resource "aws_security_group" "instance" {
  Book Review Summary service is A services
