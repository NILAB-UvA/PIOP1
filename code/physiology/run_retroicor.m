function [  ] = run_retroicor(phys_file, save_dir, n_slices, n_vols, tr)
% Runs TAPAS retroicor
physio = tapas_physio_new();

[~,basename,~] = fileparts(phys_file);
ricor_out = strrep(basename, 'physio.tsv','desc-retroicor_regressors.tsv');

%[~,ricor_out,~] = fileparts(strrep(phys_file,'physio.tsv.gz', 'retroicor.txt'));
set(0,'DefaultFigureVisible','off');

%% Individual Parameter settings. Modify to your need and remove default settings
physio.save_dir = {save_dir};
physio.log_files.vendor = 'BIDS';
physio.log_files.cardiac = {phys_file};
%physio.log_files.relative_start_acquisition = 0;
physio.log_files.align_scan = 'first';
physio.log_files.sampling_interval = 1/496;
physio.scan_timing.sqpar.Nslices = n_slices;
physio.scan_timing.sqpar.TR = tr;
physio.scan_timing.sqpar.Ndummies = 0;
physio.scan_timing.sqpar.Nscans = n_vols;
physio.scan_timing.sqpar.onset_slice = floor(n_slices / 2);
physio.scan_timing.sync.method = 'scan_timing_log';
physio.preproc.cardiac.modality = 'PPU';
physio.preproc.cardiac.initial_cpulse_select.method = 'auto_matched';
physio.preproc.cardiac.initial_cpulse_select.file = 'initial_cpulse_kRpeakfile.mat';
physio.preproc.cardiac.initial_cpulse_select.min = 0.4;
physio.preproc.cardiac.posthoc_cpulse_select.method = 'off';
physio.preproc.cardiac.posthoc_cpulse_select.percentile = 80;
physio.preproc.cardiac.posthoc_cpulse_select.upper_thresh = 60;
physio.preproc.cardiac.posthoc_cpulse_select.lower_thresh = 60;
physio.model.orthogonalise = 'none';
physio.model.censor_unreliable_recording_intervals = false;
physio.model.output_multiple_regressors = ricor_out;
physio.model.output_physio = '';
physio.model.retroicor.include = true;
physio.model.retroicor.order.c = 3;
physio.model.retroicor.order.r = 4;
physio.model.retroicor.order.cr = 1;
physio.model.rvt.include = true;
physio.model.rvt.delays = 0;
physio.model.hrv.include = true;
physio.model.hrv.delays = 0;
physio.model.noise_rois.include = false;
physio.model.movement.include = false;
physio.model.other.include = false;
physio.verbose.level = 2;
physio.verbose.process_log = cell(0, 1);
physio.verbose.fig_handles = zeros(0, 1);
physio.verbose.use_tabs = false;
physio.ons_secs.c_scaling = 1;
physio.ons_secs.r_scaling = 1;

% RETROICOR cardiac regressors [2 x 3 nOrderCardiac] = 6
% RETROICOR respiratory regressors [2 x 4 nOrderRespiratory] = 8
% RETROICOR cardXResp interaction regressors [4 x 1 nOrderCardiacXRespiratory] = 4
% HRV [nDelaysHRV] = 1
% RVT [nDelaysRVT] = 1 

%% Run physiological recording preprocessing and noise modeling
physio = tapas_physio_main_create_regressors(physio);
close all;

end

