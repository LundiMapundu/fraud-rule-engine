resource "aws_sns_topic" "fraud_alerts" {
  name = "${var.project_name}-fraud-alerts"
}
