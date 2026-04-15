import pytest
from src.core.query_classifier import QueryClassifier, QueryCategory, QueryUrgency


class TestQueryClassifierRules:
    def setup_method(self):
        self.classifier = QueryClassifier(llm_provider=None)

    def test_classify_hr(self):
        result = self.classifier._rule_based_fallback("¿Cuántos días de vacaciones me corresponden?", {"found": False})
        assert result.category == QueryCategory.HR

    def test_classify_it(self):
        result = self.classifier._rule_based_fallback("No puedo entrar al sistema, olvidé mi contraseña", {"found": False})
        assert result.category == QueryCategory.IT_SUPPORT

    def test_classify_safety(self):
        result = self.classifier._rule_based_fallback("Hubo un accidente en el piso 3", {"found": False})
        assert result.category == QueryCategory.SAFETY
        assert result.urgency == QueryUrgency.HIGH

    def test_classify_finance(self):
        result = self.classifier._rule_based_fallback("¿Cómo solicito un reembolso de gastos?", {"found": False})
        assert result.category == QueryCategory.FINANCE

    def test_classify_operations(self):
        result = self.classifier._rule_based_fallback("¿Cuál es el proceso de aprobación?", {"found": False})
        assert result.category == QueryCategory.OPERATIONS

    def test_detect_sensitive_ssn(self):
        result = self.classifier._check_sensitive_data("Mi SSN es 123-45-6789")
        assert result["found"] is True

    def test_detect_sensitive_password(self):
        result = self.classifier._check_sensitive_data("password: secreto123")
        assert result["found"] is True

    def test_no_sensitive_normal(self):
        result = self.classifier._check_sensitive_data("¿Cuántos días de vacaciones tengo?")
        assert result["found"] is False

    def test_redact_sensitive(self):
        redacted = self.classifier._redact_sensitive("Mi SSN es 123-45-6789 y email juan@test.com")
        assert "123-45-6789" not in redacted
        assert "juan@test.com" not in redacted
        assert "[DATO_REDACTADO]" in redacted

    def test_force_escalation_harassment(self):
        result = self.classifier._rule_based_fallback("Quiero reportar acoso de mi jefe", {"found": False})
        result = self.classifier._apply_escalation_rules(result)
        assert result.requires_escalation is True
        assert result.urgency == QueryUrgency.CRITICAL

    def test_force_escalation_human(self):
        result = self.classifier._rule_based_fallback("Quiero hablar con un humano", {"found": False})
        result = self.classifier._apply_escalation_rules(result)
        assert result.requires_escalation is True


class TestQueryClassifierLLM:
    @pytest.mark.asyncio
    async def test_classify_with_llm(self, mock_llm):
        classifier = QueryClassifier(mock_llm)
        result = await classifier.classify("¿Cuántas vacaciones tengo?")
        assert result.category == QueryCategory.HR
        assert result.confidence >= 0.5
