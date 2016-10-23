#!/usr/bin/env python2
# Copyright (c) 2014-2015 The Bitcoin Core developers
# Copyright (c) 2016 The Bitcoin developers
# Distributed under the MIT software license, see the accompanying
# file COPYING or http://www.opensource.org/licenses/mit-license.php.
# MVF-Core
"""
See https://github.com/BTCfork/hardfork_prototype_1_mvf-core/blob/master/doc/mvf-core-test-design.md#411

Exercise the auto backup wallet code.  Ported from walletbackup.sh.

Test case is:
5 nodes. 1 2 and 3 send transactions between each other, fourth node is a miner.
The 5th node does no transactions and only tests for the -disablewallet conflict.
.
1 2 3 each mine a block to start, then
Miner creates 100 blocks so 1 2 3 each have 50 mature coins to spend.
Then 5 iterations of 1/2/3 sending coins amongst
themselves to get transactions in the wallets,
and the miner mining one block.

Then 5 more iterations of transactions and mining a block.

The node config sets wallets to automatically back up
as defined in the backupblock constant 114.

Balances are saved for sanity check:
  Sum(1,2,3,4 balances) == 114*50

1/2/3/4 are shutdown, and their wallets erased.
Then restored using the auto backup wallets eg wallet.dat.auto.114.bak.
Sanity check to confirm 1/2/3/4 balances match the 114 block balances.
Sanity check to confirm 5th node does NOT perform the auto backup
and that the debug.log contains a conflict message
"""

import os
from test_framework.test_framework import BitcoinTestFramework
from test_framework.util import *
from random import randint
import logging
logging.basicConfig(format='%(levelname)s:%(message)s', level=logging.INFO)

# backup block must be > 113 as these blocks are used for context setup
backupblock = 114

