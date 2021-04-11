import os
import re
import shutil
import socket

plot_size = '32'
plot_cnt = '1'
parsed_plot_size = ''
thread_count = '8'
buffer_size = '8192'
parsed_buffer_size = '8192'
phase_1_time = ''
phase_2_time = ''
phase_3_time = ''
phase_4_time = ''
total_time = ''
plot_log_file = '/home/andy/chia-blockchain/chia_out.log'
tmp_dir1 = '/media/andy/bongo/tmp'
tmp_dir2 = tmp_dir1
final_dir = tmp_dir1
external_tmp_destination = '/run/user/1000/gvfs/smb-share:server=deepfreeze.local,share=deepfreeze'
external_final_destination = '/run/user/1000/gvfs/smb-share:server=deepfreeze.local,share=deepfreeze/plots'
log_file = '/home/andy/chia-blockchain/chia_bot.log'
stat_file = '/home/andy/chia-blockchain/chia_stats.log'
plot_file = ''
ds = '/'
master_log = external_tmp_destination + ds + 'chia_out.log'
master_stats = external_tmp_destination + ds + 'chia_stats.log'

rx_dict = {
    'plot_size': re.compile(r'Plot size is: (?P<plot_size>.*)\n'),
    'thread_count': re.compile(r'Using (?P<thread_count>.*) threads\n'),
    'buffer_size': re.compile(r'Buffer size is: (?P<buffer_size>MiB.*)\n'),
    'phase_1_time': re.compile(r'Time for phase 1 = (?P<phase_1_time>.*) seconds'),
    'phase_2_time': re.compile(r'Time for phase 2 = (?P<phase_2_time>.*) seconds'),
    'phase_3_time': re.compile(r'Time for phase 3 = (?P<phase_3_time>.*) seconds'),
    'phase_4_time': re.compile(r'Time for phase 4 = (?P<phase_4_time>.*) seconds'),
    'total_time': re.compile(r'Total time = (?P<total_time>.*) seconds'),
    'out_file': re.compile(r'Renamed final file from (.*) to "' + final_dir + ds + '(?P<out_file>.*)"')
}


def main():
    no_error = True
    error = ''
    log_file_handle = open(log_file, 'a')
    stat_file_handle = open(stat_file, 'a')
    host_name = socket.gethostname()

    while no_error:
        print('Starting loop on ' + host_name)
        log_file_handle.write("Starting loop on " + host_name + "\n")

        cmd = 'chia plots create -k ' + plot_size + ' -b ' + buffer_size + ' -r ' + thread_count + \
              ' -t ' + tmp_dir1 + ' -2 ' + tmp_dir2 + ' -d ' + final_dir + ' | tee ' + plot_log_file
        os.system(cmd)

        parse_file(plot_log_file)

        if plot_file is None or plot_file == '':
            error = 'Could not parse completed plot file name from log'
            no_error = False
            continue

        try:
            log_message = 'starting final copy' + ' '.join([host_name, parsed_plot_size, thread_count,
                                                            parsed_buffer_size, phase_1_time, phase_2_time, phase_3_time,
                                                            phase_4_time, total_time, plot_file])
            print(log_message)
            log_file_handle.write(log_message + "\n")
            stat_file_handle.write(', '.join([host_name, parsed_plot_size, parsed_plot_size, thread_count,
                                              parsed_buffer_size, phase_1_time, phase_2_time, phase_3_time,
                                              phase_4_time, total_time, plot_file]) + "\n")
            master_stat_handle = open(master_stats, 'a')
            master_stat_handle.write(', '.join([host_name, parsed_plot_size, parsed_plot_size, thread_count,
                                                parsed_buffer_size, phase_1_time, phase_2_time, phase_3_time,
                                                phase_4_time, total_time, plot_file]) + "\n")
            master_stat_handle.close()

            shutil.copyfile(final_dir + ds + plot_file, external_tmp_destination + ds + plot_file)
            print("File copied successfully.")
            log_file_handle.write(log_message + "File copied successfully.\n")
            os.rename(external_tmp_destination + ds + plot_file, external_final_destination + ds + plot_file)
            print('finished final move ' + plot_log_file)
            master_log_handle = open(master_log, 'a')
            master_log_handle.write(host_name + ' finished final move ' + plot_log_file + "\n")
            master_log_handle.close()
            log_file_handle.write('finished final move ' + plot_log_file + "\n")

            os.remove(final_dir + ds + plot_file)
            log_file_handle.write("Removed local plot file " + final_dir + ds + plot_file + "\n")
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


def _parse_line(line):
    for key, rx in rx_dict.items():
        match = rx.search(line)
        if match:
            return key, match
    return None, None


def parse_file(path):
    global parsed_plot_size
    global thread_count
    global parsed_buffer_size
    global phase_1_time
    global phase_2_time
    global phase_3_time
    global phase_4_time
    global total_time
    global plot_file

    # global rx_dict
    with open(path, 'r') as file_object:
        line = file_object.readline()
        while line:
            # at each line check for a match with a regex
            key, match = _parse_line(line)
            if match is not None:
                if key == 'plot_size':
                    parsed_plot_size = match.group('plot_size')
                elif key == 'thread_count':
                    thread_count = match.group('thread_count')
                elif key == 'buffer_size':
                    parsed_buffer_size = match.group('buffer_size')
                elif key == 'phase_1_time':
                    phase_1_time = match.group('phase_1_time')
                elif key == 'phase_2_time':
                    phase_2_time = match.group('phase_2_time')
                elif key == 'phase_3_time':
                    phase_3_time = match.group('phase_3_time')
                elif key == 'phase_4_time':
                    phase_4_time = match.group('phase_4_time')
                elif key == 'total_time':
                    total_time = match.group('total_time')
                elif key == 'out_file':
                    plot_file = match.group('out_file')

            line = file_object.readline()


if __name__ == "__main__":
    main()
