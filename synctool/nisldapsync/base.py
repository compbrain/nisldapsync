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

## Standard Modules
import logging
import nis
import ldap
## Package Modules
import syncldap
import syncmod

class BaseSync:
  def __init__(self, ldapbase, baseou, peopleou=None,
               syncmodule=syncldap, changemodule=syncmod):
    self._rawmap     = None
    self._changelist = []
    self._ldapbase   = ldapbase
    self._baseou     = baseou
    if peopleou is None:
      self._peopleou = 'ou=people'
    else:
      self._peopleou = peopleou
    self._syncmodule = syncmodule
    self._chgmodule  = changemodule
    self._ldapcache  = None
    self._l          = self._getLogger('base')

  def _GetNISMap(self, mapname):
    self._l.debug('Getting %s NIS Map Data' % mapname)
    return nis.cat(mapname)

  def _populateLDAPCache(self):
    if self._ldapcache is None:
      self._l.debug('Getting LDAP Cache')
      l = self._syncmodule.SyncLDAP()
      if len(self._baseou):
        dn = '%s,%s' % (self._baseou, self._ldapbase)
      else:
        dn = self._ldapbase
      try:
        results = l.search(dn, ldap.SCOPE_SUBTREE)
      except ldap.NO_SUCH_OBJECT:
        results = []
      l.close()
      self._ldapcache = results
    return self._ldapcache

  def _getLogger(self, mapname):
    return logging.getLogger('ldapsync.mod-%s' % mapname)

  def _getServerCopy(self, dnquery):
    self._populateLDAPCache()
    for x in self._ldapcache:
      if x[0] == dnquery:
        return x
    return None

  def generateRecordsFromNIS(self):
    assert False, 'Stub!'
  
  def generateMapChangeList(self, dodeletes=True):
    self._l.debug('Generating changelist')
    changelist = []
    self._createcontainer(changelist)
    generated_list = []
    for record in self.generateRecordsFromNIS():
      createddn = record[0]
      generated_list.append(createddn)
      ldaprecord = self._getServerCopy(createddn)
      if ldaprecord is None:
        self.generateAdd(record, changelist)
      else:
        self.generateDiff(record, changelist)
    if dodeletes:
      deletelist = self.generateDeletions(generated_list)
      changelist.extend(deletelist)
    return changelist
    
  def generateDeletions(self, generated_dnlist):
    self._l.debug('Generating deletions')
    changelist = []
    l = self._syncmodule.SyncLDAP()
    try:
      results = l.search('%s,%s' % (self._baseou, self._ldapbase), 
                         ldap.SCOPE_ONELEVEL)
    except:
      results = []
    l.close()
    for r in results:
      dn = r[0]
      if dn not in generated_dnlist:
        modify_obj = self._chgmodule.SyncMod(dn, 'DEL')
        changelist.append(modify_obj)
    return changelist

  def generateAdd(self, record, list=None):
    self._l.debug('Generating add for %s' % record[0])
    """ Create a Modify object for a record that does not exist in ldap
    Args:
     record -- A tuple like that returned from ldap.search
     list   -- The list to append changes to
    """
    if list is None:
      list = self._changelist
    generated_dn    = record[0]
    generated_attrs = self.sortrecord(record[1])
    modlist         = self._syncmodule.makeModlist(generated_attrs)
    modify_obj      = self._chgmodule.SyncMod(generated_dn, 'ADD', modlist)
    list.append(modify_obj)

  def generateDiff(self, record, list=None):
    """ Create a Modify object for a record if it differs from LDAP
    Args:
     record -- A tuple like that returned from ldap.search
     list   -- The list to append changes to
    """
    if list is None:
      list = self._changelist
    nisrecord = self.sortrecord(record)
    generated_dn = nisrecord[0]
    ldaprecord = self.sortrecord(self._getServerCopy(generated_dn))
    # Get a modlist, if it has changes, add them to the changelist
    modlist = self._syncmodule.makeModlist(ldaprecord[1], nisrecord[1])
    if len(modlist) > 0:
      self._l.debug('Generating diff for %s' % record[0])
      modify_obj = self._chgmodule.SyncMod(generated_dn, 'MOD', modlist)
      list.append(modify_obj)

  def sortrecord(self, attributes):
    """ Sort a list or dict recursivley
    Args:
     attributes -- Initially you would pass the second part of a tuple as
                   returned from ldap.search. Properly handles [] {} for 
                   sorting, returns everything else as is.
    Examples:
      ['zed', 'apple', 'car'] => ['apple', 'car', 'zed']
      {'list2':['a','b',c'], 'list1':['r','a','w']} => 
        {'list2':['a','b',c'], 'list1':['a','r','w']}
    """
    if type(attributes) == type([]):
      l = []
      for item in attributes:
        l.append(self.sortrecord(item))
      l.sort()
      return l
    elif type(attributes) == type({}):
      for key in attributes.iterkeys():
        attributes[key] = self.sortrecord(attributes[key])
      return attributes
    else:
      return attributes

  def _createcontainer(self, list):
    self._l.debug('Creating container entry')
    """ Creates a Modify object for the container defined by _ContainerEntry
    If _ContainerEntry does not exist in ldap, it is created. If it is somehow
    incorrect, a diff will be created to fix it.
    """
    entry = self._ContainerEntry()
    if entry is None:
      return None
    containerdn = entry[0]
    ldaprecord = self._getServerCopy(containerdn)
    if ldaprecord is None:
      self.generateAdd(entry, list)
    else:
      self.generateDiff(entry, list)

  def _ContainerEntry(self):
    """ Generates the countainer entry for this sync object
    eg: For a password sync, you would be pulling a passwd NIS map
    and produce an ou=people OU. This will generate a tuple similar to
    that returned from ldap.search
    """
    dn = '%s,%s' % (self._baseou, self._ldapbase)
    entry = {}
    entry['ou'] = [self._baseou.split('=')[1]]
    entry['objectClass'] = ['top', 'organizationalUnit']
    return (dn, entry)
