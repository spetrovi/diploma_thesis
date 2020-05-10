from drift_compare import *
import glob

chart_vdostats = ['logical blocks used','data blocks used', 'dedupe advice valid']
#chart_vdostats.sort()

baselines = {'wolverine':{}, 'hulk':{}, 'korben':{}}


#Load paths to results
#zbehnut wolverine VDO_HDD, VDO_SSD, VDO_NVMe [Running, start 13:08]
baselines['wolverine']['HDD'] = glob.glob('../results/wolverine_baselines/*-HDD-*tar.xz')
baselines['wolverine']['SSD']= glob.glob('../results/wolverine_baselines/*-SSD-*tar.xz')
baselines['wolverine']['NVMe']= glob.glob('../results/wolverine_baselines/*-NVMe-*tar.xz')

baselines['wolverine']['VDO_HDD'] = glob.glob('../results/wolverine_baselines/*-VDO_HDD-*tar.xz')
baselines['wolverine']['VDO_SSD']= glob.glob('../results/wolverine_baselines/*-VDO_SSD-*tar.xz')
baselines['wolverine']['VDO_NVMe']= glob.glob('../results/wolverine_baselines/*-VDO_NVMe-*tar.xz')

#Report baseline HDD
#Report(baselines['wolverine']['HDD'] + baselines['wolverine']['VDO_HDD'], './official/wolverine_baselines/HDD/', offset=(0,500), log_window = 0.001, smooth = True, chart_vdostats = chart_vdostats, lim_y=20) 

#Report baseline SSD
#Report(baselines['wolverine']['SSD'] + baselines['wolverine']['VDO_SSD'], './official/wolverine_baselines/SSD/', offset=(0,500), log_window = 0.001, smooth = True, chart_vdostats = chart_vdostats, lim_y=200) 

#Report baseline NVMe
#Report(baselines['wolverine']['NVMe'] + baselines['wolverine']['VDO_NVMe'], './official/wolverine_baselines/NVMe/', offset=(0,500), log_window = 0.001, smooth = True, chart_vdostats = chart_vdostats, lim_y=200) 

#zbehnut hulk VDO_NVMe
baselines['hulk']['NVMe'] = glob.glob('../results/hulk_baselines/*-NVMe-*tar.xz')
#baselines['hulk']['NVMe'] = glob.glob('./official/hulk_baselines/*-VDO_NVMe-*tar.xz') #[running 13:13]

#zbehnut korben, SSD[respin], HDD[respin], (VDO_SSD, VDO_HDD, empty&prealloc VDO_SSD, empty&prealloc VDO HDD)[done]
baselines['korben']['HDD'] = glob.glob('../results/korben_baselines/*hdd_baseline*tar.xz')
baselines['korben']['SSD'] = glob.glob('../results/korben_baselines/*ssd_baseline*tar.xz')

baselines['korben']['VDO_HDD'] = glob.glob('../results/korben_baselines/*vdo_hdd*tar.xz')
baselines['korben']['VDO_SSD'] = glob.glob('../results/korben_baselines/*vdo_ssd*tar.xz')

#korben_vdo_baselines = Report(baselines['korben']['VDO_HDD'] + baselines['korben']['VDO_SSD'], './official/korben_baselines/VDO/', offset=(0,1000), log_window = 0.001, smooth = True, chart_vdostats = chart_vdostats, lim_y=300)

#Experiment empty & alloc
empty_VDO_SSD = glob.glob('../results/empty_VDO/*vdo_ssd_empty*.tar.xz')
empty_VDO_HDD = glob.glob('../results/empty_VDO/*vdo_hdd_empty*.tar.xz')

#Report(baselines['korben']['SSD'] + empty_VDO_SSD + baselines['korben']['VDO_SSD'] , '../results/empty_VDO/SSD/', offset=(0,1000), log_window = 0.001, smooth = True, chart_vdostats = chart_vdostats, lim_y=200) 

#Report(baselines['korben']['HDD'] + empty_VDO_HDD + baselines['korben']['VDO_HDD'] , '../results/empty_VDO/HDD/', offset=(0,1000), log_window = 0.001, smooth = True, chart_vdostats = chart_vdostats, lim_y=200) 

#Experiment write policies
write_policies = glob.glob('../results/write_policies/*.tar.xz')
#Report(write_policies, '../results/write_policies/report/', offset=(0,1000), log_window = 0.001, smooth = True, chart_vdostats = chart_vdostats, lim_y=2700, test_label='write policy') 

#Experiment journal speeding
no_tail = glob.glob('../results/journal/*no_tail*.tar.xz')
tail_ssd = glob.glob('../results/journal/*tail_ssd*.tar.xz')
tail_nvme = glob.glob('../results/journal/*tail_nvme*.tar.xz')

#Report(baselines['wolverine']['VDO_HDD'] + tail_ssd + tail_nvme, '../results/journal/report/', offset=(0,1000), log_window = 0.001, smooth = True, chart_vdostats = chart_vdostats, lim_y=270, test_label='Various devices on tail of VDO') 


#Experiment discards
discards_SSD = glob.glob('../results/discards/*-SSD-*.tar.xz')

empty_discards = {}
empty_discards['4k'] = glob.glob('../results/discards/empty_VDO/*-4k*.tar.xz')
empty_discards['16k'] = glob.glob('../results/discards/empty_VDO/*-16k*.tar.xz')
empty_discards['128k'] = glob.glob('../results/discards/empty_VDO/*-128k*.tar.xz')
empty_discards['1m'] = glob.glob('../results/discards/empty_VDO/*-1m*.tar.xz')

#Report(empty_discards['4k'] + empty_discards['16k'] + empty_discards['128k'] + empty_discards['1m'], '../results/discards/empty_VDO/report/', offset=(0,1000), log_window = 0.001, smooth = True, chart_vdostats = ['bios in discard'], lim_y=1500, test_label = 'max discard size') 


full_discards = []
full_discards += glob.glob('../results/discards/full_VDO/*-4k*.tar.xz')
full_discards += glob.glob('../results/discards/full_VDO/*-16k*.tar.xz')
full_discards += glob.glob('../results/discards/full_VDO/*-128k*.tar.xz')
full_discards += glob.glob('../results/discards/full_VDO/*-1m*.tar.xz')

#Report(full_discards, '../results/discards/full_VDO/report/', offset=(0,1000), log_window = 0.001, smooth = True, chart_vdostats = ['logical blocks used','bios in discard'], lim_y=1300, test_label = 'max discard size') 




































