#!/usr/bin/env python
import re
import csv
import bz2
import os
import logging
import pickle


from functools import lru_cache

@lru_cache(maxsize=1024)
def _solve_cache(size, line_sz=64, assoc=2, nbanks=1):
    """ solve cache using CACTI interface

    Parameters
    ----------
    size : int
      the size of cache in bytes
    line_sz : int, optional
      cache line size in bytes, default is 64
    assoc : int, optional
      associativity, default is 2
    nbanks : int, optional
      number of UCA banks, default is 1

    Returns
    -------
    cacti_results
      A structure contains cacti_interface results
    """
    import lumos.model.mem.cacti as cacti
    ipara = cacti.InputParameter()

    # data array tech type
    # 0: itrs-hp
    # 1: itrs-lstp
    # 2: itrs-lop
    # 3: lp-dram
    # 4: comm-dram
    ipara.data_arr_ram_cell_tech_type = 0
    ipara.data_arr_peri_global_tech_type = 0
    ipara.tag_arr_ram_cell_tech_type = 0
    ipara.tag_arr_peri_global_tech_type = 0

    # interconnect projection type
    # 0: aggressive
    # 1: conservative
    ipara.ic_proj_type = 1

    # wire type
    # 0: local
    # 1: semi-global
    # 2: global
    ipara.wire_is_mat_type = 1
    ipara.wire_os_mat_type = 1

    # burst length
    ipara.burst_len = 8

    # internal prefetch width
    ipara.int_prefetch_w = 8

    # page size (bits)
    ipara.page_sz_bits = 8192

    # cache size
    ipara.cache_sz = size

    # line size in bytes
    ipara.line_sz = line_sz

    # associativity
    ipara.assoc = assoc

    # number of UCA banks
    ipara.nbanks = nbanks

    # output width (bits)
    ipara.out_w = 512

    # specific tag
    #  true, if specified
    #  false, if calculated by CACTI, hence tag_w will be ignored
    ipara.specific_tag = False
    ipara.tag_w = 42
    ipara.block_sz = 64

    # access mode
    # 0: normal
    # 1: sequential
    # 2: fast
    ipara.access_mode = 0

    # design objective function
    ipara.delay_wt = 0
    ipara.dynamic_power_wt = 0
    ipara.leakage_power_wt = 0
    ipara.area_wt = 0
    ipara.cycle_time_wt = 100

    # percentage deviation
    ipara.delay_dev = 20
    ipara.dynamic_power_dev = 100000
    ipara.leakage_power_dev = 100000
    ipara.area_dev = 100000
    ipara.cycle_time_dev = 100000

    # design objective function (NUCA)
    ipara.delay_wt_nuca = 100
    ipara.dynamic_power_wt_nuca = 100
    ipara.leakage_power_wt_nuca = 0
    ipara.area_wt_nuca = 100
    ipara.cycle_time_wt_nuca = 0

    # percentage deviation (NUCA)
    ipara.delay_dev_nuca = 10
    ipara.dynamic_power_dev_nuca = 10000
    ipara.leakage_power_dev_nuca = 10000
    ipara.area_dev_nuca = 10000
    ipara.cycle_time_dev_nuca = 10000

    # temperature in K
    ipara.temp = 360

    # optimization target
    # 0: None
    # 1: ED
    # 2: ED^2
    ipara.ed = 2

    # technology node
    ipara.F_sz_um = 0.022
    ipara.F_sz_nm = 22

    # memory type
    # cache: usual cache
    # ram: scratch ram similar to register file
    # cam: CAM
    # main memory: DRAM
    ipara.is_main_mem = 0
    ipara.is_cache = 1
    ipara.pure_ram = 0
    ipara.pure_cam = 0

    # repeaters in H-tree
    ipara.rpters_in_htree = True
    ipara.ver_htree_wires_over_array = False # TODO: what is the default value?
    ipara.broadcast_addr_din_over_ver_htrees = False # TODO: what is the default value?

    # number of ports
    ipara.num_rw_ports = 1
    ipara.num_rd_ports = 0
    ipara.num_wr_ports = 0
    ipara.num_se_rd_ports = 0
    ipara.num_search_ports = 1


    # UCA (0) or NUCA (1)
    ipara.nuca = 0

    # NUCA banks
    ipara.nuca_bank_count = 0
    ipara.foce_nuca_bank = 0

    # wire signal type
    # 0: global
    # 1: global_5
    # 2: global_10
    # 3: global_20
    # 4: global_30
    # 5: low swing
    # 6: semi global
    # 7: transmission
    # 8: optical
    ipara.wt = 4
    ipara.force_wiretype = True

    # force cache config
    ipara.force_cache_config = False
    ipara.ndbl = 1
    ipara.ndwl = 1
    ipara.nspd = 0
    ipara.ndcm = 1
    ipara.ndsam1 = 0
    ipara.ndsam2 = 0

    # ECC
    ipara.add_ecc_b_ = False

    # hp Vdd
    ipara.specific_hp_vdd = False
    ipara.hp_Vdd = 1.0

    ipara.specific_lstp_vdd = False
    ipara.lstp_Vdd = 1.0

    ipara.specific_lop_vdd = False
    ipara.lop_Vdd = 1.0

    # DVS
    # ipara.dvs_voltage = VectorDouble([0.8, 1.1, 1.3, 1.4, 1.5])

    # power gating
    ipara.specific_vcc_min = False
    ipara.user_defined_vcc_min = 0

    ipara.array_power_gated = False
    ipara.bitline_floating = False
    ipara.wl_power_gated = False
    ipara.cl_power_gated = False
    ipara.interconnect_power_gated = False
    ipara.perfloss = 0.01
    ipara.power_gating = False

    # number of cores
    ipara.cores = 8

    # cache level, 0: L2, 1: L3
    ipara.cache_level = 1

    # CL Driver vertical
    ipara.cl_vertical = True

    # long channel device
    ipara.long_channel_device = True

    # debug prints
    ipara.print_input_args = False
    ipara.print_detail = 0

    # call cacti to get results
    res = cacti.cacti_interface(ipara)
    return res

