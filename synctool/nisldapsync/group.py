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

import base
import constants
import passwd

class GroupSync(base.BaseSync):
  def __init__(self, ldapbase, baseou, maildomain, peopleou=None):
    base.BaseSync.__init__(self, ldapbase, baseou, peopleou)
    self._maildomain = maildomain
    self._usersyncobj = None
    self._groups = {}
    self._l          = self._getLogger('group')


  def _RawToDict(self, data):
    m = constants.GROUP_DATA_RE.match(data)
    if m is not None:
      dict = {}
      dict['groupName'] = m.group(1)
      dict['gidNumber'] = m.group(2)
      dict['users'] = []
      if m.group(3) is not None:
        for u in m.group(3).split(','):
          if u != '':
            dict['users'].append(u)
      return dict

  def _ProcessRawMap(self):
    self._rawmap = self._GetNISMap('group')
    for group_name in self._rawmap:
      if group_name not in ['', '#']:
        group_dict = self._RawToDict(self._rawmap[group_name])
        if group_name not in self._groups:
          self._groups[group_name] = group_dict
        else:
          self._groups[group_name].extend(group_dict)

  def _AddPrimaryUsersToGroup(self, group_name):
    if self._usersyncobj is None:
      self._usersyncobj = passwd.PasswdSync(ldapbase=self._ldapbase,
                                            baseou=self._baseou,
                                            peopleou=self._peopleou,
                                            maildomain=self._maildomain)
    primary_users = self._usersyncobj.UsersWithGID(
        self._groups[group_name]['gidNumber'])
    for user in primary_users:
      if user not in self._groups[group_name]['users']:
        self._groups[group_name]['users'].append(user)

  def generateRecordsFromNIS(self):
    records = []
    self._ProcessRawMap()
    for group in self._groups:
      generatedrecord = self._GroupToLDAPEntry(group)
      records.append(generatedrecord)
    return records

  def _GroupToLDAPEntry(self, group_name):
    addmember = False
    self._AddPrimaryUsersToGroup(group_name)
    objectclasses = ['top','posixGroup']
    entry = {}
    dn = 'cn=%s,%s,%s' % (group_name, self._baseou, self._ldapbase)
    entry['cn'] = [group_name]
    if len(self._groups[group_name]['users']) > 0:
      addmember = True
      objectclasses.append('groupOfNames')
      entry['member'] = []
    entry['memberUid'] = []
    for uid in self._groups[group_name]['users']:
      if uid not in entry['memberUid']:
        if addmember:
          udn = 'uid=%s,%s,%s' % (uid, self._peopleou, self._ldapbase)
          entry['member'].append(udn)
        entry['memberUid'].append(uid)
      else:
        print 'WARNING: WARNING: WARNING: Duplicate uid %s in %s' % (uid, dn)
    entry['objectClass'] = objectclasses
    entry['gidNumber'] = [self._groups[group_name]['gidNumber']]
    return (dn, entry)
