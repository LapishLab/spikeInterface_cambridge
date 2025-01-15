addpath(genpath(strcat(pwd,'/npy-matlab')))
dataDir = '/N/project/lapishLabWorkspace/DualProbes/2024-05-10-Session 2/2024-05-10_11-24-32/';
sortDir = '/N/project/lapishLabWorkspace/DualProbes/sortAll/sorted/2024-05-10_11-24-32/';
outputFile = '/N/project/lapishLabWorkspace/DualProbes/sortAll/export/2024-05-10_11-24-32.mat';
probeNames = ["ASSY-236-E-1", "ASSY-236-F"];
%%
[~,recTimestamps] = load_open_ephys_data_faster([dataDir, '100_CH1.continuous']);
clusters = getClusterInfo(sortDir, probeNames, recTimestamps);
events = getEvents(dataDir);
adc = getADC(dataDir);

%% convert tables to structs so mat file opens in scipy
events.data = table2struct(events.data);
clusters = table2struct(clusters);

% Save relevant variables
save(outputFile, 'clusters','events','adc');

%%

function clusters = getClusterInfo(sortDir, probeNames, recTimestamps)
    sorterOutputDirs = sortDir +  probeNames + "/sorter_output/";
    
    clusters = table();
    for i=1:length(sorterOutputDirs)
        sortFolder = sorterOutputDirs(1);
        cluster_info = readtable(sortFolder+"cluster_info.tsv", 'FileType','delimitedtext');
        cluster_info = addSpikeTimes(cluster_info, sortFolder, recTimestamps);
        cluster_info.probeName(:) = probeNames(i);
        cluster_info = addPosition(cluster_info, sortFolder);
        %cluster_info = addWaveForms(cluster_info, sortFolder); % TODO: get waveforms effeciently
        cluster_info = addQualityMetrics(cluster_info, sortFolder);
        clusters = cat(1, clusters, cluster_info);
    end

    %get rid of uneeded columns
    clusters(:,{'ContamPct', 'sh', 'depth'}) = [];
end

function cluster_info = addSpikeTimes(cluster_info, sortFolder, timestamps)
    spike_clusters = readNPY(sortFolder + "spike_clusters.npy");
    spike_Inds = readNPY(sortFolder + "spike_times.npy");
    
    nClusters = size(cluster_info,1);
    for i = 1:nClusters
        clusterID = cluster_info.cluster_id(i);
        inds = spike_Inds(spike_clusters == clusterID);
        cluster_info.spikeTimes{i} = timestamps(inds);
    end
end

function cluster_info = addPosition(cluster_info, sortFolder)
channel_map = readNPY(sortFolder + "channel_map.npy");
channel_positions = readNPY(sortFolder + "channel_positions.npy");

matchingID = cluster_info.ch == channel_map;
[clusterInd, mapInd] = ind2sub(size(matchingID), find(matchingID));
cluster_info.xPosition(clusterInd) = channel_positions(mapInd, 1);
cluster_info.yPosition(clusterInd) = channel_positions(mapInd, 2);
end

function cluster_info = addWaveForms(cluster_info, sortFolder)
%% collect spike times and waveform for each cluster
disp('Starting waveform extraction. This may take a while.')
gwfparams = struct;
gwfparams.dataDir = strcat(spikeSortingDir,'NeuropixelProbeSpikeSortingResults/',dataSetName,'/sorter_output/');    % KiloSort/Phy output folder
gwfparams.fileName = 'recording.dat';         % .dat file containing the raw
gwfparams.dataType = 'int16';            % Data type of .dat file (this should be BP filtered)
gwfparams.nCh = size(channel,1);         % Number of channels that were streamed to disk in .dat file
gwfparams.wfWin = [-40 41];              % Number of samples before and after spiketime to include in waveform
gwfparams.nWf = 2000;                    % Number of waveforms per unit to pull out

%%
nClusters = size(cluster_info,1);
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
end

function cluster_info = addQualityMetrics(cluster_info, sortFolder)
qualityMetrics = readtable(sortFolder+"qualityMetrics.csv");
cluster_info = cat(2, cluster_info, qualityMetrics(:,2:end)); % TODO: check that cluster IDs match. Currently quality metrics is not updated when clusters are merged in phy
end

function events = getEvents(dataDir)

[openEphysEvents,openEphysEventTimeStamps,info] = load_open_ephys_data_faster(dataDir+ "all_channels.events");
events = struct();
events.header = info.header;
data = table();

data.event = openEphysEvents;
data.time = openEphysEventTimeStamps;
infoTable = struct2table(rmfield(info, 'header'));
data = cat(2,data, infoTable);
events.data = data;
end

function adc = getADC(dataDir)
adc = struct();

adcFiles = dir(dataDir + "*ADC*");
auxFiles = dir(dataDir + "*AUX*");
allFiles = string([{adcFiles.name}, {auxFiles.name}])';

if isempty(allFiles)
    return
end

downsampleFactor = 100;
[~,timestamps] = load_open_ephys_data_faster(dataDir+allFiles(1));
adc.timestamps = timestamps(1:downsampleFactor:end);
adc.labels = allFiles;
adc.data = nan(length(allFiles), length(adc.timestamps));

for i=1:length(allFiles)
    file = dataDir+allFiles(i);
    [signal,~] = load_open_ephys_data_faster(file);
    adc.data(i,:) = signal(1:downsampleFactor:end);
end
end