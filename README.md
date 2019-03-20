# collabrative-text-editor-server

### Features

* User login
* Create and share documents
* Save the document on the server
* Real time collaborative editing with other users

### Implementation Detail

##### Client Document Storage

* To avoid naming conflict, such as both users create documents with same name while not sharing with each other, we give each document a unique id and match that id with user's document name.

  ```python
  docID = str(uuid.uuid4())
  ```

* We used sqlAlchemy as our database to keep this relationship

  ```python
  class User(db.Model):
      userID = db.Column(db.String, primary_key=True)
      docName = db.Column(db.String, primary_key=True, nullable=True)
      docID = db.Column(db.String, nullable=True)
  ```

##### OT Deployment on Server

* We have a queue that holds all the operations passed by the user. Every time a user pass operation to the server, server will queue up the operation and pop a operation

* The queue won't actually pop the operation. Instead, it retrieves the operation and move the head pointer to next element. We want the server to keep previous operation as a reference of which operations the current operation needs to transfer with

  ```python
  class MyQueue():
      queue = []
      head = None
  
      def push(self, op):
          self.queue.append(op)
          if self.head == None:
              self.head = 0
  
      def pop(self):
          print(self.queue)
          temp = self.queue[self.head]
          self.head += 1
          return temp
  
  ```

  

* All queue operations are protected by the lock to get rid of race condition

* Along with the operation, the client will pass a version number representing the state of document while the client passing this operation. Our server also keeps a version, which is always ahead or equal to that of clients'

* The server will then check the version of the operation and server version. If the version is behind, the server will apply OT on the operation with all the previous operations between the version difference

  ```python
  while cur_version < server_version:
              OT = OT_String("verbose")
              prev_ops = MyQueue.queue[cur_version][0]
  			      op = OT.transform(prev_ops, op)[1]
          		retain = {'retain': op['index']}
              op.pop('index')
              op = [retain, op]
              cur_version += 1
  ```

  

* After finishing OT, the server will apply the transformed operation on its document and pass the document to all the clients.