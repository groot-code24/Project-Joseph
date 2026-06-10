from dataclasses import dataclass, field


@dataclass
class RuleResult:
    triggered: bool
    section: str
    rationale: str


@dataclass
class GuardResult:
    decision: str
    violated_rules: list[str] = field(default_factory=list)
    cited_sections: list[str] = field(default_factory=list)
    rationale: str = ""
    is_escalation: bool = False


class PolicyGuard:
    def evaluate(
        self, order: dict, refund_history: list[dict], is_duplicate: bool
    ) -> GuardResult:
        duplicate = self._check_duplicate(is_duplicate)
        if duplicate.triggered:
            return GuardResult(
                decision="deny",
                violated_rules=[duplicate.section],
                cited_sections=[duplicate.section],
                rationale=duplicate.rationale,
            )

        delivery = self._check_delivery_status(order)
        if delivery.triggered:
            return GuardResult(
                decision="deny",
                violated_rules=[delivery.section],
                cited_sections=[delivery.section],
                rationale=delivery.rationale,
            )

        defective = self._check_defective(order)

        final_sale = self._check_final_sale(order)
        digital = self._check_digital_goods(order)
        window = self._check_return_window(order)
        gift = self._check_gift_order(order)

        deny_rules: list[RuleResult] = []
        if final_sale.triggered and not defective.triggered:
            deny_rules.append(final_sale)
        if digital.triggered:
            deny_rules.append(digital)
        if window.triggered:
            deny_rules.append(window)
        if gift.triggered:
            deny_rules.append(gift)

        escalate_rules: list[RuleResult] = []
        high_value = self._check_high_value(order)
        abuse = self._check_abuse(refund_history)
        if high_value.triggered:
            escalate_rules.append(high_value)
        if abuse.triggered:
            escalate_rules.append(abuse)

        if escalate_rules:
            sections = [r.section for r in escalate_rules]
            rationale = " ".join(r.rationale for r in escalate_rules)
            return GuardResult(
                decision="escalate",
                cited_sections=sections,
                rationale=rationale,
                is_escalation=True,
            )

        if deny_rules:
            sections = [r.section for r in deny_rules]
            rationale = " ".join(r.rationale for r in deny_rules)
            return GuardResult(
                decision="deny",
                violated_rules=sections,
                cited_sections=sections,
                rationale=rationale,
            )

        cited = []
        if defective.triggered:
            cited.append(defective.section)
            rationale = defective.rationale
        else:
            rationale = (
                "Request satisfies all policy requirements and falls within the "
                "standard return window."
            )
        cited.append("§1 STANDARD RETURN WINDOW")
        return GuardResult(decision="approve", cited_sections=cited, rationale=rationale)

    def _check_duplicate(self, is_duplicate: bool) -> RuleResult:
        section = "§8 DUPLICATE REFUND REQUESTS"
        if is_duplicate:
            return RuleResult(
                triggered=True,
                section=section,
                rationale="A refund for this order has already been resolved; only one resolution is permitted per order.",
            )
        return RuleResult(False, section, "No prior resolution found for this order.")

    def _check_delivery_status(self, order: dict) -> RuleResult:
        section = "§7 UNDELIVERED OR IN-TRANSIT ORDERS"
        status = order.get("status")
        if status != "delivered":
            return RuleResult(
                triggered=True,
                section=section,
                rationale=f"Order status is '{status}'. Orders not yet delivered are not eligible for a refund.",
            )
        return RuleResult(False, section, "Order has been delivered.")

    def _check_final_sale(self, order: dict) -> RuleResult:
        section = "§2 FINAL SALE ITEMS"
        if int(order.get("is_final_sale", 0)) == 1:
            return RuleResult(
                triggered=True,
                section=section,
                rationale="Item was marked Final Sale at purchase and is non-refundable.",
            )
        return RuleResult(False, section, "Item is not a Final Sale item.")

    def _check_digital_goods(self, order: dict) -> RuleResult:
        section = "§3 DIGITAL GOODS & SOFTWARE"
        if int(order.get("is_digital_good", 0)) == 1:
            return RuleResult(
                triggered=True,
                section=section,
                rationale="Digital goods are non-refundable once delivered or accessed; the defective exception does not apply to digital goods.",
            )
        return RuleResult(False, section, "Item is a physical good.")

    def _check_return_window(self, order: dict) -> RuleResult:
        section = "§1 STANDARD RETURN WINDOW"
        days = int(order.get("days_since_delivery", 0))
        if days > 30:
            return RuleResult(
                triggered=True,
                section=section,
                rationale=f"Request submitted {days} days after delivery, exceeding the 30-day return window.",
            )
        return RuleResult(False, section, f"Within the 30-day window ({days} days since delivery).")

    def _check_defective(self, order: dict) -> RuleResult:
        section = "§5 DEFECTIVE OR DAMAGED ITEMS"
        is_defective = int(order.get("is_defective", 0)) == 1
        is_digital = int(order.get("is_digital_good", 0)) == 1
        within_window = int(order.get("days_since_delivery", 0)) <= 30
        if is_defective and not is_digital and within_window:
            return RuleResult(
                triggered=True,
                section=section,
                rationale="Item reported as defective/damaged; eligible under §5 as a physical good within 30 days. This overrides Final Sale status.",
            )
        return RuleResult(False, section, "Defective exception does not apply.")

    def _check_high_value(self, order: dict) -> RuleResult:
        section = "§4 HIGH-VALUE ESCALATION THRESHOLD"
        if float(order.get("amount_usd", 0.0)) > 500.0:
            return RuleResult(
                triggered=True,
                section=section,
                rationale=f"Order value ${float(order['amount_usd']):.2f} exceeds $500.00 and must be escalated to a human agent.",
            )
        return RuleResult(False, section, "Order value is within the autonomous-decision threshold.")

    def _check_abuse(self, refund_history: list[dict]) -> RuleResult:
        section = "§6 REFUND ABUSE PREVENTION"
        count = len(refund_history)
        if count >= 3:
            return RuleResult(
                triggered=True,
                section=section,
                rationale=f"Customer has {count} approved/escalated refunds in the rolling 90-day window; subsequent requests require manual review.",
            )
        return RuleResult(False, section, "Customer refund frequency is within policy limits.")

    def _check_gift_order(self, order: dict) -> RuleResult:
        section = "§10 GIFT ORDERS"
        if str(order.get("product_category", "")).lower() == "gift":
            return RuleResult(
                triggered=True,
                section=section,
                rationale="Gift orders require the original order ID and proof of purchase from the original purchaser; denied pending documentation.",
            )
        return RuleResult(False, section, "Order is not a gift order.")
