Search.setIndex({envversion:47,filenames:["apidoc/lumos","apidoc/lumos.analysis","apidoc/lumos.model","apidoc/lumos.model.core","apidoc/lumos.model.system","apidoc/lumos.model.tech","apidoc/lumos.model.tech.cmos","apidoc/lumos.model.tech.cmos.hp","apidoc/lumos.model.tech.cmos.lp","apidoc/lumos.model.tech.tfet","apidoc/lumos.model.tech.tfet.homoTFET30nm","apidoc/lumos.model.tech.tfet.homoTFET60nm","apidoc/lumos.unittests","index"],objects:{"":{lumos:[0,7,0,"-"]},"lumos.analysis":{LumosAnalysisError:[1,13,1,""],argparser:[1,7,0,"-"]},"lumos.analysis.argparser":{LumosArgumentParser:[1,9,1,""],LumosNumlist:[1,10,1,""]},"lumos.analysis.argparser.LumosArgumentParser":{add_argument:[1,8,1,""],epilog:[1,11,1,""],parse_args:[1,8,1,""]},"lumos.model":{Budget:[2,9,1,""],Sys_L:[2,12,1,""],Sys_M:[2,12,1,""],Sys_S:[2,12,1,""],application:[2,7,0,"-"],asacc:[2,7,0,"-"],core:[3,7,0,"-"],kernel:[2,7,0,"-"],misc:[2,7,0,"-"],plot:[2,7,0,"-"],system:[4,7,0,"-"],tech:[5,7,0,"-"],ucore:[2,7,0,"-"],workload:[2,7,0,"-"]},"lumos.model.Budget":{area:[2,11,1,""],bw:[2,11,1,""],power:[2,11,1,""]},"lumos.model.application":{AppDAG:[2,9,1,""],Application:[2,9,1,""],ApplicationError:[2,13,1,""],random_kernel_cov:[2,10,1,""],random_uc_cov:[2,10,1,""]},"lumos.model.application.AppDAG":{add_dependence:[2,8,1,""],add_kernel:[2,8,1,""],get_kernel:[2,8,1,""]},"lumos.model.application.Application":{add_kernel:[2,8,1,""],get_all_kernels:[2,8,1,""],get_cov:[2,8,1,""],get_kernel:[2,8,1,""],set_cov:[2,8,1,""],tag_update:[2,8,1,""]},"lumos.model.asacc":{ASAcc:[2,9,1,""],ASAccError:[2,13,1,""]},"lumos.model.asacc.ASAcc":{area:[2,11,1,""],bandwidth:[2,8,1,""],dp:[2,11,1,""],kid:[2,11,1,""],perf:[2,8,1,""],power:[2,11,1,""],sp:[2,11,1,""],tech:[2,11,1,""],tech_model:[2,11,1,""],vdd:[2,11,1,""]},"lumos.model.core":{BaseCore:[3,9,1,""],BaseCoreError:[3,13,1,""],io_cmos:[3,7,0,"-"],io_tfet:[3,7,0,"-"],o3_cmos:[3,7,0,"-"],o3_tfet:[3,7,0,"-"]},"lumos.model.core.BaseCore":{area:[3,11,1,""],ctype:[3,11,1,""],dp:[3,11,1,""],freq:[3,11,1,""],init:[3,8,1,""],perf:[3,11,1,""],power:[3,11,1,""],sp:[3,11,1,""],tech:[3,11,1,""],vdd:[3,11,1,""],vmax:[3,11,1,""],vmin:[3,11,1,""],vnom:[3,11,1,""]},"lumos.model.core.io_cmos":{IOCore:[3,9,1,""]},"lumos.model.core.io_cmos.IOCore":{init:[3,8,1,""]},"lumos.model.core.io_tfet":{IOCore:[3,9,1,""]},"lumos.model.core.io_tfet.IOCore":{init:[3,8,1,""]},"lumos.model.core.o3_cmos":{O3Core:[3,9,1,""]},"lumos.model.core.o3_cmos.O3Core":{init:[3,8,1,""]},"lumos.model.core.o3_tfet":{O3Core:[3,9,1,""]},"lumos.model.core.o3_tfet.O3Core":{init:[3,8,1,""]},"lumos.model.kernel":{Kernel:[2,9,1,""],KernelError:[2,13,1,""],KernelParam:[2,9,1,""],create_fixednorm:[2,10,1,""],create_fixednorm_xml:[2,10,1,""],create_randnorm:[2,10,1,""],create_randnorm_xml:[2,10,1,""],do_generate:[2,10,1,""],do_test:[2,10,1,""],gen_kernel_gauss:[2,10,1,""],load:[2,10,1,""],load_from_xml:[2,10,1,""],load_kernels:[2,10,1,""],load_xml:[2,10,1,""],reg_kernels:[2,10,1,""]},"lumos.model.kernel.Kernel":{add_kernel_param:[2,8,1,""],del_kernel_param:[2,8,1,""],get_all_accs:[2,8,1,""],get_kernel_param:[2,8,1,""],kid:[2,11,1,""]},"lumos.model.kernel.KernelParam":{PARAMS:[2,11,1,""],bw:[2,11,1,""],perf:[2,11,1,""],power:[2,11,1,""]},"lumos.model.misc":{make_ws_dirs:[2,10,1,""],mk_dir:[2,10,1,""],parse_bw:[2,10,1,""],try_update:[2,10,1,""]},"lumos.model.plot":{line_plot:[2,10,1,""],plot_data:[2,10,1,""],plot_data_nomarker:[2,10,1,""],plot_errbar:[2,10,1,""],plot_series2:[2,10,1,""],plot_series:[2,10,1,""],plot_twinx:[2,10,1,""]},"lumos.model.system":{het:[4,7,0,"-"],hetero:[4,7,0,"-"],hom:[4,7,0,"-"],homo:[4,7,0,"-"],mpsoc:[4,7,0,"-"]},"lumos.model.system.het":{HetSys:[4,9,1,""]},"lumos.model.system.het.HetSys":{del_all_asics:[4,8,1,""],del_asic:[4,8,1,""],del_target_asics:[4,8,1,""],get_all_asics:[4,8,1,""],get_perf:[4,8,1,""],get_supported_kernels:[4,8,1,""],get_target_asics:[4,8,1,""],realloc_gpacc:[4,8,1,""],set_asic:[4,8,1,""],set_tech:[4,8,1,""]},"lumos.model.system.hetero":{HeterogSys:[4,9,1,""]},"lumos.model.system.hetero.HeterogSys":{del_asic:[4,8,1,""],del_asics:[4,8,1,""],get_perf:[4,8,1,""],realloc_gpacc:[4,8,1,""],set_asic:[4,8,1,""],set_tech:[4,8,1,""]},"lumos.model.system.hom":{HomSys:[4,9,1,""]},"lumos.model.system.hom.HomSys":{get_core_num:[4,8,1,""],opt_core_num:[4,8,1,""],perf_by_cnum:[4,8,1,""],perf_by_dark:[4,8,1,""],perf_by_vdd:[4,8,1,""],set_core_prop:[4,8,1,""],set_sys_prop:[4,8,1,""],speedup_by_vfslist:[4,8,1,""],speedup_by_vlist:[4,8,1,""]},"lumos.model.system.homo":{HomogSys:[4,9,1,""]},"lumos.model.system.homo.HomogSys":{get_core_num:[4,8,1,""],opt_core_num:[4,8,1,""],perf_by_cnum:[4,8,1,""],perf_by_dark:[4,8,1,""],perf_by_vdd:[4,8,1,""],set_core_prop:[4,8,1,""],set_sys_prop:[4,8,1,""],speedup_by_vfslist:[4,8,1,""],speedup_by_vlist:[4,8,1,""]},"lumos.model.system.mpsoc":{MPSoC:[4,9,1,""],MPSoCError:[4,13,1,""]},"lumos.model.system.mpsoc.MPSoC":{change_asic_vdd:[4,8,1,""],change_serial_core_vdd:[4,8,1,""],change_tput_core_vdd:[4,8,1,""],del_all_asics:[4,8,1,""],del_asic:[4,8,1,""],del_target_asics:[4,8,1,""],get_all_asics:[4,8,1,""],get_perf:[4,8,1,""],get_perf_appdag:[4,8,1,""],get_supported_kernels:[4,8,1,""],get_target_asics:[4,8,1,""],realloc_gpacc:[4,8,1,""],set_asic:[4,8,1,""],set_tech:[4,8,1,""]},"lumos.model.tech":{BaseTechModel:[5,9,1,""],TechModelError:[5,13,1,""],cmos:[6,7,0,"-"],tfet:[9,7,0,"-"]},"lumos.model.tech.BaseTechModel":{name:[5,11,1,""]},"lumos.model.tech.cmos":{CMOSTechModel:[6,9,1,""],hp:[7,7,0,"-"],lp:[8,7,0,"-"]},"lumos.model.tech.cmos.CMOSTechModel":{dynamic_power:[6,8,1,""],freq:[6,8,1,""],power:[6,8,1,""],static_power:[6,8,1,""],vmax:[6,8,1,""],vmin:[6,8,1,""],vnom:[6,8,1,""]},"lumos.model.tech.tfet":{TFETTechModel:[9,9,1,""],homoTFET30nm:[10,7,0,"-"],homoTFET60nm:[11,7,0,"-"],tfet_interp:[9,7,0,"-"]},"lumos.model.tech.tfet.TFETTechModel":{dynamic_power:[9,8,1,""],freq:[9,8,1,""],power:[9,8,1,""],static_power:[9,8,1,""],vmax:[9,8,1,""],vmin:[9,8,1,""],vnom:[9,8,1,""]},"lumos.model.ucore":{AppAccelerator:[2,9,1,""],GPAccelerator:[2,9,1,""],UCore:[2,9,1,""],UCoreError:[2,13,1,""]},"lumos.model.ucore.AppAccelerator":{kid:[2,11,1,""],perf:[2,8,1,""]},"lumos.model.ucore.UCore":{area:[2,11,1,""],bandwidth:[2,8,1,""],config:[2,8,1,""],ctype:[2,11,1,""],perf:[2,8,1,""],power:[2,8,1,""],tech:[2,11,1,""]},"lumos.model.workload":{add_fixedcov:[2,10,1,""],build:[2,10,1,""],build_fixedcov:[2,10,1,""],build_with_single_kernel:[2,10,1,""],dump_xml:[2,10,1,""],load_from_xml:[2,10,1,""],load_workload:[2,10,1,""]},"lumos.unittests":{test_acc:[12,7,0,"-"],test_homogsys:[12,7,0,"-"],test_mpsoc:[12,7,0,"-"],test_ptmnew_app:[12,7,0,"-"]},"lumos.unittests.test_acc":{TestAccelerator:[12,9,1,""]},"lumos.unittests.test_acc.TestAccelerator":{setUp:[12,8,1,""],test_acc_vdd_scale:[12,8,1,""]},"lumos.unittests.test_homogsys":{TestHomogSys:[12,9,1,""]},"lumos.unittests.test_homogsys.TestHomogSys":{setUp:[12,8,1,""],test_perf_by_cnum:[12,8,1,""]},"lumos.unittests.test_mpsoc":{TestMPSoC:[12,9,1,""],load_kernel:[12,10,1,""],load_workload:[12,10,1,""]},"lumos.unittests.test_mpsoc.TestMPSoC":{setUp:[12,8,1,""],test_acc:[12,8,1,""]},"lumos.unittests.test_ptmnew_app":{TestApp:[12,9,1,""]},"lumos.unittests.test_ptmnew_app.TestApp":{setUp:[12,8,1,""],test_tag:[12,8,1,""]},lumos:{analysis:[1,7,0,"-"],model:[2,7,0,"-"],settings:[0,7,0,"-"],unittests:[12,7,0,"-"]}},objnames:{"0":["py","module","Python module"],"1":["py","method","Python method"],"10":["np","function","Python function"],"11":["np","attribute","Python attribute"],"12":["np","data","Python data"],"13":["np","exception","Python exception"],"2":["py","class","Python class"],"3":["py","function","Python function"],"4":["py","attribute","Python attribute"],"5":["py","data","Python data"],"6":["py","exception","Python exception"],"7":["np","module","Python module"],"8":["np","method","Python method"],"9":["np","class","Python class"]},objtypes:{"0":"py:module","1":"py:method","10":"np:function","11":"np:attribute","12":"np:data","13":"np:exception","2":"py:class","3":"py:function","4":"py:attribute","5":"py:data","6":"py:exception","7":"np:module","8":"np:method","9":"np:class"},terms:{"1rc":13,"45nm":13,"_gen_fixednorm_004":13,"_gen_fixednorm_005":13,"_gen_fixednorm_006":13,"abstract":3,"case":[12,13],"class":[1,2,3,4,5,6,9,12],"default":[2,4,13],"export":13,"final":13,"float":[2,4],"function":13,"int":[2,4],"new":[2,4],"public":13,"return":[2,4,12,13],"switch":13,"true":[2,13],"try":[4,13],"while":1,abov:[1,13],abstractcor:3,acc_id:[2,4],acceleartor:4,acceler:[2,4,13],achiev:[4,13],acknowledg:13,activ:[4,13],actual:[2,4],acycl:2,add:2,add_argu:1,add_depend:2,add_fixedcov:2,add_kernel:2,add_kernel_param:2,addit:13,adjust:4,advantag:13,advertis:13,advis:13,after:4,aid:4,all:[2,4,13],alloc:[2,4,13],alreadi:2,also:[2,4,13],altern:[2,13],although:13,alwai:13,amount:13,analysi:[],analyt:13,analyz:13,ani:[4,13],anl_nam:2,app0:13,app:[2,4,13],app_num:2,appacceler:2,appdag:[2,4],appli:13,applic:[],applicationerror:2,architectur:13,area:[2,3,4,13],area_ratio:4,arg:[1,2,4,12],argpars:[],argument:[1,4],aris:13,arrai:13,asacc:[],asaccerror:2,asic:[2,4,13],asic_dict:4,assist:13,associ:2,assum:13,attribut:4,author:13,avail:[2,4],bandwidth:[2,4],bandwith:2,base:[1,2,3,4,5,6,9,12],basecor:[3,4],basecoreerror:3,baselin:13,basetechmodel:[5,6,9],becom:13,been:[2,12,13],befor:13,best:[4,13],binari:13,bool:4,boundari:4,broad:13,budget:[2,4,13],build:[2,13],build_fixedcov:[2,13],build_with_single_kernel:2,built:2,busi:13,bw_cfg:2,calcul:2,call:4,can:[4,13],caus:13,cb_func:2,cdf:2,certain:[2,13],cfg:[2,13],change_asic_vdd:4,change_serial_core_vdd:4,change_tput_core_vdd:4,characterist:2,check:13,chip:[2,4],choos:2,chung:2,cite:13,cmo:[],cmostechmodel:[2,6],cnum:4,code:13,coerag:2,collect:13,command:[1,13],compar:13,compil:13,compon:4,compos:[2,4,13],comput:[2,4,13],condit:13,config:2,config_dir:1,configur:[1,2,4,13],configuraiton:4,consequenti:13,consid:13,consider:13,constraint:[2,4,13],consum:2,consumpt:13,contain:[2,12],contract:13,contributor:13,convent:[3,13],copyright:13,core2:2,core:[],core_typ:3,correspond:4,could:[2,4],coupl:13,cov:[2,13],cov_dist:2,cov_param1:2,cov_param2:2,cov_param:2,coverag:[2,13],cpu:13,creat:2,create_fixednorm:2,create_fixednorm_xml:[2,13],create_randnorm:2,create_randnorm_xml:[2,13],ctech:13,ctype:[2,3],current:[2,4],custom:[2,13],dag:2,damag:13,dark:[4,13],darkdim:2,data:[2,13],ddir:2,dedic:[4,13],del_all_as:4,del_as:4,del_kernel_param:2,del_target_as:4,delet:4,demonstr:13,densiti:13,depart:13,depend:2,deriv:[3,13],desc:1,descript:[2,13],design:[2,13],detail:13,develop:13,deviat:2,dict:[2,4,12],differ:2,dim:13,diminish:13,direct:[2,13],directori:[2,13],diretori:2,disclaim:13,displai:13,dist:2,dist_param:2,distribut:[2,13],divid:13,dname:2,do_gener:2,do_test:2,docstr:2,document:13,doe:[2,13],done:13,down:4,download:13,drawn:2,due:[2,13],dump_xml:2,dynamic_pow:[6,9],each:[2,4,13],effici:13,either:4,emploi:13,enabl:13,end:13,endors:13,entri:4,enumer:[1,13],environ:13,epilog:1,eric:2,err_list:2,etc:2,even:13,event:13,exampl:[],except:[1,2,3,4,5],execut:[2,4,13],exemplari:13,exhaust:13,exist:[2,13],expect:[2,13],expens:13,explicit:13,explor:13,express:13,extend:13,extern:13,extra:13,extract:2,f_parallel:13,fals:2,fast:13,fdir:2,featur:13,fedcor:[4,13],feder:13,figdir:2,figsiz:2,figur:[2,13],file:[1,2,12,13],filepath:2,find:4,fit:13,fix:2,fixedcov:2,fixednorm:2,flexibl:13,fname:[2,12],follow:[1,2,13],form:[2,13],format:[2,13],found:13,four:13,fpga:[2,4,13],free:4,freed:4,freq:[3,4,6,9],frequenc:[4,13],from:[2,3,4,12,13],from_:2,full:[2,13],futur:[2,13],gbyte:2,gen_kernel_gauss:2,gener:[2,4,13],get:[],get_all_acc:2,get_all_as:4,get_all_kernel:2,get_core_num:4,get_cov:2,get_kernel:2,get_kernel_param:2,get_perf:[4,13],get_perf_appdag:4,get_supported_kernel:4,get_target_as:4,github:13,given:[2,4,13],global:[0,2],good:13,gpacceler:2,gpgpu:[2,4],gpu:[2,4],graph:2,grow:13,hardwar:[2,13],have:[2,12,13],helper:13,here:13,het:[],hetero:[],heterogen:[4,13],heterogener:2,heterogsi:[4,13],heterosys_exampl:13,hetsi:4,high:13,highest:13,hkmg:13,hom:[],homo:[],homogen:[4,13],homogsi:[4,13],homosys_exampl:13,homotfet30nm:[],homotfet60nm:[],homsi:4,howev:13,identifi:2,immedi:13,impli:13,incident:13,includ:[2,13],increas:13,index:[2,4,12,13],indic:[],indirect:13,induc:13,init:3,initi:2,input:13,instal:13,interpret:13,interrupt:13,involv:13,io_cmo:[],io_tfet:[],iocor:[3,4,13],just:[4,13],keep:1,kei:4,ker005:13,ker_obj:[2,4],kernel:[],kernel_asic_t:4,kernel_config:13,kernel_nam:2,kernel_object:2,kernel_param:2,kernel_pool:2,kernelerror:2,kernelparam:2,kernels_asicfpgaratio10x:13,kerobj:2,kevin:13,kfirst:13,kid:[2,4],kid_prefix:2,kind:13,kwarg:[1,2,4,6,9],larg:[2,13],larger:[2,4],latenc:4,later:13,latest:13,layout:2,legend:2,legend_label:2,legend_loc:2,legend_prop:2,legend_titl:2,legitim:1,less:[4,13],liabil:13,liabl:13,liang:13,like:[2,13],limit:13,line:[1,2,13],line_plot:2,linux:13,list:[1,2,4,12,13],llabel:2,lloc:2,lncol:2,load:[2,12,13],load_from_xml:2,load_kernel:[2,12],load_workload:[2,12],load_xml:[2,13],logic:[2,4,13],lognorm:2,look:2,loss:13,lot:13,low:13,lower:13,lowest:4,lumos_hom:13,lumosanalysiserror:1,lumosargumentpars:1,lumosnumlist:1,lxml:13,machin:13,mai:13,make:13,make_ws_dir:2,mani:[4,13],marker_list:2,materi:13,matplotlib:13,max:2,maximum:[2,13],mean:2,mech:13,medium:2,meet:13,memori:[2,4],mention:13,merchant:13,met:[4,13],meter:2,method:[4,13],methodnam:12,metric:2,micro:2,mili:2,min:2,minimum:2,misc:[],miu:13,mix:1,mk_dir:2,model:[],model_nam:[2,3,5,6,9],modern:13,modif:13,moment:13,more:[2,13],moreov:13,mpltool:13,mpsoc:[],mpsocerror:4,ms_list:2,much:13,multi:[4,13],multicor:13,must:13,name:[2,4,5,12,13],necessarili:13,need:13,neglig:13,neither:13,newli:2,niagara2:13,node:[2,4,13],nomin:[2,13],none:[1,2,4],nor:13,norm:[2,12],normal:2,notic:13,now:13,num:[2,4],number:[1,2,4,13],numpi:13,o3_cmo:[],o3_tfet:[],o3cor:[3,4,13],object:[1,2,3,4,5],obsolet:2,obtain:13,occur:[2,13],ofn:2,old:2,onc:2,onli:[2,4,13],oper:13,opt_core_num:[4,13],optim:[4,13],option:[1,2,4,13],order:[1,3,4,13],other:[4,13],otherwis:[4,13],out:[3,4,13],overal:[2,4,13],overid:2,overrid:1,page:13,pair:2,paper:2,parallel:[2,4,13],parallel_factor:2,param1:2,param2:2,param:2,paramet:[2,4,13],parent:2,pars:[1,13],parse_arg:1,parse_bw:2,part:[4,13],particular:13,partit:13,path:[2,13],penalti:13,percentag:13,perf:[2,3,4,13],perf_by_cnum:[4,13],perf_by_dark:4,perf_by_vdd:[4,13],perf_by_vf:13,perf_rang:2,perform:[2,4,13],permiss:13,permit:13,physic:2,place:13,plot:[],plot_data:2,plot_data_nomark:2,plot_errbar:2,plot_seri:[2,13],plot_series2:2,plot_twinx:2,point:[2,13],pool:[2,13],popular:13,possibl:[4,13],potenti:13,power:[2,3,4,6,9,13],pre:13,predefin:2,prefix:2,presenc:2,present:[2,13],previou:2,prior:13,probabl:[2,13],probe:13,processor:2,procur:13,product:13,profit:13,program:[2,4],promis:13,promot:13,properti:[2,4],provid:13,pure:13,purpos:[4,13],python:[2,4,13],quantifi:13,rais:[2,4],rand_uc_cov:2,randnorm:2,random_kernel_cov:2,random_uc_cov:2,randomli:2,rang:[1,2],ratio:[2,4,13],read:2,readi:13,real:2,realloc_gpacc:[4,13],reconfigur:[4,13],redistribut:13,reduc:13,reg_kernel:2,regist:[2,4],regular:4,rel:[2,4,13],relat:13,relatvi:4,remov:4,report:13,repositori:13,reproduc:13,requir:[4,13],requri:4,reserv:13,resourc:2,respect:[2,3,13],rest:13,result:[4,13],ret:13,retain:13,retriev:13,right:13,root:13,run:[2,13],runtest:12,same:2,sampl:[2,13],save:2,scale:[4,13],scenario:13,scienc:13,scipi:13,script:13,search:13,second:13,section:[2,13],see:13,select:2,self:13,serial:[2,4,13],serial_cor:4,series_col:2,servic:13,set_as:[4,13],set_core_prop:[4,13],set_cov:2,set_grid:2,set_mech:13,set_sys_prop:[4,13],set_tech:[4,13],setup:12,sever:13,shall:13,should:[1,2,4,13],silicon:[4,13],similar:[2,4],simultan:13,sinc:13,sing:2,singl:13,size:2,skadron:13,small:2,softwar:13,some:13,sort:[2,12],sourc:[1,2,3,4,5,6,9,12,13],space:13,sparc:2,speak:13,special:[2,13],specif:[2,13],specifi:[1,2,4,13],speed:13,speedup:13,speedup_by_vfslist:4,speedup_by_vlist:4,standard:2,static_pow:[6,9],statist:[2,13],std:2,step:[1,13],store:[2,4,13],str:[2,4,12],strict:13,string:[1,2],substitut:13,success:4,successfulli:[2,4],suffer:13,sum:13,suppli:[2,4,13],support:[2,4,13],sure:13,synthet:13,sys_:[2,4],sys_area:[4,13],sys_bandwidth:4,sys_l:[2,4],sys_m:[2,4],sys_pow:13,sys_pwoer:4,syslarg:4,sysmedium:4,syssmal:4,system:[],tabl:[],tag_upd:2,take:13,tar:13,tarbal:13,target:[2,4],task:2,tdp:2,tech:[],tech_model:[2,3,4],techmodelerror:5,technic:13,technolog:[2,4,13],term:[4,13],test:13,test_acc:[],test_acc_vdd_scal:12,test_homogsi:[],test_mpsoc:[],test_perf_by_cnum:12,test_ptmnew_app:[],test_tag:12,testacceler:12,testapp:12,testcas:12,testhomogsi:12,testmpsoc:12,tfet:[],tfet_interp:[],tfettechmodel:[2,9],than:[2,4],thei:13,theori:13,thi:[2,3,4,12,13],three:[1,4,13],threshold:13,throughput:[4,13],time:13,titl:2,to_:2,todo:2,top:13,tort:13,total:2,tput_cor:4,transistor:13,transpar:13,try_upd:2,turn:4,tweak:13,two:[3,13],type:2,typic:13,ubuntu:13,ucor:[],ucoreerror:2,uid:2,unconvent:2,under:4,unfortun:13,uniform:2,uniformli:2,unit:13,unittest:[],univers:13,unpack:13,updat:[2,4],usag:13,use_gpacc:13,user:13,usual:13,util:4,v_list:4,valu:4,variabl:13,variant:3,variat:13,variou:13,vdd:[2,3,4],vdd_mv:[4,6,9],vfs_list:4,virginia:13,vmax:[3,6,9],vmin:[3,4,6,9],vnom:[3,6,9],voltag:[2,4,13],wai:[1,13],wang:13,warranti:13,watt:[2,4],well:13,when:4,where:13,whether:[4,13],which:[2,4,13],within:[2,13],without:13,work:2,workload:[],workload_from:2,workload_norm40x10:13,workload_to:2,worload:13,wrap:4,written:13,x_col:2,x_list:2,xeon:2,xgrid:2,xlabel:2,xlim:2,xml:[2,12,13],y1_list:2,y1label:2,y1lim:2,y2_list:2,y2label:2,y2lim:2,y_col:2,y_list:2,ygrid:2,ylabel:2,ylim:2,ylog:2,you:13,zip:13,zxvf:13},titles:["lumos package","lumos.analysis package","lumos.model package","lumos.model.core package","lumos.model.system package","lumos.model.tech package","lumos.model.tech.cmos package","lumos.model.tech.cmos.hp package","lumos.model.tech.cmos.lp package","lumos.model.tech.tfet package","lumos.model.tech.tfet.homoTFET30nm package","lumos.model.tech.tfet.homoTFET60nm package","lumos.unittests package","Lumos Framework"],titleterms:{analys:13,analysi:[1,13],applic:2,argpars:1,asacc:2,cmo:[6,7,8],content:[0,1,2,3,4,5,6,7,8,9,10,11,12],core:3,defin:13,exampl:13,framework:13,get:13,het:4,hetero:4,hom:4,homo:4,homotfet30nm:10,homotfet60nm:11,how:13,indic:13,introduct:13,io_cmo:3,io_tfet:3,kernel:2,licens:13,lumo:[0,1,2,3,4,5,6,7,8,9,10,11,12,13],misc:2,model:[2,3,4,5,6,7,8,9,10,11],modul:[0,1,2,3,4,5,6,7,8,9,10,11,12],mpsoc:4,o3_cmo:3,o3_tfet:3,packag:[0,1,2,3,4,5,6,7,8,9,10,11,12],plot:2,quick:13,set:0,start:13,submodul:[0,1,2,3,4,9,12],subpackag:[0,2,5,6,9],system:[4,13],tabl:13,tech:[5,6,7,8,9,10,11],test_acc:12,test_homogsi:12,test_mpsoc:12,test_ptmnew_app:12,tfet:[9,10,11],tfet_interp:9,ucor:2,unittest:12,workload:[2,13]}})