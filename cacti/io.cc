/*------------------------------------------------------------
 *                              CACTI 6.5
 *         Copyright 2008 Hewlett-Packard Development Corporation
 *                         All Rights Reserved
 *
 * Permission to use, copy, and modify this software and its documentation is
 * hereby granted only under the following terms and conditions.  Both the
 * above copyright notice and this permission notice must appear in all copies
 * of the software, derivative works or modified versions, and any portions
 * thereof, and both notices must appear in supporting documentation.
 *
 * Users of this software agree to the terms and conditions set forth herein, and
 * hereby grant back to Hewlett-Packard Company and its affiliated companies ("HP")
 * a non-exclusive, unrestricted, royalty-free right and license under any changes, 
 * enhancements or extensions  made to the core functions of the software, including 
 * but not limited to those affording compatibility with other hardware or software
 * environments, but excluding applications which incorporate this software.
 * Users further agree to use their best efforts to return to HP any such changes,
 * enhancements or extensions that they make and inform HP of noteworthy uses of
 * this software.  Correspondence should be provided to HP at:
 *
 *                       Director of Intellectual Property Licensing
 *                       Office of Strategy and Technology
 *                       Hewlett-Packard Company
 *                       1501 Page Mill Road
 *                       Palo Alto, California  94304
 *
 * This software may be distributed (but not offered for sale or transferred
 * for compensation) to third parties, provided such third parties agree to
 * abide by the terms and conditions of this notice.
 *
 * THE SOFTWARE IS PROVIDED "AS IS" AND HP DISCLAIMS ALL
 * WARRANTIES WITH REGARD TO THIS SOFTWARE, INCLUDING ALL IMPLIED WARRANTIES
 * OF MERCHANTABILITY AND FITNESS.   IN NO EVENT SHALL HP 
 * CORPORATION BE LIABLE FOR ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL
 * DAMAGES OR ANY DAMAGES WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR
 * PROFITS, WHETHER IN AN ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS
 * ACTION, ARISING OUT OF OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS
 * SOFTWARE.
 *------------------------------------------------------------*/

#include <fstream>
#include <iostream>
#include <sstream>


#include "io.h"
#include "area.h"
#include "basic_circuit.h"
#include "parameter.h"
#include "Ucache.h"
#include "nuca.h"
#include "crossbar.h"
#include "arbiter.h"

// using namespace std;


