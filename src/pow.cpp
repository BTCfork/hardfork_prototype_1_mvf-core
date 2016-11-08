// Copyright (c) 2009-2010 Satoshi Nakamoto
// Copyright (c) 2009-2015 The Bitcoin Core developers
// Copyright (c) 2015-2016 The Bitcoin Unlimited developers
// Distributed under the MIT software license, see the accompanying
// file COPYING or http://www.opensource.org/licenses/mit-license.php.

#include "pow.h"

#include "arith_uint256.h"
#include "chain.h"
#include "primitives/block.h"
#include "uint256.h"
#include "util.h"
#include "mvf-core.h"  // MVF-Core added


unsigned int GetNextWorkRequired(const CBlockIndex* pindexLast, const CBlockHeader *pblock, const Consensus::Params& params)
{
    unsigned int nProofOfWorkLimit = UintToArith256(params.powLimit).GetCompact();
    static bool force_retarget=GetBoolArg("-force-retarget", false);  //MVF-Core added

    // Genesis block
    if (pindexLast == NULL)
        return nProofOfWorkLimit;

    // MVF-Core begin difficulty re-targeting reset
	if (pindexLast->nHeight == FinalActivateForkHeight)
	{
        LogPrintf("MVF: FORK BLOCK DIFFICULTY RESET  %08x  \n", pindexLast->nBits);
		return pindexLast->nBits;
	}
	LogPrintf("MVF DEBUG DifficultyAdjInterval = %d , TimeSpan = %d \n", params.DifficultyAdjustmentInterval(pindexLast->nHeight), params.MVFPowTargetTimespan(pindexLast->nHeight));
    // MVF-Core end

	// Only change once per difficulty adjustment interval
	if ((pindexLast->nHeight+1) % params.DifficultyAdjustmentInterval(pindexLast->nHeight) != 0)  // MVF-Core
	{
		if (params.fPowAllowMinDifficultyBlocks && !force_retarget)  // MVF-Core
		{
			// Special difficulty rule for testnet:
			// If the new block's timestamp is more than 2* 10 minutes
			// then allow mining of a min-difficulty block.
			if (pblock->GetBlockTime() > pindexLast->GetBlockTime() + params.nPowTargetSpacing*2)
				return nProofOfWorkLimit;
			else
			{
				// Return the last non-special-min-difficulty-rules-block
				const CBlockIndex* pindex = pindexLast;
				while (pindex->pprev && pindex->nHeight % params.DifficultyAdjustmentInterval(pindexLast->nHeight) != 0 && pindex->nBits == nProofOfWorkLimit)  // MVF-Core
					pindex = pindex->pprev;
				return pindex->nBits;
			}
		}
		return pindexLast->nBits;
    }

	// Go back by what we want to be 14 days worth of blocks
    // MVF-Core begin adjust nHeightFirst
	int nHeightFirst = pindexLast->nHeight - (params.DifficultyAdjustmentInterval(pindexLast->nHeight)-1);
	if (params.MVFisWithinRetargetPeriod(pindexLast->nHeight))
		nHeightFirst = pindexLast->nHeight - params.DifficultyAdjustmentInterval(pindexLast->nHeight);
    // MVF-Core end
	assert(nHeightFirst >= 0);
	const CBlockIndex* pindexFirst = pindexLast->GetAncestor(nHeightFirst);
	assert(pindexFirst);

	return CalculateNextWorkRequired(pindexLast, pindexFirst->GetBlockTime(), params);

}