class WalletBackupTest(BitcoinTestFramework):

    def setup_chain(self):
        logging.info("Initializing test directory "+self.options.tmpdir)
        initialize_chain_clean(self.options.tmpdir, 5)

    # This mirrors how the network was setup in the bash test
    def setup_network(self, split=False):
        logging.info("Starting nodes")

        # nodes 1, 2,3 are spenders, let's give them a keypool=100
        # and configure option autobackupwalletpath
        # testing each file path variant
        # as per the test design at sw-req-10-1
        extra_args = [
            ["-keypool=100",
                "-autobackupwalletpath=%s"%(self.options.tmpdir + "/node0/newabsdir/pathandfile.@.bak"),
                "-autobackupblock=%s"%(backupblock)],
            ["-keypool=100",
                "-autobackupwalletpath=filenameonly.@.bak",
                "-autobackupblock=%s"%(backupblock)],
            ["-keypool=100",
                "-autobackupwalletpath=./newreldir/",
                "-autobackupblock=%s"%(backupblock)],
            ["-autobackupblock=%s"%(backupblock)],
            ["-disablewallet",
                "-autobackupwalletpath="+self.options.tmpdir+"/node4",
                "-autobackupblock=%s"%(backupblock)]]

        self.nodes = start_nodes(5, self.options.tmpdir, extra_args)
        connect_nodes(self.nodes[0], 3)
        connect_nodes(self.nodes[1], 3)
        connect_nodes(self.nodes[2], 3)
        connect_nodes(self.nodes[4], 3)
        self.is_network_split=False
        self.sync_all()

    def one_send(self, from_node, to_address):
        if (randint(1,2) == 1):
            amount = Decimal(randint(1,10)) / Decimal(10)
            self.nodes[from_node].sendtoaddress(to_address, amount)

    def do_one_round(self):
        a0 = self.nodes[0].getnewaddress()
        a1 = self.nodes[1].getnewaddress()
        a2 = self.nodes[2].getnewaddress()

        self.one_send(0, a1)
        self.one_send(0, a2)
        self.one_send(1, a0)
        self.one_send(1, a2)
        self.one_send(2, a0)
        self.one_send(2, a1)

        # Have the miner (node3) mine a block.
        # Must sync mempools before mining.
        sync_mempools(self.nodes)
        self.nodes[3].generate(1)

    # As above, this mirrors the original bash test.
    def start_four(self):

        self.nodes[0] = start_node(0, self.options.tmpdir)
        self.nodes[1] = start_node(1, self.options.tmpdir)
        self.nodes[2] = start_node(2, self.options.tmpdir)
        self.nodes[3] = start_node(3, self.options.tmpdir)

        connect_nodes(self.nodes[0], 3)
        connect_nodes(self.nodes[1], 3)
        connect_nodes(self.nodes[2], 3)


    def stop_four(self):
        stop_node(self.nodes[0], 0)
        stop_node(self.nodes[1], 1)
        stop_node(self.nodes[2], 2)
        stop_node(self.nodes[3], 3)

    def erase_four(self):
        os.remove(self.options.tmpdir + "/node0/regtest/wallet.dat")
        os.remove(self.options.tmpdir + "/node1/regtest/wallet.dat")
        os.remove(self.options.tmpdir + "/node2/regtest/wallet.dat")
        os.remove(self.options.tmpdir + "/node3/regtest/wallet.dat")

    def run_test(self):
        logging.info("Automatic backup configured for block %s"%(backupblock))
        assert_greater_than(backupblock, 113)

        # target backup files
        node0backupfile = self.options.tmpdir + "/node0/newabsdir/pathandfile.%s.bak"%(backupblock)
        node1backupfile = self.options.tmpdir + "/node1/regtest/filenameonly.%s.bak"%(backupblock)
        node2backupfile = self.options.tmpdir + "/node2/regtest/newreldir/wallet.dat.auto.%s.bak"%(backupblock)
        node3backupfile = self.options.tmpdir + "/node3/regtest/wallet.dat.auto.%s.bak"%(backupblock)

        logging.info("Generating initial blockchain")
        self.nodes[0].generate(1)
        sync_blocks(self.nodes)
        self.nodes[1].generate(1)
        sync_blocks(self.nodes)
        self.nodes[2].generate(1)
        sync_blocks(self.nodes)
        self.nodes[3].generate(100)

        sync_blocks(self.nodes)
        logging.info("Generated %s blocks"%(self.nodes[0].getblockcount()))

        assert_equal(self.nodes[0].getbalance(), 50)
        assert_equal(self.nodes[1].getbalance(), 50)
        assert_equal(self.nodes[2].getbalance(), 50)
        assert_equal(self.nodes[3].getbalance(), 0)

        tmpdir = self.options.tmpdir

        logging.info("Creating transactions")
        # Five rounds of sending each other transactions.
        for i in range(5):
            self.do_one_round()

        logging.info("More transactions")
        for i in range(5):
            self.do_one_round()

        # At this point should be 113 blocks
        self.sync_all()
        logging.info("Generated %s blocks"%(self.nodes[0].getblockcount()))

        # Generate any further blocks to reach the backup block
        blocks_remaining = backupblock - self.nodes[0].getblockcount() - 1
        if (blocks_remaining) > 0:
            self.nodes[3].generate(blocks_remaining)

        self.sync_all()
        logging.info("Generated %s blocks"%(self.nodes[0].getblockcount()))

        # Only 1 more block until the auto backup is triggered
        # Test the auto backup files do NOT exist yet
        node0backupexists = 0
        node1backupexists = 0
        node2backupexists = 0
        node3backupexists = 0

        if os.path.isfile(node0backupfile):
            node0backupexists = 1
            logging.info("Error backup exists too early: %s"%(node0backupfile))

        if os.path.isfile(node1backupfile):
            node1backupexists = 1
            logging.info("Error backup exists too early: %s"%(node1backupfile))

        if os.path.isfile(node2backupfile):
            node2backupexists = 1
            logging.info("Error backup exists too early: %s"%(node2backupfile))

        if os.path.isfile(node3backupfile):
            node3backupexists = 1
            logging.info("Error backup exists too early: %s"%(node3backupfile))

        assert_equal(0, node0backupexists)
        assert_equal(0, node1backupexists)
        assert_equal(0, node2backupexists)
        assert_equal(0, node3backupexists)

        # Generate the block that should trigger the auto backup
        self.nodes[3].generate(1)
        self.sync_all()
        assert_equal(self.nodes[0].getblockcount(),backupblock)

        logging.info("Reached backup block %s automatic backup triggered"%(self.nodes[0].getblockcount()))

        # Test if the backup files exist
        if os.path.isfile(node0backupfile): node0backupexists = 1
        else: logging.info("Error backup does not exist: %s"%(node0backupfile))

        if os.path.isfile(node1backupfile): node1backupexists = 1
        else: logging.info("Error backup does not exist: %s"%(node1backupfile))

        if os.path.isfile(node2backupfile): node2backupexists = 1
        else: logging.info("Error backup does not exist: %s"%(node2backupfile))

        if os.path.isfile(node3backupfile): node3backupexists = 1
        else: logging.info("Error backup does not exist: %s"%(node3backupfile))

        assert_equal(1, node0backupexists)
        assert_equal(1, node1backupexists)
        assert_equal(1, node2backupexists)
        assert_equal(1, node3backupexists)

        ##
        # Calculate wallet balances for comparison after restore
        ##

        # Balance of each wallet
        balance0 = self.nodes[0].getbalance()
        balance1 = self.nodes[1].getbalance()
        balance2 = self.nodes[2].getbalance()
        balance3 = self.nodes[3].getbalance()

        total = balance0 + balance1 + balance2 + balance3

        logging.info("Node0 balance:" + str(balance0))
        logging.info("Node1 balance:" + str(balance1))
        logging.info("Node2 balance:" + str(balance2))
        logging.info("Node3 balance:" + str(balance3))

        logging.info("Original Wallet Total: " + str(total))

        ##
        # Test restoring spender wallets from backups
        ##
        logging.info("Switching wallets. Restoring using automatic wallet backups...")
        self.stop_four()
        self.erase_four()

        # Restore wallets from backup
        shutil.copyfile(node0backupfile, tmpdir + "/node0/regtest/wallet.dat")
        shutil.copyfile(node1backupfile, tmpdir + "/node1/regtest/wallet.dat")
        shutil.copyfile(node2backupfile, tmpdir + "/node2/regtest/wallet.dat")
        shutil.copyfile(node3backupfile, tmpdir + "/node3/regtest/wallet.dat")

        logging.info("Re-starting nodes")
        self.start_four()
        self.sync_all()

        total2 = self.nodes[0].getbalance() + self.nodes[1].getbalance() + self.nodes[2].getbalance() + self.nodes[3].getbalance()
        logging.info("Node0 balance:" + str(self.nodes[0].getbalance()))
        logging.info("Node1 balance:" + str(self.nodes[1].getbalance()))
        logging.info("Node2 balance:" + str(self.nodes[2].getbalance()))
        logging.info("Node3.balance:" + str(self.nodes[3].getbalance()))

        logging.info("Backup Wallet Total: " + str(total2))

        # balances should equal the auto backup balances
        assert_equal(self.nodes[0].getbalance(), balance0)
        assert_equal(self.nodes[1].getbalance(), balance1)
        assert_equal(self.nodes[2].getbalance(), balance2)
        assert_equal(self.nodes[3].getbalance(), balance3)
        assert_equal(total,total2)

        # Test Node4 auto backup wallet does NOT exist: tmpdir + "/node4/wallet.dat.auto.114.bak"
        # when -disablewallet is enabled then no backup file should be created and graceful exit happens
        # without causing a runtime error
        node4backupexists = 0
        if os.path.isfile(tmpdir + "/node4/regtest/wallet.dat.auto.%s.bak"%(backupblock)):
            node4backupexists = 1
            logging.info("Error: Auto backup performed on node4 with -disablewallet!")

        # Test Node4 debug.log contains a conflict message - length test should be > 0
        debugmsg_list = search_file(tmpdir + "/node4/regtest/debug.log","-disablewallet and -autobackupwalletpath conflict")

        assert_equal(0,node4backupexists)
        assert_greater_than(len(debugmsg_list),0)

if __name__ == '__main__':
    WalletBackupTest().main()
