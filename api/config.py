#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import re

from copy import deepcopy
from glob import glob
from ruamel import yaml
from attrdict import AttrDict
from urlpath import URL
from pathlib2 import Path

from utils.format import fmt

try:
    from utils.dictionary import merge
    from utils.exceptions import AutocertError
except ImportError:
    from dictionary import merge
    from exceptions import AutocertError

CONFIG_DIR = os.path.dirname(__file__)
CONFIG_YML = '{0}/config.yml'.format(CONFIG_DIR)
DOT_CONFIG_YML = '{0}/.config.yml'.format(CONFIG_DIR)

IP_PATTERN = '[0-9]{1,3}(.[0-9]{1,3}){3}'

class ConfigLoadError(AutocertError):
    def __init__(config, errors=None):
        message = 'Error loading config file =%s'.format(config)
        super(ConfigLoadError, self).__init__(message)
        self.errors = errors

class ConfigWriteError(AutocertError):
    def __init__(config, errors=None):
        message = 'Error loading config file =%s'.format(config)
        super(ConfigLoadError, self).__init__(message)
        self.errors = errors

class AuthKeyNotAllowedError(AutocertError):
    def __init__(d, errors=None):
        message = '"auth" key found on dict =%s'.format(d)
        super(AuthKeyNotAllowedError, self).__init__(message)
        self.errors = errors

class ApikeyNotFoundError(AutocertError):
    def __init__(d, errors=None):
        message = 'Could not find apikey in this dict %s' % d
        super(ApikeyNotFoundError, self).__init__(message)
        self.errors = errors

def _fixup(obj):
    if isinstance(obj, dict):
        d = deepcopy(obj)
        for k,v in obj.items():
            if isinstance(v, str):
                if 'url' in k:
                    d[k] = URL(v)
                elif 'path' in k:
                    d[k] = Path(v)
                elif 'auth' == k:
                    with open(fmt('{CONFIG_DIR}/{v}'), 'r') as f:
                        d[k] = yaml.safe_load(f.read())
            elif isinstance(v, dict):
                d[k] = _fixup(v)
        return d
    return obj

def _load_config(filename=DOT_CONFIG_YML, roundtrip=False, fixup=True):
    cfg = {}
    if os.path.isfile(filename):
        try:
            with open(filename, 'r') as f:
                if roundtrip:
                    cfg = yaml.round_trip_load(f.read())
                else:
                    cfg = yaml.safe_load(f.read())
            if fixup:
                cfg = _fixup(cfg)
        except Exception as ex:
            print('ex =', ex)
            raise ConfigLoadError(filename, errors=[ex])
    return AttrDict(cfg)

def _write_config(filename, cfg, roundtrip=False):
    try:
        with open(filename, 'w') as f:
            if roundtrip:
                f.write(yaml.round_trip_dump(dict(cfg), indent=4))
            else:
                f.write(yaml.dump(cfg, indent=4))
    except Exception as ex:
        raise ConfigWriteError(filename, errors=[ex])
    return cfg

def _update_config(filename, *cfgs):
    if cfgs:
        updated = _load_config(filename, roundtrip=True, fixup=False)
        for cfg in cfgs:
            if not isinstance(cfg, AttrDict):
                cfg = AttrDict(cfg)
            updated += cfg
    return _write_config(filename, updated, roundtrip=True)

CFG = _load_config()
