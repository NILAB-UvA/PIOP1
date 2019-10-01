cd /home/lsnoek1/projects/PIOP1/bids/code

FAILED = {};
main_dir = '../'; 
subs = dir(fullfile(main_dir, 'sub-*'));
for i=1:numel(subs)
    this_sub = fullfile(main_dir, subs(i).name);
    physios = dir(fullfile(this_sub, 'func', '*physio.tsv.gz'));
    for ii=1:numel(physios)
       this_phys = fullfile(this_sub, 'func', physios(ii).name);
       this_func = strrep(this_phys,'recording-respcardiac_physio.tsv.gz', 'bold.nii.gz');
       ricor_file = strrep(this_phys, 'physio.tsv.gz', 'retroicor.txt');
       if exist(ricor_file, 'file') ~= 2
           nii = load_untouch_header_only(this_func);
           n_slices = nii.dime.dim(2);
           n_vols = nii.dime.dim(5);
           tr = nii.dime.pixdim(5);
           fprintf('Trying to create %s with %i vols and TR=%.3f...', ricor_file, n_vols, tr); 
           
           try
               run_retroicor(this_phys, n_slices, n_vols, tr);
           catch
               fprintf('\n--------------\nFAILED!!! %s \n--------------\n\n', this_phys);
               FAILED{end+1} = this_phys;
           end
       else
           fprintf('%s already exists ... skipping!\n', ricor_file);
       end
    end
end

% just to check what's wrong
for i=4:numel(FAILED)
    this_phys = FAILED{i};
    this_func = strrep(this_phys,'physio.tsv.gz', 'bold.nii.gz');
    ricor_file = strrep(this_phys, 'physio.tsv.gz', 'retroicor.txt');
    fprintf('Trying to create %s ...', ricor_file); 
    nii = load_untouch_header_only(this_func);
    n_slices = nii.dime.dim(2);
    n_vols = nii.dime.dim(5);
    tr = nii.dime.pixdim(5);
    run_retroicor(this_phys, n_slices, n_vols, 1.317);
end