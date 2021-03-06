# collabrative-text-editor-server

### Configuration
* Install the requirement.txt of the "collaborative_text_editor_python" folder.
* Launch the sever by using `python3 app.py`
* Test the demo on `0.0.0.0:5000`
* Verify the basic algorithm on the Doc Options of our froned-end layout.
* <img src="meeting_notes/options.png" width="275">

### Features

* User login
* Create and share documents
* Save the document on the server
* Real time collaborative editing with other users

### Code Structure & Implementation Detail

##### Code Structure 
    |-collaborative_text_editor_python
    |-- app.py        (including the implements of Basic / Mayer's diff / OT algorithm)
    |-- db_create.py  (including the database)
    |-- templates     (including the frond-end layout)
    |-- static        (including how we send, share, save DOC with front-end and back-end)

##### Basic Framework
* Socket io for DOC updating.
* Basic / Mayer's diff / OT algorithm for achieving collabrative edting.

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
##### Basic Deployment on Server
* We will get the doc directly from the updated status of the frond-end with specific shaing docID, then we will broadcast it to whole users who can get access to it.

```python
      document = Document.query.filter_by(docID=json["docID"]).first()
      document.content = json["doc"]
      db.session.commit()
      socketio.emit('DOC', json, room=json["docID"])
 ```
##### Mayers Deployment on Server
* For the mayer's implement, the patch which is the difference between our init_state and update_state will be used for updating DOC.

```python
      diff = myers_diff(init_state, update_state)
      for elem in diff:
            if isinstance(elem, Keep):
                print(' ' + elem.line)
            elif isinstance(elem, Insert):
                print('+' + elem.line)
            else:
                print('-' + elem.line)
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

### Evaluation
We successfully evaluate demo by inserting the x and y to the begining and end of the initial status "abc".
<img src="meeting_notes/evaluation.png">
