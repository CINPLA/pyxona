"""
Authors: Svenn-Arne Dragly (CINPLA), Milad Hobbi Mobarhan (CINPLA)
"""

from __future__ import division
from __future__ import print_function
from __future__ import with_statement

import sys
import quantities as pq
import os
import glob
import numpy as np


def parse_attrs(text):
    attrs = {}

    for line in text.split("\n"):
        line = line.strip()

        if len(line) == 0:
            continue

        line_splitted = line.split(" ", 1)

        name = line_splitted[0]
        attrs[name] = None

        if len(line_splitted) > 1:
            try:
                attrs[name] = int(line_splitted[1])
            except:
                try:
                    attrs[name] = float(line_splitted[1])
                except:
                    attrs[name] = line_splitted[1]
    return attrs


def parse_header_and_leave_cursor(file_handle):
    header = ""
    while True:
        search_string = "data_start"
        byte = file_handle.read(1)
        header += str(byte, 'latin-1')

        if not byte:
            raise IOError("Hit end of file '" + eeg_filename + "'' before '" + search_string + "' found.")

        if header[-len(search_string):] == search_string:
            break

    attrs = parse_attrs(header)

    return attrs


def assert_end_of_data(file_handle):
    remaining_data = str(file_handle.read(), 'latin1')
    assert(remaining_data.strip() == "data_end")


def scale_analog_signal(value, gain, adc_fullscale_mv, bytes_per_sample):
    """
    Takes value as raw sample data and converts it to millivolts quantity.

    The mapping in the case of bytes_per_sample = 1 is

        [-128, 127] -> [-1.0, (127.0/128.0)] * adc_fullscale_mv / gain (mV)

    The correctness of this mapping has been verified by contacting Axona.
    """
    if type(value) is np.ndarray and value.base is not None:
        raise ValueError("Value passed to scale_analog_signal cannot be a numpy view because we need to convert the entire array to a quantity.")
    max_value = 2**(8 * bytes_per_sample - 1)  # 128 when bytes_per_sample = 1
    result = (value / max_value) * (adc_fullscale_mv / gain)
    result = result
    return result
    

class Channel:
    def __init__(self, index, name, gain):
        self.index = index
        self.name = name
        self.gain = gain


class Shank:
    def __init__(self, shank_id, filename, channels, adc_fullscale, attrs):
        self.attrs = attrs
        self.filename = filename
        self.shank_id = shank_id
        self.channels = channels
        self._spike_trains = []
        self._spike_trains_dirty = True
        self._adc_fullscale = adc_fullscale
        
    @property
    def analog_signals(self):
        return self.analog_signals
        
    @property
    def spike_trains(self):
        if self._spike_trains_dirty:
            self._read_spike_trains()
            
        return self._spike_trains
        
    def _read_spike_trains(self):
        with open(self.filename, "rb") as f:
            attrs = parse_header_and_leave_cursor(f)

            shank_index = self.shank_id
            bytes_per_timestamp = attrs.get("bytes_per_timestamp", 4)
            bytes_per_sample = attrs.get("bytes_per_sample", 1)
            num_spikes = attrs.get("num_spikes", 0)
            num_chans = attrs.get("num_chans", 1)
            samples_per_spike = attrs.get("samples_per_spike", 50)
            timebase = int(attrs.get("timebase", "96000 hz").split(" ")[0]) * pq.Hz

            bytes_per_spike_without_timestamp = samples_per_spike * bytes_per_sample
            bytes_per_spike = bytes_per_spike_without_timestamp + bytes_per_timestamp

            timestamp_dtype = ">u" + str(bytes_per_timestamp)
            waveform_dtype = "<i" + str(bytes_per_sample)

            dtype = np.dtype([("times", (timestamp_dtype, 1), 1), ("waveforms", (waveform_dtype, 1), samples_per_spike)])

            data = np.fromfile(f, dtype=dtype, count=num_spikes * num_chans)
            assert_end_of_data(f)

        times = data["times"][::4] / timebase  # time for each waveform is the same, so we take each fourth time
        waveforms = data["waveforms"]
        # TODO is this the correct way to reshape waveforms?
        waveforms = waveforms.reshape(num_spikes, num_chans, samples_per_spike)
        waveforms = waveforms.astype(float)

        channel_gain_matrix = np.ones(waveforms.shape)
        for i, channel in enumerate(self.channels):
            channel_gain_matrix[:, i, :] *= channel.gain

        waveforms = scale_analog_signal(waveforms,
                                        channel_gain_matrix,
                                        self._adc_fullscale,
                                        bytes_per_sample)

        # TODO get proper t_stop
        spike_train = SpikeTrain(
            times=times,
            waveforms=waveforms,
            spike_count=num_spikes,
            channel_count=num_chans,
            samples_per_spike=samples_per_spike,
            attrs=attrs
        )
        self._spike_trains.append(spike_train)
        self._spike_trains_dirty = False
    
    def __str__(self):
        return "<Axona shank {}: channel_count: {}>".format(
            self.shank_id, len(self.channels)
        )


