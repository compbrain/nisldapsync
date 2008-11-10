#!/usr/bin/python

import base
import constants
class _AutomountEntry:
  def __init__(self, key, information):
    self._key = key
    self._information = information
    self._root = None

  def setRoot(self, rootdn):
    self._root = rootdn

  def dn(self):
    return 'cn=%s,%s' % (self._key, self._root)

  def ldapEntry(self):
    entry = {}
    entry['objectClass'] = ['top', 'automount']
    entry['cn'] = [self._key]
    entry['automountInformation'] = [self._information]
    return (self.dn(), entry)


class _AutomountMap:
  def __init__(self, mapname, maproot):
    self._name = mapname
    self._root = maproot
    self._submaps = []
    self._entries = []

  def dn(self):
    return 'ou=%s,%s' % (self._name, self._root)

  def addSubMap(self, submap):
    self._submaps.append(submap)

  def addEntry(self, entry):
    entry.setRoot(self.dn())
    self._entries.append(entry)

  def updateRoot(self, newroot):
    self._root = newroot

  def ldapEntry(self):
    entry = {}
    entry['objectClass'] = ['top', 'automountMap']
    entry['ou'] = [self._name]
    return (self.dn(), entry)
  
  def mapLDAPEntries(self):
    maplist = []
    maplist.append(self.ldapEntry())
    for submap in self._submaps:
      maplist.extend(submap.mapLDAPEntries())
    return maplist

  def entryLDAPEntries(self):
    entrylist = []
    for entry in self._entries:
      entrylist.append(entry.ldapEntry())
    for submap in self._submaps:
      entrylist.extend(submap.entryLDAPEntries())
    return entrylist

  def __str__(self):
    return 'Map: %s Entries: %s Subs: %s' % (self._name, len(self._entries), len(self._submaps))
  def __repr__(self):
    return self.__str__()

class AutomountSync(base.BaseSync):
  def __init__(self, ldapbase, baseou, peopleou=None, maildomain=None):
    base.BaseSync.__init__(self, ldapbase, baseou, peopleou)

  def _maproot(self):
    return '%s,%s' % (self._baseou, self._ldapbase)

  def _ProcessRawMap(self, mapname='auto.master'):
    map_obj = _AutomountMap(mapname, self._maproot())
    fullmap = self._GetNISMap(mapname)
    for key in fullmap:
       data = fullmap[key]
       if data.split('\t')[0][:5] == 'auto.':
         map_obj.addSubMap(self._ProcessRawMap(data.split('\t')[0]))
       else:
         subs = None
       entry_obj = _AutomountEntry(key, data)
       map_obj.addEntry(entry_obj)
    return map_obj

  def generateRecordsFromNIS(self):
    records = []
    mastermap = self._ProcessRawMap()
    records.extend(mastermap.mapLDAPEntries())
    records.extend(mastermap.entryLDAPEntries())
    return records
