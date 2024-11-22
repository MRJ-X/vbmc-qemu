#!/usr/bin/env python

import os
import stat
import errno
import subprocess
import netifaces
from netifaces import AF_INET, AF_LINK

from portpicker import is_port_free

from virtbmc.clrlog import LOG
from virtbmc import procutils

def get_netiface_config(iface):
    if iface not in netifaces.interfaces():
        raise Exception("Not found net interface: %s" % iface)
    addr = None
    mask = None
    mac = None
    if_info = netifaces.ifaddresses(iface)
    nw_info = if_info.get(AF_INET)
    if nw_info is not None:
        addr = nw_info[0]['addr']
        mask = nw_info[0]['netmask']
    dl_info = if_info.get(AF_LINK)
    mac = dl_info[0]['addr']
    return {'addr': addr, 'mask': mask, 'mac': mac}


def get_netiface_ip(iface):
    net_config = get_netiface_config(iface)
    addr = net_config['addr']
    if not addr:
        raise Exception("Net interface %s need ip address" % iface)
    return addr


def get_free_port(start, end):
    return [port for port in range(start, end) if is_port_free(port)]

def get_br0_ips():
    # 执行 shell 命令来获取 br0 网桥的 IP 地址
    result = subprocess.run(
        ["ip", "-4", "addr", "show", "br0"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        universal_newlines=True
    )

    # 检查命令是否执行成功
    if result.returncode != 0:
        print("Error:", result.stderr)
        return []

    # 使用正则表达式提取 IP 地址
    ip_addresses = []
    for line in result.stdout.splitlines():
        if "inet " in line:
            ip = line.split()[1].split("/")[0]
            ip_addresses.append(ip)

    return ip_addresses


def is_port_open(port):
    if not is_port_free(port):
        return True
    else:
        return False


def random_mac():
    import random
    mac = [0x00, 0x16, 0x3e,
           random.randint(0x00, 0x7f),
           random.randint(0x00, 0xff),
           random.randint(0x00, 0xff)]
    return ':'.join(map(lambda x: "%02x" % x, mac))


def mkdir_p(path):
    try:
        os.makedirs(path)
    except OSError as exc:
        if exc.errno == errno.EEXIST and os.path.isdir(path):
            pass
        else:
            raise


def mkdir_of_file(file_path):
    mkdir_p(os.path.dirname(file_path))


def rmdirs(dirpath):
    import shutil
    shutil.rmtree(dirpath)


def rmfile(filename):
    os.remove(filename)


def cpto(src, dst):
    from shutil import copy
    copy(src, dst)


def dirname(file_path, steps=0):
    parent_dir = os.path.dirname(os.path.realpath(file_path))
    for x in range(0, steps):
        parent_dir = os.path.dirname(parent_dir)
    return parent_dir


def make_executable(path):
    st = os.stat(path)
    os.chmod(path, st.st_mode | stat.S_IEXEC)


def run_cmd(cmd):
    if hasattr(cmd, '__iter__'):
        cmdstr = ' '.join(cmd)
    else:
        cmdstr = cmd
    print('cmdstr:',cmdstr)
    try:
        LOG.info("Run command: %s" % cmdstr)
        res = procutils.check_output(cmd)
        return res
    except Exception as e:
        e = Exception("Run command: '{}'\nError: {}".format(cmdstr, e))
        LOG.error(e)
        raise e


def ranges(num_lst):
    from itertools import groupby
    pos = (j - i for i, j in enumerate(num_lst))
    t = 0
    for i, els in groupby(pos):
        l = len(list(els))
        el = num_lst[t]
        t += l
        yield range(el, el+l)
