import os
import re
import shutil
import socket
from os import path

ds = '/'
plot_size = '32'
thread_count = '2'
buffer_size = '4096'
plot_log_file = './chia_out.log'

# set this to fastest drive with space that IS NOT your OS drive
tmp_dir1 = '/media/andy/bongo/tmp'
tmp_dir2 = tmp_dir1
final_dir = tmp_dir1

# set this to big slow drive where your harvester will run, but not your actual plot directory so
# harvester doesn't take it as corrupt while it copies over
external_tmp_destination = '/run/user/1000/gvfs/smb-share:server=deepfreeze.local,share=deepfreeze'

# set to your final plot directory, after being copied to above, file is moved here (which is almost instantaneous)
external_final_destination = '/run/user/1000/gvfs/smb-share:server=deepfreeze.local,share=deepfreeze/plots'

# local log and stats
local_log_file = '/home/andy/chia-blockchain/chia_bot.log'
local_stat_file = '/home/andy/chia-blockchain/chia_stats.csv'

# shared log and stats, for instance if running this on multiple machines all copying to a shared network drive
master_log = external_tmp_destination + ds + 'chia_out.log'
master_stats = external_tmp_destination + ds + 'chia_stats.csv'

rx_dict = {
    'plot_size': re.compile(r'Plot size is: (?P<plot_size>.*)\n'),
    'phase_1_time': re.compile(r'Time for phase 1 = (?P<phase_1_time>.*) seconds'),
    'phase_2_time': re.compile(r'Time for phase 2 = (?P<phase_2_time>.*) seconds'),
    'phase_3_time': re.compile(r'Time for phase 3 = (?P<phase_3_time>.*) seconds'),
    'phase_4_time': re.compile(r'Time for phase 4 = (?P<phase_4_time>.*) seconds'),
    'total_time': re.compile(r'Total time = (?P<total_time>.*) seconds'),
    'out_file': re.compile(r'Renamed final file from (.*) to "' + final_dir + ds + '(?P<out_file>.*)"')
}


def main():

    init_stats_file(local_stat_file)
    init_stats_file(master_stats)
    log_file_handle = open(local_log_file, 'a')
    stat_file_handle = open(local_stat_file, 'a')
    host_name = socket.gethostname()

    no_error = True
    error = ''

    while no_error:
        print('Starting loop on ' + host_name)
        log_file_handle.write("Starting loop on " + host_name + "\n")

        cmd = 'chia plots create -k ' + plot_size + ' -b ' + buffer_size + ' -r ' + thread_count + \
              ' -t ' + tmp_dir1 + ' -2 ' + tmp_dir2 + ' -d ' + final_dir + ' | tee ' + plot_log_file
        os.system(cmd)

        results = parse_file(plot_log_file)

        if results['plot_file'] is None or results['plot_file'] == '':
            error = 'Could not parse completed plot file name from log'
            no_error = False
            continue

        try:
            log_message = 'starting final copy' + ' '.join([host_name, results['parsed_plot_size'], thread_count,
                                                            buffer_size, results['phase_1_time'],
                                                            results['phase_2_time'], results['phase_3_time'],
                                                            results['phase_4_time'], results['total_time'],
                                                            results['plot_file']])
            print(log_message)
            log_file_handle.write(log_message + "\n")
            stat_file_handle.write(', '.join([host_name, results['parsed_plot_size'], thread_count,
                                              buffer_size, results['phase_1_time'],
                                              results['phase_2_time'], results['phase_3_time'],
                                              results['phase_4_time'], results['total_time'],
                                              results['plot_file']]) + "\n")
            master_stat_handle = open(master_stats, 'a')
            master_stat_handle.write(', '.join([host_name, results['parsed_plot_size'], thread_count,
                                                buffer_size, results['phase_1_time'],
                                                results['phase_2_time'], results['phase_3_time'],
                                                results['phase_4_time'], results['total_time'],
                                                results['plot_file']]) + "\n")
            master_stat_handle.close()

            shutil.copyfile(final_dir + ds + results['plot_file'], external_tmp_destination + ds + results['plot_file'])
            print("File copied successfully.")
            log_file_handle.write("File copied successfully.\n")
            os.rename(external_tmp_destination + ds + results['plot_file'], external_final_destination + ds
                      + results['plot_file'])
            print('finished final move ' + plot_log_file)
            master_log_handle = open(master_log, 'a')
            master_log_handle.write(host_name + ' finished final move ' + plot_log_file + "\n")
            master_log_handle.close()
            log_file_handle.write('finished final move ' + plot_log_file + "\n")

            os.remove(final_dir + ds + results['plot_file'])
            log_file_handle.write("Removed local plot file " + final_dir + ds + results['plot_file'] + "\n")
            os.system('rm ' + plot_log_file)
            log_file_handle.write("Removed plot log file " + plot_log_file + "\n")

        # If source and destination are same
        except shutil.SameFileError:
            no_error = False
            error = "Source and destination represents the same file."

        # If destination is a directory.
        except IsADirectoryError:
            no_error = False
            error = "Destination is a directory."

        # If there is any permission issue
        except PermissionError:
            no_error = False
            print("Permission denied.")

        # For other errors
        except:
            no_error = False
            error = "Error occurred while copying file."

    if no_error is False:
        print('Loop exited: ' + error)
        log_file_handle.write("Loop exited: " + error + "\n")
        master_log_handle = open(master_log, 'a')
        master_log_handle.write(host_name + "Loop exited: " + error + "\n")
        master_log_handle.close()

    log_file_handle.close()
    stat_file_handle.close()


def init_stats_file(stat_file):
    if not path.exists(stat_file):
        handle = open(stat_file, 'w')
        handle.write("Host, Plot Size, Threads, Buffer Size, Phase 1, Phase 2, Phase 3, Phase 4, Total Time, Out\n")
        handle.close()


def _parse_line(line):
    for key, rx in rx_dict.items():
        match = rx.search(line)
        if match:
            return key, match
    return None, None


def parse_file(file_path):

    parsed_values = {}

    with open(file_path, 'r') as file_object:
        line = file_object.readline()
        while line:
            # at each line check for a match with a regex
            key, match = _parse_line(line)
            if match is not None:
                if key == 'plot_size':
                    parsed_values['parsed_plot_size'] = match.group('plot_size')
                elif key == 'phase_1_time':
                    parsed_values['phase_1_time'] = match.group('phase_1_time')
                elif key == 'phase_2_time':
                    parsed_values['phase_2_time'] = match.group('phase_2_time')
                elif key == 'phase_3_time':
                    parsed_values['phase_3_time'] = match.group('phase_3_time')
                elif key == 'phase_4_time':
                    parsed_values['phase_4_time'] = match.group('phase_4_time')
                elif key == 'total_time':
                    parsed_values['total_time'] = match.group('total_time')
                elif key == 'out_file':
                    parsed_values['plot_file'] = match.group('out_file')

            line = file_object.readline()

        return parsed_values


if __name__ == "__main__":
    main()