class SpikeTrain:
    def __init__(self, times, waveforms, 
                 spike_count, channel_count, samples_per_spike, attrs):
        self.times = times
        self.waveforms = waveforms
        self.attrs = attrs
        
        assert(self.waveforms.shape[0] == spike_count)
        assert(self.waveforms.shape[1] == channel_count)
        assert(self.waveforms.shape[2] == samples_per_spike)
        
        self.spike_count = spike_count
        self.channel_count = channel_count
        self.samples_per_spike = samples_per_spike
        
    @property
    def num_spikes(self):
        """
        Alias for spike_count, using same name as in .[0-9]* file.
        """
        return self.spike_count

    @property
    def num_chans(self):
        """
        Alias for channel_count, using same name as in .[0-9]* file.
        """
        return self.channel_count


class AnalogSignal:
    def __init__(self, channel_id, signal, sample_rate, attrs):
        self.channel_id = channel_id
        self.signal = signal
        self.sample_rate = sample_rate
        self.attrs = attrs
        
    def __str__(self):
        return "<Axona analog signal: channel: {}, shape: {}, sample_rate: {}>".format(
            self.channel_id, self.signal.shape, self.sample_rate
        )


class TrackingData:
    def __init__(self, times, positions, attrs):
        self.attrs = attrs
        self.times = times
        self.positions = positions
        
    def __str__(self):
        return "<Axona tracking data: times shape: {}, positions shape: {}>".format(
            self.times.shape, self.positions.shape
        )


