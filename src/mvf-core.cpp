// Copyright (c) 2016 The Bitcoin developers
// Distributed under the MIT software license, see the accompanying
// file COPYING or http://www.opensource.org/licenses/mit-license.php.
// MVF-Core common objects and functions

#include "mvf-core.h"
#include "init.h"
#include "util.h"
#include "chainparams.h"
#include "validationinterface.h"

#include <iostream>
#include <fstream>
#include <boost/filesystem.hpp>

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


/** Add MVF-specific command line options (MVHF-CORE-DES-TRIG-8) */
std::string ForkCmdLineHelp()
{
    std::string strUsage;
    strUsage += HelpMessageGroup(_("Bitcoin MVF-Core Options:"));

    // automatic wallet backup parameters (MVHF-CORE-DES-WABU-1)
    strUsage += HelpMessageOpt("-autobackupwalletpath=<path>", _("Automatically backup the wallet to the autobackupwalletfile path after the block specified becomes the best block (-autobackupblock). Default: Enabled"));
    strUsage += HelpMessageOpt("-autobackupblock=<n>", _("Specify the block number that triggers the automatic wallet backup. Default: forkheight-1"));

    // fork height parameter (MVHF-CORE-DES-TRIG-1)
    strUsage += HelpMessageOpt("-forkheight=<n>", strprintf(_("Block height at which to fork on active network (integer). Defaults (also minimums): mainnet:%u,testnet=%u,regtest=%u"), (unsigned)HARDFORK_HEIGHT_MAINNET, (unsigned)HARDFORK_HEIGHT_TESTNET, (unsigned)HARDFORK_HEIGHT_REGTEST));

    // fork id (MVHF-CORE-DES-CSIG-1)
    strUsage += HelpMessageOpt("-forkid=<n>", strprintf(_("Fork id to use for signature change. Value must be between 0 and %d. Default is 0x%06x (%u)"), (unsigned)MAX_HARDFORK_SIGHASH_ID, (unsigned)HARDFORK_SIGHASH_ID, (unsigned)HARDFORK_SIGHASH_ID));

    return strUsage;
}


/** Performs fork-related setup / validation actions when the program starts */
void ForkSetup(const CChainParams& chainparams)
{
    int defaultForkHeightForNetwork = 0;
    std:string activeNetworkID = chainparams.NetworkIDString();

    LogPrintf("%s: MVF: doing setup\n", __func__);
    LogPrintf("%s: MVF: active network = %s\n", __func__, activeNetworkID);

    // determine minimum fork height according to network
    // (these are set to the same as the default fork heights for now, but could be made different)
    if (activeNetworkID == CBaseChainParams::MAIN)
        defaultForkHeightForNetwork = HARDFORK_HEIGHT_MAINNET;
    else if (activeNetworkID == CBaseChainParams::TESTNET)
        defaultForkHeightForNetwork = HARDFORK_HEIGHT_TESTNET;
    else if (activeNetworkID == CBaseChainParams::REGTEST)
        defaultForkHeightForNetwork = HARDFORK_HEIGHT_REGTEST;
    else
        throw std::runtime_error(strprintf("%s: Unknown chain %s.", __func__, activeNetworkID));

    FinalActivateForkHeight = GetArg("-forkheight", defaultForkHeightForNetwork);

    FinalForkId = GetArg("-forkid", HARDFORK_SIGHASH_ID);
    // check fork id for validity (MVHF-CORE-DES-CSIG-2)
    if (FinalForkId == 0) {
        LogPrintf("MVF: Warning: fork id = 0 will result in vulnerability to replay attacks\n");
    }
    else {
        if (FinalForkId < 0 || FinalForkId > MAX_HARDFORK_SIGHASH_ID) {
            LogPrintf("MVF: Error: specified fork id (%d) is not in range 0..%u\n", FinalForkId, (unsigned)MAX_HARDFORK_SIGHASH_ID);
            StartShutdown();
        }
    }

    LogPrintf("%s: MVF: active fork height = %d\n", __func__, FinalActivateForkHeight);
    LogPrintf("%s: MVF: active fork id = 0x%06x (%d)\n", __func__, FinalForkId, FinalForkId);
    LogPrintf("%s: MVF: auto backup block = %d\n", __func__, GetArg("-autobackupblock", FinalActivateForkHeight - 1));

    // check if btcfork.conf exists (MVHF-CORE-DES-TRIG-10)
    boost::filesystem::path pathBTCforkConfigFile(BTCFORK_CONF_FILENAME);
    if (!pathBTCforkConfigFile.is_complete())
        pathBTCforkConfigFile = GetDataDir(false) / pathBTCforkConfigFile;
    if (boost::filesystem::exists(pathBTCforkConfigFile)) {
        LogPrintf("%s: MVF: found marker config file at %s - client has already forked before\n", __func__, pathBTCforkConfigFile.string().c_str());
        wasMVFHardForkPreviouslyActivated = true;
    }
    else {
        LogPrintf("%s: MVF: no marker config file at %s - client has not forked yet\n", __func__, pathBTCforkConfigFile.string().c_str());
        wasMVFHardForkPreviouslyActivated = false;
    }

    // we should always set the activation flag to false during setup
    isMVFHardForkActive = false;
}


