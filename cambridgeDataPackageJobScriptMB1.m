% cambridgeDataPackage
%
%   This script packages curated spike sorting data for Cambridge probes.
%   It assumes the data have been spike sorted and curated using phy2. This
%   is part of the Lapish lab spike sorting workflow.

%% Settings

% Set the location of the spike sorting data on Slate
spikeSortingDir = '/N/project/lapishLabWorkspace/SpikeInterfaceSpikeSorting/';

% Get the slurm task ID
% TaskID = str2double(getenv('SLURM_ARRAY_TASK_ID'));
TaskID = 15;
disp(strcat('Task ID = ',num2str(TaskID)))

%% Read the list of file names and channel maps

lines = readlines(strcat(spikeSortingDir,'cambridgeRecordingsPackaging_AllDMS.txt'));
nDataSets = length(lines);
filenames = cell([nDataSets,1]);
chanMaps = cell([nDataSets,1]);
timeTrimmings = cell([nDataSets,1]);
for iDataSet = 1:nDataSets
    newstr = split(lines(iDataSet),',');
    filenames{iDataSet} = newstr{1};
    chanMaps{iDataSet} = newstr{2};
    if length(newstr) == 3
        timeTrimmings{iDataSet} = newstr{3};
    else
        timeTrimmings{iDataSet} = [];
    end
end

%% Load the curated spike sorting results for the data set identified by the Task ID

addChanAll = false;

% Get the name for this data set
pathParts = regexp(filenames{TaskID},'/','split');
dataSetName = pathParts{end};

% Update the user on status
disp(strcat('Processing ',dataSetName,'.'))

% Record the channel map file name and the time trimming (if performed).
% Note, time trimming has been accounted for using the timestamps from the
% trimmed open ephys recordings.
chanMapFileName = chanMaps{TaskID};
timeTrimmingPerformed = timeTrimmings{TaskID};

% Load information about which ADC and AUX channels to save
try
    load(strcat(spikeSortingDir,'CambridgeProbeSpikeSortingResults/',dataSetName,'/sorter_output/ADCAUXChannelSettings.mat'),'ADCAUXChannelsToKeep')
catch
    error('No ADC/AUX retention information found! Make sure to run cambridgeADCAUXSet.m first!')
end

% Load phy2 output files
spike_clusters = readNPY(strcat(spikeSortingDir,'CambridgeProbeSpikeSortingResults/',dataSetName,'/sorter_output/spike_clusters.npy'));
spike_times = readNPY(strcat(spikeSortingDir,'CambridgeProbeSpikeSortingResults/',dataSetName,'/sorter_output/spike_times.npy'));
channelPositions = readNPY(strcat(spikeSortingDir,'CambridgeProbeSpikeSortingResults/',dataSetName,'/sorter_output/channel_positions.npy'));
channelMap = readNPY(strcat(spikeSortingDir,'CambridgeProbeSpikeSortingResults/',dataSetName,'/sorter_output/channel_map.npy'));
clusterInfo = readtable(strcat(spikeSortingDir,'CambridgeProbeSpikeSortingResults/',dataSetName,'/sorter_output/cluster_info.tsv'), 'FileType','delimitedtext');
t = readtable(strcat(spikeSortingDir,'CambridgeProbeSpikeSortingResults/',dataSetName,'/sorter_output/cluster_group.tsv'), 'FileType','delimitedtext');
clusterRuling = t{:,2};
clusterRulingCluster = t{:,1};

nChannels = size(channelPositions,1);
nClustersAll = length(clusterRuling);

% Get necessary parameters
paramsFile = readcell(strcat(spikeSortingDir,'CambridgeProbeSpikeSortingResults/',dataSetName,'/sorter_output/params.py'),'Delimiter',' = ','FileType','text');
sample_rate = NaN;
for iParam = 1:size(paramsFile,1)
    if strcmp(paramsFile{iParam,1},'sample_rate')
        sample_rate = paramsFile{iParam,2};
    end
end
if ~isfinite(sample_rate)
    error('Could not read params.py properly to get sample rate.')
end

% Get the timestamps from the raw open ephys recordings to match
[data,timestamps] = load_open_ephys_data_faster(strcat(filenames{TaskID},'/100_CH1.continuous'));

% Organize the clusters based on user classification and convert to
% spike time rasters
clustersGood = [];
clustersMUA = [];
clustersNoise = [];
for iCluster = 1:nClustersAll
    if strcmp(clusterRuling(iCluster),'good')
        clustersGood = [clustersGood,clusterRulingCluster(iCluster)];
    elseif strcmp(clusterRuling(iCluster),'mua')
        clustersMUA = [clustersMUA,clusterRulingCluster(iCluster)];
    elseif strcmp(clusterRuling(iCluster),'noise')
        clustersNoise = [clustersNoise,clusterRulingCluster(iCluster)];
    end
end
clustersGood = sort(clustersGood);
clustersMUA = sort(clustersMUA);
clustersNoise = sort(clustersNoise);
spkGood = cell([length(clustersGood),1]);
for iCluster = 1:length(clustersGood)
    spkGood{iCluster} = timestamps(spike_times(spike_clusters == clustersGood(iCluster)));
end
spkMUA = cell([length(clustersMUA),1]);
for iCluster = 1:length(clustersMUA)
    spkMUA{iCluster} = timestamps(spike_times(spike_clusters == clustersMUA(iCluster)));
end
spkNoise = cell([length(clustersNoise),1]);
for iCluster = 1:length(clustersNoise)
    spkNoise{iCluster} = timestamps(spike_times(spike_clusters == clustersNoise(iCluster)));
end

