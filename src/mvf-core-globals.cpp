// Copyright (c) 2016 The Bitcoin developers
// Distributed under the MIT software license, see the accompanying
// file COPYING or http://www.opensource.org/licenses/mit-license.php.
// MVF-Core common objects and functions

#include "mvf-core-globals.h"

using namespace std;

// key-value maps for btcfork.conf configuration items
map<string, string> btcforkMapArgs;
map<string, vector<string> > btcforkMapMultiArgs;

// version string identifying the consensus-relevant algorithmic changes
// so that a user can quickly see if MVF fork clients are compatible
// for test purposes (since they may diverge during development/testing).
// A new value must be chosen whenever there are changes to consensus
// relevant functionality (excepting things which are parameterized).
// Values are surnames chosen from the name list of space travelers at
// https://en.wikipedia.org/wiki/List_of_space_travelers_by_name
// already used: AKIYAMA (add current one to the list when replacing)
std::string post_fork_consensus_id = "YAMAZAKI";

// actual fork height, taking into account user configuration parameters (MVHF-CORE-DES-TRIG-4)
int FinalActivateForkHeight = 0;

// actual difficulty drop factor, taking into account user configuration parameters (MVF-Core TODO: MVHF-CORE-DES-DIAD-?)
unsigned FinalDifficultyDropFactor = 0;
// actual fork id, taking into account user configuration parameters (MVHF-CORE-DES-CSIG-1)
int FinalForkId = 0;

// track whether HF has been activated before in previous run (MVHF-CORE-DES-TRIG-5)
// is set at startup based on btcfork.conf presence
bool wasMVFHardForkPreviouslyActivated = false;

// track whether HF is active (MVHF-CORE-DES-TRIG-5)
bool isMVFHardForkActive = false;

// track whether auto wallet backup might still need to be done
// this is set to true at startup if client detects fork already triggered
// otherwise when the backup is made. (MVHF-CORE-DES-WABU-1)
bool fAutoBackupDone = false;

// default suffix to append to wallet filename for auto backup (MVHF-CORE-DES-WABU-1)
std::string autoWalletBackupSuffix = "auto.@.bak";

