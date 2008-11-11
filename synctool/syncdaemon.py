#!/usr/bin/python

# NIS to LDAP Sync Tool
# Copyright (C) 2008 Will Nowak <wan@ccs.neu.edu>

# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the
# Free Software Foundation, Inc.
# 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.

from SimpleXMLRPCServer import SimpleXMLRPCServer
from threading import Thread
import thread
import time
import logging

import nisldapsync.runner

logging.basicConfig(level=logging.DEBUG)

# Create server
server = SimpleXMLRPCServer(("0.0.0.0", 8000))

running = False

class syncthread(Thread):
  def __init__(self, modules=[]):
    Thread.__init__(self)
    self.modules=modules

  def run(self):
    global running
    running = True
    runner = nisldapsync.runner.Runner()
    runner.remoteexec(self.modules)
    running = False

# Register a function under a different name
def init_sync(x=[]):
  if not running:
    p = syncthread(x)
    p.start()
    return 'ok'
  return 'running'

server.register_function(init_sync, 'init')

# Run the server's main loop
server.serve_forever()
