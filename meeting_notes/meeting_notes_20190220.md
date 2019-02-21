# collabrative-text-editor-server
## Meeting Notes:
### Date 2019.2.20

## Idea discussion
* This week we looked into how to solve the race condition when users edit the same portion documents. 
Currently, We found the `Operational transformation` be a potential solution.

## Completed this week
* We have designed the initial version of frontend using the Javascript.
* We have decided our server backend using the Flask web framework, and built it in our localhost.
* We discussed our idea on the collabrative logic and implemented the simple text model.

## Paper read
* We look at some reference paper as follows:
  * Event-driven Programming for Robust Software 
  * Formalization and Veriﬁcation of Event-driven Process Chains 
  * SunOS Multi-thread Architecture 
  * Scheduler Activations: Effective Kernel Support for the User-Level Management of Parallelism 
  * Capriccio: Scalable Threads for Internet Services 
  * SEDA: An Architecture for Well-Conditioned, Scalable Internet Services
  * The Andrew File System
  * Coda file system
  
## To do 
* Plan to continue to render the frondend layout to make it better.
* Achieve the collabrative editing between two users on one document.

## Problem
* The basic problems which we are trying to solve are:
  * Convergence
  * Causal order 
  * Cntention preservation
* Now, we are considering the intention preservation problem, which using the OT algorithm to achieve it or maybe it would be better that we can lauch the other simple lock session to supervise the user's action to solve it.


## Trello
https://trello.com/b/mojw0uyH/os-251
