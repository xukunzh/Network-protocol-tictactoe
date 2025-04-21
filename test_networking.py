import unittest
import socketio
import time

class TestNetworking(unittest.TestCase):
    def setUp(self):
        # Create Socket.IO test client
        self.sio = socketio.Client()
        self.received_events = []

        # Event handlers for test verification
        @self.sio.on('wait')
        def on_wait(data):
            self.received_events.append(('wait', data))

        @self.sio.on('start')
        def on_start(data):
            self.received_events.append(('start', data))

        @self.sio.on('chat')
        def on_chat(data):
            self.received_events.append(('chat', data))

        self.sio.connect('http://localhost:5001')
        time.sleep(0.5)

    def tearDown(self):
        self.sio.disconnect()

    def test_join_room(self):
        # Test if 'join' event results in 'wait' or 'start'
        self.sio.emit('join')
        time.sleep(1)  # Wait for server response
        events = [e[0] for e in self.received_events]
        self.assertTrue('wait' in events or 'start' in events)

    def test_chat_message(self):
        # Test if chat message can be sent and received
        self.sio.emit('join')
        time.sleep(1)
        self.sio.emit('chat', {
            'playerId': '1',
            'message': 'Hello from test client',
            # Use received room ID
            'room': self.received_events[0][1]['room']
        })
        time.sleep(1)
        events = [e[0] for e in self.received_events]
        self.assertIn('chat', events)

if __name__ == '__main__':
    unittest.main()