_size_to_bytes = {'b': 1, 'k': 1024, 'm': 1048576, 'g': 1073741824}
def cache_sz_nom(cache_sz_str):
    mo = re.match(r'([0-9]+)([BbKkMmGg])', cache_sz_str)
    if not mo:
        raise Exception('cache size not recognizable: {0}'.format(cache_sz_str))
    cache_size = int(mo.group(1))
    size_suffix = mo.group(2).lower()
    return cache_size * _size_to_bytes[size_suffix]


# To model cache characteristics (area, power, delay), use cacti-p to calculate
# characteristics of a cache at 22nm with the given size. Then scale to desired
# (type, node) using lumos technology library.
_tech_scale_table = {
    # 'tech_type': {
    #     tech_node: {
    #     'power': 1,
    #     'area': 1,
    #     'time': 1,
    #     },
    # }
    # use scale factors in tech/cmos/hp/__init__.py
    ('cmos-hp', 45): {
        'power': 4.85,
        'area': 4,
        'time': 1.21,
    },
    ('cmos-hp', 32): {
        'power': 2.39,
        'area': 2,
        'time': 1.1,
    },
    ('cmos-hp', 22): {
        'power': 1,
        'area': 1,
        'time': 1,
    },
    ('cmos-hp', 16): {
        'power': 0.45,
        'area': 0.5,
        'time': 0.91,
    },
    ('finfet-hp', 20): {
        # compare RCA circuit simulation of cmos-hp and finfet-hp at nominal supply for 20nm node, or 900mV.
        # Other nodes will be scaled to 20nm@Finfet accordingly.
        # This could be improved by more releastic data comparing CMOS to finfet
        'power': 1.26,
        'area': 1,
        'time': 0.8,
    },
    ('finfet-hp', 16): {
        'power': 1.21,
        'area': 0.53,
        'time': 0.52,
    },
    ('finfet-hp', 14): {
        'power': 1.15,
        'area': 0.4,
        'time': 0.35,
    },
    ('finfet-hp', 10): {
        'power': 0.974,
        'area': 0.25,
        'time': 0.305,
    },
    ('finfet-hp', 7): {
        'power': 0.767,
        'area': 0.125,
        'time': 0.26,
    },
    ('tfet-homo30nm', 22): {
        # use the same scaling factors of io-tfet-homo30nm in lumos/model/core/base.py
        'power': 0.337,
        'area': 1,
        'time': 1.65,
    },
    ('tfet-homo60nm', 22): {
        'power': 0.337,
        'area': 1,
        'time': 1.65,
    },
}


