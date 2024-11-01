addpath(genpath(strcat(pwd,'/npy-matlab-master')))
dataDir = '/N/u/lapishla/Quartz/Desktop/SpikeInterfaceSpikeSorting/CambridgeProbeSpikeSortingResults/2024-05-03_11-34-01/ASSY-236-E-1';
sorter_output = strcat(dataDir,'/sorter_output/');
% Load phy2 output files
spike_clusters = readNPY(strcat(sorter_output,'spike_clusters.npy'));
spike_Inds = readNPY(strcat(spikeSortingDir,'NeuropixelProbeSpikeSortingResults/',dataSetName,'/sorter_output/spike_times.npy'));

continuousTimes = readNPY([filename, '/Record Node 102/experiment1/recording1/continuous/Neuropix-PXI-100.ProbeA-AP/timestamps_global.npy']);

channel = table();
channel.map = readNPY(strcat(spikeSortingDir,'NeuropixelProbeSpikeSortingResults/',dataSetName,'/sorter_output/channel_map.npy'))';
channel.position = readNPY(strcat(spikeSortingDir,'NeuropixelProbeSpikeSortingResults/',dataSetName,'/sorter_output/channel_positions.npy'));

clusterInfo = readtable(strcat(spikeSortingDir,'NeuropixelProbeSpikeSortingResults/',dataSetName,'/sorter_output/cluster_info.tsv'), 'FileType','delimitedtext');
t = readtable(strcat(spikeSortingDir,'NeuropixelProbeSpikeSortingResults/',dataSetName,'/sorter_output/cluster_group.tsv'), 'FileType','delimitedtext');
clusterInfo.phyLabel = t.group;

% Get necessary parameters
paramsFile = readcell(strcat(spikeSortingDir,'NeuropixelProbeSpikeSortingResults/',dataSetName,'/sorter_output/params.py'),'Delimiter',' = ','FileType','text');
sample_rate = NaN;
for iParam = 1:size(paramsFile,1)
    if strcmp(paramsFile{iParam,1},'sample_rate')
        sample_rate = paramsFile{iParam,2};
    end
end
if ~isfinite(sample_rate)
    error('Could not read params.py properly to get sample rate.')
end


%% collect spike times and waveform for each cluster
disp('Starting waveform extraction. This may take a while.')
gwfparams = struct;
gwfparams.dataDir = strcat(spikeSortingDir,'NeuropixelProbeSpikeSortingResults/',dataSetName,'/sorter_output/');    % KiloSort/Phy output folder
gwfparams.fileName = 'recording.dat';         % .dat file containing the raw
gwfparams.dataType = 'int16';            % Data type of .dat file (this should be BP filtered)
gwfparams.nCh = size(channel,1);         % Number of channels that were streamed to disk in .dat file
gwfparams.wfWin = [-40 41];              % Number of samples before and after spiketime to include in waveform
gwfparams.nWf = 2000;                    % Number of waveforms per unit to pull out
waveformsTime = (gwfparams.wfWin(1):gwfparams.wfWin(2))/sample_rate;

%% throw out clusters with firing rate less than 0.1 Hz

clusterInfo = clusterInfo(clusterInfo.fr>0.1,:);
%%
nClusters = size(clusterInfo,1);
for i = 1:nClusters
    clusterID = clusterInfo.cluster_id(i);

    inds = spike_Inds(spike_clusters == clusterID);
    clusterInfo.spikeTimes{i} = continuousTimes(inds);

    gwfparams.spikeTimes = inds;
    gwfparams.spikeClusters = spike_clusters(spike_clusters == clusterID);
    wf = getWaveForms(gwfparams);
    clusterInfo.waveForm{i} = wf.waveFormsMean;
    allWF = wf.waveForms;
    amps = max(squeeze(max(allWF,[],4) - min(allWF,[],4)),[],2);
    clusterInfo.allAmps{i} = amps(~isnan(amps));
    disp(['Completed ' num2str(i) '/' num2str(nClusters) ' clusters.']);
end

%% Pull in the original open ephys events

% eventFolder = [filename, '/Record Node 102/experiment1/recording1/events/NI-DAQmx-104.PXIe-6341/TTL'];
% events = table();
% events.sampleNumber = readNPY([eventFolder,'/sample_numbers.npy']);
% s = readNPY([eventFolder,'/states.npy']);
% events.state = s>0;
% events.line = abs(s);
% events.timestamp = readNPY([eventFolder,'/timestamps.npy']);

events = readtable([filename,'/Record Node 102/experiment1/recording1/events/events.csv']);

% line 8 is the TTL from the trials, the first trial marks the true start
% of the session. Some of the sample numbers are weird at the start. Also,
% the time stamps are weird at the start, but start advancing a little bit
% after the sample numbers start working. Weird.


disp('Saving mat file.')
% Save relevant variables
matName = strcat(spikeSortingDir,'NeuropixelProbeSpikeSortingResults/',dataSetName,'.mat');
save(matName,"channel","events","clusterInfo","paramsFile","waveformsTime");


% % Copy over post-processing code
% if exist(strcat(spikeSortingDir,'NeuropixelProbeSpikeSortingResults/',dataSetName,'/sorter_output/postProcessingCode'),'dir') == 7
%     rmdir(strcat(spikeSortingDir,'NeuropixelProbeSpikeSortingResults/',dataSetName,'/sorter_output/postProcessingCode'),'s')
% end
% mkdir(strcat(spikeSortingDir,'NeuropixelProbeSpikeSortingResults/',dataSetName,'/sorter_output/postProcessingCode'))
% filesToCopy = {'neuropixelDataPackageJobScript.m','constructNPYheader.m','datToNPY.m','getWaveForms.m','readNPY.m','readNPYheader.m','openEphysMatlabTools'};
% for iFile = 1:length(filesToCopy)
%     copyfile(strcat(pwd,'/',filesToCopy{iFile}),strcat(spikeSortingDir,'NeuropixelProbeSpikeSortingResults/',dataSetName,'/sorter_output/postProcessingCode/',filesToCopy{iFile}))
% end
% 
% % Tar and zip the raw spike sorting results
% disp('Zipping post-sorting directory. This may take a while.')
% tar(strcat(spikeSortingDir,'NeuropixelProbeSpikeSortingResults/',dataSetName,'_PostSorting'),strcat(spikeSortingDir,'NeuropixelProbeSpikeSortingResults/',dataSetName))
% gzip(strcat(spikeSortingDir,'NeuropixelProbeSpikeSortingResults/',dataSetName,'_PostSorting.tar'))
% delete(strcat(spikeSortingDir,'NeuropixelProbeSpikeSortingResults/',dataSetName,'_PostSorting.tar'))
% 