/* Parses "cache.cfg" file */
void
InputParameter::parse_cfg(const std::string & in_file)
{
  FILE *fp = fopen(in_file.c_str(), "r");
  char line[5000];
  char jk[5000];
  char temp_var[5000];

  if(!fp) {
    std::cout << in_file << " is missing!\n";
    exit(-1);
  }

  while(fscanf(fp, "%[^\n]\n", line) != EOF) {

    if (!strncmp("-size", line, strlen("-size"))) {
      sscanf(line, "-size %[(:-~)*]%u", jk, &(cache_sz));
      continue;
    }

    if (!strncmp("-page size", line, strlen("-page size"))) {
      sscanf(line, "-page size %[(:-~)*]%u", jk, &(page_sz_bits));
      continue;
    }

    if (!strncmp("-burst length", line, strlen("-burst length"))) {
      sscanf(line, "-burst %[(:-~)*]%u", jk, &(burst_len));
      continue;
    }

    if (!strncmp("-internal prefetch width", line, strlen("-internal prefetch width"))) {
      sscanf(line, "-internal prefetch %[(:-~)*]%u", jk, &(int_prefetch_w));
      continue;
    }

    if (!strncmp("-block", line, strlen("-block"))) {
      sscanf(line, "-block size (bytes) %d", &(line_sz)); 
      continue;
    }

    if (!strncmp("-associativity", line, strlen("-associativity"))) {
      sscanf(line, "-associativity %d", &(assoc));
      continue;
    }

    if (!strncmp("-read-write", line, strlen("-read-write"))) {
      sscanf(line, "-read-write port %d", &(num_rw_ports));
      continue;
    }

    if (!strncmp("-exclusive read", line, strlen("exclusive read"))) {
      sscanf(line, "-exclusive read port %d", &(num_rd_ports));
      continue;
    }

    if(!strncmp("-exclusive write", line, strlen("-exclusive write"))) {
      sscanf(line, "-exclusive write port %d", &(num_wr_ports));
      continue;
    }

    if (!strncmp("-single ended", line, strlen("-single ended"))) {
      sscanf(line, "-single %[(:-~)*]%d", jk, 
          &(num_se_rd_ports));
      continue;
    }

    if (!strncmp("-UCA bank", line, strlen("-UCA bank"))) {
      sscanf(line, "-UCA bank%[((:-~)| )*]%d", jk, &(nbanks));
      continue;
    }

    if (!strncmp("-technology", line, strlen("-technology"))) {
      sscanf(line, "-technology (u) %lf", &(F_sz_um));
      F_sz_nm = F_sz_um*1000;
      continue;
    }

    if (!strncmp("-output/input", line, strlen("-output/input"))) {
      sscanf(line, "-output/input bus %[(:-~)*]%d", jk, &(out_w));
      continue;
    }

    if (!strncmp("-operating temperature", line, strlen("-operating temperature"))) {
      sscanf(line, "-operating temperature %[(:-~)*]%d", jk, &(temp));
      continue;
    }

    if (!strncmp("-cache type", line, strlen("-cache type"))) {
      sscanf(line, "-cache type%[^\"]\"%[^\"]\"", jk, temp_var);

      if (!strncmp("cache", temp_var, sizeof("cache"))) {
        is_cache = true;
      }
      else
      {
        is_cache = false;
      }

      if (!strncmp("main memory", temp_var, sizeof("main memory"))) {
        is_main_mem = true;
      }
      else {
        is_main_mem = false;
      }

      continue;
    }


    if (!strncmp("-tag size", line, strlen("-tag size"))) {
      sscanf(line, "-tag size%[^\"]\"%[^\"]\"", jk, temp_var);
      if (!strncmp("default", temp_var, sizeof("default"))) {
        specific_tag = false;
        tag_w = 42; /* the acutal value is calculated
                     * later based on the cache size, bank count, and associativity
                     */
      }
      else {
        specific_tag = true;
        sscanf(line, "-tag size (b) %d", &(tag_w));
      }
      continue;
    }

    if (!strncmp("-access mode", line, strlen("-access mode"))) {
      sscanf(line, "-access %[^\"]\"%[^\"]\"", jk, temp_var);
      if (!strncmp("fast", temp_var, strlen("fast"))) {
        access_mode = 2;
      }
      else if (!strncmp("sequential", temp_var, strlen("sequential"))) {
        access_mode = 1;
      }
      else if(!strncmp("normal", temp_var, strlen("normal"))) {
        access_mode = 0;
      }
      else {
        std::cout << "ERROR: Invalid access mode!\n";
        exit(0);
      }
      continue;
    }

    if (!strncmp("-Data array cell type", line, strlen("-Data array cell type"))) {
      sscanf(line, "-Data array cell type %[^\"]\"%[^\"]\"", jk, temp_var);

      if(!strncmp("itrs-hp", temp_var, strlen("itrs-hp"))) {
        data_arr_ram_cell_tech_type = 0;
      }
      else if(!strncmp("itrs-lstp", temp_var, strlen("itrs-lstp"))) {
        data_arr_ram_cell_tech_type = 1;
      }
      else if(!strncmp("itrs-lop", temp_var, strlen("itrs-lop"))) {
        data_arr_ram_cell_tech_type = 2;
      }
      else if(!strncmp("lp-dram", temp_var, strlen("lp-dram"))) {
        data_arr_ram_cell_tech_type = 3;
      }
      else if(!strncmp("comm-dram", temp_var, strlen("comm-dram"))) {
        data_arr_ram_cell_tech_type = 4;
      }
      else {
        std::cout << "ERROR: Invalid type!\n";
        exit(0);
      }
      continue;
    }

    if (!strncmp("-Data array peripheral type", line, strlen("-Data array peripheral type"))) {
      sscanf(line, "-Data array peripheral type %[^\"]\"%[^\"]\"", jk, temp_var);

      if(!strncmp("itrs-hp", temp_var, strlen("itrs-hp"))) {
        data_arr_peri_global_tech_type = 0;
      }
      else if(!strncmp("itrs-lstp", temp_var, strlen("itrs-lstp"))) {
        data_arr_peri_global_tech_type = 1;
      }
      else if(!strncmp("itrs-lop", temp_var, strlen("itrs-lop"))) {
        data_arr_peri_global_tech_type = 2;
      }
      else {
        std::cout << "ERROR: Invalid type!\n";
        exit(0);
      }
      continue;
    }

    if (!strncmp("-Tag array cell type", line, strlen("-Tag array cell type"))) {
      sscanf(line, "-Tag array cell type %[^\"]\"%[^\"]\"", jk, temp_var);

      if(!strncmp("itrs-hp", temp_var, strlen("itrs-hp"))) {
        tag_arr_ram_cell_tech_type = 0;
      }
      else if(!strncmp("itrs-lstp", temp_var, strlen("itrs-lstp"))) {
        tag_arr_ram_cell_tech_type = 1;
      }
      else if(!strncmp("itrs-lop", temp_var, strlen("itrs-lop"))) {
        tag_arr_ram_cell_tech_type = 2;
      }
      else if(!strncmp("lp-dram", temp_var, strlen("lp-dram"))) {
        tag_arr_ram_cell_tech_type = 3;
      }
      else if(!strncmp("comm-dram", temp_var, strlen("comm-dram"))) {
        tag_arr_ram_cell_tech_type = 4;
      }
      else {
        std::cout << "ERROR: Invalid type!\n";
        exit(0);
      }
      continue;
    }

    if (!strncmp("-Tag array peripheral type", line, strlen("-Tag array peripheral type"))) {
      sscanf(line, "-Tag array peripheral type %[^\"]\"%[^\"]\"", jk, temp_var);

      if(!strncmp("itrs-hp", temp_var, strlen("itrs-hp"))) {
        tag_arr_peri_global_tech_type = 0;
      }
      else if(!strncmp("itrs-lstp", temp_var, strlen("itrs-lstp"))) {
        tag_arr_peri_global_tech_type = 1;
      }
      else if(!strncmp("itrs-lop", temp_var, strlen("itrs-lop"))) {
        tag_arr_peri_global_tech_type = 2;
      }
      else {
        std::cout << "ERROR: Invalid type!\n";
        exit(0);
      }
      continue;
    }
    if(!strncmp("-design", line, strlen("-design"))) {
      sscanf(line, "-%[((:-~)| |,)*]%d:%d:%d:%d:%d", jk,
          &(delay_wt), &(dynamic_power_wt), 
          &(leakage_power_wt),
          &(cycle_time_wt), &(area_wt));
      continue;
    }

    if(!strncmp("-deviate", line, strlen("-deviate"))) {
      sscanf(line, "-%[((:-~)| |,)*]%d:%d:%d:%d:%d", jk,
          &(delay_dev), &(dynamic_power_dev), 
          &(leakage_power_dev),
          &(cycle_time_dev), &(area_dev));
      continue;
    }

    if(!strncmp("-Optimize", line, strlen("-Optimize"))) {
      sscanf(line, "-Optimize  %[^\"]\"%[^\"]\"", jk, temp_var);

      if(!strncmp("ED^2", temp_var, strlen("ED^2"))) {
        ed = 2;
      }
      else if(!strncmp("ED", temp_var, strlen("ED"))) {
        ed = 1;
      }
      else {
        ed = 0;
      }
    }

    if(!strncmp("-NUCAdesign", line, strlen("-NUCAdesign"))) {
      sscanf(line, "-%[((:-~)| |,)*]%d:%d:%d:%d:%d", jk,
          &(delay_wt_nuca), &(dynamic_power_wt_nuca), 
          &(leakage_power_wt_nuca),
          &(cycle_time_wt_nuca), &(area_wt_nuca));
      continue;
    }

    if(!strncmp("-NUCAdeviate", line, strlen("-NUCAdeviate"))) {
      sscanf(line, "-%[((:-~)| |,)*]%d:%d:%d:%d:%d", jk,
          &(delay_dev_nuca), &(dynamic_power_dev_nuca), 
          &(leakage_power_dev_nuca),
          &(cycle_time_dev_nuca), &(area_dev_nuca));
      continue;
    }

    if(!strncmp("-Cache model", line, strlen("-cache model"))) {
      sscanf(line, "-Cache model %[^\"]\"%[^\"]\"", jk, temp_var);

      if (!strncmp("UCA", temp_var, strlen("UCA"))) {
        nuca = 0;
      }
      else {
        nuca = 1;
      }
      continue;
    }

    if(!strncmp("-NUCA bank", line, strlen("-NUCA bank"))) {
      sscanf(line, "-NUCA bank count %d", &(nuca_bank_count));

      if (nuca_bank_count != 0) {
        force_nuca_bank = 1;
      }
      continue;
    }

    if(!strncmp("-Wire inside mat", line, strlen("-Wire inside mat"))) {
      sscanf(line, "-Wire%[^\"]\"%[^\"]\"", jk, temp_var);

      if (!strncmp("global", temp_var, strlen("global"))) {
        wire_is_mat_type = 2;
        continue;
      }
      else if (!strncmp("local", temp_var, strlen("local"))) {
        wire_is_mat_type = 0;
        continue;
      }
      else {
        wire_is_mat_type = 1;
        continue;
      }
    }

    if(!strncmp("-Wire outside mat", line, strlen("-Wire outside mat"))) {
      sscanf(line, "-Wire%[^\"]\"%[^\"]\"", jk, temp_var);

      if (!strncmp("global", temp_var, strlen("global"))) {
        wire_os_mat_type = 2;
      }
      else {
        wire_os_mat_type = 1;
      }
      continue;
    }

    if(!strncmp("-Interconnect projection", line, strlen("-Interconnect projection"))) {
      sscanf(line, "-Interconnect projection%[^\"]\"%[^\"]\"", jk, temp_var);

      if (!strncmp("aggressive", temp_var, strlen("aggressive"))) {
        ic_proj_type = 0;
      }
      else {
        ic_proj_type = 1;
      }
      continue;
    }

    if(!strncmp("-Wire signalling", line, strlen("-wire signalling"))) {
      sscanf(line, "-Wire%[^\"]\"%[^\"]\"", jk, temp_var);

      if (!strncmp("default", temp_var, strlen("default"))) {
        force_wiretype = 0;
        wt = Global;
      }
      else if (!(strncmp("Global_10", temp_var, strlen("Global_10")))) {
        force_wiretype = 1;
        wt = Global_10;        
      }
      else if (!(strncmp("Global_20", temp_var, strlen("Global_20")))) {
        force_wiretype = 1;
        wt = Global_20;        
      }
      else if (!(strncmp("Global_30", temp_var, strlen("Global_30")))) {
        force_wiretype = 1;
        wt = Global_30;        
      }
      else if (!(strncmp("Global_5", temp_var, strlen("Global_5")))) {
        force_wiretype = 1;
        wt = Global_5;        
      }
      else if (!(strncmp("Global", temp_var, strlen("Global")))) {
        force_wiretype = 1;
        wt = Global;        
      }
      else {
        wt = Low_swing;
        force_wiretype = 1;
      }
      continue;
    }



    if(!strncmp("-Core", line, strlen("-Core"))) {
      sscanf(line, "-Core count %d\n", &(cores));
      if (cores > 16) {
        printf("No. of cores should be less than 16!\n");
      }
      continue;
    }

    if(!strncmp("-Cache level", line, strlen("-Cache level"))) {
      sscanf(line, "-Cache l%[^\"]\"%[^\"]\"", jk, temp_var);
      if (!strncmp("L2", temp_var, strlen("L2"))) {
        cache_level = 0;
      }
      else {
        cache_level = 1;
      }
    }

    if(!strncmp("-Print level", line, strlen("-Print level"))) {
      sscanf(line, "-Print l%[^\"]\"%[^\"]\"", jk, temp_var);
      if (!strncmp("DETAILED", temp_var, strlen("DETAILED"))) {
        print_detail = 1;
      }
      else {
        print_detail = 0;
      }

    }
    if(!strncmp("-Add ECC", line, strlen("-Add ECC"))) {
      sscanf(line, "-Add ECC %[^\"]\"%[^\"]\"", jk, temp_var);
      if (!strncmp("true", temp_var, strlen("true"))) {
        add_ecc_b_ = true;
      }
      else {
        add_ecc_b_ = false;
      }
    }

    if(!strncmp("-Print input parameters", line, strlen("-Print input parameters"))) {
      sscanf(line, "-Print input %[^\"]\"%[^\"]\"", jk, temp_var);
      if (!strncmp("true", temp_var, strlen("true"))) {
        print_input_args = true;
      }
      else {
        print_input_args = false;
      }
    }

    if(!strncmp("-Force cache config", line, strlen("-Force cache config"))) {
      sscanf(line, "-Force cache %[^\"]\"%[^\"]\"", jk, temp_var);
      if (!strncmp("true", temp_var, strlen("true"))) {
        force_cache_config = true;
      }
      else {
        force_cache_config = false;
      }
    }

    if(!strncmp("-Ndbl", line, strlen("-Ndbl"))) {
      sscanf(line, "-Ndbl %d\n", &(ndbl));
      continue;
    }
    if(!strncmp("-Ndwl", line, strlen("-Ndwl"))) {
      sscanf(line, "-Ndwl %d\n", &(ndwl));
      continue;
    }
    if(!strncmp("-Nspd", line, strlen("-Nspd"))) {
      sscanf(line, "-Nspd %d\n", &(nspd));
      continue;
    }
    if(!strncmp("-Ndsam1", line, strlen("-Ndsam1"))) {
      sscanf(line, "-Ndsam1 %d\n", &(ndsam1));
      continue;
    }
    if(!strncmp("-Ndsam2", line, strlen("-Ndsam2"))) {
      sscanf(line, "-Ndsam2 %d\n", &(ndsam2));
      continue;
    }
   if(!strncmp("-Ndcm", line, strlen("-Ndcm"))) {
      sscanf(line, "-Ndcm %d\n", &(ndcm));
      continue;
    }

  }
  rpters_in_htree = true;
  fclose(fp);
}

  void
