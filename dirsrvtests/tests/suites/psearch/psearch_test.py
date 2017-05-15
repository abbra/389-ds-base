# --- BEGIN COPYRIGHT BLOCK ---
# Copyright (C) 2016 Red Hat, Inc.
# All rights reserved.
#
# License: GPL (version 3 or any later version).
# See LICENSE for details.
# --- END COPYRIGHT BLOCK ---
#
import pytest
from lib389._constants import DEFAULT_SUFFIX
from lib389.topologies import topology_st
from lib389.idm.group import Groups
import ldap
from ldap.controls.psearch import PersistentSearchControl,EntryChangeNotificationControl

def _run_psearch(inst, msg_id):
    results = []
    while True:
        try:
            _, data, _, _, _, _ = inst.result4(msgid=msg_id, all=0, timeout=1.0, add_ctrls=1, add_intermediates=1,
                                                                resp_ctrl_classes={EntryChangeNotificationControl.controlType:EntryChangeNotificationControl})
            # See if there are any entry changes
            for dn, entry, srv_ctrls in data:
                ecn_ctrls = filter(lambda c: c.controlType == EntryChangeNotificationControl.controlType, srv_ctrls)
                if ecn_ctrls:
                    inst.log.info('%s has changed!' % dn)
                    results.append(dn)
        except ldap.TIMEOUT:
            # There are no more results, so we timeout.
            inst.log.info('No more results')
            return results

def test_psearch(topology_st):
    # Create the search control
    psc = PersistentSearchControl()
    # do a search extended with the control
    msg_id = topology_st.standalone.search_ext(base=DEFAULT_SUFFIX, scope=ldap.SCOPE_SUBTREE, attrlist=['*'], serverctrls=[psc])
    # Get the result for the message id with result4
    _run_psearch(topology_st.standalone, msg_id)
    # Change an entry / add one
    groups = Groups(topology_st.standalone, DEFAULT_SUFFIX)
    group = groups.create(properties={'cn': 'group1', 'description': 'testgroup'})
    # Now run the result again and see what's there.
    results = _run_psearch(topology_st.standalone, msg_id)
    # assert our group is in the changeset.
    assert(group.dn == results[0])


if __name__ == '__main__':
    # Run isolated
    # -s for DEBUG mode
    CURRENT_FILE = os.path.realpath(__file__)
    pytest.main("-s %s" % CURRENT_FILE)