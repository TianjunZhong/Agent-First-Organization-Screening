# Install required packages in the root directory: pip install -e .
# Go to the parent folder of this file (multiple_choice), then Run python -m unittest test.py to test the code in this file.

import unittest
import json


from arklex.orchestrator.orchestrator import AgentOrg
from arklex.env.env import Env


class Logic_Test(unittest.TestCase):
    file_path = "test_cases.json"
    with open(file_path, "r", encoding="UTF-8") as f:
        TEST_CASES = json.load(f)

    @classmethod
    def setUpClass(cls):
        """Method to prepare the test fixture. Run BEFORE the test methods."""
        cls.user_prefix = "user"
        cls.worker_prefix = "assistant"
        file_path = "taskgraph.json"
        with open(file_path, "r", encoding="UTF-8") as f:
            cls.config = json.load(f)
        cls.env = Env(
            tools = cls.config.get("tools", []),
            workers = cls.config.get("workers", []),
            slotsfillapi = cls.config["slotfillapi"]
        )
        
    @classmethod
    def tearDownClass(cls):
        """Method to tear down the test fixture. Run AFTER the test methods."""
        pass
    
    def _get_api_bot_response(self, user_text, history, params):

        data = {"text": user_text, 'chat_history': history, 'parameters': params}
        orchestrator = AgentOrg(config=self.config, env=self.env)
        result = orchestrator.get_response(data)

        return result['answer'], result['parameters']

    def test_Unittest0(self):
        print("\n=============Unit Test 0=============")
        print(f"Task descrption: {self.TEST_CASES[0]['description']}")
        history = []
        params = {}
        nodes = []
        for node in self.config['nodes']:
            if node[1].get("type", "") == 'start':
                start_message = node[1]['attribute']["value"]
                break
        history.append({"role": self.worker_prefix, "content": start_message})
        
        assistant_messages = []
        for user_text in self.TEST_CASES[0]["user_utterance"]:
            print(f"User: {user_text}")
            output, params = self._get_api_bot_response(user_text, history, params)
            print(f"Bot: {output}")
            nodes.append(params.get("curr_node"))
            history.append({"role": self.user_prefix, "content": user_text})
            history.append({"role": self.worker_prefix, "content": output})
            assistant_messages.append(output)
        print(f"Success criteria: {self.TEST_CASES[0]['criteria']}")
        self.assertEqual(assistant_messages, self.TEST_CASES[0]["assistant_messages"])


if __name__ == '__main__':
    unittest.main()