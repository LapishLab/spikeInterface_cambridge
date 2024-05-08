% cambridgeADCAUXSet
%
%   This script allows the user to set which ADC and AUX channels to retain
%   for further analyses. It is part of the Lapish lab spike sorting
%   pipeline.

%% Settings

% Set the location of the spike sorting data on Slate
spikeSortingDir = '/N/project/lapishLabWorkspace/SpikeInterfaceSpikeSorting/';

%% Read the list of file names and channel maps

lines = readlines(strcat(spikeSortingDir,'cambridgeRecordingsPackaging.txt'));
nDataSets = length(lines);
filenames = cell([nDataSets,1]);
chanMaps = cell([nDataSets,1]);
for iDataSet = 1:nDataSets
    filenames{iDataSet} = extractBefore(lines(iDataSet),',');
    chanMaps{iDataSet} = extractAfter(lines(iDataSet),',');
end

%% Load the curated spike sorting results for each data set

addChanAll = false;
for iDataSet = 1:nDataSets

    % Get the name for this data set
    pathParts = regexp(filenames{iDataSet},'/','split');
    dataSetName = pathParts(end);

    % Update the user on status
    disp(strcat('Processing ',dataSetName,'.'))

    % Ask the user which ADC and AUX channels they want to save.
    if ~addChanAll
        list = {'ADC1','ADC2','ADC3','ADC4','ADC5','ADC6','ADC7','ADC8','AUX1','AUX2','AUX3','None'};
        [addChanKeep,tf] = listdlg('ListString',list,'PromptString','Select ADC and AUX channels with data:','ListSize',[350,250],'CancelString','None');
        addChanKeep(addChanKeep == 12) = [];
        answer = questdlg('Apply ADC and AUX channel selections to all data sets?', ...
	        'Apply to all?', ...
	        'Yes','No','No');
        if strcmp(answer,'Yes')
            addChanAll = true;
        end
    end
    ADCAUXChannelsToKeep = list(addChanKeep);

    % Save the results
    try
        save(strcat(spikeSortingDir,'CambridgeProbeSpikeSortingResults/',dataSetName,'/sorter_output/ADCAUXChannelSettings.mat'),'ADCAUXChannelsToKeep')
    catch
        disp(strcat('Could not save ADC AUX Settings for ',dataSetName,'. Perhaps this data set has not been sorted yet?'))
    end

end