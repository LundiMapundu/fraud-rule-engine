from fraud_engine.domain.enums import TransactionCategory
from fraud_engine.domain.models import CustomerRiskProfile
from fraud_engine.domain.rules.category_anomaly import CategoryAnomalyRule
from tests.unit.domain.rules.conftest import make_context, make_transaction


class TestCategoryAnomalyRule:
    def setup_method(self):
        self.rule = CategoryAnomalyRule()

    def test_usual_category_not_triggered(self):
        txn = make_transaction(category=TransactionCategory.GROCERIES)
        profile = CustomerRiskProfile(
            id="P1",
            customer_id="CUST001",
            usual_categories=["groceries", "fuel"],
        )
        ctx = make_context(transaction=txn, customer_profile=profile)
        result = self.rule.evaluate(ctx)
        assert not result.triggered

    def test_unusual_category_triggered(self):
        txn = make_transaction(category=TransactionCategory.ELECTRONICS)
        profile = CustomerRiskProfile(
            id="P1",
            customer_id="CUST001",
            usual_categories=["groceries", "fuel"],
        )
        ctx = make_context(transaction=txn, customer_profile=profile)
        result = self.rule.evaluate(ctx)
        assert result.triggered
        assert "electronics" in result.description.lower()

    def test_no_profile_not_triggered(self):
        txn = make_transaction(category=TransactionCategory.ELECTRONICS)
        ctx = make_context(transaction=txn, customer_profile=None)
        result = self.rule.evaluate(ctx)
        assert not result.triggered
