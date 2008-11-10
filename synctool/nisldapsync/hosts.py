#!/usr/bin/python

import base
import constants

class HostsSync(base.BaseSync):
  def __init__(self, ldapbase, baseou, peopleou=None, maildomain=None):
    base.BaseSync.__init__(self, ldapbase, baseou, peopleou)
    self._ips = []
    self._names = []

  def _maproot(self):
    return '%s,%s' % (self._baseou, self._ldapbase)

  def _ProcessRawMap(self):
    entries = []
    fullmap = self._GetNISMap('hosts')
    for key in fullmap:
      entry = self.ldapEntryFromNIS(key, fullmap[key])
      if entry is not None:
        entries.append(entry)
    return entries
  
  def ldapEntryFromNIS(self, key, nisentry):
    (ip, names) = nisentry.split('\t', 2)
    namestouse = []
    if ip in self._ips:
      return None
    self._ips.append(ip)
    for name in names.split(' '):
      if name == '':
        continue
      elif name in self._names:
        continue
      else:
        self._names.append(name)
        namestouse.append(name)
    return self._ldapEntry(ip, namestouse)

  def _ldapEntry(self, ip, names):
    dn = 'ipHostNumber=%s,%s' % (ip, self._maproot())
    entry = {}
    entry['objectClass'] = ['top', 'ipHost', 'device']
    entry['cn'] = names # []
    entry['ipHostNumber'] = [ip]
    return (dn, entry)

  def generateRecordsFromNIS(self):
    self._ips = []
    self._names = []
    return self._ProcessRawMap()