unsigned int CalculateNextWorkRequired(const CBlockIndex* pindexLast, int64_t nFirstBlockTime, const Consensus::Params& params)
{
    static bool force_retarget=GetBoolArg("-force-retarget", false);  // MVF-Core

    if (params.fPowNoRetargeting && !force_retarget)  // MVF-Core
        return pindexLast->nBits;

    // Limit adjustment step
    int64_t nActualTimespan = pindexLast->GetBlockTime() - nFirstBlockTime;
    LogPrintf("  nActualTimespan = %d  before bounds\n", nActualTimespan);

    // MVF-Core begin target time span while within the re-target period
    int64_t nTargetTimespan = params.nPowTargetTimespan; // the original 14 days
    if (params.MVFisWithinRetargetPeriod(pindexLast->nHeight))
        nTargetTimespan = params.MVFPowTargetTimespan(pindexLast->nHeight);

    // permit abrupt changes for a few blocks after the fork i.e. when nTargetTimespan is < 30 minutes
    if (nTargetTimespan >= params.nPowTargetSpacing * 3)
    {
        // prevent abrupt changes to target
        if (nActualTimespan < nTargetTimespan/4)
            nActualTimespan = nTargetTimespan/4;
        if (nActualTimespan > nTargetTimespan*4)
            nActualTimespan = nTargetTimespan*4;
    }
    else LogPrintf("Abrupt RETARGET permitted.\n");
    // MVF-Core end

    // Retarget
    const arith_uint256 bnPowLimit = UintToArith256(params.powLimit);
    arith_uint256 bnNew;
    arith_uint256 bnOld;
    bnNew.SetCompact(pindexLast->nBits);
    bnOld = bnNew;
    bnNew *= nActualTimespan;
    bnNew /= nTargetTimespan;  // MVF-Core

    if (bnNew > bnPowLimit)
        bnNew = bnPowLimit;

    /// debug print
    LogPrintf("GetNextWorkRequired RETARGET\n");
    LogPrintf("nTargetTimespan = %d    nActualTimespan = %d\n", nTargetTimespan, nActualTimespan);  // MVF-Core
    LogPrintf("Before: %08x  %s\n", pindexLast->nBits, bnOld.ToString());
    LogPrintf("After:  %08x  %s\n", bnNew.GetCompact(), bnNew.ToString());

    return bnNew.GetCompact();
}

bool CheckProofOfWork(uint256 hash, unsigned int nBits, const Consensus::Params& params)
{
    bool fNegative;
    bool fOverflow;
    arith_uint256 bnTarget;
    static bool force_retarget=GetBoolArg("-force-retarget", false);  // MVF-Core

    bnTarget.SetCompact(nBits, &fNegative, &fOverflow);

    // Check range
    // MVF-Core begin suppress trace output to enable faster test runs when
    // -force-retarget is used for retargeting tests
    if (fNegative || bnTarget == 0 || fOverflow || bnTarget > UintToArith256(params.powLimit)) {
        if (!force_retarget)
            return error("CheckProofOfWork(): nBits below minimum work");
        else
            return false;
    }

    // Check proof of work matches claimed amount
    // if retargeting is enforced on testnets, suppress this warning
    // because it would flood the logs when lots of hashing going on
    if (UintToArith256(hash) > bnTarget) {
        if (!force_retarget)
            return error("CheckProofOfWork(): hash %s doesn't match nBits 0x%x",hash.ToString(),nBits);
        else
            return false;
    }
    // MVF-Core end

    return true;
}

arith_uint256 GetBlockProof(const CBlockIndex& block)
{
    arith_uint256 bnTarget;
    bool fNegative;
    bool fOverflow;
    bnTarget.SetCompact(block.nBits, &fNegative, &fOverflow);
    if (fNegative || fOverflow || bnTarget == 0)
        return 0;
    // We need to compute 2**256 / (bnTarget+1), but we can't represent 2**256
    // as it's too large for a arith_uint256. However, as 2**256 is at least as large
    // as bnTarget+1, it is equal to ((2**256 - bnTarget - 1) / (bnTarget+1)) + 1,
    // or ~bnTarget / (nTarget+1) + 1.
    return (~bnTarget / (bnTarget + 1)) + 1;
}

int64_t GetBlockProofEquivalentTime(const CBlockIndex& to, const CBlockIndex& from, const CBlockIndex& tip, const Consensus::Params& params)
{
    arith_uint256 r;
    int sign = 1;
    if (to.nChainWork > from.nChainWork) {
        r = to.nChainWork - from.nChainWork;
    } else {
        r = from.nChainWork - to.nChainWork;
        sign = -1;
    }
    r = r * arith_uint256(params.nPowTargetSpacing) / GetBlockProof(tip);
    if (r.bits() > 63) {
        return sign * std::numeric_limits<int64_t>::max();
    }
    return sign * r.GetLow64();
}