class File:
    """
    Class for reading experimental data from an Axona dataset.
    """
    def __init__(self, filename):
        self._absolute_filename = filename
        self._path, relative_filename = os.path.split(filename)
        self._base_filename, extension = os.path.splitext(relative_filename)

        if extension != ".set":
            raise ValueError("file extension must be '.set'")

        with open(self._absolute_filename, "r") as f:
            text = f.read()

        attrs = parse_attrs(text)

        self._adc_fullscale = float(attrs["ADC_fullscale_mv"]) * 1000.0 * pq.uV
        self._duration = float(attrs["duration"]) * pq.s
        self._tracked_spots_count = int(attrs["tracked_spots"])
        self.attrs = attrs
        
        self._shanks = []
        self._analog_signals = []
        self._tracking = []

        self._shanks_dirty = True
        self._spike_trains_dirty = True
        self._analog_signals_dirty = True
        self._tracking_dirty = True
        
    def shank(self, channel_id):
        if self._shanks_dirty:
            self._read_shanks()
            
        return self._channel_id_to_shank[channel_id]
        
    @property
    def shanks(self):
        if self._shanks_dirty:
            self._read_shanks()
            
        return self._shanks

    @property
    def analog_signals(self):
        if self._analog_signals_dirty:
            self._read_analog_signals()

        return self._analog_signals

    @property
    def tracking(self):
        if self._tracking_dirty:
            self._read_tracking()

        return self._tracking

    def _read_shanks(self):
        # TODO this file reading can be removed, perhaps?
        shank_filenames = glob.glob(os.path.join(self._path, self._base_filename) + ".[0-9]*")

        self._channel_id_to_shank = {}
        self._shank_id_to_shank = {}
        self._channel_count = 0
        self._shanks = []
        for shank_filename in shank_filenames:
            # increment before, because shanks start at 1
            basename, extension = os.path.splitext(shank_filename)
            shank_id = int(extension[1:])
            with open(shank_filename, "rb") as f:
                shank_attrs = parse_header_and_leave_cursor(f)
                num_chans = shank_attrs["num_chans"]
                channels = []
                for i in range(num_chans):
                    channel_id = self._channel_count + i
                    channel = Channel(
                        channel_id,
                        name="channel_{}_shank_{}_internal_{}".format(channel_id, shank_id, i),
                        gain=self._channel_gain(shank_id, channel_id)
                    )
                    channels.append(channel)

                shank = Shank(
                    shank_id,
                    filename=shank_filename,
                    channels=channels,
                    adc_fullscale=self._adc_fullscale,
                    attrs=shank_attrs
                )

                self._shanks.append(shank)
                self._shank_id_to_shank[shank_id] = shank

                for i in range(num_chans):
                    channel_id = self._channel_count + i
                    self._channel_id_to_shank[channel_id] = shank

                # increment after, because channels start at 0
                self._channel_count += num_chans

        # TODO add channels only for files that exist
        self._channel_ids = np.arange(self._channel_count)
        self._shanks_dirty = False

    def _channel_gain(self, shank_index, channel_index):
        # TODO split into two functions, one for mapping and one for gain lookup
        global_channel_index = shank_index * 4 + channel_index
        param_name = "gain_ch_{}".format(global_channel_index)
        return float(self.attrs[param_name])

    def _read_epoch():
        # TODO read epoch data?
        pass

    def _read_tracking(self):
        # TODO fix for multiple .pos files if necessary
        # TODO store attributes, such as pixels_per_metre
        self._tracking = []
        
        pos_filename = os.path.join(self._path, self._base_filename + ".pos")
        if not os.path.exists(pos_filename):
            raise IOError("'.pos' file not found:" + pos_filename)

        with open(pos_filename, "rb") as f:
            attrs = parse_header_and_leave_cursor(f)

            sample_rate_split = attrs["sample_rate"].split(" ")
            assert(sample_rate_split[1] == "hz")
            sample_rate = float(sample_rate_split[0]) * pq.Hz  # sample_rate 50.0 hz

            eeg_samples_per_position = float(attrs["EEG_samples_per_position"])  # TODO remove?
            pos_samples_count = int(attrs["num_pos_samples"])
            bytes_per_timestamp = int(attrs["bytes_per_timestamp"])
            bytes_per_coord = int(attrs["bytes_per_coord"])

            timestamp_dtype = ">i" + str(bytes_per_timestamp)
            coord_dtype = ">i" + str(bytes_per_coord)

            bytes_per_pixel_count = 4
            pixel_count_dtype = ">i" + str(bytes_per_pixel_count)

            bytes_per_pos = (bytes_per_timestamp + 2 * self._tracked_spots_count * bytes_per_coord + 8)  # pos_format is as follows for this file t,x1,y1,x2,y2,numpix1,numpix2.

            # read data:
            dtype = np.dtype([("t", (timestamp_dtype, 1)),
                              ("coords", (coord_dtype, 1), 2 * self._tracked_spots_count),
                              ("pixel_count", (pixel_count_dtype, 1), 2)])

            data = np.fromfile(f, dtype=dtype, count=pos_samples_count)
            assert_end_of_data(f)

            time_scale = float(attrs["timebase"].split(" ")[0]) * pq.Hz
            times = data["t"].astype(float) / time_scale

            length_scale = float(attrs["pixels_per_metre"]) / pq.m
            coords = data["coords"].astype(float) / length_scale
            # positions with value 1023 are missing
            for i in range(2 * self._tracked_spots_count):
                coords[np.where(data["coords"][:, i] == 1023)] = np.nan * pq.m

            tracking_data = TrackingData(
                times=times,
                positions=coords,
                attrs=attrs
            )
            
            self._tracking.append(tracking_data)
            
        self._tracking_dirty = False

    def _read_analog_signals(self):
        # TODO read for specific channel

        # TODO check that .egf file exists

        self._analog_signals = []
        eeg_basename = os.path.join(self._path, self._base_filename)
        eeg_files = glob.glob(eeg_basename + ".eeg")
        eeg_files += glob.glob(eeg_basename + ".eeg[0-9]*")
        eeg_files += glob.glob(eeg_basename + ".egf")
        eeg_files += glob.glob(eeg_basename + ".egf[0-9]*")
        for eeg_filename in sorted(eeg_files):
            extension = os.path.splitext(eeg_filename)[-1][1:]
            file_type = extension[:3]
            suffix = extension[3:]
            if suffix == "":
                suffix = "1"
            suffix = int(suffix)
            with open(eeg_filename, "rb") as f:
                attrs = parse_header_and_leave_cursor(f)
                attrs["raw_filename"] = eeg_filename

                if file_type == "eeg":
                    sample_count = int(attrs["num_EEG_samples"])
                elif file_type == "egf":
                    sample_count = int(attrs["num_EGF_samples"])
                else:
                    raise IOError("Unknown file type. Should be .eeg or .efg.")

                sample_rate_split = attrs["sample_rate"].split(" ")
                bytes_per_sample = attrs["bytes_per_sample"]
                assert(sample_rate_split[1].lower() == "hz")
                sample_rate = float(sample_rate_split[0]) * pq.Hz  # sample_rate 250.0 hz

                sample_dtype = (('<i' + str(bytes_per_sample), 1), attrs["num_chans"])
                data = np.fromfile(f, dtype=sample_dtype, count=sample_count)
                assert_end_of_data(f)

                eeg_final_channel_id = self.attrs["EEG_ch_" + str(suffix)]
                eeg_mode = self.attrs["mode_ch_" + str(eeg_final_channel_id)]
                ref_id = self.attrs["b_in_ch_" + str(eeg_final_channel_id)]
                eeg_original_channel_id = self.attrs["ref_" + str(ref_id)]

                attrs["channel_id"] = eeg_original_channel_id

                gain = self.attrs["gain_ch_{}".format(eeg_final_channel_id)]

                signal = scale_analog_signal(data,
                                             gain,
                                             self._adc_fullscale,
                                             bytes_per_sample)

                # TODO read start time

                analog_signal = AnalogSignal(
                    channel_id=eeg_original_channel_id,
                    signal=signal,
                    sample_rate=sample_rate,
                    attrs=attrs
                )

                self._analog_signals.append(analog_signal)
                
        self._analog_signals_dirty = False