InputParameter::display_ip()
{
  std::cout << "Cache size                    : " << cache_sz << std::endl;
  std::cout << "Block size                    : " << line_sz << std::endl;
  std::cout << "Associativity                 : " << assoc << std::endl;
  std::cout << "Read only ports               : " << num_rd_ports << std::endl;
  std::cout << "Write only ports              : " << num_wr_ports << std::endl;
  std::cout << "Read write ports              : " << num_rw_ports << std::endl;
  std::cout << "Single ended read ports       : " << num_se_rd_ports << std::endl;
  std::cout << "Cache banks (UCA)             : " << nbanks << std::endl;
  std::cout << "Technology                    : " << F_sz_um << std::endl;
  std::cout << "Temperature                   : " << temp << std::endl;
  std::cout << "Tag size                      : " << tag_w << std::endl;
  if (is_cache) {
    std::cout << "cache type                    : " << "Cache" << std::endl;
  }
  else {
    std::cout << "cache type                    : " << "Scratch RAM" << std::endl;
  }
  std::cout << "Model as memory               : " << is_main_mem << std::endl;
  std::cout << "Access mode                   : " << access_mode << std::endl;
  std::cout << "Data array cell type          : " << data_arr_ram_cell_tech_type << std::endl;
  std::cout << "Data array peripheral type    : " << data_arr_peri_global_tech_type << std::endl;
  std::cout << "Tag array cell type           : " << tag_arr_ram_cell_tech_type << std::endl;
  std::cout << "Tag array peripheral type     : " << tag_arr_peri_global_tech_type << std::endl;
  std::cout << "Design objective (UCA wt)     : " << delay_wt << " "
                                                << dynamic_power_wt << " " << leakage_power_wt << " " << cycle_time_wt
                                                << " " << area_wt << std::endl;
  std::cout << "Design objective (UCA dev)    : " << delay_dev << " "
                                                << dynamic_power_dev << " " << leakage_power_dev << " " << cycle_time_dev
                                                << " " << area_dev << std::endl;
  std::cout << "Design objective (NUCA wt)    : " << delay_wt_nuca << " "
                                                << dynamic_power_wt_nuca << " " << leakage_power_wt_nuca << " " << cycle_time_wt_nuca
                                                << " " << area_wt_nuca << std::endl;
  std::cout << "Design objective (NUCA dev)   : " << delay_dev_nuca << " "
                                                << dynamic_power_dev_nuca << " " << leakage_power_dev_nuca << " " << cycle_time_dev_nuca
                                                << " " << area_dev_nuca << std::endl;
  std::cout << "Cache model                   : " << nuca << std::endl;
  std::cout << "Nuca bank                     : " << nuca_bank_count << std::endl;
  std::cout << "Wire inside mat               : " << wire_is_mat_type << std::endl;
  std::cout << "Wire outside mat              : " << wire_os_mat_type << std::endl;
  std::cout << "Interconnect projection       : " << ic_proj_type << std::endl;
  std::cout << "Wire signalling               : " << force_wiretype << std::endl;
  std::cout << "Cores                         : " << cores << std::endl;
  std::cout << "Print level                   : " << print_detail << std::endl;
  std::cout << "ECC overhead                  : " << add_ecc_b_ << std::endl;
  std::cout << "Page size                     : " << page_sz_bits << std::endl;
  std::cout << "Burst length                  : " << burst_len << std::endl;
  std::cout << "Internal prefetch width       : " << int_prefetch_w << std::endl;
  std::cout << "Force cache config            : " << g_ip->force_cache_config << std::endl;
  if (g_ip->force_cache_config) {
    std::cout << "Ndwl                          : " << g_ip->ndwl << std::endl;
    std::cout << "Ndbl                          : " << g_ip->ndbl << std::endl;
    std::cout << "Nspd                          : " << g_ip->nspd << std::endl;
    std::cout << "Ndcm                          : " << g_ip->ndcm << std::endl;
    std::cout << "Ndsam1                        : " << g_ip->ndsam1 << std::endl;
    std::cout << "Ndsam2                        : " << g_ip->ndsam2 << std::endl;
  }
}


void InputParameter::dump_input_parameter(const std::string &ofs_name)
{
  std::ofstream ofs(ofs_name.c_str());
  ofs<<"cash_sz:"<<cache_sz<<std::endl;  // in bytes
  ofs<<"line_sz:"<<line_sz<<std::endl;
  ofs<<"assoc:"<<assoc<<std::endl;
  ofs<<"nbanks:"<<nbanks<<std::endl;
  ofs<<"out_w:"<<out_w<<std::endl;// == nr_bits_out
  ofs<<"specific_tag:"<<specific_tag<<std::endl;
  ofs<<"tag_w:"<<tag_w<<std::endl;
  ofs<<"access_mode:"<<access_mode<<std::endl;
  ofs<<"obj_func_dyn_energy:"<<obj_func_dyn_energy<<std::endl;
  ofs<<"obj_func_dyn_power:"<<obj_func_dyn_power<<std::endl;
  ofs<<"obj_func_leak_power:"<<obj_func_leak_power<<std::endl;
  ofs<<"obj_func_cycle_time:"<<obj_func_cycle_t<<std::endl;
  ofs<<"F_sz_nm:"<<F_sz_nm<<std::endl;          // feature size in nm
  ofs<<"F_sz_um:"<<F_sz_um<<std::endl;          // feature size in um
  ofs<<"num_rw_ports:"<<num_rw_ports<<std::endl;
  ofs<<"num_rd_ports:"<<num_rd_ports<<std::endl;
  ofs<<"num_wr_ports:"<<num_wr_ports<<std::endl;
  ofs<<"num_se_rd_ports:"<<num_se_rd_ports<<std::endl;  // number of single ended read ports
  ofs<<"is_main_mem:"<<is_main_mem<<std::endl;
  ofs<<"is_cache:"<<is_cache<<std::endl;
  ofs<<"rpters_in_htree:"<<rpters_in_htree<<std::endl;  // if there are repeaters in htree segment
  ofs<<"ver_htree_wires_over_array:"<<ver_htree_wires_over_array<<std::endl;
  ofs<<"broadcast_addr_din_over_ver_htrees:"<<broadcast_addr_din_over_ver_htrees<<std::endl;
  ofs<<"temp:"<<temp<<std::endl;
  ofs<<"ram_cell_tech_type:"<<ram_cell_tech_type<<std::endl;
  ofs<<"peri_global_tech_type:"<<peri_global_tech_type<<std::endl;
  ofs<<"data_arr_ram_cell_tech_type:"<<data_arr_ram_cell_tech_type<<std::endl;
  ofs<<"data_arr_peri_global_tech_type:"<<data_arr_peri_global_tech_type<<std::endl;
  ofs<<"tag_arr_ram_cell_tech_type:"<<tag_arr_ram_cell_tech_type<<std::endl;
  ofs<<"tag_arr_peri_global_tech_type:"<<tag_arr_peri_global_tech_type<<std::endl;
  ofs<<"burst_len:"<<burst_len<<std::endl;
  ofs<<"int_prefetch_w:"<<int_prefetch_w<<std::endl;
  ofs<<"page_sz_bits:"<<page_sz_bits<<std::endl;
  ofs<<"ic_proj_type:"<<ic_proj_type<<std::endl;      // interconnect_projection_type
  ofs<<"wire_is_mat_type:"<<wire_is_mat_type<<std::endl;  // wire_inside_mat_type 
  ofs<<"wire_os_mat_type:"<<wire_os_mat_type<<std::endl; // wire_outside_mat_type
  ofs<<"force_wiretype:"<<force_wiretype<<std::endl; 
  ofs<<"print_input_args:"<<print_input_args<<std::endl;
  ofs<<"nuca_cache_sz:"<<nuca_cache_sz<<std::endl; // TODO
  ofs<<"ndbl:"<<ndbl<<std::endl;
  ofs<<"ndwl:"<<ndwl<<std::endl;
  ofs<<"nspd:"<<nspd<<std::endl;
  ofs<<"ndsam1:"<<ndsam1<<std::endl;
  ofs<<"ndsam2:"<<ndsam2<<std::endl;
  ofs<<"ndcm:"<<ndcm<<std::endl;
  ofs<<"force_cache_config:"<<force_cache_config<<std::endl;
  ofs<<"cache_level:"<<cache_level<<std::endl;
  ofs<<"cores:"<<cores<<std::endl;
  ofs<<"nuca_bank_count:"<<nuca_bank_count<<std::endl;
  ofs<<"force_nuca_bank:"<<force_nuca_bank<<std::endl;
  ofs<<"delay_wt:"<<delay_wt<<std::endl;
  ofs<<"dynamic_power_wt:"<<dynamic_power_wt<<std::endl;
  ofs<<"leakage_power_wt:"<<leakage_power_wt<<std::endl;
  ofs<<"cycle_time_wt:"<<cycle_time_wt<<std::endl;
  ofs<<"area_wt:"<<area_wt<<std::endl;
  ofs<<"delay_wt_nuca:"<<delay_wt_nuca<<std::endl;
  ofs<<"idynamic_power_wt_nuca:"<<dynamic_power_wt_nuca<<std::endl;
  ofs<<"leakage_power_wt_nuca:"<<leakage_power_wt_nuca<<std::endl;
  ofs<<"cycle_time_wt_nuca:"<<cycle_time_wt_nuca<<std::endl;
  ofs<<"area_wt_nuca:"<<area_wt_nuca<<std::endl;
  ofs<<"delay_dev:"<<delay_dev<<std::endl;
  ofs<<"dynamice_power_dev:"<<dynamic_power_dev<<std::endl;
  ofs<<"leakage_power_dev:"<<leakage_power_dev<<std::endl;
  ofs<<"cycle_time_dev:"<<cycle_time_dev<<std::endl;
  ofs<<"area_dev:"<<area_dev<<std::endl;
  ofs<<"delay_dev_nuca:"<<delay_dev_nuca<<std::endl;
  ofs<<"dynamic_power_dev_nuca:"<<dynamic_power_dev_nuca<<std::endl;
  ofs<<"leakage_power_dev_nuca:"<<leakage_power_dev_nuca<<std::endl;
  ofs<<"cycle_time_dev_nuca:"<<cycle_time_dev_nuca<<std::endl;
  ofs<<"area_dev_nuca:"<<area_dev_nuca<<std::endl;
  ofs<<"ed:"<<ed<<std::endl; //ED or ED2 optimization
  ofs<<"nuca:"<<nuca<<std::endl;
  ofs<<"fast_access:"<<fast_access<<std::endl;
  ofs<<"block_sz:"<<block_sz<<std::endl;  // bytes
  ofs<<"tag_assoc:"<<tag_assoc<<std::endl;
  ofs<<"data_assoc:"<<data_assoc<<std::endl;
  ofs<<"is_seq_acc:"<<is_seq_acc<<std::endl;
  ofs<<"fully_assoc:"<<fully_assoc<<std::endl;
  ofs<<"nsets:"<<nsets<<std::endl;  // == number_of_sets
  ofs<<"print_details:"<<print_detail<<std::endl;
  ofs<<"add_ecc_b_:"<<add_ecc_b_<<std::endl;
  ofs<<"wire_type:"<<wt<<std::endl;
  ofs.close();
}


