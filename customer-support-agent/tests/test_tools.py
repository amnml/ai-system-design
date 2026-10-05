import unittest
from types import SimpleNamespace

from google.adk.tools import FunctionTool

from support_agent.agent import root_agent
from support_agent.tools import (
    create_ticket,
    get_customer_details,
    get_order_details,
    get_ticket_details,
    search_knowledge_base,
)


class SupportToolsTest(unittest.TestCase):
    def setUp(self):
        self.context = SimpleNamespace(state={})

    def test_order_tracking(self):
        result = get_order_details(" ord-1001 ")
        self.assertEqual(result["status"], "success")
        self.assertEqual(result["order_status"], "shipped")
        self.assertEqual(result["tracking_number"], "DEMO-TRACK-001")
        self.assertEqual(get_customer_details()["order_ids"], ["ORD-1001", "ORD-1002"])

    def test_unknown_and_other_customer_orders_are_hidden(self):
        self.assertEqual(get_order_details("ORD-2001"), get_order_details("unknown"))
        self.assertEqual(get_order_details("ORD-2001")["status"], "error")

    def test_knowledge_lookup_and_no_match(self):
        articles = search_knowledge_base("What is your refund policy?")["articles"]
        self.assertEqual(articles[0]["article_id"], "KB-RETURNS")
        self.assertEqual(search_knowledge_base("weather")["status"], "not_found")

    def test_ticket_creation_lookup_and_retry(self):
        result = create_ticket("Missing parcel", "support", self.context)
        self.assertEqual(result["ticket"]["status"], "open")
        self.assertEqual(create_ticket("Missing parcel", "support", self.context), result)
        self.assertEqual(get_ticket_details("tkt-0001", self.context), result)
        self.assertEqual(len(self.context.state["tickets"]), 1)

    def test_sensitive_request_stays_pending(self):
        result = create_ticket("Refund ORD-1001", "human_review", self.context)
        self.assertEqual(result["ticket"]["status"], "pending_human_review")
        self.assertEqual(get_order_details("ORD-1001")["order_status"], "shipped")

    def test_ticket_isolation(self):
        create_ticket("Missing parcel", "support", self.context)
        other_session = SimpleNamespace(state={})
        self.assertEqual(get_ticket_details("TKT-0001", other_session)["status"], "error")

    def test_invalid_ticket_inputs(self):
        self.assertEqual(create_ticket(" ", "support", self.context)["status"], "error")
        self.assertEqual(create_ticket("Refund", "approved", self.context)["status"], "error")
        self.assertEqual(self.context.state, {})

    def test_adk_tool_schemas_hide_context(self):
        self.assertEqual(len(root_agent.tools), 5)
        for tool in root_agent.tools:
            declaration = FunctionTool(tool)._get_declaration()
            if declaration.parameters:
                self.assertNotIn("tool_context", declaration.parameters.properties)


if __name__ == "__main__":
    unittest.main()
