#!/usr/bin/python

import syncldap

class SyncMod:
  def __init__(self, dn, type, changeobj=None):
    self._dn = dn
    
    assert type in ['ADD', 'MOD', 'DEL']
    self._type = type

    self._change = changeobj

  def __str__(self):
    return '%s -- TYPE-%s' % (self._dn, self._type)

  def __repr__(self):
    return self.__str__()

  def chgobj(self):
    return self._change
  def apply(self):
    print ' **** APPLYING CHANGE TO %s' % self._dn
    print ' **** TYPE: %s' % self._type
    l = syncldap.SyncLDAP() 
    if self._type == 'ADD':
      assert self._change is not None
      l.add(self._dn, self._change)
    elif self._type == 'DEL':
      l.delete(self._dn)
    elif self._type == 'MOD':
      assert self._change is not None
      print 'MMMM: %s' % (str(self._change))
      l.change(self._dn, self._change)
    l.close()
