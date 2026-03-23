from __future__ import annotations


class DomainError(Exception):
    pass


class TransactionNotFoundError(DomainError):
    def __init__(self, transaction_id: str) -> None:
        super().__init__(f"Transaction not found: {transaction_id}")
        self.transaction_id = transaction_id


class RuleNotFoundError(DomainError):
    def __init__(self, rule_id: str) -> None:
        super().__init__(f"Rule not found: {rule_id}")
        self.rule_id = rule_id


class AlertNotFoundError(DomainError):
    def __init__(self, alert_id: str) -> None:
        super().__init__(f"Alert not found: {alert_id}")
        self.alert_id = alert_id


class CustomerNotFoundError(DomainError):
    def __init__(self, customer_id: str) -> None:
        super().__init__(f"Customer not found: {customer_id}")
        self.customer_id = customer_id


class RuleEvaluationError(DomainError):
    def __init__(self, rule_name: str, reason: str) -> None:
        super().__init__(f"Rule evaluation failed for '{rule_name}': {reason}")
        self.rule_name = rule_name
        self.reason = reason


class InvalidTransitionError(DomainError):
    def __init__(self, from_status: str, to_status: str) -> None:
        super().__init__(f"Invalid status transition: {from_status} -> {to_status}")
