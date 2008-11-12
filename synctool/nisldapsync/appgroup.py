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

class AppGroupSync(base.BaseSync):
  def __init__(self, ldapbase, baseou, maildomain, peopleou=None):
    base.BaseSync.__init__(self, ldapbase, baseou, peopleou)
    self._maildomain = maildomain
    self._usersyncobj = None
    self._groups = {}
    self._l          = self._getLogger('appgroup')

  def _GroupRawToDict(self, data):
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
    self._rawmap = {}
    self._ProcessRawGroup()
    self._ProcessRawNetgroup()

  def _ProcessRawGroup(self):
    self._rawmap['group'] = self._GetNISMap('group')
    for group_name in self._rawmap['group']:
      if group_name not in ['', '#']:
        group_dict = self._GroupRawToDict(self._rawmap['group'][group_name])
        if group_name not in self._groups:
          self._groups[group_name] = group_dict
        else:
          self._groups[group_name].extend(group_dict)

  def _ProcessRawNetgroup(self):
    self._rawmap['netgroup']  = self._GetNISMap('netgroup')
    for netgroup_name in self._rawmap['netgroup']:
      if netgroup_name not in ['', '#']:
        name = self._EffectiveNetgroupName(netgroup_name)
        netgroup_tuples = self._RawNetgroupToTuple(
                                     self._rawmap['netgroup'][netgroup_name])
        self._AddNetgroupUsersToGroup(name, netgroup_tuples)

  def _AddNetgroupUsersToGroup(self, group_name, tuples):
    if group_name not in self._groups:
      self._groups[group_name] = {'users':[], 'gidNumber':-1}
    for tuple in tuples:
      if (tuple[1] != '') and (tuple[1] != '-'):
        username = tuple[1]
        if username not in self._groups[group_name]['users']:
          self._groups[group_name]['users'].append(username)

  def _RawNetgroupToTuple(self, data):
    m = constants.NETGROUP_TRIP_RE.findall(data)
    tuple_list = []
    for tuple in m:
      if tuple[0] == '-':
        one = ''
      else:
        one = tuple[0]
      if tuple[1] == '-':
        two = ''
      else:
        two = tuple[1]
      three = tuple[2]
      tuple_list.append((one, two, three))
    return tuple_list
 
  def _EffectiveNetgroupName(self, given_name):
    name_match_obj = constants.NETGROUP_NAME_RE.match(given_name)
    if name_match_obj is not None:
      return name_match_obj.group(1)
    else:
      return given_name

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
    self._AddPrimaryUsersToGroup(group_name)
    # Create DN for this group
    dn = 'cn=%s,%s,%s' % (group_name, self._baseou, self._ldapbase)
    # Prepare LDAP entry body
    entry = {}
    entry['objectClass'] = ['top','groupOfNames']
    entry['cn'] = [group_name]
    entry['member'] = []
    for uid in self._groups[group_name]['users']:
      udn = 'uid=%s,%s,%s' % (uid, self._peopleou, self._ldapbase)
      entry['member'].append(udn)
    return (dn, entry)
