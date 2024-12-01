import unittest
from unittest.mock import patch
from io import StringIO
import sys

# Adjusting the path to include the src directory
sys.path.insert(0, '../src')

from ada_dev_rag_py_ai.main import main

class TestOption4(unittest.TestCase):
    @patch('builtins.input', side_effect=['4', 'What is Visa?', '14'])
    @patch('sys.stdout', new_callable=StringIO)
    def test_ask_question(self, mock_stdout, mock_input):
        # Mock the QA chain response
        with patch('ada_dev_rag_py_ai.core.create_qa_chain') as mock_qa_chain:
            mock_qa_chain.return_value.invoke.return_value = {
                'answer': 'Visa is a global payments technology company.',
                'source_documents': [
                    {'metadata': {'source': 'source1.pdf', 'page': 1}},
                    {'metadata': {'source': 'source2.pdf', 'page': 2}}
                ]
            }
            main()

        # Capture the output
        output = mock_stdout.getvalue()

        # Validate the answer
        self.assertIn('Visa is a global payments technology company.', output)
        
        # Validate the source documents
        self.assertIn('Fonte 1: source1.pdf, Página: 1', output)
        self.assertIn('Fonte 2: source2.pdf, Página: 2', output)

if __name__ == '__main__':
    unittest.main()