class CacheError(Exception): pass


_cache_db = None
_dbfile = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'cache_db.p.bz2')


def get_cache_trait(size, tech_type='cmos-hp', tech_node=22, line_sz=64, assoc=2, nbanks=1):
    global _cache_db, _dbfile
    if not _cache_db:
        try:
            with bz2.open(_dbfile, 'rb') as f:
                _cache_db = pickle.load(f)
        except OSError:
            raise CacheError('Fail to find {0}, go to $LUMOS_HOME and run '
                             '"python -m lumos.model.mem.cache" to generate '
                             'cache_db'.format(_dbfile))

    key = (tech_type, tech_node, size, line_sz, assoc, nbanks)
    try:
        return _cache_db[key]
    except KeyError:
        raise CacheError(
            'No cache config for tech_type: {tech_type}, tech_node: {tech_node}, '
            'size: {size}, line_sz: {line_sz}, assoc: {assoc}, nbanks: {nbanks}.'
            'Add config line to $LUMOS_HOME/lumos/model/mem/cache_db.csv.bz2, '
            'then rerun "python -m lumos.model.mem.cache" to re-generate cache_db.')


if __name__ == '__main__':
    import argparse
    from itertools import product

    parser = argparse.ArgumentParser()
    logging_levels = ('CRITICAL', 'ERROR', 'WARNING', 'INFO', 'DEBUG', 'NOTSET')
    parser.add_argument('-l', '--logging-level', default='NOTSET', choices=logging_levels)
    parser.add_argument('-f', '--force-update', action='store_true')
    parser.add_argument('-i', '--ignore-csvfile', action='store_true')
    args = parser.parse_args()

    _logger = logging.getLogger()
    _logger.setLevel(args.logging_level)

    csvfile = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'cache_db.csv.bz2')

    if not args.force_update:
        try:
            with bz2.open(_dbfile, 'rb') as f:
                cachedb = pickle.load(f)
        except OSError:
            cachedb = dict()
    else:
        cachedb = dict()

    index_fields = ('tech','node','size','line_sz','assoc','nbanks')
    if os.path.exists(csvfile) and not args.ignore_csvfile:
        with bz2.open(csvfile, 'rt') as f:
            reader = csv.DictReader(f)
            for row in reader:
                tech = row['tech']
                node = int(row['node'])
                size = int(row['size'])
                line_sz = int(row['line_sz'])
                assoc = int(row['assoc'])
                nbanks = int(row['nbanks'])
                key = (tech, node, size, line_sz, assoc, nbanks)
                if key in cachedb and not args.force_update:
                    continue
                tech_table_index = (tech, node)
                area_scale = _tech_scale_table[tech_table_index]['area']
                power_scale = _tech_scale_table[tech_table_index]['power']
                time_scale = _tech_scale_table[tech_table_index]['time']
                print('solve {0} {1} {2} {3}'.format(size, line_sz, assoc, nbanks))
                res = _solve_cache(size, line_sz=line_sz, assoc=assoc, nbanks=nbanks)
                cachedb[key] = {
                    'power': (res.power.readOp.dynamic/res.access_time + res.power.readOp.leakage) * power_scale,
                    'area': res.cache_ht * 1e-3 * res.cache_len * 1e-3 * area_scale,
                    'latency': res.access_time * 1e9 * time_scale,
                }

        with bz2.open(_dbfile, 'wb') as f:
            pickle.dump(cachedb, f)
    else:
        rows = []
        # small caches, e.g. L1
        size_list = (16384, 32768, 65536, 131072, 262144, 524288)
        linesz_list = (64, 128)
        assoc_list = (1, 2, 4)
        nbanks_list = (1,)
        for (tech, node), size, line_sz, assoc, nbanks in product(_tech_scale_table.keys(),
                                                                size_list, linesz_list,
                                                                assoc_list, nbanks_list):
                key = (tech, node, size, line_sz, assoc, nbanks)
                rows.append(
                    {'tech': tech, 'node': node, 'size': size,
                     'line_sz': line_sz, 'assoc': assoc, 'nbanks': nbanks})
                if key in cachedb and not args.force_update:
                    continue
                tech_table_index = (tech, node)
                area_scale = _tech_scale_table[tech_table_index]['area']
                power_scale = _tech_scale_table[tech_table_index]['power']
                time_scale = _tech_scale_table[tech_table_index]['time']
                print('solve {0} {1} {2} {3}'.format(size, line_sz, assoc, nbanks))
                res = _solve_cache(size, line_sz=line_sz, assoc=assoc, nbanks=nbanks)
                cachedb[key] = {
                    'power': (res.power.readOp.dynamic/res.access_time + res.power.readOp.leakage) * power_scale,
                    'area': res.cache_ht * 1e-3 * res.cache_len * 1e-3 * area_scale,
                    'latency': res.access_time * 1e9 * time_scale,
                }

        # large caches, e.g. L2
        size_list = (1048576, 2097152, 3145728, 4194304, 5242880, 6291456, 7340032, 8388608,
                     9437184, 10485760, 11534336, 12582912, 13631488, 14680064, 15728640,
                     16777216, 33554432, 67108864, 18874368, 134217728)
        linesz_list = (64, 128, 256)
        assoc_list = (1, 2, 4, 8)
        nbanks_list = (1, 2, 4)
        for (tech, node), size, line_sz, assoc, nbanks in product(_tech_scale_table.keys(),
                                                                size_list, linesz_list,
                                                                assoc_list, nbanks_list):
                key = (tech, node, size, line_sz, assoc, nbanks)
                rows.append(
                    {'tech': tech, 'node': node, 'size': size,
                     'line_sz': line_sz, 'assoc': assoc, 'nbanks': nbanks})
                if key in cachedb and not args.force_update:
                    continue
                tech_table_index = (tech, node)
                area_scale = _tech_scale_table[tech_table_index]['area']
                power_scale = _tech_scale_table[tech_table_index]['power']
                time_scale = _tech_scale_table[tech_table_index]['time']
                print('solve {0} {1} {2} {3}'.format(size, line_sz, assoc, nbanks))
                res = _solve_cache(size, line_sz=line_sz, assoc=assoc, nbanks=nbanks)
                cachedb[key] = {
                    'power': (res.power.readOp.dynamic/res.access_time + res.power.readOp.leakage) * power_scale,
                    'area': res.cache_ht * 1e-3 * res.cache_len * 1e-3 * area_scale,
                    'latency': res.access_time * 1e9 * time_scale,
                }

        with bz2.open(csvfile, 'wt') as f:
            csvwriter = csv.DictWriter(f, fieldnames=index_fields)
            csvwriter.writeheader()
            csvwriter.writerows(rows)

        with bz2.open(_dbfile, 'wb') as f:
            pickle.dump(cachedb, f)
