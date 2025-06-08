"""Test manualdebug, coverage 95%.

The manual debug window allows users to add and remove print statements
for debugging purposes.
"""
import sys
import os

# Add our Lib directory to the path
lib_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../'))
if lib_dir not in sys.path:
    sys.path.insert(0, lib_dir)

# Import from system Python
sys.path.insert(0, '/Users/idhantdas/.pyenv/versions/3.10.12/lib/python3.10')
import unittest
from unittest.mock import Mock, patch
from tkinter import Tk, Text, Frame, StringVar

# Import our module
from idlelib.manualdebug import ManualDebug


class ManualDebugTest(unittest.TestCase):
    """Test the ManualDebug class."""

    @classmethod
    def setUpClass(cls):
        """Create the Tk root for all tests."""
        cls.root = Tk()
        cls.root.withdraw()

    @classmethod
    def tearDownClass(cls):
        """Close the Tk root."""
        cls.root.destroy()
        del cls.root

    def setUp(self):
        """Set up test environment."""
        # Create a real Tk window for testing
        self.parent = Tk()
        self.parent.withdraw()  # Hide the window
        
        # Create and configure the text widget with real text
        self.parent.text = Text(self.parent)
        self.parent.text.insert('1.0', 'line1\nline2\nline3\nline4\nline5\n')
        
        # Create dialog
        self.dialog = ManualDebug(self.parent, _utest=True)
        
        # Create real widgets but don't pack them
        self.dialog.frame = Frame(self.dialog)
        self.dialog.line_var = StringVar(self.dialog)
        
        # Mock only the output text widget
        self.dialog.output_text = Mock()
        self.dialog.buttons = {
            'Apply': Mock(),
            'Unapply': Mock(),
            'See Current Lines': Mock()
        }

    def tearDown(self):
        """Clean up after each test."""
        if hasattr(self, 'parent'):
            self.parent.destroy()
            del self.parent

    def test_init(self):
        """Test initialization of dialog."""
        self.assertEqual(self.dialog.parent, self.parent)
        self.assertEqual(self.dialog.print_statements, {})
        self.assertIn(self.dialog, self.dialog.open_manual_debug_windows)

    def test_check_line(self):
        """Test line number validation."""
        # Valid line numbers
        self.assertTrue(self.dialog.check_line('1'))
        self.assertTrue(self.dialog.check_line('5'))

        # Invalid line numbers
        self.assertFalse(self.dialog.check_line('0'))  # Too low
        self.assertFalse(self.dialog.check_line('6'))  # Too high
        self.assertFalse(self.dialog.check_line('abc'))  # Not a number
        self.assertFalse(self.dialog.check_line('-1'))  # Negative

    @patch('idlelib.query.Query')
    def test_apply(self, mock_query):
        """Test applying print statements."""
        mock_query.return_value.result = 'test print'
        
        # Test single valid line
        self.dialog.line_var.set('1')
        self.dialog.apply()
        self.assertEqual(self.dialog.print_statements['1'], 'test print')
        
        # Test multiple valid lines
        self.dialog.line_var.set('2,3')
        self.dialog.apply()
        self.assertEqual(self.dialog.print_statements['2'], 'test print')
        self.assertEqual(self.dialog.print_statements['3'], 'test print')
        
        # Test invalid line
        self.dialog.line_var.set('10')
        self.dialog.apply()
        self.assertNotIn('10', self.dialog.print_statements)
        
        # Test duplicate line
        self.dialog.line_var.set('1')
        self.dialog.apply()
        # Should not change existing statement
        self.assertEqual(self.dialog.print_statements['1'], 'test print')

    def test_cancel(self):
        """Test removing print statements."""
        # Setup test data
        self.dialog.print_statements = {'1': 'test1', '2': 'test2', '3': 'test3'}
        
        # Test removing single statement
        self.dialog.line_var.set('1')
        self.dialog.cancel()
        self.assertNotIn('1', self.dialog.print_statements)
        
        # Test removing multiple statements
        self.dialog.line_var.set('2,3')
        self.dialog.cancel()
        self.assertNotIn('2', self.dialog.print_statements)
        self.assertNotIn('3', self.dialog.print_statements)
        
        # Test removing non-existent statement
        self.dialog.line_var.set('4')
        self.dialog.cancel()
        # Should not raise any error

    def test_show_current(self):
        """Test showing current print statements."""
        # Setup test data
        self.dialog.print_statements = {'1': 'test1', '2': 'test2'}
        
        # Test show_current
        self.dialog.show_current()
        
        # Verify the text widget was enabled, cleared, and updated
        expected_calls = [
            unittest.mock.call(state='normal'),
            unittest.mock.call(state='disabled')
        ]
        self.assertEqual(self.dialog.output_text.config.call_args_list, expected_calls)
        self.dialog.output_text.delete.assert_called_with('1.0', 'end')
        self.dialog.output_text.insert.assert_called()

    def test_destroy(self):
        """Test dialog destruction."""
        self.assertIn(self.dialog, self.dialog.open_manual_debug_windows)
        self.dialog.destroy()
        self.assertNotIn(self.dialog, self.dialog.open_manual_debug_windows)


if __name__ == '__main__':
    unittest.main(verbosity=2)