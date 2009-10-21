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
import datetime
import gflags
import logging
import mutex
import os
import sys
import time
import thread
import threading

import nisldapsync.runner

gflags.DEFINE_string('pidfile', '/var/run/ldapsyncdaemon.pid',
                     'PID File Path')
gflags.DEFINE_string('logfile', '/var/log/ldapsyncdaemon.log', 'Log Filename')
gflags.DEFINE_boolean('debug', False, 'Enable/Disable debug logging.')
gflags.DEFINE_boolean('daemonize', True, 'Enable/Disable spawning a daemon.')
FLAGS = gflags.FLAGS

class SyncDaemon(object):
  def __init__(self):
    self.modules = ['passwd', 'automount', 'group', 'appgroup', 'hosts', 
                    'ldapbase']
    self.mutex = mutex.mutex()

  def DoSync(self):
    if self.mutex.testandset():
      logging.info('Starting sync run')
      runner = nisldapsync.runner.Runner()
      runner.remoteexec(self.modules, 'debug')
      logging.info('Sync run complete')
      self.mutex.unlock()
    else:
      logging.warning('Could not start sync, already running')

  def Run(self):
    while True:
      now = datetime.datetime.now()
      if (now.minute % 5 == 0) and (now.second == 0):
        syncthread = threading.Thread(target=self.DoSync)
        syncthread.start()
      time.sleep(1)

  def Daemonize(self):
    """Turns the running process into a daemon."""
    # first fork
    pid = os.fork()
    if pid > 0:
      sys.exit(0)
    os.chdir('/')
    os.setsid()
    os.umask(0)
    # second fork
    pid = os.fork()
    if pid > 0:
      open(FLAGS.pidfile, 'w').write(str(pid))
      sys.exit(0)

  def Main(self):
    logging.basicConfig(filename=FLAGS.logfile, level=logging.DEBUG,
                        format='%(asctime)s %(name)s %(levelname)s'
                               ' %(message)s')
    if FLAGS.daemonize:
      self.Daemonize()
    self.Run()

if __name__ == '__main__':
  FLAGS(sys.argv)
  sd = SyncDaemon()
  sd.Main()
