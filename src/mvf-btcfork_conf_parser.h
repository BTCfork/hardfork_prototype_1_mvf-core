// Copyright (c) 2016 The Bitcoin developers
// Distributed under the MIT software license, see the accompanying
// file COPYING or http://www.opensource.org/licenses/mit-license.php.
// MVF-Core btcfork.conf file parsing declarations

#pragma once
#ifndef BITCOIN_MVF_BTCFORK_CONF_PARSER_H
#define BITCOIN_MVF_BTCFORK_CONF_PARSER_H

#include <boost/filesystem.hpp>

#include "mvf-core.h"

// read btcfork.conf file
extern void MVFReadConfigFile(boost::filesystem::path pathCfgFile, std::map<std::string, std::string>& mapSettingsRet, std::map<std::string, std::vector<std::string> >& mapMultiSettingsRet);

#endif

