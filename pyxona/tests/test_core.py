# TODO write tests with an open dataset

import pyxona


def test_core():
    import getpass
    username = getpass.getuser()
    if username == "milad":
        path = "/home/milad/Dropbox/cinpla-shared/project/axonaio/2016-03-02-083928-1596/raw/02031602.set"
    elif username == "svenni":
        path = "/home/svenni/Dropbox/studies/cinpla/cinpla-shared/project/axonaio/2016-03-02-083928-1596/raw/02031602.set"
    else:
        print("Sorry, tests are not yet available.")
        return
        
    axona_file = pyxona.File(path)

    for analog_signal in axona_file.analog_signals:
        print(analog_signal)
        print(axona_file.shank(channel_id=analog_signal.channel_id))

    for shank in axona_file.shanks:
        print(shank)

    for tracking_data in axona_file.tracking:
        print(tracking_data)
