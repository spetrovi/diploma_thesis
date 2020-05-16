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
baselines['korben']['HDD'] = glob.glob('../results/korben_baselines/*-HDD-*baseline*tar.xz')
baselines['korben']['HDD'].sort()
baselines['korben']['SSD'] = glob.glob('../results/korben_baselines/*-ssd_baseline*tar.xz')

baselines['korben']['VDO_HDD'] = glob.glob('../results/korben_baselines/*-VDO_HDD-*tar.xz')
baselines['korben']['VDO_HDD'].sort()
baselines['korben']['VDO_SSD'] = glob.glob('../results/korben_baselines/*-VDO_SSD-*tar.xz')

#Report( baselines['korben']['VDO_HDD'] + baselines['korben']['HDD'], '../results/korben_baselines/VDO_HDD/', offset=(0,1000), log_window = 0.001, smooth = True, chart_vdostats = chart_vdostats, lim_y=300)

#Experiment empty & alloc
empty_VDO_SSD = glob.glob('../results/empty_VDO/*vdo_ssd_empty*.tar.xz')
empty_VDO_HDD = glob.glob('../results/empty_VDO/*vdo_hdd_empty*.tar.xz')

#Report(baselines['korben']['SSD'] + empty_VDO_SSD + baselines['korben']['VDO_SSD'] , '../results/empty_VDO/SSD/', offset=(0,1000), log_window = 0.001, smooth = True, chart_vdostats = chart_vdostats, lim_y=200) 

#Report(baselines['korben']['HDD'] + empty_VDO_HDD + baselines['korben']['VDO_HDD'] , '../results/empty_VDO/HDD/', offset=(0,1000), log_window = 0.001, smooth = True, chart_vdostats = chart_vdostats, lim_y=200) 

#Experiment write policies
write_policies = glob.glob('../results/write_policies/*.tar.xz')
#Report(write_policies, '../results/write_policies/latest/', offset=(0,1000), log_window = 0.001, smooth = True, chart_vdostats = chart_vdostats, lim_y=500, test_label='write policy') 

#Experiment journal speeding
no_tail = glob.glob('../results/journal/*no_tail*.tar.xz')
tail_ssd = glob.glob('../results/journal/*tail_ssd*.tar.xz')
tail_nvme = glob.glob('../results/journal/*tail_nvme*.tar.xz')

#Report(baselines['wolverine']['VDO_HDD'] + tail_ssd + tail_nvme, '../results/journal/report/', offset=(0,1000), log_window = 0.001, smooth = True, chart_vdostats = chart_vdostats, lim_y=60, test_label='Various devices on tail of VDO') 


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
block_map_cache = {}
block_map_cache['400g_default'] = glob.glob('../results/block_map_cache/*-400g_default*.tar.xz')
block_map_cache['increased_cache'] = glob.glob('../results/block_map_cache/*-400g_increased*.tar.xz')
block_map_cache['80g'] = glob.glob('../results/block_map_cache/*-80g*.tar.xz')

#Report(block_map_cache['80g']+ block_map_cache['400g_default'] + block_map_cache['increased_cache'], '../results/block_map_cache/report/', offset=(0,1000), log_window = 0.001, smooth = True, chart_vdostats = chart_vdostats, lim_y=200, test_label = 'block map cache')

#Experiments half full
half = glob.glob('../results/half/*half.tar.xz')
seq = glob.glob('../results/half/*seq*.tar.xz')
rand = glob.glob('../results/half/*rand*.tar.xz')
Report(seq + half + rand, '../results/half/report/', offset=(0,1000), log_window = 0.001, smooth = True, chart_vdostats = ['logical blocks used', 'data blocks used'], lim_y=200, test_label = 'VDO')

tun = glob.glob('../results/tuning/*.tar.xz')

#Report(tun, '../results/tuning/report/', offset=(0,1000), log_window = 0.001, smooth = True, chart_vdostats = ['current VDO IO requests in progress','maximum VDO IO requests in progress'], lim_y=12000, test_label = 'VDO')

aging = glob.glob('../results/aging/*.tar.xz')
aging.sort()
#Report(aging, '../results/aging/report/', offset=(0,1000), log_window = 0.001, smooth = True, chart_vdostats = chart_vdostats + ['current VDO IO requests in progress'], lim_y=600, test_label = 'aging')

queue = glob.glob('../results/queue/**tar.xz')
queue.sort()
#Report(queue, '../results/queue/report/', offset=(0,1000), log_window = 0.001, smooth = True, chart_vdostats = chart_vdostats + ['current VDO IO requests in progress'], lim_y=600, test_label = 'queue_tiering')
#Report(iodepth, '../results/korben_baselines/report/', offset=(0,1000), log_window = 0.001, smooth = True, chart_vdostats = chart_vdostats, lim_y=200, test_label = 'aging')

threads = glob.glob('../results/threads/*tar.xz')
threads.sort()

#Report(threads, '../results/threads/report/', offset=(0,1000), log_window = 0.01, smooth = True, chart_vdostats = chart_vdostats + ['current VDO IO requests in progress'], lim_y=600, test_label = 'threads')

steady_prepare = glob.glob('../results/steady/*prepare*.tar.xz')
steady_test = glob.glob('../results/steady/*tes*.tar.xz')
#Report(steady_prepare + steady_test, '../results/steady/report/', offset=(0,1000), log_window = 0.001, smooth = True, chart_vdostats = chart_vdostats, lim_y=300, test_label = 'steady state testing phases')
































