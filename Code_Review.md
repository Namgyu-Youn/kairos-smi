# How it works?
1. SSH access requires 2 pieces of information.
  - "host", "ip", "port" : These informations are features of the server.
  - RSA((Rivest-Shamir-Adleman) key : The public key format   
2. It is also possible to occupy all GPUs by connecting all of the SSH servers in a specific local area.
  - **HEAD** : The local connected to all servers.
3. If HEAD connects all SSH servers at the same time, it becomes a kind of cluster.
4. Head can generate public RSA keys.
5. If you are not HEAD, then you can access the cluster by inputing the public RSA key.


# 2. Expected pros and cons
1. Pros
- By inputing the public RSA key, SSH (GPU) automatic distribution is possible.
- HEAD can monitor GPU usage on all servers in hand.

2. Cons
- Latency can occur.
- Storage synchronization problem: The user can be assigned a different server every time they connect.
