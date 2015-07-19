import re
from . import cacti

from functools import lru_cache

@lru_cache(maxsize=1024)
def _solve_cache(size):
    """ solve cache using CACTI interface

    Parameters
    ----------
    size : int
      the size of cache in bytes

    Returns
    -------
    cacti_results
      A structure contains cacti_interface results
    """
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
    ipara.line_sz = 64

    # associativity
    ipara.assoc = 2

    # number of UCA banks
    ipara.nbanks = 1

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
    mo = re.match(r'([0-9]+)([BbKkMmGg])', size)
    if not mo:
        raise Exception('cache size not recognizable: {0}'.format(cache_sz_str))
    cache_size = int(mo.group(1))
    size_suffix = mo.group(2).lower()
    return cache_size * _size_to_bytes[size_suffix]

def _get_tech_scale(tech_type, tech_node):
    return None

class CacheTraits():
    def __init__(self, size, tech_type='cmos-hp', tech_node=22):
        self._cacti_res = _solve_cache(size)
        self._tech_scale = _get_tech_scale(tech_type, tech_node)

    @property
    def access_time(self):
        return self._cacti_res.access_time * 1e9

    @property
    def cycle_time(self):
        return self._cacti_res.cycle_tiem * 1e9

    @property
    def power(self):
        lclr = 0.1+0.9*(0.8*self._cacti_res.data_array2.long_channel_leakage_reduction_memcell + 0.2*self._cacti_res.data_array2.long_channel_leakage_reduction_periperal)
        return self._cacti_res.power.readOp.dynamic / self._cacti_res.access_time + self._cacti_res.power.readOp.leakage

    @property
    def area(self):
        return self._cacti_res.cache_ht*1e-3 * self._cacti_res.cache_len*1e-3


