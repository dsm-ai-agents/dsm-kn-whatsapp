"""
WhatsApp AI Chatbot - Enhanced Webhook Processing Tests
=====================================================
Comprehensive tests for the enhanced webhook processing system including
message status tracking, all webhook event types, and database integration.

Author: Rian Infotech
Version: 1.0 (Enhanced Webhook Testing)
"""

import unittest
import json
import sys
import os
from unittest.mock import patch, MagicMock
from datetime import datetime, timezone

# Add the project root to the path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Import the Flask app and components
from app import app
from src.handlers.webhook_handler import (
    process_webhook_event,
    process_messages_upsert,
    process_message_sent,
    process_message_receipt_update,
    process_messages_update,
    extract_message_id_from_webhook,
    extract_phone_number_from_webhook
)
from src.core.supabase_client import get_supabase_manager

class TestWebhookProcessing(unittest.TestCase):
    """Test enhanced webhook processing functionality."""

    def setUp(self):
        """Set up test environment."""
        self.app = app.test_client()
        self.app.testing = True
        
        # Sample webhook data for different event types
        self.sample_messages_upsert = {
            "event": "messages.upsert",
            "data": {
                "messages": {
                    "key": {
                        "remoteJid": "919876543210@s.whatsapp.net",
                        "fromMe": False,
                        "id": "test_msg_001"
                    },
                    "message": {
                        "conversation": "Hello, I need help with my order"
                    },
                    "messageTimestamp": 1640995200
                }
            }
        }
        
        self.sample_message_sent = {
            "event": "message.sent",
            "data": {
                "message_id": "test_msg_002",
                "to": "919876543210@s.whatsapp.net",
                "from": "bot@s.whatsapp.net",
                "timestamp": 1640995300,
                "status": "sent"
            }
        }
        
        self.sample_message_receipt = {
            "event": "message-receipt.update",
            "data": {
                "message_id": "test_msg_002",
                "from": "919876543210@s.whatsapp.net",
                "receipt": {
                    "type": "delivered"
                },
                "timestamp": 1640995400
            }
        }
        
        self.sample_message_read_receipt = {
            "event": "message-receipt.update",
            "data": {
                "message_id": "test_msg_002",
                "from": "919876543210@s.whatsapp.net",
                "receipt": {
                    "type": "read"
                },
                "timestamp": 1640995500
            }
        }
        
        self.sample_messages_update = {
            "event": "messages.update",
            "data": {
                "message_id": "test_msg_003",
                "from": "919876543210@s.whatsapp.net",
                "update_type": "edit",
                "new_content": "Updated message content"
            }
        }

    def test_webhook_endpoint_messages_upsert(self):
        """Test webhook endpoint with messages.upsert event."""
        response = self.app.post('/webhook',
                               data=json.dumps(self.sample_messages_upsert),
                               content_type='application/json')
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(data['status'], 'success')
        self.assertEqual(data['event_type'], 'messages.upsert')

    def test_webhook_endpoint_message_sent(self):
        """Test webhook endpoint with message.sent event."""
        response = self.app.post('/webhook',
                               data=json.dumps(self.sample_message_sent),
                               content_type='application/json')
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(data['status'], 'success')
        self.assertEqual(data['event_type'], 'message.sent')

    def test_webhook_endpoint_message_receipt(self):
        """Test webhook endpoint with message-receipt.update event."""
        response = self.app.post('/webhook',
                               data=json.dumps(self.sample_message_receipt),
                               content_type='application/json')
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(data['status'], 'success')
        self.assertEqual(data['event_type'], 'message-receipt.update')

    def test_webhook_endpoint_empty_data(self):
        """Test webhook endpoint with empty data."""
        response = self.app.post('/webhook',
                               data='',
                               content_type='application/json')
        
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.data)
        self.assertEqual(data['status'], 'error')

    def test_webhook_endpoint_invalid_json(self):
        """Test webhook endpoint with invalid JSON."""
        response = self.app.post('/webhook',
                               data='invalid json',
                               content_type='application/json')
        
        self.assertEqual(response.status_code, 400)

    @patch('src.handlers.webhook_handler.get_supabase_manager')
    @patch('src.handlers.message_processor.process_incoming_message')
    def test_process_messages_upsert(self, mock_process_message, mock_supabase):
        """Test processing messages.upsert event."""
        # Mock successful message processing
        mock_process_message.return_value = (True, "Message processed successfully")
        
        # Mock Supabase manager
        mock_supabase_instance = MagicMock()
        mock_supabase_instance.is_connected.return_value = True
        mock_supabase_instance.log_webhook_event.return_value = True
        mock_supabase.return_value = mock_supabase_instance
        
        success, message = process_messages_upsert(self.sample_messages_upsert)
        
        self.assertTrue(success)
        self.assertEqual(message, "Message processed successfully")
        mock_process_message.assert_called_once()
        mock_supabase_instance.log_webhook_event.assert_called()

    @patch('src.handlers.webhook_handler.get_supabase_manager')
    def test_process_message_sent(self, mock_supabase):
        """Test processing message.sent event."""
        # Mock Supabase manager
        mock_supabase_instance = MagicMock()
        mock_supabase_instance.is_connected.return_value = True
        mock_supabase_instance.update_message_status.return_value = True
        mock_supabase_instance.log_webhook_event.return_value = True
        mock_supabase.return_value = mock_supabase_instance
        
        success, message = process_message_sent(self.sample_message_sent)
        
        self.assertTrue(success)
        self.assertIn("marked as sent", message)
        mock_supabase_instance.update_message_status.assert_called_once_with(
            "919876543210@s.whatsapp.net", "test_msg_002", "sent"
        )

    @patch('src.handlers.webhook_handler.get_supabase_manager')
    def test_process_message_receipt_delivered(self, mock_supabase):
        """Test processing message-receipt.update event for delivered status."""
        # Mock Supabase manager
        mock_supabase_instance = MagicMock()
        mock_supabase_instance.is_connected.return_value = True
        mock_supabase_instance.update_message_status.return_value = True
        mock_supabase_instance.log_webhook_event.return_value = True
        mock_supabase.return_value = mock_supabase_instance
        
        success, message = process_message_receipt_update(self.sample_message_receipt)
        
        self.assertTrue(success)
        self.assertIn("marked as delivered", message)
        mock_supabase_instance.update_message_status.assert_called_once_with(
            "919876543210@s.whatsapp.net", "test_msg_002", "delivered"
        )

    @patch('src.handlers.webhook_handler.get_supabase_manager')
    def test_process_message_receipt_read(self, mock_supabase):
        """Test processing message-receipt.update event for read status."""
        # Mock Supabase manager
        mock_supabase_instance = MagicMock()
        mock_supabase_instance.is_connected.return_value = True
        mock_supabase_instance.update_message_status.return_value = True
        mock_supabase_instance.log_webhook_event.return_value = True
        mock_supabase.return_value = mock_supabase_instance
        
        success, message = process_message_receipt_update(self.sample_message_read_receipt)
        
        self.assertTrue(success)
        self.assertIn("marked as read", message)
        mock_supabase_instance.update_message_status.assert_called_once_with(
            "919876543210@s.whatsapp.net", "test_msg_002", "read"
        )

    @patch('src.handlers.webhook_handler.get_supabase_manager')
    def test_process_messages_update(self, mock_supabase):
        """Test processing messages.update event."""
        # Mock Supabase manager
        mock_supabase_instance = MagicMock()
        mock_supabase_instance.is_connected.return_value = True
        mock_supabase_instance.log_webhook_event.return_value = True
        mock_supabase.return_value = mock_supabase_instance
        
        success, message = process_messages_update(self.sample_messages_update)
        
        self.assertTrue(success)
        self.assertIn("Message update event processed", message)
        mock_supabase_instance.log_webhook_event.assert_called()

    def test_process_webhook_event_unknown_type(self):
        """Test processing unknown webhook event type."""
        unknown_webhook = {
            "event": "unknown.event.type",
            "data": {"some": "data"}
        }
        
        success, message = process_webhook_event(unknown_webhook)
        
        self.assertTrue(success)
        self.assertIn("Unknown event type", message)

    def test_extract_message_id_from_webhook(self):
        """Test extracting message ID from various webhook formats."""
        # Test with message_id in data
        webhook1 = {"data": {"message_id": "msg_123"}}
        self.assertEqual(extract_message_id_from_webhook(webhook1), "msg_123")
        
        # Test with id in key
        webhook2 = {"data": {"key": {"id": "msg_456"}}}
        self.assertEqual(extract_message_id_from_webhook(webhook2), "msg_456")
        
        # Test with direct id
        webhook3 = {"data": {"id": "msg_789"}}
        self.assertEqual(extract_message_id_from_webhook(webhook3), "msg_789")
        
        # Test with no message ID
        webhook4 = {"data": {"other": "data"}}
        self.assertIsNone(extract_message_id_from_webhook(webhook4))

    def test_extract_phone_number_from_webhook(self):
        """Test extracting phone number from various webhook formats."""
        # Test with remoteJid in key
        webhook1 = {"data": {"key": {"remoteJid": "919876543210@s.whatsapp.net"}}}
        self.assertEqual(extract_phone_number_from_webhook(webhook1), "919876543210@s.whatsapp.net")
        
        # Test with from field
        webhook2 = {"data": {"from": "919876543210@s.whatsapp.net"}}
        self.assertEqual(extract_phone_number_from_webhook(webhook2), "919876543210@s.whatsapp.net")
        
        # Test with to field
        webhook3 = {"data": {"to": "919876543210@s.whatsapp.net"}}
        self.assertEqual(extract_phone_number_from_webhook(webhook3), "919876543210@s.whatsapp.net")
        
        # Test with no phone number
        webhook4 = {"data": {"other": "data"}}
        self.assertIsNone(extract_phone_number_from_webhook(webhook4))

    @patch('src.handlers.webhook_handler.get_supabase_manager')
    def test_webhook_processing_with_supabase_disconnected(self, mock_supabase):
        """Test webhook processing when Supabase is disconnected."""
        # Mock Supabase manager as disconnected
        mock_supabase_instance = MagicMock()
        mock_supabase_instance.is_connected.return_value = False
        mock_supabase.return_value = mock_supabase_instance
        
        success, message = process_message_sent(self.sample_message_sent)
        
        # Should still succeed but without database updates
        self.assertTrue(success)
        mock_supabase_instance.update_message_status.assert_not_called()

    def test_webhook_event_routing(self):
        """Test that webhook events are routed to correct processors."""
        # Test messages.upsert routing
        with patch('src.handlers.webhook_handler.process_messages_upsert') as mock_upsert:
            mock_upsert.return_value = (True, "Processed")
            process_webhook_event(self.sample_messages_upsert)
            mock_upsert.assert_called_once()
        
        # Test message.sent routing
        with patch('src.handlers.webhook_handler.process_message_sent') as mock_sent:
            mock_sent.return_value = (True, "Processed")
            process_webhook_event(self.sample_message_sent)
            mock_sent.assert_called_once()
        
        # Test message-receipt.update routing
        with patch('src.handlers.webhook_handler.process_message_receipt_update') as mock_receipt:
            mock_receipt.return_value = (True, "Processed")
            process_webhook_event(self.sample_message_receipt)
            mock_receipt.assert_called_once()
        
        # Test messages.update routing
        with patch('src.handlers.webhook_handler.process_messages_update') as mock_update:
            mock_update.return_value = (True, "Processed")
            process_webhook_event(self.sample_messages_update)
            mock_update.assert_called_once()

    @patch('src.handlers.webhook_handler.logger')
    def test_error_handling_in_webhook_processing(self, mock_logger):
        """Test error handling in webhook processing."""
        # Test with malformed webhook data
        malformed_webhook = {"invalid": "structure"}
        
        success, message = process_webhook_event(malformed_webhook)
        
        # Should handle gracefully
        self.assertTrue(success)  # Unknown events return True
        self.assertIn("Unknown event type", message)

    def test_message_status_progression(self):
        """Test the complete message status progression."""
        with patch('src.handlers.webhook_handler.get_supabase_manager') as mock_supabase:
            mock_supabase_instance = MagicMock()
            mock_supabase_instance.is_connected.return_value = True
            mock_supabase_instance.update_message_status.return_value = True
            mock_supabase_instance.log_webhook_event.return_value = True
            mock_supabase.return_value = mock_supabase_instance
            
            # 1. Message sent
            success1, _ = process_message_sent(self.sample_message_sent)
            self.assertTrue(success1)
            
            # 2. Message delivered
            success2, _ = process_message_receipt_update(self.sample_message_receipt)
            self.assertTrue(success2)
            
            # 3. Message read
            success3, _ = process_message_receipt_update(self.sample_message_read_receipt)
            self.assertTrue(success3)
            
            # Verify all status updates were called
            expected_calls = [
                unittest.mock.call("919876543210@s.whatsapp.net", "test_msg_002", "sent"),
                unittest.mock.call("919876543210@s.whatsapp.net", "test_msg_002", "delivered"),
                unittest.mock.call("919876543210@s.whatsapp.net", "test_msg_002", "read")
            ]
            mock_supabase_instance.update_message_status.assert_has_calls(expected_calls)


