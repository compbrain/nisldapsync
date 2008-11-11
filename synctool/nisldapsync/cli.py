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

# Standard Imports
import logging
import sys
from optparse import OptionParser

# Site Imports
import nisldapsync
import nisldapsync.group
import nisldapsync.hosts
import nisldapsync.passwd
import nisldapsync.automount
import nisldapsync.netgroup
import nisldapsync.syncconfigfile

SYNC_MODS = {
             'netgroup':nisldapsync.netgroup.NetgroupSync,
             'passwd': nisldapsync.passwd.PasswdSync,
             'hosts':nisldapsync.hosts.HostsSync,
             'group':nisldapsync.group.GroupSync,
             'automount':nisldapsync.automount.AutomountSync,
            }

class MasterSync:
  def __init__(self):
    self._l = logging.getLogger('ldapsync')
    self._config = None
    self._l.debug('Instantiating Master Sync Object')
  
  def getConfig(self):
    if self._config is None:
      self._l.debug('Reading Sync Config File')
      self._config = nisldapsync.syncconfigfile.SyncConfigFile()

  def syncobj(self, module):
    self.getConfig()
    if module not in SYNC_MODS:
      self._l.error('Attempted to create sync object for unsupported %s mod' % 
                    (module))
      sys.exit(255)
    # LDAP/Site Info retrival from the config file
    ldapbase = self._config.getLDAPConnectionInfo()['searchbase']
    mapbaseou = self._config.getLDAPLayout()['%sou' % module]
    maildomain = self._config.getSiteInfo()['maildomain']
    # Create the sync object
    sync_mod = SYNC_MODS[module]
    sync_obj = sync_mod(ldapbase=ldapbase, baseou=mapbaseou,
                        maildomain=maildomain)
    self._l.debug('Created %s sync object' % module)
    return sync_obj

  def getDiffDict(self, maptype=None):
    # Create a list of maps to process
    if maptype is None:
      maptype = SYNC_MODS.keys()
    elif type(maptype) == type(''):
      maptype = [maptype]
    elif type(maptype) == type([]):
      pass
    self._l.info('Getting diff for maps %s' % (str(maptype)))
    # Collect changes that need to be made
    changedict = {}
    for map in maptype:
      obj = self.syncobj(map)
      changes = obj.generateMapChangeList()
      changedict[map] = changes
      self._l.debug('Added %s %s changes to the list' % (len(changes), map))
    return changedict

  def applychangedict(self, changedict):
    self._l.info('Beginning change application')
    for map in changedict:
      self._l.info('Applying changes for %s' % map)
      for change in changedict[map]:
        change.apply()

  def main(self):
    parser = OptionParser()
    parser.add_option('-d', '--debug', dest='debuglvl', help='Debug Level')
    parser.add_option('-a', '--all', dest='all', action='store_true',
                      default=False, help='Sync all modules')
    (options, args) = parser.parse_args()
    parser.print_usage()

if __name__ == '__main__':
  logging.basicConfig() 
  ms = MasterSync()
  ms.main()