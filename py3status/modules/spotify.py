# -*- coding: utf-8 -*-
"""
Display information about the current song playing on Spotify.

Configuration parameters:
    cache_timeout: how often to update the bar
    format: see placeholders below
    format_down: define output if spotify is not running
    format_stopped: define output if spotify is not playing

Format of status string placeholders:
    {album} album name
    {artist} artiste name (first one)
    {time} time duration of the song
    {title} name of the song

Color options:
    color_offline: Spotify is not running, defaults to color_bad
    color_paused: Song is stopped or paused, defaults to color_degraded
    color_playing: Song is playing, defaults to color_good

i3status.conf example:

```
spotify {
    format = "{title} by {artist} -> {time}"
    format_down = "no Spotify"
}
```

Requires:
        spotify (>=1.0.27.71.g0a26e3b2)

@author Pierre Guilbert, Jimmy Garpehäll, sondrele, Andrwe
"""

from datetime import timedelta
from time import time
import dbus


class Py3status:
    """
    """
    # available configuration parameters
    cache_timeout = 5
    format = '{artist} : {title}'
    format_down = 'Spotify not running'
    format_stopped = 'Spotify stopped'

    def _get_text(self):
        """
        Get the current song metadatas (artist - title)
        """
        bus = dbus.SessionBus()
        try:
            self.__bus = bus.get_object('org.mpris.MediaPlayer2.spotify',
                                        '/org/mpris/MediaPlayer2')
            self.player = dbus.Interface(
                self.__bus, 'org.freedesktop.DBus.Properties')

            try:
                metadata = self.player.Get('org.mpris.MediaPlayer2.Player',
                                           'Metadata')
                album = metadata.get('xesam:album')
                artist = metadata.get('xesam:artist')[0]
                microtime = metadata.get('mpris:length')
                rtime = str(timedelta(microseconds=microtime))[:-7]
                title = metadata.get('xesam:title')
                playback_status = self.player.Get(
                    'org.mpris.MediaPlayer2.Player', 'PlaybackStatus'
                )
                if playback_status.strip() == 'Playing':
                    color = self.py3.COLOR_PLAYING or self.py3.COLOR_GOOD
                else:
                    color = self.py3.COLOR_PAUSED or self.py3.COLOR_DEGRADED
            except Exception:
                return (
                    self.format_stopped,
                    self.py3.COLOR_PAUSED or self.py3.COLOR_DEGRADED)

            return (
                self.format.format(title=title,
                                   artist=artist,
                                   album=album,
                                   time=rtime), color)
        except Exception:
            return (
                self.format_down,
                self.py3.COLOR_OFFLINE or self.py3.COLOR_BAD)

    def spotify(self):
        """
        Get the current "artist - title" and return it.
        """
        (text, color) = self._get_text()
        response = {
            'cached_until': time() + self.cache_timeout,
            'full_text': text,
            'color': color
        }
        return response


if __name__ == "__main__":
    """
    Run module in test mode.
    """
    from py3status.module_test import module_test
    module_test(Py3status)
