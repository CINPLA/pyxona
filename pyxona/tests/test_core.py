import pyxona
import numpy as np
import os

current_dir = os.path.dirname(os.path.abspath(__file__))
test_data_dir = os.path.join(current_dir, "test_data")
axona_file_path = os.path.join(current_dir, "axona_raw_data/DVH_2013103103.set")


def _check_array_equal(a, b):
    if a.dtype == "<U1" and b.dtype == "<U1":
        return (a == b).all()
    else:
        return ((a == b) | (np.isnan(a) & np.isnan(b))).all()

# def test_spike_train_reader():
#     axona_file = pyxona.File(axona_file_path)
#
#     for i, channel_group in enumerate(axona_file.channel_groups):
#         times = np.load(os.path.join(test_data_dir, "spike_train_times"+str(i)+".npy"))
#         waveforms = np.load(os.path.join(test_data_dir, "spike_train_waveforms"+str(i)+".npy"))
#         assert _check_array_equal(times, channel_group.spike_train.times)
#         assert _check_array_equal(waveforms, channel_group.spike_train.waveforms)


def test_cut_data_reader():
    axona_file = pyxona.File(axona_file_path)

    for i, cut in enumerate(axona_file.cuts):
        indices = np.load(os.path.join(test_data_dir, "cut_indices"+str(i)+".npy"))
        assert _check_array_equal(indices, cut.indices)


def test_analog_signal_reader():
    axona_file = pyxona.File(axona_file_path)

    for i, analog_signal in enumerate(axona_file.analog_signals):
        signal = np.load(os.path.join(test_data_dir, "analog_signal_"+str(i)+".npy"))
        assert _check_array_equal(signal, analog_signal.signal)


def test_pos_reader():
    axona_file = pyxona.File(axona_file_path)
    positions = np.load(os.path.join(test_data_dir, "positions.npy"))
    pos_times = np.load(os.path.join(test_data_dir, "pos_times.npy"))

    assert _check_array_equal(positions, axona_file.tracking.positions)
    assert _check_array_equal(pos_times, axona_file.tracking.times)


def test_inp_reader():
    axona_file = pyxona.File(axona_file_path)

    times = np.load(os.path.join(test_data_dir, "inp_times.npy"))
    event_types = np.load(os.path.join(test_data_dir, "inp_event_type.npy"))
    values = np.load(os.path.join(test_data_dir, "inp_value.npy"))

    assert _check_array_equal(times, axona_file.inp_data.times)
    assert _check_array_equal(event_types, axona_file.inp_data.event_types)
    assert _check_array_equal(values, axona_file.inp_data.values)
