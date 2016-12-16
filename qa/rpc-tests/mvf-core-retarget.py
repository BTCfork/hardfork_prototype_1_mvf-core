#!/usr/bin/env python2
# Copyright (c) 2016 The Bitcoin developers
# Distributed under the MIT software license, see the accompanying
# file COPYING or http://www.opensource.org/licenses/mit-license.php.

#
# Test MVF post fork retargeting
#
# on node 0, test pure block height trigger at height FORK_BLOCK
#

from test_framework.test_framework import BitcoinTestFramework
from test_framework.util import *
from random import randint
import decimal
from datetime import datetime

# period (in blocks) from fork activation until retargeting returns to normal
HARDFORK_RETARGET_BLOCKS = 180*144
FORK_BLOCK = 2017

class MVF_RETARGET_BlockHeight_Test(BitcoinTestFramework):

    def add_options(self, parser):
        parser.add_option("--quick", dest="quick", default=False, action="store_true",
        help="Run shortened version of test")

    def setup_chain(self):
        print("Initializing test directory " + self.options.tmpdir)
        initialize_chain_clean(self.options.tmpdir, 1)

    def setup_network(self):
        self.nodes = []
        self.is_network_split = False
        self.nodes.append(start_node(0, self.options.tmpdir
            ,["-forkheight=%s"%FORK_BLOCK, "-force-retarget","-rpcthreads=100","-blockversion=%s" % "0x20000000" ]
            ))

    def is_fork_triggered_on_node(self, node=0):
        """ check in log file if fork has triggered and return true/false """
        # MVF-Core TODO: extend to check using RPC info about forks
        nodelog = self.options.tmpdir + "/node%s/regtest/debug.log" % node
        hf_active = search_file(nodelog, "isMVFHardForkActive=1")
        fork_actions_performed = search_file(nodelog, "MVF: performing fork activation actions")
        return (len(hf_active) > 0 and len(fork_actions_performed) == 1)

    def run_test(self):
        # check that fork does not triggered before the height
        print "Generating %s pre-fork blocks" % (FORK_BLOCK - 1)

        for n in range(FORK_BLOCK - 1):
            # Change block times so that difficulty develops
            best_block = self.nodes[0].getblock(self.nodes[0].getbestblockhash(), True)
            #print "%s %s" %(
                #best_block['height'],
                #time.strftime("%Y-%m-%d %H:%M",time.gmtime(best_block['time'])))
            self.nodes[0].setmocktime(best_block['time'] + 600)
            self.nodes[0].generate(1)

        # Read difficulty before the fork
        best_block = self.nodes[0].getblock(self.nodes[0].getbestblockhash(), True)
        print "Pre-fork difficulty: %s %s " % (round(best_block['difficulty'],8), best_block['bits'])
        best_diff_expected = best_block['difficulty'] / 10

        # Test fork did not trigger prematurely
        assert_equal(False, self.is_fork_triggered_on_node(0))
        print "Fork did not trigger prematurely"

        # Generate fork block
        best_block = self.nodes[0].getblock(self.nodes[0].getbestblockhash(), True)
        self.nodes[0].setmocktime(best_block['time'] + 600)
        self.nodes[0].generate(1)
        assert_equal(True,   self.is_fork_triggered_on_node(0))
        print "Fork triggered successfully (block height %s)" % FORK_BLOCK

        # use to track how many times the same bits are used in a row
        prev_block = 0
        diffadjinterval = 0
        next_block_time = 0
        count_bits_used = 0
        prev_block_delta = 0
        best_diff_expected = 0
        prev_blocks_delta_avg = 0
        diff_factor = 0

        best_block_hash = self.nodes[0].getbestblockhash()
        last_retarget_block_timestamp = self.nodes[0].getblock(best_block_hash, True)['time']
        last_wallclock_timestamp = time.time()

        if self.options.quick:
            # used for CI - just test one day after fork
            # this is basically just to test reset and initial response
            number_of_blocks_to_test_after_fork = 144
        else:
            # full range
            number_of_blocks_to_test_after_fork = HARDFORK_RETARGET_BLOCKS + 2016

        # start generating MVF blocks with varying time stamps
        for n in xrange(number_of_blocks_to_test_after_fork):
            best_block_hash = self.nodes[0].getbestblockhash()
            best_block = self.nodes[0].getblock(best_block_hash, True)
            prev_block = self.nodes[0].getblock(best_block['previousblockhash'], True)

            # test fork difficult reset
            if best_block['height'] == FORK_BLOCK + 1 :
                #assert_equal(round(best_block['difficulty'],8), round(best_diff_expected,8))
                assert_equal(best_block['bits'], "207eeeee")
                print "Post-fork difficulty reset successfull: %s %s " % (round(best_diff_expected,8), best_block['bits'])

                # print column titles
                print "WallTime WallStamp WallDelta nBits changed @ Time,Block,Delta(secs),nBits,Used,DiffInterval,Difficulty,NextDifficulty,DiffFactor,WallSecsPerBlock"
            # end if best_block['height'] == FORK_BLOCK + 1

            # track bits used
            if prev_block['bits'] == best_block['bits'] or best_block['height'] == FORK_BLOCK:
                count_bits_used += 1
            else:
                # when the bits change then output the retargeting metrics
                # for the previous group of bits
                timenow = time.time()
                wall_per_block=(timenow - last_wallclock_timestamp) / float(count_bits_used)

                prev_blocks_delta_avg = decimal.Decimal(prev_block_delta) / count_bits_used
                diff_factor = 600 / decimal.Decimal(prev_blocks_delta_avg)
                best_diff_expected = prev_block['difficulty'] * diff_factor

                #print "%s %d%+5d %s nBits changed @ Height:nBits:Diff:Used %5d : %s : %0.12f : %4d %4ds/block %0.2fs" %(
                print "%s %d%+5d %s,%d,%d,%s,%d,%d,%f,%f,%f,%0.2fs" %(
                    datetime.utcnow().isoformat(),
                    int(timenow),
                    int(timenow) - int(last_wallclock_timestamp),
                    time.strftime("%Y-%m-%d %H:%M",time.gmtime(prev_block['time'])),
                    prev_block['height'],
                    prev_blocks_delta_avg,
                    prev_block['bits'],
                    count_bits_used,
                    diffadjinterval,
                    prev_block['difficulty'],
                    best_diff_expected,
                    diff_factor,
                    wall_per_block
                    )

                last_retarget_block_timestamp = best_block['time']
                last_wallclock_timestamp = timenow

                # Test processed bits are used within the expected difficulty interval
                # except when the bits is at the bits limit: 207fffff
                if prev_block['bits'] <> "207fffff":
                    assert_less_than_equal(count_bits_used, diffadjinterval)

                # Test difficulty
                if n <= 500 :
                    assert_equal(round(best_block['difficulty'],8), round(best_diff_expected,8))

                # reset bits tracking variables
                count_bits_used = 1
                prev_block_delta = 0

            #### end if prev_block['bits'] == best_block['bits']

            # setup various block time interval tests
            if n in range(0,11) :
                next_block_time = next_block_time + 50
            elif n in range(11,18) :
                next_block_time = 300
            elif n in range(18,26) :
                next_block_time = 1200
            elif n in range(26,500) :
                next_block_time = 600
            elif n in range(500,2500) :
                # simulate slow blocks just after the fork i.e. low hash power/high difficulty
                # this will cause bits to hit the limit 207fffff
                next_block_time = randint(4000,6000)
            else:
                # simulate ontime blocks i.e. hash power/difficult around 600 secs
                next_block_time = randint(500,700)

            self.nodes[0].setmocktime(best_block['time'] + next_block_time)

            # track block metrics
            prev_block_delta = prev_block_delta + (best_block['time'] - prev_block['time'])
            diffadjinterval = self.nodes[0].getblockchaininfo()['difficultyadjinterval']

            # Test the interval matches the interval defined in params.MVFPowTargetTimespan()
            if n in range(0,11) :
                diff_interval_expected = 1
            elif n in range(11,44) :
                diff_interval_expected = 3
            elif n in range(44,102) :
                diff_interval_expected = 6
            elif n in range(102,2012) :
                diff_interval_expected = 18
            elif n in range(2012,HARDFORK_RETARGET_BLOCKS) :
                diff_interval_expected = 72
            else:
                diff_interval_expected = 2016

            #print "%d %d" % (diff_interval_expected, diffadjinterval)
            #if diff_interval_expected <> diffadjinterval : raw_input()
            assert_equal(diff_interval_expected, diffadjinterval)

            # print info for every block
            #print "%s :: %s :: %d :: %s :: %d" %(
                #best_block['height'],
                #time.strftime("%H:%M",time.gmtime(best_block['time'])),
                #decimal.Decimal(prev_block_delta) / count_bits_used,
                #best_block['bits'],
                #count_bits_used)

            # generate the next block
            self.nodes[0].generate(1)

        #### end for n in xrange

        print "Done."
        #raw_input() # uncomment here to pause shutdown and check the logs

if __name__ == '__main__':
    MVF_RETARGET_BlockHeight_Test().main()