powerComponents operator+(const powerComponents & x, const powerComponents & y)
{
  powerComponents z;

  z.dynamic = x.dynamic + y.dynamic;
  z.leakage = x.leakage + y.leakage;

  return z;
}



powerDef operator+(const powerDef & x, const powerDef & y)
{
  powerDef z;

  z.readOp  = x.readOp  + y.readOp;
  z.writeOp = x.writeOp + y.writeOp;

  return z;
}


const uca_org_t cacti_solve(const std::string & infile_name)
{

  uca_org_t fin_res;
  //  uca_org_t result;
  fin_res.valid = false;

  g_ip = new InputParameter();
  g_ip->parse_cfg(infile_name);
  if (g_ip->error_checking() == false) exit(0);

  init_tech_params(g_ip->F_sz_um, false);
  Wire winit; // Do not delete this line. It initializes wires.

  if (g_ip->nuca == 1)
    {
      Nuca n(&g_tp.peri_global);
      n.sim_nuca();
    }
  //  g_ip->display_ip();
  solve(&fin_res);

  delete (g_ip);
  return fin_res;
}

const uca_org_t cacti_interface(const std::string & infile_name)
{

  uca_org_t fin_res;
//  uca_org_t result;
  fin_res.valid = false;

  g_ip = new InputParameter();
  g_ip->parse_cfg(infile_name);
  if (g_ip->error_checking() == false) exit(0);
  if (g_ip->print_input_args) 
    g_ip->display_ip();

  init_tech_params(g_ip->F_sz_um, false);
  Wire winit; // Do not delete this line. It initializes wires.

  if (g_ip->nuca == 1)
  {
    Nuca n(&g_tp.peri_global);
    n.sim_nuca();
  }
//  g_ip->display_ip();
  solve(&fin_res);

  output_UCA(&fin_res);

  delete (g_ip);
  return fin_res;
}

const uca_org_t cacti_interface(
    int cache_size,
    int line_size,
    int associativity,
    int rw_ports,
    int excl_read_ports,
    int excl_write_ports,
    int single_ended_read_ports,
    int banks,
    double tech_node, // in nm
    int page_sz,
    int burst_length,
    int pre_width,
    int output_width,
    int specific_tag,
    int tag_width,
    int access_mode, //0 normal, 1 seq, 2 fast
    int cache, //scratch ram or cache
    int main_mem,
    int obj_func_delay,
    int obj_func_dynamic_power,
    int obj_func_leakage_power,
    int obj_func_area,
    int obj_func_cycle_time,
    int dev_func_delay,
    int dev_func_dynamic_power,
    int dev_func_leakage_power,
    int dev_func_area,
    int dev_func_cycle_time,
    int ed_ed2_none, // 0 - ED, 1 - ED^2, 2 - use weight and deviate
    int temp,
    int wt, //0 - default(search across everything), 1 - global, 2 - 5% delay penalty, 3 - 10%, 4 - 20 %, 5 - 30%, 6 - low-swing 
    int data_arr_ram_cell_tech_flavor_in, // 0-4
    int data_arr_peri_global_tech_flavor_in, 
    int tag_arr_ram_cell_tech_flavor_in,
    int tag_arr_peri_global_tech_flavor_in,
    int interconnect_projection_type_in, // 0 - aggressive, 1 - normal
    int wire_inside_mat_type_in, 
    int wire_outside_mat_type_in, 
    int is_nuca, // 0 - UCA, 1 - NUCA
    int core_count,
    int cache_level, // 0 - L2, 1 - L3
    int nuca_bank_count,
    int nuca_obj_func_delay,
    int nuca_obj_func_dynamic_power,
    int nuca_obj_func_leakage_power,
    int nuca_obj_func_area,
    int nuca_obj_func_cycle_time,
    int nuca_dev_func_delay,
    int nuca_dev_func_dynamic_power,
    int nuca_dev_func_leakage_power,
    int nuca_dev_func_area,
    int nuca_dev_func_cycle_time,
    int REPEATERS_IN_HTREE_SEGMENTS_in,//TODO for now only wires with repeaters are supported
    int p_input)
{
  g_ip = new InputParameter();
  g_ip->add_ecc_b_ = true;

  g_ip->data_arr_ram_cell_tech_type    = data_arr_ram_cell_tech_flavor_in;
  g_ip->data_arr_peri_global_tech_type = data_arr_peri_global_tech_flavor_in;
  g_ip->tag_arr_ram_cell_tech_type     = tag_arr_ram_cell_tech_flavor_in;
  g_ip->tag_arr_peri_global_tech_type  = tag_arr_peri_global_tech_flavor_in;

  g_ip->ic_proj_type     = interconnect_projection_type_in;
  g_ip->wire_is_mat_type = wire_inside_mat_type_in;
  g_ip->wire_os_mat_type = wire_outside_mat_type_in;
  g_ip->burst_len        = burst_length;
  g_ip->int_prefetch_w   = pre_width;
  g_ip->page_sz_bits     = page_sz;

  g_ip->cache_sz            = cache_size;
  g_ip->line_sz             = line_size;
  g_ip->assoc               = associativity;
  g_ip->nbanks              = banks;
  g_ip->out_w               = output_width;
  g_ip->specific_tag        = specific_tag;
  if (tag_width == 0) {
    g_ip->tag_w = 42; 
  }
  else {
    g_ip->tag_w               = tag_width;
  }

  g_ip->access_mode         = access_mode;
  g_ip->delay_wt = obj_func_delay;
  g_ip->dynamic_power_wt = obj_func_dynamic_power;
  g_ip->leakage_power_wt = obj_func_leakage_power;
  g_ip->area_wt = obj_func_area;
  g_ip->cycle_time_wt    = obj_func_cycle_time;
  g_ip->delay_dev = dev_func_delay;
  g_ip->dynamic_power_dev = dev_func_dynamic_power;
  g_ip->leakage_power_dev = dev_func_leakage_power;
  g_ip->area_dev = dev_func_area;
  g_ip->cycle_time_dev    = dev_func_cycle_time;
  g_ip->ed = ed_ed2_none;

  switch(wt) {
    case (0):
      g_ip->force_wiretype = 0;
      g_ip->wt = Global;
      break;
    case (1):
      g_ip->force_wiretype = 1;
      g_ip->wt = Global;
      break;
    case (2):
      g_ip->force_wiretype = 1;
      g_ip->wt = Global_5;
      break;
    case (3):
      g_ip->force_wiretype = 1;
      g_ip->wt = Global_10;
      break;
    case (4):
      g_ip->force_wiretype = 1;
      g_ip->wt = Global_20;
      break;
    case (5):
      g_ip->force_wiretype = 1;
      g_ip->wt = Global_30;
      break;
    case (6):
      g_ip->force_wiretype = 1;
      g_ip->wt = Low_swing;
      break;
    default:
      std::cout << "Unknown wire type!\n";
      exit(0);
  }

  g_ip->delay_wt_nuca = nuca_obj_func_delay;
  g_ip->dynamic_power_wt_nuca = nuca_obj_func_dynamic_power;
  g_ip->leakage_power_wt_nuca = nuca_obj_func_leakage_power;
  g_ip->area_wt_nuca = nuca_obj_func_area;
  g_ip->cycle_time_wt_nuca    = nuca_obj_func_cycle_time;
  g_ip->delay_dev_nuca = nuca_dev_func_delay;
  g_ip->dynamic_power_dev_nuca = nuca_dev_func_dynamic_power;
  g_ip->leakage_power_dev_nuca = nuca_dev_func_leakage_power;
  g_ip->area_dev_nuca = nuca_dev_func_area;
  g_ip->cycle_time_dev_nuca    = nuca_dev_func_cycle_time;
  g_ip->nuca = is_nuca;
  g_ip->nuca_bank_count = nuca_bank_count;
  if(nuca_bank_count > 0) {
    g_ip->force_nuca_bank = 1;
  }
  g_ip->cores = core_count;
  g_ip->cache_level = cache_level;

  g_ip->temp = temp;

  g_ip->F_sz_nm         = tech_node;
  g_ip->F_sz_um         = tech_node / 1000;
  g_ip->is_main_mem     = (main_mem != 0) ? true : false;
  g_ip->is_cache        = (cache != 0) ? true : false;
  g_ip->rpters_in_htree = (REPEATERS_IN_HTREE_SEGMENTS_in != 0) ? true : false;

  g_ip->num_rw_ports    = rw_ports;
  g_ip->num_rd_ports    = excl_read_ports;
  g_ip->num_wr_ports    = excl_write_ports;
  g_ip->num_se_rd_ports = single_ended_read_ports;
  g_ip->print_detail = 1;
  g_ip->nuca = 0;

  // g_ip->wt = Global_5;
  g_ip->force_cache_config = false;
  // g_ip->force_wiretype = false;
  g_ip->print_input_args = p_input;


  uca_org_t fin_res;
  fin_res.valid = false;

  if (g_ip->error_checking() == false) exit(0);
  if (g_ip->print_input_args) 
    g_ip->display_ip();
  init_tech_params(g_ip->F_sz_um, false);
  Wire winit; // Do not delete this line. It initializes wires.

  if (g_ip->nuca == 1)
  {
    Nuca n(&g_tp.peri_global);
    n.sim_nuca();
  }
  solve(&fin_res);

  output_UCA(&fin_res);

  delete (g_ip);
  return fin_res;
}


