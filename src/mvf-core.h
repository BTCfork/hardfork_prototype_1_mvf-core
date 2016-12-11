// Copyright (c) 2016 The Bitcoin developers
// Distributed under the MIT software license, see the accompanying
// file COPYING or http://www.opensource.org/licenses/mit-license.php.
// MVF-Core common declarations
#pragma once
#ifndef BITCOIN_MVF_CORE_H
#define BITCOIN_MVF_CORE_H

#include "mvf-core-globals.h"

class CChainParams;

extern std::string ForkCmdLineHelp();  // fork-specific command line option help (MVHF-CORE-DES-TRIG-8)
extern bool ForkSetup(const CChainParams& chainparams);  // actions to perform at program setup (parameter validation etc.)
extern void ActivateFork(int actualForkHeight, bool doBackup=true);  // actions to perform at fork triggering (MVHF-CORE-DES-TRIG-6)
extern void DeactivateFork(void);  // actions to revert if reorg deactivates fork (MVHF-CORE-DES-TRIG-7)

#endif
