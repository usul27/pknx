Native KNX/IPNET library for Python
===================================

This library uses an IP socket connection to a KNX IP interface (like the Weinzierl 730). It does not need knxd or any
other external program to control devices on the KNX bus. 

The library support reads and writes to group addresses. It actively listens to the KNX bus and caches the state of
every group address. This greatly reduces the traffic on the KNX bus as read operations are usually fetched from the
cache.