const uca_org_t cacti_solve(
    int cache_size,
    int line_size,
    int associativity,
    int rw_ports,
    int excl_read_ports,
    int excl_write_ports,
    int single_ended_read_ports,
    int banks,
    double tech_node, // in nm
    int page_sz,
    int burst_length,
    int pre_width,
    int output_width,
    int specific_tag,
    int tag_width,
    int access_mode, //0 normal, 1 seq, 2 fast
    int cache, //scratch ram or cache
    int main_mem,
    int obj_func_delay,
    int obj_func_dynamic_power,
    int obj_func_leakage_power,
    int obj_func_area,
    int obj_func_cycle_time,
    int dev_func_delay,
    int dev_func_dynamic_power,
    int dev_func_leakage_power,
    int dev_func_area,
    int dev_func_cycle_time,
    int ed_ed2_none, // 0 - ED, 1 - ED^2, 2 - use weight and deviate
    int temp,
    int wt, //0 - default(search across everything), 1 - global, 2 - 5% delay penalty, 3 - 10%, 4 - 20 %, 5 - 30%, 6 - low-swing 
    int data_arr_ram_cell_tech_flavor_in, // 0-4
    int data_arr_peri_global_tech_flavor_in, 
    int tag_arr_ram_cell_tech_flavor_in,
    int tag_arr_peri_global_tech_flavor_in,
    int interconnect_projection_type_in, // 0 - aggressive, 1 - normal
    int wire_inside_mat_type_in, 
    int wire_outside_mat_type_in, 
    int is_nuca, // 0 - UCA, 1 - NUCA
    int core_count,
    int cache_level, // 0 - L2, 1 - L3
    int nuca_bank_count,
    int nuca_obj_func_delay,
    int nuca_obj_func_dynamic_power,
    int nuca_obj_func_leakage_power,
    int nuca_obj_func_area,
    int nuca_obj_func_cycle_time,
    int nuca_dev_func_delay,
    int nuca_dev_func_dynamic_power,
    int nuca_dev_func_leakage_power,
    int nuca_dev_func_area,
    int nuca_dev_func_cycle_time,
    int REPEATERS_IN_HTREE_SEGMENTS_in,//TODO for now only wires with repeaters are supported
    int p_input)
{
  g_ip = new InputParameter();
  g_ip->add_ecc_b_ = true;

  g_ip->data_arr_ram_cell_tech_type    = data_arr_ram_cell_tech_flavor_in;
  g_ip->data_arr_peri_global_tech_type = data_arr_peri_global_tech_flavor_in;
  g_ip->tag_arr_ram_cell_tech_type     = tag_arr_ram_cell_tech_flavor_in;
  g_ip->tag_arr_peri_global_tech_type  = tag_arr_peri_global_tech_flavor_in;

  g_ip->ic_proj_type     = interconnect_projection_type_in;
  g_ip->wire_is_mat_type = wire_inside_mat_type_in;
  g_ip->wire_os_mat_type = wire_outside_mat_type_in;
  g_ip->burst_len        = burst_length;
  g_ip->int_prefetch_w   = pre_width;
  g_ip->page_sz_bits     = page_sz;

  g_ip->cache_sz            = cache_size;
  g_ip->line_sz             = line_size;
  g_ip->assoc               = associativity;
  g_ip->nbanks              = banks;
  g_ip->out_w               = output_width;
  g_ip->specific_tag        = specific_tag;
  if (tag_width == 0) {
    g_ip->tag_w = 42; 
  }
  else {
    g_ip->tag_w               = tag_width;
  }

  g_ip->access_mode         = access_mode;
  g_ip->delay_wt = obj_func_delay;
  g_ip->dynamic_power_wt = obj_func_dynamic_power;
  g_ip->leakage_power_wt = obj_func_leakage_power;
  g_ip->area_wt = obj_func_area;
  g_ip->cycle_time_wt    = obj_func_cycle_time;
  g_ip->delay_dev = dev_func_delay;
  g_ip->dynamic_power_dev = dev_func_dynamic_power;
  g_ip->leakage_power_dev = dev_func_leakage_power;
  g_ip->area_dev = dev_func_area;
  g_ip->cycle_time_dev    = dev_func_cycle_time;
  g_ip->ed = ed_ed2_none;

  switch(wt) {
    case (0):
      g_ip->force_wiretype = 0;
      g_ip->wt = Global;
      break;
    case (1):
      g_ip->force_wiretype = 1;
      g_ip->wt = Global;
      break;
    case (2):
      g_ip->force_wiretype = 1;
      g_ip->wt = Global_5;
      break;
    case (3):
      g_ip->force_wiretype = 1;
      g_ip->wt = Global_10;
      break;
    case (4):
      g_ip->force_wiretype = 1;
      g_ip->wt = Global_20;
      break;
    case (5):
      g_ip->force_wiretype = 1;
      g_ip->wt = Global_30;
      break;
    case (6):
      g_ip->force_wiretype = 1;
      g_ip->wt = Low_swing;
      break;
    default:
      std::cout << "Unknown wire type!\n";
      exit(0);
  }

  g_ip->delay_wt_nuca = nuca_obj_func_delay;
  g_ip->dynamic_power_wt_nuca = nuca_obj_func_dynamic_power;
  g_ip->leakage_power_wt_nuca = nuca_obj_func_leakage_power;
  g_ip->area_wt_nuca = nuca_obj_func_area;
  g_ip->cycle_time_wt_nuca    = nuca_obj_func_cycle_time;
  g_ip->delay_dev_nuca = nuca_dev_func_delay;
  g_ip->dynamic_power_dev_nuca = nuca_dev_func_dynamic_power;
  g_ip->leakage_power_dev_nuca = nuca_dev_func_leakage_power;
  g_ip->area_dev_nuca = nuca_dev_func_area;
  g_ip->cycle_time_dev_nuca    = nuca_dev_func_cycle_time;
  g_ip->nuca = is_nuca;
  g_ip->nuca_bank_count = nuca_bank_count;
  if(nuca_bank_count > 0) {
    g_ip->force_nuca_bank = 1;
  }
  g_ip->cores = core_count;
  g_ip->cache_level = cache_level;

  g_ip->temp = temp;

  g_ip->F_sz_nm         = tech_node;
  g_ip->F_sz_um         = tech_node / 1000;
  g_ip->is_main_mem     = (main_mem != 0) ? true : false;
  g_ip->is_cache        = (cache != 0) ? true : false;
  g_ip->rpters_in_htree = (REPEATERS_IN_HTREE_SEGMENTS_in != 0) ? true : false;

  g_ip->num_rw_ports    = rw_ports;
  g_ip->num_rd_ports    = excl_read_ports;
  g_ip->num_wr_ports    = excl_write_ports;
  g_ip->num_se_rd_ports = single_ended_read_ports;
  g_ip->print_detail = 1;
  g_ip->nuca = 0;

  // g_ip->wt = Global_5;
  g_ip->force_cache_config = false;
  // g_ip->force_wiretype = false;
  g_ip->print_input_args = p_input;


  uca_org_t fin_res;
  fin_res.valid = false;

  if (g_ip->error_checking() == false) exit(0);
  init_tech_params(g_ip->F_sz_um, false);
  Wire winit; // Do not delete this line. It initializes wires.

  if (g_ip->nuca == 1)
  {
    Nuca n(&g_tp.peri_global);
    n.sim_nuca();
  }
  solve(&fin_res);

  delete (g_ip);
  return fin_res;
}

