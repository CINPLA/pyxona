"""
Generates axona test files (saved as numpy arrays)
"""

import pyxona
import numpy as np
import os

current_dir = os.path.dirname(os.path.abspath(__file__))
test_data_dir = os.path.join(current_dir, "../test_data")
axona_file_path = os.path.join(current_dir, "DVH_2013103103.set")


def generate_cut_test_data():
    axona_file = pyxona.File(axona_file_path)

    for i, cut in enumerate(axona_file.cuts):
        indices = cut.indices
        np.save(os.path.join(test_data_dir, "cut_indices"+str(i)+".npy"), indices)


def generate_spike_train_test_data():
    axona_file = pyxona.File(axona_file_path)

    for i, channel_group in enumerate(axona_file.channel_groups):
        times = channel_group.spike_train.times
        waveforms = channel_group.spike_train.waveforms
        np.save(os.path.join(test_data_dir, "spike_train_times"+str(i)+".npy"), times)
        np.save(os.path.join(test_data_dir, "spike_train_waveforms"+str(i)+".npy"), waveforms)


def generate_analog_signal_test_data():
    axona_file = pyxona.File(axona_file_path)

    for i, analog_signal in enumerate(axona_file.analog_signals):
        signal = analog_signal.signal
        np.save(os.path.join(test_data_dir, "analog_signal_"+str(i)+".npy"), signal)


def generate_pos_test_data():
    axona_file = pyxona.File(axona_file_path)
    
    positions = axona_file.tracking.positions
    times = axona_file.tracking.times
    
    np.save(os.path.join(test_data_dir, "positions.npy"), positions)
    np.save(os.path.join(test_data_dir, "pos_times.npy"), times)
    

def generate_inp_test_data():
    axona_file = pyxona.File(axona_file_path)
    
    times = axona_file.inp_data.times
    event_type = axona_file.inp_data.event_type
    value = axona_file.inp_data.value
    
    np.save(os.path.join(test_data_dir, "inp_times.npy"), times)
    np.save(os.path.join(test_data_dir, "inp_event_type.npy"), event_type)
    np.save(os.path.join(test_data_dir, "inp_value.npy"), value)
    
    
def generate_axona_test_data():
    import argparse

    parser = argparse.ArgumentParser(description='Generate Axona test files')
    parser.add_argument('-f', '--force', action="store_true", default=False,
                        help='Axona raw data path')
    args = parser.parse_args()

    if(args.force is True):
        generate_pos_test_data()
        generate_analog_signal_test_data()
        generate_spike_train_test_data()
        generate_inp_test_data()
        generate_cut_test_data()
    else:
        print("use -f if you really want to regenerate test data")

    
if __name__ == "__main__":
    generate_axona_test_data()
