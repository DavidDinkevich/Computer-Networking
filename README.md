# Syncer
A cross-platform cloud file-backup service complete with a desktop client and server. Currently has support for Windows and Linux.<br>
Clients can:<br>
* Connect to the server at any time and register an account (including in parallel).
* Choose a directory to be tracked, and any changes in the directory are backed up to the server autonomously.
* Open multiple instances of the same account across an unlimited amount of computers, and changes in each instance are synced with the others.

<b>Tools:</b>
* Syncing and file transfers are done over TCP connections
* <i>Watchdog</i> - python library for tracking changes in directories