bool InputParameter::error_checking()
{
  int  A;
  bool seq_access  = false;
  fast_access = true;

  switch (access_mode)
  {
    case 0:
      seq_access  = false;
      fast_access = false;
      break;
    case 1:
      seq_access  = true;
      fast_access = false;
      break;
    case 2:
      seq_access  = false;
      fast_access = true;
      break;
  }

  if(is_main_mem)
  {
    if(ic_proj_type == 0)
    {
      std::cerr << "DRAM model supports only conservative interconnect projection!\n\n";
      return false;
    }
  }

  uint32_t B = line_sz;

  if (B < 1)
  {
    std::cerr << "Block size must >= 1" << std::endl;
    return false;
  }
  else if (B*8 < out_w)
  {
    std::cerr << "Block size must be at least " << out_w/8 << std::endl;
    return false;
  }

  if (F_sz_um <= 0)
  {
    std::cerr << "Feature size must be > 0" << std::endl;
    return false;
  }
  else if (F_sz_um > 0.091)
  {
    std::cerr << "Feature size must be <= 90 nm" << std::endl;
    return false;
  }


  uint32_t RWP  = num_rw_ports;
  uint32_t ERP  = num_rd_ports;
  uint32_t EWP  = num_wr_ports;
  uint32_t NSER = num_se_rd_ports;

//  // If multiple banks and multiple ports are specified, then if number of ports is less than or equal to
//  // the number of banks, we assume that the multiple ports are implemented via the multiple banks.
//  // In such a case we assume that each bank has 1 RWP port. 
//  if ((RWP + ERP + EWP) <= nbanks)
//  {
//    RWP  = 1;
//    ERP  = 0;
//    EWP  = 0;
//    NSER = 0;
//  }
//  else if ((RWP < 0) || (EWP < 0) || (ERP < 0))
//  {
//    std::cerr << "Ports must >=0" << std::endl;
//    return false;
//  }
//  else if (RWP > 2)
//  {
//    std::cerr << "Maximum of 2 read/write ports" << std::endl;
//    return false;
//  }

  //  The number of ports specified at input is per bank
  if ((RWP+ERP+EWP) < 1)
  {
    std::cerr << "Must have at least one port" << std::endl;
    return false;
  }

  if (is_pow2(nbanks) == false)
  {
    std::cerr << "Number of subbanks should be greater than or equal to 1 and should be a power of 2" << std::endl;
    return false;
  }

  int C = cache_sz/nbanks;
  if (C < 64)
  {
    std::cerr << "Cache size must >=64" << std::endl;
    return false;
  }

  if (assoc == 0)
  {
    A = C/B;
    fully_assoc = true;
  }
  else
  {
    if (assoc == 1)
    {
      A = 1;
      fully_assoc = false;
    }
    else
    {
      fully_assoc = false;
      A = assoc;
      if (is_pow2(A) == false)
      {
        std::cerr << "Associativity must be a power of 2" << std::endl;
        return false;
      }
    }
  }

  if (C/(B*A) <= 1 && !fully_assoc)
  {
    std::cerr << "Number of sets is too small: " << std::endl;
    std::cerr << " Need to either increase cache size, or decrease associativity or block size" << std::endl;
    std::cerr << " (or use fully associative cache)" << std::endl;
    return false;
  }

  block_sz = B;

  /*dt: testing sequential access mode*/
  if(seq_access)
  {
    tag_assoc  = A;
    data_assoc = 1;
    is_seq_acc = true;
  }
  else
  {
    tag_assoc  = A;
    data_assoc = A;
    is_seq_acc = false;
  }

  if (fully_assoc)
  {
    data_assoc = 1;
  }
  num_rw_ports    = RWP;
  num_rd_ports    = ERP;
  num_wr_ports    = EWP;
  num_se_rd_ports = NSER;
  nsets           = C/(B*A);

  if (temp < 300 || temp > 400 || temp%10 != 0)
  {
    std::cerr << temp << " Temperature must be between 300 and 400 Kelvin and multiple of 10." << std::endl;
    return false;
  }

  if (nsets < 1)
  {
    std::cerr << "Less than one set..." << std::endl;
    return false;
  }

  return true;
}



void output_data_csv(const uca_org_t & fin_res)
{
  std::fstream file("out.csv", std::ios::in);
  bool    print_index = file.fail();
  file.close();

  file.open("out.csv", std::ios::out|std::ios::app);
  if (file.fail() == true)
  {
    std::cerr << "File out.csv could not be opened successfully" << std::endl;
  }
  else
  {
    if (print_index == true)
    {
      file << "Tech node (nm), ";
      file << "Capacity (bytes), ";
      file << "Number of banks, ";
      file << "Associativity, ";
      file << "Output width (bits), ";
      file << "Access time (ns), ";
      file << "Random cycle time (ns), ";
      file << "Multisubbank interleave cycle time (ns), ";
      file << "Delay request network (ns), ";
      file << "Delay inside mat (ns), ";
      file << "Delay reply network (ns), ";
      file << "Tag array access time (ns), ";
      file << "Refresh period (microsec), ";
      file << "DRAM array availability (%), ";
      file << "Dynamic read energy (nJ), ";
      file << "Dynamic write energy (nJ), ";
      file << "Dynamic read power (mW), ";
      file << "Standby leakage per bank(mW), ";
      file << "Leakage per bank with leak power management (mW), ";
      file << "Refresh power as percentage of standby leakage, ";
      file << "Area (mm2), ";
      file << "Ndwl, ";
      file << "Ndbl, ";
      file << "Nspd, ";
      file << "Ndcm, ";
      file << "Ndsam_level_1, ";
      file << "Ndsam_level_2, ";
      file << "Ntwl, ";
      file << "Ntbl, ";
      file << "Ntspd, ";
      file << "Ntcm, ";
      file << "Ntsam_level_1, ";
      file << "Ntsam_level_2, ";
      file << "Area efficiency, ";
      file << "Resistance per unit micron (ohm-micron), ";
      file << "Capacitance per unit micron (fF per micron), ";
      file << "Unit-length wire delay (ps), ";
      file << "FO4 delay (ps), ";
      file << "delay route to bank (including crossb delay) (ps), ";
      file << "Crossbar delay (ps), ";
      file << "Dyn read energy per access from closed page (nJ), ";
      file << "Dyn read energy per access from open page (nJ), ";
      file << "Leak power of an subbank with page closed (mW), ";
      file << "Leak power of a subbank with page  open (mW), ";
      file << "Leak power of request and reply networks (mW), ";
      file << "Number of subbanks, ";
      file << "Page size in bits, ";
      file << "Activate power, ";
      file << "Read power, ";
      file << "Write power, ";
      file << "Precharge power, ";
      file << "tRCD, ";
      file << "CAS latency, ";
      file << "Precharge delay, ";
      file << "Perc dyn energy bitlines, ";
      file << "perc dyn energy wordlines, ";
      file << "perc dyn energy outside mat, ";
      file << "Area opt (perc), ";
      file << "Delay opt (perc), ";
      file << "Repeater opt (perc), ";
      file << "Aspect ratio" << std::endl;
    }
    file << g_ip->F_sz_nm << ", ";
    file << g_ip->cache_sz << ", ";
    file << g_ip->nbanks << ", ";
    file << g_ip->tag_assoc << ", ";
    file << g_ip->out_w << ", ";
    file << fin_res.access_time*1e+9 << ", ";
    file << fin_res.cycle_time*1e+9 << ", ";
    file << fin_res.data_array.multisubbank_interleave_cycle_time*1e+9 << ", ";
    file << fin_res.data_array.delay_request_network*1e+9 << ", ";
    file << fin_res.data_array.delay_inside_mat*1e+9 <<  ", ";
    file << fin_res.data_array.delay_reply_network*1e+9 << ", ";
    file << fin_res.tag_array.access_time*1e+9 << ", ";
    file << fin_res.data_array.dram_refresh_period*1e+6 << ", ";
    file << fin_res.data_array.dram_array_availability <<  ", ";
    file << fin_res.power.readOp.dynamic*1e+9 << ", ";
    file << fin_res.power.writeOp.dynamic*1e+9 << ", ";
    file << fin_res.power.readOp.dynamic*1000/fin_res.cycle_time << ", ";
    file << fin_res.power.readOp.leakage*1000 << ", ";
    file << fin_res.leak_power_with_sleep_transistors_in_mats*1000 << ", ";
    file << fin_res.data_array.refresh_power / fin_res.data_array.total_power.readOp.leakage << ", ";
    file << fin_res.area << ", ";
    file << fin_res.data_array.Ndwl << ", ";
    file << fin_res.data_array.Ndbl << ", ";
    file << fin_res.data_array.Nspd << ", ";
    file << fin_res.data_array.deg_bl_muxing << ", ";
    file << fin_res.data_array.Ndsam_lev_1 << ", ";
    file << fin_res.data_array.Ndsam_lev_2 << ", ";
    file << fin_res.tag_array.Ndwl << ", ";
    file << fin_res.tag_array.Ndbl << ", ";
    file << fin_res.tag_array.Nspd << ", ";
    file << fin_res.tag_array.deg_bl_muxing << ", ";
    file << fin_res.tag_array.Ndsam_lev_1 << ", ";
    file << fin_res.tag_array.Ndsam_lev_2 << ", ";
    file << fin_res.area_efficiency << ", ";
    file << g_tp.wire_inside_mat.R_per_um << ", ";
    file << g_tp.wire_inside_mat.C_per_um / 1e-15 << ", ";
    file << g_tp.unit_len_wire_del / 1e-12 << ", ";
    file << g_tp.FO4 / 1e-12 << ", ";
    file << fin_res.data_array.delay_route_to_bank / 1e-9 << ", ";
    file << fin_res.data_array.delay_crossbar / 1e-9 << ", ";
    file << fin_res.data_array.dyn_read_energy_from_closed_page / 1e-9 << ", ";
    file << fin_res.data_array.dyn_read_energy_from_open_page / 1e-9 << ", ";
    file << fin_res.data_array.leak_power_subbank_closed_page / 1e-3 << ", ";
    file << fin_res.data_array.leak_power_subbank_open_page / 1e-3 << ", ";
    file << fin_res.data_array.leak_power_request_and_reply_networks / 1e-3 << ", ";
    file << fin_res.data_array.number_subbanks << ", " ;
    file << fin_res.data_array.page_size_in_bits << ", " ;
    file << fin_res.data_array.activate_energy * 1e9 << ", " ;
    file << fin_res.data_array.read_energy * 1e9 << ", " ;
    file << fin_res.data_array.write_energy * 1e9 << ", " ;
    file << fin_res.data_array.precharge_energy * 1e9 << ", " ;
    file << fin_res.data_array.trcd * 1e9 << ", " ;
    file << fin_res.data_array.cas_latency * 1e9 << ", " ;
    file << fin_res.data_array.precharge_delay * 1e9 << ", " ;
    file << fin_res.data_array.all_banks_height / fin_res.data_array.all_banks_width << std::endl;
  }
  file.close();
}