class TestWebhookDatabaseIntegration(unittest.TestCase):
    """Test webhook processing database integration."""

    def setUp(self):
        """Set up test environment."""
        self.app = app.test_client()
        self.app.testing = True

    @patch('src.core.supabase_client.create_client')
    def test_webhook_event_logging(self, mock_create_client):
        """Test that webhook events are properly logged to database."""
        # Mock Supabase client
        mock_client = MagicMock()
        mock_table = MagicMock()
        mock_client.table.return_value = mock_table
        mock_table.insert.return_value.execute.return_value.data = [{"id": "test_id"}]
        mock_create_client.return_value = mock_client
        
        # Get Supabase manager and test logging
        supabase = get_supabase_manager()
        
        # Test webhook event logging
        test_event_data = {"event": "test", "data": {"test": "data"}}
        result = supabase.log_webhook_event("test.event", test_event_data, "processed")
        
        # Verify logging was attempted
        self.assertTrue(result)

    def test_message_status_update_integration(self):
        """Test message status update integration."""
        # This would be an integration test with actual database
        # For now, we'll test the structure
        sample_webhook = {
            "event": "message.sent",
            "data": {
                "message_id": "integration_test_msg",
                "to": "919876543210@s.whatsapp.net",
                "status": "sent"
            }
        }
        
        # Test webhook endpoint
        response = self.app.post('/webhook',
                               data=json.dumps(sample_webhook),
                               content_type='application/json')
        
        self.assertEqual(response.status_code, 200)


if __name__ == '__main__':
    # Create test suite
    test_suite = unittest.TestSuite()
    
    # Add test classes
    test_suite.addTest(unittest.makeSuite(TestWebhookProcessing))
    test_suite.addTest(unittest.makeSuite(TestWebhookDatabaseIntegration))
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(test_suite)
    
    # Print summary
    print(f"\n{'='*60}")
    print(f"TEST SUMMARY")
    print(f"{'='*60}")
    print(f"Tests run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print(f"Success rate: {((result.testsRun - len(result.failures) - len(result.errors)) / result.testsRun * 100):.1f}%")
    
    if result.failures:
        print(f"\nFAILURES:")
        for test, traceback in result.failures:
            print(f"- {test}: {traceback.split('AssertionError:')[-1].strip()}")
    
    if result.errors:
        print(f"\nERRORS:")
        for test, traceback in result.errors:
            print(f"- {test}: {traceback.split('Error:')[-1].strip()}")