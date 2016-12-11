// Copyright (c) 2016 The Bitcoin developers
// Distributed under the MIT software license, see the accompanying
// file COPYING or http://www.opensource.org/licenses/mit-license.php.
// MVF-Core common objects and functions

#include "mvf-core-globals.h"

using namespace std;

// actual fork height, taking into account user configuration parameters (MVHF-CORE-DES-TRIG-4)
int FinalActivateForkHeight = 0;

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