void output_UCA(uca_org_t *fr)
{
  //    if (NUCA) 
  if (0) {
    std::cout << "\n\n Detailed Bank Stats:\n";
    std::cout << "    Bank Size (bytes): %d\n" << 
                                     (int) (g_ip->cache_sz);
  }
  else {
    if (g_ip->data_arr_ram_cell_tech_type == 3) {
      std::cout << "\n---------- CACTI version 6.5, Uniform Cache Access " <<
        "Logic Process Based DRAM Model ----------\n"; 
    }
    else if (g_ip->data_arr_ram_cell_tech_type == 4) {
      std::cout << "\n---------- CACTI version 6.5, Uniform" <<
        "Cache Access Commodity DRAM Model ----------\n";
    }
    else {
      std::cout << "\n---------- CACTI version 6.5, Uniform Cache Access "
        "SRAM Model ----------\n";
    }
    std::cout << "\nCache Parameters:\n";
    std::cout << "    Total cache size (bytes): " << 
      (int) (g_ip->cache_sz) << std::endl;
  }

  std::cout << "    Number of banks: " << (int) g_ip->nbanks << std::endl;
  if (g_ip->fully_assoc)
    std::cout << "    Associativity: fully associative\n";
  else {
    if (g_ip->tag_assoc == 1)
      std::cout << "    Associativity: direct mapped\n";
    else
      std::cout << "    Associativity: " << 
        g_ip->tag_assoc << std::endl;
  }


  std::cout << "    Block size (bytes): " << g_ip->line_sz << std::endl;
  std::cout << "    Read/write Ports: " <<
    g_ip->num_rw_ports << std::endl;
  std::cout << "    Read ports: " <<
    g_ip->num_rd_ports << std::endl;
  std::cout << "    Write ports: " <<
    g_ip->num_wr_ports << std::endl;;
  std::cout << "    Technology size (nm): " <<  
    g_ip->F_sz_nm << std::endl << std::endl;

  std::cout << "    Access time (ns): " << fr->access_time*1e9 << std::endl;
  std::cout << "    Cycle time (ns):  " << fr->cycle_time*1e9 << std::endl;
  if (g_ip->data_arr_ram_cell_tech_type >= 4) {
    std::cout << "    Precharge Delay (ns): " << fr->data_array2->precharge_delay*1e9 << std::endl;
    std::cout << "    Activate Energy (nJ): " << fr->data_array2->activate_energy*1e9 << std::endl;
    std::cout << "    Read Energy (nJ): " << fr->data_array2->read_energy*1e9 << std::endl;
    std::cout << "    Write Energy (nJ): " << fr->data_array2->write_energy*1e9 << std::endl;
    std::cout << "    Precharge Energy (nJ): " << fr->data_array2->precharge_energy*1e9 << std::endl;
    std::cout << "    Leakage Power Closed Page (mW): " << fr->data_array2->leak_power_subbank_closed_page*1e3 << std::endl;
    std::cout << "    Leakage Power Open Page (mW): " << fr->data_array2->leak_power_subbank_open_page*1e3 << std::endl;
    std::cout << "    Leakage Power I/O (mW): " << fr->data_array2->leak_power_request_and_reply_networks*1e3 << std::endl;
    std::cout << "    Refresh power (mW): " << 
      fr->data_array2->refresh_power*1e3 << std::endl; 
  }
  else {
    std::cout << "    Total dynamic read energy per access (nJ): " <<
      fr->power.readOp.dynamic*1e9 << std::endl;
    std::cout << "    Total leakage power of a bank"
      " (mW): " << fr->power.readOp.leakage*1e3 << std::endl;
  }

  if (g_ip->data_arr_ram_cell_tech_type ==3 || g_ip->data_arr_ram_cell_tech_type ==4)
  {
  }
  std::cout <<  "    Cache height x width (mm): " <<
    fr->cache_ht*1e-3 << " x " << fr->cache_len*1e-3 << std::endl << std::endl;


  std::cout << "    Best Ndwl : " << fr->data_array2->Ndwl << std::endl;
  std::cout << "    Best Ndbl : " << fr->data_array2->Ndbl << std::endl;
  std::cout << "    Best Nspd : " << fr->data_array2->Nspd << std::endl;
  std::cout << "    Best Ndcm : " << fr->data_array2->deg_bl_muxing << std::endl;
  std::cout << "    Best Ndsam L1 : " << fr->data_array2->Ndsam_lev_1 << std::endl;
  std::cout << "    Best Ndsam L2 : " << fr->data_array2->Ndsam_lev_2 << std::endl << std::endl;

  if (g_ip->is_cache && !g_ip->is_main_mem)
  {
    std::cout << "    Best Ntwl : " << fr->tag_array2->Ndwl << std::endl;
    std::cout << "    Best Ntbl : " << fr->tag_array2->Ndbl << std::endl;
    std::cout << "    Best Ntspd : " << fr->tag_array2->Nspd << std::endl;
    std::cout << "    Best Ntcm : " << fr->tag_array2->deg_bl_muxing << std::endl;
    std::cout << "    Best Ntsam L1 : " << fr->tag_array2->Ndsam_lev_1 << std::endl;
    std::cout << "    Best Ntsam L2 : " << fr->tag_array2->Ndsam_lev_2 << std::endl;
  }

  switch (fr->data_array2->wt) {
    case (0):
      std::cout <<  "    Data array, H-tree wire type: Delay optimized global wires\n";
      break;
    case (1):
      std::cout <<  "    Data array, H-tree wire type: Global wires with 5\% delay penalty\n";
      break;
    case (2):
      std::cout <<  "    Data array, H-tree wire type: Global wires with 10\% delay penalty\n";
      break;
    case (3):
      std::cout <<  "    Data array, H-tree wire type: Global wires with 20\% delay penalty\n";
      break;
    case (4):
      std::cout <<  "    Data array, H-tree wire type: Global wires with 30\% delay penalty\n";
      break;
    case (5):
      std::cout <<  "    Data array, wire type: Low swing wires\n";
      break;
    default:
      std::cout << "ERROR - Unknown wire type " << (int) fr->data_array2->wt <<std::endl;
      exit(0);
  }

  if (g_ip->is_cache) {
    switch (fr->tag_array2->wt) {
      case (0):
        std::cout <<  "    Tag array, H-tree wire type: Delay optimized global wires\n";
        break;
      case (1):
        std::cout <<  "    Tag array, H-tree wire type: Global wires with 5\% delay penalty\n";
        break;
      case (2):
        std::cout <<  "    Tag array, H-tree wire type: Global wires with 10\% delay penalty\n";
        break;
      case (3):
        std::cout <<  "    Tag array, H-tree wire type: Global wires with 20\% delay penalty\n";
        break;
      case (4):
        std::cout <<  "    Tag array, H-tree wire type: Global wires with 30\% delay penalty\n";
        break;
      case (5):
        std::cout <<  "    Tag array, wire type: Low swing wires\n";
        break;
      default:
        std::cout << "ERROR - Unknown wire type " << (int) fr->tag_array2->wt <<std::endl;
        exit(-1);
    }
  }

  if (g_ip->print_detail)
  {
    if(g_ip->fully_assoc) return;

    /* Delay stats */
    /* data array stats */ 
    std::cout << std::endl << "Time Components:" << std::endl << std::endl;

    std::cout << "  Data side (with Output driver) (ns): " <<
      fr->data_array2->access_time/1e-9 << std::endl;

    std::cout <<  "\tH-tree input delay (ns): " << 
      fr->data_array2->delay_route_to_bank * 1e9 +
      fr->data_array2->delay_input_htree * 1e9 << std::endl;

    std::cout <<  "\tDecoder + wordline delay (ns): " <<
      fr->data_array2->delay_row_predecode_driver_and_block * 1e9 +
      fr->data_array2->delay_row_decoder * 1e9 << std::endl;

    std::cout <<  "\tBitline delay (ns): " <<
      fr->data_array2->delay_bitlines/1e-9 << std::endl;

    std::cout <<  "\tSense Amplifier delay (ns): " <<
      fr->data_array2->delay_sense_amp * 1e9 << std::endl;


    std::cout <<  "\tH-tree output delay (ns): " <<
      fr->data_array2->delay_subarray_output_driver * 1e9 +
      fr->data_array2->delay_dout_htree * 1e9 << std::endl;

    if (g_ip->is_cache && !g_ip->is_main_mem)
    {
      /* tag array stats */
      std::cout << std::endl << "  Tag side (with Output driver) (ns): " <<
        fr->tag_array2->access_time/1e-9 << std::endl;

      std::cout <<  "\tH-tree input delay (ns): " << 
        fr->tag_array2->delay_route_to_bank * 1e9 +
        fr->tag_array2->delay_input_htree * 1e9 << std::endl;

      std::cout <<  "\tDecoder + wordline delay (ns): " <<
        fr->tag_array2->delay_row_predecode_driver_and_block * 1e9 +
        fr->tag_array2->delay_row_decoder * 1e9 << std::endl;

      std::cout <<  "\tBitline delay (ns): " <<
        fr->tag_array2->delay_bitlines/1e-9 << std::endl;

      std::cout <<  "\tSense Amplifier delay (ns): " <<
        fr->tag_array2->delay_sense_amp * 1e9 << std::endl;

      std::cout <<  "\tComparator delay (ns): " <<
        fr->tag_array2->delay_comparator * 1e9 << std::endl;

      std::cout <<  "\tH-tree output delay (ns): " << 
        fr->tag_array2->delay_subarray_output_driver * 1e9 +
        fr->tag_array2->delay_dout_htree * 1e9 << std::endl;
    }

    /* Energy/Power stats */
    std::cout << std::endl << std::endl << "Power Components:" << std::endl << std::endl;
    std::cout << "  Data array: Total dynamic read energy/access  (nJ): " <<
      fr->data_array2->power.readOp.dynamic * 1e9 << std::endl;
    std::cout << "\tTotal leakage read/write power of a bank (mW): " <<
        fr->data_array2->power.readOp.leakage * 1e3 << std::endl;
    std::cout << "\tTotal energy in H-tree (that includes both "
      "address and data transfer) (nJ): " << 
        (fr->data_array2->power_addr_input_htree.readOp.dynamic +
         fr->data_array2->power_data_output_htree.readOp.dynamic +
         fr->data_array2->power_routing_to_bank.readOp.dynamic) * 1e9 << std::endl;

    std::cout << "\tOutput Htree Energy (nJ): " <<
      fr->data_array2->power_data_output_htree.readOp.dynamic * 1e9 << std::endl;
    std::cout <<  "\tDecoder (nJ): " <<
      fr->data_array2->power_row_predecoder_drivers.readOp.dynamic * 1e9 +
      fr->data_array2->power_row_predecoder_blocks.readOp.dynamic * 1e9 << std::endl;
    std::cout <<  "\tWordline (nJ): " <<
      fr->data_array2->power_row_decoders.readOp.dynamic * 1e9 << std::endl;
    std::cout <<  "\tBitline mux & associated drivers (nJ): " <<
      fr->data_array2->power_bit_mux_predecoder_drivers.readOp.dynamic * 1e9 +
      fr->data_array2->power_bit_mux_predecoder_blocks.readOp.dynamic * 1e9 +
      fr->data_array2->power_bit_mux_decoders.readOp.dynamic * 1e9 << std::endl;
    std::cout <<  "\tSense amp mux & associated drivers (nJ): " <<
      fr->data_array2->power_senseamp_mux_lev_1_predecoder_drivers.readOp.dynamic * 1e9 +
      fr->data_array2->power_senseamp_mux_lev_1_predecoder_blocks.readOp.dynamic * 1e9 +
      fr->data_array2->power_senseamp_mux_lev_1_decoders.readOp.dynamic * 1e9  +
      fr->data_array2->power_senseamp_mux_lev_2_predecoder_drivers.readOp.dynamic * 1e9 +
      fr->data_array2->power_senseamp_mux_lev_2_predecoder_blocks.readOp.dynamic * 1e9 +
      fr->data_array2->power_senseamp_mux_lev_2_decoders.readOp.dynamic * 1e9 << std::endl;
    std::cout <<  "\tBitlines (nJ): " <<
      fr->data_array2->power_bitlines.readOp.dynamic * 1e9 << std::endl;
    std::cout <<  "\tSense amplifier energy (nJ): " <<
      fr->data_array2->power_sense_amps.readOp.dynamic * 1e9 << std::endl;
    std::cout <<  "\tSub-array output driver (nJ): " <<
      fr->data_array2->power_output_drivers_at_subarray.readOp.dynamic * 1e9 << std::endl;

    if (g_ip->is_cache && !g_ip->is_main_mem)
    {
      std::cout << std::endl << "  Tag array:  Total dynamic read energy/access (nJ): " <<
        fr->tag_array2->power.readOp.dynamic * 1e9 << std::endl;
      std::cout << "\tTotal leakage read/write power of a bank (mW): " <<
          fr->tag_array2->power.readOp.leakage * 1e3 << std::endl;
      std::cout << "\tTotal energy in H-tree (that includes both "
        "address and data transfer) (nJ): " << 
          (fr->tag_array2->power_addr_input_htree.readOp.dynamic +
           fr->tag_array2->power_data_output_htree.readOp.dynamic +
           fr->tag_array2->power_routing_to_bank.readOp.dynamic) * 1e9 << std::endl;

      std::cout << "\tOutput Htree Energy (nJ): " <<
        fr->tag_array2->power_data_output_htree.readOp.dynamic * 1e9 << std::endl;
      std::cout <<  "\tDecoder (nJ): " <<
        fr->tag_array2->power_row_predecoder_drivers.readOp.dynamic * 1e9 +
        fr->tag_array2->power_row_predecoder_blocks.readOp.dynamic * 1e9 << std::endl;
      std::cout <<  "\tWordline (nJ): " <<
        fr->tag_array2->power_row_decoders.readOp.dynamic * 1e9 << std::endl;
      std::cout <<  "\tBitline mux & associated drivers (nJ): " <<
        fr->tag_array2->power_bit_mux_predecoder_drivers.readOp.dynamic * 1e9 +
        fr->tag_array2->power_bit_mux_predecoder_blocks.readOp.dynamic * 1e9 +
        fr->tag_array2->power_bit_mux_decoders.readOp.dynamic * 1e9 << std::endl;
      std::cout <<  "\tSense amp mux & associated drivers (nJ): " <<
        fr->tag_array2->power_senseamp_mux_lev_1_predecoder_drivers.readOp.dynamic * 1e9 +
        fr->tag_array2->power_senseamp_mux_lev_1_predecoder_blocks.readOp.dynamic * 1e9 +
        fr->tag_array2->power_senseamp_mux_lev_1_decoders.readOp.dynamic * 1e9  +
        fr->tag_array2->power_senseamp_mux_lev_2_predecoder_drivers.readOp.dynamic * 1e9 +
        fr->tag_array2->power_senseamp_mux_lev_2_predecoder_blocks.readOp.dynamic * 1e9 +
        fr->tag_array2->power_senseamp_mux_lev_2_decoders.readOp.dynamic * 1e9 << std::endl;
      std::cout <<  "\tBitlines (nJ): " <<
        fr->tag_array2->power_bitlines.readOp.dynamic * 1e9 << std::endl;
      std::cout <<  "\tSense amplifier energy (nJ): " <<
        fr->tag_array2->power_sense_amps.readOp.dynamic * 1e9 << std::endl;
      std::cout <<  "\tSub-array output driver (nJ): " <<
        fr->tag_array2->power_output_drivers_at_subarray.readOp.dynamic * 1e9 << std::endl;
    }

    std::cout << std::endl << std::endl <<  "Area Components:" << std::endl << std::endl;
    /* Data array area stats */
    std::cout <<  "  Data array: Area (mm2): " << fr->data_array2->area * 1e-6 << std::endl;
    std::cout <<  "\tHeight (mm): " <<
      fr->data_array2->all_banks_height*1e-3 << std::endl;
    std::cout <<  "\tWidth (mm): " <<
      fr->data_array2->all_banks_width*1e-3 << std::endl;
    if (g_ip->print_detail) {
      std::cout <<  "\tArea efficiency (Memory cell area/Total area) - " <<
        fr->data_array2->area_efficiency << " %" << std::endl;
      std::cout << "\t\tMAT Height (mm): " <<
        fr->data_array2->mat_height*1e-3 << std::endl;
      std::cout << "\t\tMAT Length (mm): " <<
        fr->data_array2->mat_length*1e-3 << std::endl;
      std::cout << "\t\tSubarray Height (mm): " <<
        fr->data_array2->subarray_height*1e-3 << std::endl;
      std::cout << "\t\tSubarray Length (mm): " <<
        fr->data_array2->subarray_length*1e-3 << std::endl;
    }

    /* Tag array area stats */
    if (g_ip->is_cache && !g_ip->is_main_mem)
    {
      std::cout << std::endl << "  Tag array: Area (mm2): " << fr->tag_array2->area * 1e-6 << std::endl;
      std::cout <<  "\tHeight (mm): " <<
        fr->tag_array2->all_banks_height*1e-3 << std::endl;
      std::cout <<  "\tWidth (mm): " <<
        fr->tag_array2->all_banks_width*1e-3 << std::endl;
      if (g_ip->print_detail)
      {
        std::cout <<  "\tArea efficiency (Memory cell area/Total area) - " <<
          fr->tag_array2->area_efficiency << " %" << std::endl;
        std::cout << "\t\tMAT Height (mm): " <<
          fr->tag_array2->mat_height*1e-3 << std::endl;
        std::cout << "\t\tMAT Length (mm): " <<
          fr->tag_array2->mat_length*1e-3 << std::endl;
        std::cout << "\t\tSubarray Height (mm): " <<
          fr->tag_array2->subarray_height*1e-3 << std::endl;
        std::cout << "\t\tSubarray Length (mm): " <<
          fr->tag_array2->subarray_length*1e-3 << std::endl;
      }
    }


    Wire wpr;
    wpr.print_wire();

    //std::cout << "FO4 = " << g_tp.FO4 << std::endl;
  }
}
