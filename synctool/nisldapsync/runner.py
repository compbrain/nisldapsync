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
from ldif import LDIFWriter
from optparse import OptionParser

# Site Imports
import group
import hosts
import passwd
import automount
import netgroup
import syncconfigfile

SYNC_MODS = {
             'netgroup':netgroup.NetgroupSync,
             'passwd': passwd.PasswdSync,
             'hosts':hosts.HostsSync,
             'group':group.GroupSync,
             'automount':automount.AutomountSync,
            }

DEBUG_LEVELS = ['debug', 'info', 'warning', 'error']

class Runner:
  def __init__(self):
    self._l = logging.getLogger('ldapsync')
    self._config = None
    self._l.debug('Instantiating Master Sync Object')
  
  def getConfig(self):
    if self._config is None:
      self._l.debug('Reading Sync Config File')
      self._config = syncconfigfile.SyncConfigFile()

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

  def applychangedict(self, changedict, pretend=False):
    self._l.info('Beginning change application')
    for map in changedict:
      self._l.info('Applying changes for %s' % map)
      for change in changedict[map]:
        if not pretend:
          change.apply()
        else:
          self._l.debug('Pretended to apply %s' % str(change))
  
  def _set_debug_level(self, level):
    m = {'debug':logging.DEBUG, 'info':logging.INFO,
         'warning':logging.WARNING, 'error':logging.ERROR}
    if level not in DEBUG_LEVELS:
      self._l.error('Invalid debug level set')
    else:
      self._l.setLevel(m[level])

  def _run_options(self, options, parser):
    ''' Run a sync with the given options dict and parser object '''

    # all and module are mutually exclusive, one must be given
    if options.all and options.module:
      parser.error('You cannot specify all and a list of modules.')
    if not (options.all or options.module):
      parser.error('You must specify all or list of modules.')

    # check to make sure module list contains only modules we support
    for module in options.module:
      if module not in SYNC_MODS:
        parser.error('Given module "%s" is unsupported' % module)

    # check debug level is supported
    if options.debuglevel and (options.debuglevel not in DEBUG_LEVELS):
      parser.error('Given level "%s" is not a valid debug level.\n'
                   '%s accepted' %
                   (options.debuglevel, str(DEBUG_LEVELS)))
    # Runnnn
    self._run(options.debuglevel, options.module, options.pretend,
              options.ldif)

  def ldifoutput(self, changedict):
    writer = LDIFWriter(sys.stdout)
    for map in changedict:
      for change in changedict[map]:
        dne = change.dnentry()
        writer.unparse(dne[0], dne[1])

  def _run(self, debug_level, modules, pretend, ldif):
    # Set Debug Level
    self._set_debug_level(debug_level)

    # Generate Change Dict
    if modules:
      maplist = modules
    else:
      maplist = None
    changedict = self.getDiffDict(maplist)

    if ldif:
      self.ldifoutput(changedict)
    else:
      self.applychangedict(changedict, pretend)

  def main(self):
    ''' Create a parser and handle user input '''
    parser = OptionParser()
    parser.add_option('-d', '--debug', dest='debuglevel',
                      help='Debug Level', default=DEBUG_LEVELS[-1])
    parser.add_option('-a', '--all', dest='all', action='store_true',
                      default=False, help='Sync all modules')
    parser.add_option('-m', '--module', dest='module', action='append',
                      default=[], help='Module to sync')
    parser.add_option('-p', '--pretend', dest='pretend', action='store_true',
                      default=False,
                      help='Pretend to sync, do not apply changes')
    parser.add_option('-l', '--ldif', dest='ldif', action='store_true',
                      default=False,
                      help='Generate LDIF instead of applying changes')
    (options, args) = parser.parse_args()
    self._run_options(options, parser)
