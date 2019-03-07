import unittest
from ot import Client
from operations import Add
import Queue

class Remotes(object):
    def __init__(self):
        self.remotes = []

    def process_messages(self):
        while True:
            if not any([remote.process_messages() for remote in self.remotes]):
                break

    def create(self, client):
        capturing_remote = Remote(client)
        self.remotes.append(capturing_remote)
        return capturing_remote


class Remote(object):
    def __init__(self, client):
        self.client = client
        self.args_queue = Queue.Queue()

    def send_message(self, *args):
        self.args_queue.put(args)

    def process_messages(self):
        had_messages = False
        try:
            while True:
                args = self.args_queue.get_nowait()
                self.client.receive(*args)
                had_messages = True
        except Queue.Empty:
            pass
        return had_messages

    def client_id(self):
        return self.client.client_id()


class TwoClients(object):
    def __init__(self):
        self.remotes = Remotes()

        self.client1 = Client()
        self.client2 = Client()

        self.remote_client1 = self.remotes.create(self.client1)
        self.remote_client2 = self.remotes.create(self.client2)

        self.client1.add_remote(self.remote_client2)
        self.client2.add_remote(self.remote_client1)


class ServerAndTwoClients(object):
    def __init__(self):
        self.remotes = Remotes()

        self.server = Client()
        self.client1 = Client()
        self.client2 = Client()

        self.remote_server = self.remotes.create(self.server)
        self.remote_client1 = self.remotes.create(self.client1)
        self.remote_client2 = self.remotes.create(self.client2)

        self.server.add_remote(self.remote_client1)
        self.server.add_remote(self.remote_client2)
        self.client1.add_remote(self.remote_server)
        self.client2.add_remote(self.remote_server)


class TestTransform(unittest.TestCase):
    def test_generating_operation_changes_data(self):
        client = Client()
        client.generate(Add(0, 'x'))
        self.assertEquals(client.data, ['x'])

    def test_connected_client_updates(self):
        f = TwoClients()

        f.client1.generate(Add(0, 'x'))

        f.remotes.process_messages()

        self.assertEquals(f.client1.data, ['x'])
        self.assertEquals(f.client2.data, ['x'])

    def test_conflicting_adds_are_reverted(self):
        f = TwoClients()

        f.client1.generate(Add(0, 'x'))
        f.client2.generate(Add(0, 'y'))

        self.assertEquals(f.client1.data, ['x'])
        self.assertEquals(f.client2.data, ['y'])

        f.remotes.process_messages()

        self.assertEquals(f.client1.data, [])
        self.assertEquals(f.client2.data, [])

    def test_multiple_concurrent_pending_message_are_reverted(self):
        f = TwoClients()

        f.client1.generate(Add(0, 'x'))
        f.client1.generate(Add(1, 'y'))

        f.client2.generate(Add(0, 'o'))

        self.assertEquals(f.client1.data, ['x', 'y'])
        self.assertEquals(f.client2.data, ['o'])

        f.remotes.process_messages()

        self.assertEquals(f.client1.data, [])
        self.assertEquals(f.client2.data, [])

    def test_multiple_pending_messages_are_applied(self):
        f = TwoClients()

        f.client1.generate(Add(0, 'x'))
        f.client1.generate(Add(1, 'y'))
        f.remotes.process_messages()

        f.client2.generate(Add(0, 'o'))
        f.remotes.process_messages()

        self.assertEquals(f.client1.data, ['o', 'x', 'y'])
        self.assertEquals(f.client2.data, ['o', 'x', 'y'])

    def test_operations_are_forwarded_to_multiple_clients(self):
        f = ServerAndTwoClients()

        f.client1.generate(Add(0, 'x'))
        f.client1.generate(Add(1, 'y'))
        f.remotes.process_messages()

        self.assertEquals(f.client1.data, ['x', 'y'])
        self.assertEquals(f.client2.data, ['x', 'y'])

        f.client2.generate(Add(0, 'o'))
        f.remotes.process_messages()

        self.assertEquals(f.client1.data, ['o', 'x', 'y'])
        self.assertEquals(f.client2.data, ['o', 'x', 'y'])

    def test_conflicting_adds_are_reverted_with_server(self):
        f = ServerAndTwoClients()

        f.client1.generate(Add(0, 'x'))
        f.client2.generate(Add(0, 'y'))

        self.assertEquals(f.client1.data, ['x'])
        self.assertEquals(f.client2.data, ['y'])

        f.remotes.process_messages()

        self.assertEquals(f.client1.data, [])
        self.assertEquals(f.client2.data, [])
