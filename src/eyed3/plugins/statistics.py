# -*- coding: utf-8 -*-
################################################################################
#  Copyright (C) 2009  Travis Shirk <travis@pobox.com>
#
#  This program is free software; you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation; either version 2 of the License, or
#  (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software
#  Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA
#
################################################################################
from __future__ import print_function
import sys, os, operator
from collections import Counter

from eyed3 import id3
from eyed3.utils import guessMimetype
from eyed3.utils.cli import printMsg, printError
from eyed3.plugins import LoaderPlugin

ID3_VERSIONS = [id3.ID3_V1_0, id3.ID3_V1_1,
                id3.ID3_V2_2, id3.ID3_V2_3, id3.ID3_V2_4]

_OP_STRINGS = {operator.le: "<=",
               operator.lt: "< ",
               operator.ge: ">=",
               operator.gt: "> ",
               operator.eq: "= ",
               operator.ne: "!=",
              }


class StatisticsPlugin(LoaderPlugin):
    NAMES = ['stats']
    SUMMARY = u"Computes statistics for all audio files scanned."

    def __init__(self, arg_parser):
        super(StatisticsPlugin, self).__init__(arg_parser)

        self.file_counter = Counter(total=0, audio=0, hidden=0)

        self.id3_version_counter = Counter()
        for v in ID3_VERSIONS:
            self.id3_version_counter[v] = 0

        self.bitrates = Counter(cbr=0, vbr=0)
        self.bitrate_keys = [(operator.le, 96),
                             (operator.le, 112),
                             (operator.le, 128),
                             (operator.le, 160),
                             (operator.le, 192),
                             (operator.le, 256),
                             (operator.le, 320),
                             (operator.gt, 320),
                            ]
        for k in self.bitrate_keys:
            self.bitrates[k] = 0

        self.mts = Counter()

    def handleFile(self, f):
        super(StatisticsPlugin, self).handleFile(f)

        self.file_counter["total"] += 1
        if self.audio_file:
            self.file_counter["audio"] += 1
        if os.path.basename(f).startswith('.'):
            self.file_counter["hidden"] += 1

        # mimetype stats
        mt = guessMimetype(f)
        if mt in self.mts:
            self.mts[mt] += 1
        else:
            self.mts[mt] = 1

        if self.audio_file and self.audio_file.tag:
            # ID3 versions
            id3_version = self.audio_file.tag.version
            self.id3_version_counter[id3_version] += 1
            sys.stdout.write('.')
            sys.stdout.flush()

            # mp3 bit rates
            vbr, br =  self.audio_file.info.bit_rate
            if vbr:
                self.bitrates["vbr"] += 1
            else:
                self.bitrates["cbr"] += 1
            for key in self.bitrate_keys:
                key_op, key_br = key
                if key_op(br, key_br):
                    self.bitrates[key] += 1
                    break

    def handleDone(self):
        print("\nAnalyzed %d files (%d audio, %d non-audio, %d hidden)" %
              (self.file_counter["total"], self.file_counter["audio"],
               (self.file_counter["total"] - self.file_counter["audio"]),
               self.file_counter["hidden"]))

        if not self.file_counter["total"]:
            return

        printMsg("\nMime-types:")
        types = list(self.mts.keys())
        types.sort()
        for t in types:
            count = self.mts[t]
            percent = (float(count) / float(self.file_counter["total"])) * 100
            printMsg("\t%s:%s (%%%.2f)" % (str(t).ljust(12),
                                           str(count).rjust(8),
                                           percent))

        print("\nMP3 bitrates:")
        for key in ["cbr", "vbr"]:
            val = self.bitrates[key]
            print("\t%s   : %d \t%.2f%%" %
                  (key, val,
                   (float(val) / float(self.file_counter["audio"])) * 100))

        for key in self.bitrate_keys:
            val = self.bitrates[key]
            key_op, key_br = key
            print("\t%s%03d : %d \t%.2f%%" %
                  (_OP_STRINGS[key_op], key_br, val,
                   (float(val) / float(self.file_counter["audio"])) * 100))

        print("\nID3 versions:")
        for v in ID3_VERSIONS:
            v_count = self.id3_version_counter[v]
            v_percent = (float(v_count) /
                         float(self.file_counter["audio"])) * 100
            print("\t%s : %d \t%.2f%%" % (id3.versionToString(v),
                                          v_count, v_percent))


