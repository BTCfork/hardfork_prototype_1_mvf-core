#!/usr/bin/env python2
# Copyright (c) 2016 The Bitcoin developers
# Distributed under the MIT software license, see the accompanying
# file COPYING or http://www.opensource.org/licenses/mit-license.php.

#
# Test MVF post fork retargeting
#
# on node 0, test pure block height trigger at height 100
#

import time
from test_framework.test_framework import BitcoinTestFramework
from test_framework.util import *
from random import randint
from datetime import datetime

BLOCK_SPACING=600               # seconds
SPACING_WINDOW_TIGHT=100        # +- this many seconds for normal blocks
SPECIAL_PERIOD=200*144          # ~185 days worth of blocks

class MVF_RETARGET_Test(BitcoinTestFramework):

    def setup_chain(self):
        print("Initializing test directory " + self.options.tmpdir)
        initialize_chain_clean(self.options.tmpdir, 4)

    def setup_network(self):
        self.nodes = []
        self.is_network_split = False
        self.nodes.append(start_node(0, self.options.tmpdir,
                            ["-forkheight=100", "-force-retarget" ]))

    def is_fork_triggered_on_node(self, node=0):
        """ check in log file if fork has triggered and return true/false """
        # MVF-Core TODO: extend to check using RPC info about forks
        nodelog = self.options.tmpdir + "/node%s/regtest/debug.log" % node
        hf_active = search_file(nodelog, "isMVFHardForkActive=1")
        fork_actions_performed = search_file(nodelog, "MVF: performing fork activation actions")
        return (len(hf_active) > 0 and len(fork_actions_performed) == 1)

    def run_test(self):
        # check that fork does not triggered before the height
        print "Generating 99 pre-fork blocks"
        for n in xrange(len(self.nodes)):
            self.nodes[n].generate(99)
            assert_equal(False, self.is_fork_triggered_on_node(n))
        print "Fork did not trigger prematurely"

        # check that fork triggers for nodes 0 and 1 at designated height
        # move all nodes to height 100
        for n in xrange(len(self.nodes)):
            self.nodes[n].generate(1)
        assert_equal(True,   self.is_fork_triggered_on_node(0))

        print "Fork triggered successfully on node 0 (block height 100)"

        # use to track how many times the same bits are used in a row
        prev_block = 0
        count_bits_used = 1
        #diffadjinterval = 0
        prev_block_delta = 0
        best_block_hash = self.nodes[0].getbestblockhash()
        last_retarget_block_timestamp = self.nodes[0].getblock(best_block_hash, True)['time']
        last_wallclock_timestamp = time.time()

        # start generating MVF blocks with varying time stamps
        for n in xrange(SPECIAL_PERIOD):
            best_block_hash = self.nodes[0].getbestblockhash()
            best_block = self.nodes[0].getblock(best_block_hash, True)
            prev_block = self.nodes[0].getblock(best_block['previousblockhash'], True)

            #if prev_block <> 0 :
            if prev_block['bits'] == best_block['bits']:
                count_bits_used += 1
            else:
                timenow = time.time()
                wall_per_block=(timenow - last_wallclock_timestamp) / float(count_bits_used)
                print "%s %d%+5d %s nBits changed @ Height:nBits:Diff:Used %5d : %s : %0.12f : %4d %4ds/block %0.2fswall/block" %(
                    datetime.utcnow().isoformat(),
                    int(timenow),
                    int(timenow) - int(last_wallclock_timestamp),
                    time.strftime("%Y-%m-%d %H:%M",time.gmtime(prev_block['time'])),
                    prev_block['height'],
                    prev_block['bits'],
                    prev_block['difficulty'],
                    count_bits_used,
                    int((best_block['time'] - last_retarget_block_timestamp) / float(count_bits_used)),
                    wall_per_block
                    )
                    
                count_bits_used = 1
                last_retarget_block_timestamp = best_block['time']
                last_wallclock_timestamp = timenow

            if n <= 36 :
                # simulate slow blocks just after the fork i.e. low hash power/high difficulty
                #self.nodes[0].setmocktime(best_block['time'] + randint(4000,6000))
                # simulate fast blocks just after the fork i.e. high hash power/low difficulty
                self.nodes[0].setmocktime(best_block['time'] + randint(100,200))
            else:
                # simulate ontime blocks i.e. hash power/difficult around 600 secs
                middle=BLOCK_SPACING   # the regular block spacing
                window_size=SPACING_WINDOW_TIGHT
                self.nodes[0].setmocktime(best_block['time'] + randint(int(middle - window_size),
                                                                       int(middle + window_size)))

            self.nodes[0].generate(1)

            prev_block = best_block
        #end for n in xrange
        #diffadjinterval = self.nodes[0].getblockchaininfo()['difficultyadjinterval']

        #print "Final retargeting interval: %s" % diffadjinterval

        print "Done."

if __name__ == '__main__':
    MVF_RETARGET_Test().main()