/** Actions when the fork triggers (MVHF-CORE-DES-TRIG-6) */
// doBackup parameter default is true
void ActivateFork(int actualForkHeight, bool doBackup)
{
    LogPrintf("%s: MVF: checking whether to perform fork activation\n", __func__);
    if (!isMVFHardForkActive && !wasMVFHardForkPreviouslyActivated)  // sanity check to protect the one-off actions
    {
        LogPrintf("%s: MVF: performing fork activation actions\n", __func__);

        // set so that we capture the actual height at which it forked
        // because this can be different from user-specified configuration
        // (e.g. soft-fork activated)
        FinalActivateForkHeight = actualForkHeight;

        boost::filesystem::path pathBTCforkConfigFile(BTCFORK_CONF_FILENAME);
        if (!pathBTCforkConfigFile.is_complete())
            pathBTCforkConfigFile = GetDataDir(false) / pathBTCforkConfigFile;

        LogPrintf("%s: MVF: checking for existence of %s\n", __func__, pathBTCforkConfigFile.string().c_str());

        // remove btcfork.conf if it already exists - it shall be overwritten
        if (boost::filesystem::exists(pathBTCforkConfigFile)) {
            LogPrintf("%s: MVF: removing %s\n", __func__, pathBTCforkConfigFile.string().c_str());
            try {
                boost::filesystem::remove(pathBTCforkConfigFile);
            } catch (const boost::filesystem::filesystem_error& e) {
                LogPrintf("%s: Unable to remove pidfile: %s\n", __func__, e.what());
            }
        }
        // try to write the btcfork.conf (MVHF-CORE-DES-TRIG-10)
        LogPrintf("%s: MVF: writing %s\n", __func__, pathBTCforkConfigFile.string().c_str());
        std::ofstream  btcforkfile(pathBTCforkConfigFile.string().c_str(), std::ios::out);
        btcforkfile << "forkheight=" << FinalActivateForkHeight << "\n";
        btcforkfile << "forkid=" << FinalForkId << "\n";

        LogPrintf("%s: MVF: active fork height = %d\n", __func__, FinalActivateForkHeight);
        LogPrintf("%s: MVF: active fork id = 0x%06x (%d)\n", __func__, FinalForkId, FinalForkId);

        // MVF-Core begin MVHF-CORE-DES-WABU-3
        // check if we need to do wallet auto backup at fork block
        // this is in case of soft-fork triggered activation
        // MVF-Core TODO: reduce code duplication between this block and main.cpp:UpdateTip()
        if (doBackup && !fAutoBackupDone)
        {
            std::string strWalletBackupFile = GetArg("-autobackupwalletpath", "");
            int BackupBlock = actualForkHeight;

            //LogPrintf("MVF DEBUG: autobackupwalletpath=%s\n",strWalletBackupFile);
            //LogPrintf("MVF DEBUG: autobackupblock=%d\n",BackupBlock);

            if (GetBoolArg("-disablewallet", false))
            {
                LogPrintf("MVF: -disablewallet and -autobackupwalletpath conflict so automatic backup disabled.");
                fAutoBackupDone = true;
            }
            else {
                // Auto Backup defined, but no need to check block height since
                // this is fork activation time and we still have not backed up
                // so just get on with it
                if (GetMainSignals().BackupWalletAuto(strWalletBackupFile, BackupBlock))
                    fAutoBackupDone = true;
                else {
                    // shutdown in case of wallet backup failure (MVHF-CORE-DES-WABU-5)
                    // MVF-Core TODO: investigate if this is safe in terms of wallet flushing/closing or if more needs to be done
                    btcforkfile << "error: unable to perform automatic backup - exiting" << "\n";
                    btcforkfile.close();
                    throw std::runtime_error("CWallet::BackupWalletAuto() : Auto wallet backup failed!");
                }
            }
            btcforkfile << "autobackupblock=" << FinalActivateForkHeight << "\n";
            LogPrintf("%s: MVF: soft-forked auto backup block = %d\n", __func__, FinalActivateForkHeight);

        }
        else {
            // auto backup was already made pre-fork - emit parameters
            btcforkfile << "autobackupblock=" << GetArg("-autobackupblock", FinalActivateForkHeight - 1) << "\n";
            LogPrintf("%s: MVF: height-based auto backup block = %d\n", __func__, GetArg("-autobackupblock", FinalActivateForkHeight - 1));
        }

        // close fork parameter file
        btcforkfile.close();
    }
    // set the flag so that other code knows HF is active
    LogPrintf("%s: MVF: enabling isMVFHardForkActive\n", __func__);
    isMVFHardForkActive = true;
}


/** Actions when the fork is deactivated in reorg (MVHF-CORE-DES-TRIG-7) */
void DeactivateFork(void)
{
    LogPrintf("%s: MVF: checking whether to perform fork deactivation\n", __func__);
    if (isMVFHardForkActive)
    {
        LogPrintf("%s: MVF: performing fork deactivation actions\n", __func__);
    }
    LogPrintf("%s: MVF: disabling isMVFHardForkActive\n", __func__);
    isMVFHardForkActive = false;
}
