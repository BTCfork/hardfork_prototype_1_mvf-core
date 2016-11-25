#!/usr/bin/env python2
#
# Distributed under the MIT/X11 software license, see the accompanying
# file COPYING or http://www.opensource.org/licenses/mit-license.php.
#

from test_framework.test_framework import ComparisonTestFramework
from test_framework.comptool import TestManager, TestInstance, RejectResult
from test_framework.blocktools import *
from test_framework.util import start_nodes
import time


'''
In this test we connect to one node over p2p, and test tx requests.
'''

# Use the ComparisonTestFramework with 1 node: only use --testbinary.
class InvalidTxRequestTest(ComparisonTestFramework):

    ''' Can either run this test as 1 node with expected answers, or two and compare them. 
        Change the "outcome" variable from each TestInstance object to only do the comparison. '''
    def __init__(self):
        self.num_nodes = 1

    # MVF-Core begin added setup_network to work around default regtest fork height interference with this test
    # MVF-Core TODO: clarify why fork diff reset to 0x207eeeee at default forkheight 100 produces interference with this test
    #                once that problem is sorted out, remove the forkheight parameter again
    #                for now, set the forkheight to workaround this interference.
    def setup_network(self):
        self.nodes = start_nodes(1, self.options.tmpdir,
                                 extra_args=[['-forkheight=999999', '-debug', '-whitelist=127.0.0.1', ]],
                                 binary=[self.options.testbinary])
    # MVF-Core end

    def run_test(self):
        test = TestManager(self, self.options.tmpdir)
        test.add_all_connections(self.nodes)
        self.tip = None
        self.block_time = None
        NetworkThread().start() # Start up network handling in another thread
        test.run()

    def get_tests(self):
        if self.tip is None:
            self.tip = int ("0x" + self.nodes[0].getbestblockhash() + "L", 0)
        self.block_time = int(time.time())+1

        '''
        Create a new block with an anyone-can-spend coinbase
        '''
        height = 1
        block = create_block(self.tip, create_coinbase(height), self.block_time)
        self.block_time += 1
        block.solve()
        # Save the coinbase for later
        self.block1 = block
        self.tip = block.sha256
        height += 1
        yield TestInstance([[block, True]])

        '''
        Now we need that block to mature so we can spend the coinbase.
        '''
        test = TestInstance(sync_every_block=False)
        for i in xrange(100):
            block = create_block(self.tip, create_coinbase(height), self.block_time)
            block.solve()
            self.tip = block.sha256
            self.block_time += 1
            test.blocks_and_transactions.append([block, True])
            height += 1
        yield test

        # chr(100) is OP_NOTIF
        # Transaction will be rejected with code 16 (REJECT_INVALID)
        tx1 = create_transaction(self.block1.vtx[0], 0, chr(100), 50*100000000)
        yield TestInstance([[tx1, RejectResult(16, 'mandatory-script-verify-flag-failed')]])

        # TODO: test further transactions...

if __name__ == '__main__':
    InvalidTxRequestTest().main()
