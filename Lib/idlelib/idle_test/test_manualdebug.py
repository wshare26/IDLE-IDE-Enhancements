
import sys
import os


lib_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../'))
if lib_dir not in sys.path:
    sys.path.insert(0, lib_dir)


sys.path.insert(0, '/Users/idhantdas/.pyenv/versions/3.10.12/lib/python3.10')
import unittest
from unittest.mock import Mock, patch


from idlelib.manualdebug import ManualDebug


class ManualDebugTest(unittest.TestCase):
    """Test the ManualDebug class."""

    def setUp(self):
        """Set up test environment."""
        # Mock parent
        self.parent = Mock()
        self.parent.text = Mock()
        self.parent.text.index.return_value = "5.0"  # Simulate 5 lines
        
        # Create dialog
        self.dialog = ManualDebug(self.parent, _utest=True)
        
        # Mock dialog widgets
        self.dialog.frame = Mock()
        self.dialog.output_text = Mock()
        self.dialog.line_entry = Mock()
        self.dialog.line_var = Mock()
        self.dialog.buttons = {
            'Apply': Mock(),
            'Unapply': Mock(),
            'See Current Lines': Mock()
        }

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
        self.dialog.line_var.get.return_value = '1'
        self.dialog.apply()
        self.assertEqual(self.dialog.print_statements['1'], 'test print')
        
        # Test multiple valid lines
        self.dialog.line_var.get.return_value = '2,3'
        self.dialog.apply()
        self.assertEqual(self.dialog.print_statements['2'], 'test print')
        self.assertEqual(self.dialog.print_statements['3'], 'test print')
        
        # Test invalid line
        self.dialog.line_var.get.return_value = '10'
        self.dialog.apply()
        self.assertNotIn('10', self.dialog.print_statements)
        
        # Test duplicate line
        self.dialog.line_var.get.return_value = '1'
        self.dialog.apply()
        # Should not change existing statement
        self.assertEqual(self.dialog.print_statements['1'], 'test print')

    def test_cancel(self):
        """Test removing print statements."""
        # Setup test data
        self.dialog.print_statements = {'1': 'test1', '2': 'test2', '3': 'test3'}
        
        # Test removing single statement
        self.dialog.line_var.get.return_value = '1'
        self.dialog.cancel()
        self.assertNotIn('1', self.dialog.print_statements)
        
        # Test removing multiple statements
        self.dialog.line_var.get.return_value = '2,3'
        self.dialog.cancel()
        self.assertNotIn('2', self.dialog.print_statements)
        self.assertNotIn('3', self.dialog.print_statements)
        
        # Test removing non-existent statement
        self.dialog.line_var.get.return_value = '4'
        self.dialog.cancel()
        # Should not raise any error

    def test_show_current(self):
        """Test showing current print statements."""
        # Setup test data
        self.dialog.print_statements = {'1': 'test1', '2': 'test2'}
        
        # Test show_current
        self.dialog.show_current()
        self.dialog.output_text.config.assert_called_with(state="normal")
        self.dialog.output_text.delete.assert_called()
        self.dialog.output_text.insert.assert_called()

    def test_destroy(self):
        """Test dialog destruction."""
        self.assertIn(self.dialog, self.dialog.open_manual_debug_windows)
        self.dialog.destroy()
        self.assertNotIn(self.dialog, self.dialog.open_manual_debug_windows)


if __name__ == '__main__':
    unittest.main(verbosity=2)