% Prepare waveform parameters variable
gwfparams = struct;
gwfparams.dataDir = strcat(spikeSortingDir,'CambridgeProbeSpikeSortingResults/',dataSetName,'/sorter_output/');    % KiloSort/Phy output folder
gwfparams.fileName = 'recording.dat';         % .dat file containing the raw
gwfparams.dataType = 'int16';            % Data type of .dat file (this should be BP filtered)
gwfparams.nCh = nChannels;                      % Number of channels that were streamed to disk in .dat file
gwfparams.wfWin = [-40 41];              % Number of samples before and after spiketime to include in waveform
gwfparams.nWf = 2000;                    % Number of waveforms per unit to pull out
gwfparams.spikeTimes = spike_times; % Vector of cluster spike times (in samples) same length as .spikeClusters
gwfparams.spikeClusters = spike_clusters; % Vector of cluster IDs (Phy nomenclature)   same length as .spikeTimes

% Get the waveforms
disp('Starting waveform extraction. This may take a while.')
wf = getWaveForms(gwfparams);

% Organize the mean waveforms
waveformsGood = wf.waveFormsMean(ismember(clusterRulingCluster,clustersGood),:,:);
waveformsMUA = wf.waveFormsMean(ismember(clusterRulingCluster,clustersMUA),:,:);
waveformsNoise = wf.waveFormsMean(ismember(clusterRulingCluster,clustersNoise),:,:);
waveformsTime = (gwfparams.wfWin(1):gwfparams.wfWin(2))/sample_rate;

% Load the ADC and AUX channels
ADCAUXChannels = struct;
if ~isempty(ADCAUXChannelsToKeep)
    for iChannel = 1:length(ADCAUXChannelsToKeep)
        [data,timestamps] = load_open_ephys_data_faster(strcat(filenames{TaskID},'/100_',ADCAUXChannelsToKeep{iChannel},'.continuous'));
        eval(strcat('ADCAUXChannels.',ADCAUXChannelsToKeep{iChannel},'=data;'))
        if ~isfield(ADCAUXChannels,'time')
            ADCAUXChannels.time = timestamps;
        end
    end
else
    disp('No additional channels selected for retention in analysis. Raw ADC and AUX files have not been altered.')
end

% Load the open ephys event file
[openEphysEvents,openEphysEventTimeStamps,info] = load_open_ephys_data_faster(strcat(filenames{TaskID},'/all_channels.events'));

% Copy over post-processing code
if exist(strcat(spikeSortingDir,'CambridgeProbeSpikeSortingResults/',dataSetName,'/sorter_output/postProcessingCode'),'dir') == 7
    rmdir(strcat(spikeSortingDir,'CambridgeProbeSpikeSortingResults/',dataSetName,'/sorter_output/postProcessingCode'),'s')
end
mkdir(strcat(spikeSortingDir,'CambridgeProbeSpikeSortingResults/',dataSetName,'/sorter_output/postProcessingCode'))
filesToCopy = {'cambridgeDataPackageJobScript.m','constructNPYheader.m','datToNPY.m','getWaveForms.m','load_open_ephys_data_faster.m','readNPY.m','readNPYheader.m','cambridgeADCAUXSet.m'};
for iFile = 1:length(filesToCopy)
    copyfile(strcat(pwd,'/',filesToCopy{iFile}),strcat(spikeSortingDir,'CambridgeProbeSpikeSortingResults/',dataSetName,'/sorter_output/postProcessingCode/',filesToCopy{iFile}))
end

% Find the slurm job file and copy it over
temp = dir;
dates = NaN([length(temp),1]);
for iFile = 1:length(temp)
    if (length(temp(iFile).name) > 25) && strcmp(temp(iFile).name(1:25),'spikeSortCambridgeDataJob') && strcmp(temp(iFile).name((end - 2):end),'txt')
        lines = readlines(temp(iFile).name);
        try
            if strcmp(lines{3}(22:end),dataSetName)
                dates(iFile) = temp(iFile).datenum;
            end
        end
    end
end
if sum(isnan(dates)) < length(dates)
    [~,iFile] = max(dates,[],'omitnan');
    copyfile(strcat(pwd,'/',temp(iFile).name),strcat(spikeSortingDir,'CambridgeProbeSpikeSortingResults/',dataSetName,'/SlurmJobOutputLog.txt'))
else
    disp('No slurm job file found with matching data set name.')
end

% Tar and zip the raw spike sorting results
disp('Zipping post-sorting directory. This may take a while.')
tar(strcat(spikeSortingDir,'CambridgeProbeSpikeSortingResults/',dataSetName,'_PostSorting'),strcat(spikeSortingDir,'CambridgeProbeSpikeSortingResults/',dataSetName))
gzip(strcat(spikeSortingDir,'CambridgeProbeSpikeSortingResults/',dataSetName,'_PostSorting.tar'))
delete(strcat(spikeSortingDir,'CambridgeProbeSpikeSortingResults/',dataSetName,'_PostSorting.tar'))

% Save relevant variables
save(strcat(spikeSortingDir,'CambridgeProbeSpikeSortingResults/',dataSetName,'.mat'),'spkGood','spkMUA','spkNoise',...
    'channelPositions','channelMap',...
    'clusterRuling','clusterRulingCluster','clustersGood','clustersMUA','clustersNoise','clusterInfo','paramsFile',...
    'waveformsGood','waveformsMUA','waveformsNoise','waveformsTime',...
    'openEphysEvents','openEphysEventTimeStamps',...
    'chanMapFileName','timeTrimmingPerformed');
if ~isempty(ADCAUXChannelsToKeep)
    save(strcat(spikeSortingDir,'CambridgeProbeSpikeSortingResults/',dataSetName,'_ADCAUX.mat'),'ADCAUXChannels','-v7.3');
end

