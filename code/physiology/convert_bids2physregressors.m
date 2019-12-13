addpath('/home/lsnoek1/software/scanphyslog2bids/scripts');
cd /home/lsnoek1/projects/PIOP1/bids/code/physiology

FAILED = {};
main_dir = '../../';
subs = dir(fullfile(main_dir, 'sub-*'));

for i=1:numel(subs)
    this_sub = fullfile(main_dir, subs(i).name);
    [~,sub_base,~] = fileparts(this_sub);
    
    physios = dir(fullfile(this_sub, 'func', '*physio.tsv.gz'));
    for ii=1:numel(physios)
       this_phys = fullfile(this_sub, 'func', physios(ii).name);
       this_func = strrep(this_phys,'recording-respcardiac_physio.tsv.gz', 'bold.nii.gz');    
       save_dir = fullfile('../../derivatives/physiology', sub_base, 'physio');
       try
           run_physIO(this_phys, this_func, 496, save_dir, 0, 1);
       catch
           fprintf('\n--------------\nFAILED!!! %s \n--------------\n\n', this_phys);
           FAILED{end+1} = this_phys;
       end
    end
end