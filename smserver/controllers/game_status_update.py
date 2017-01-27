#!/usr/bin/env python3
# -*- coding: utf8 -*-

import datetime

from smserver import models
from smserver.smutils import smpacket
from smserver.stepmania_controller import StepmaniaController
from smserver.chathelper import with_color

class GameStatusUpdateController(StepmaniaController):
    command = smpacket.SMClientCommand.NSCGSU
    require_login = False

    def handle(self):
        if not self.conn.room:
            return

        if "start_at" not in self.conn.songstats:
            return
        stats = {"time": datetime.datetime.now() - self.conn.songstats.get("start_at"),
                 "stepid": self.packet["step_id"],
                 "grade": self.packet["grade"],
                 "score": self.packet["score"],
                 "combo": self.packet["combo"],
                 "health": self.packet["health"],
                 "offset": self.packet["offset"],
                 "note_size": self.packet["note_size"]
                }
        with self.conn.mutex:
            pid = self.packet["player_id"]
            best_score = self.conn.songstats[pid]["best_score"]


            offset = float(stats["offset"]) / 2000.0 - 16.384
            self.conn.songstats[pid]["offsetacum"] += offset
            if self.conn.stepmania_version < 3:
                stats["stepid"] += 2
                
            if not stats["note_size"] or stats["note_size"] <= 0:
                notesize = self.notesize(stats["combo"], self.conn.songstats[pid]["data"])
            else:
                notesize = stats["note_size"]

            if stats["stepid"] > 3 and stats["stepid"] < 9:
                stats["stepid"] = self.get_stepid(offset)
                self.conn.songstats[pid]["taps"] += 1
                if notesize > 1:
                    self.conn.songstats[pid]["jumps"] += 1
                    if notesize > 2:
                        self.conn.songstats[pid]["hands"] += 1

            if stats["stepid"] == 4 or stats["stepid"] == 5:
                self.conn.songstats[pid]["perfect_combo"] = 0
            elif stats["stepid"] == 7 or stats["stepid"] == 8:
                self.conn.songstats[pid]["perfect_combo"] += notesize
            elif stats["stepid"] == 6:
                self.conn.songstats[pid]["perfect_combo"] = 0
            elif stats["stepid"] == 10 or stats["stepid"] == 9:
                self.conn.songstats[pid]["holds"] += 1
            elif stats["stepid"] == 3 :
                self.conn.songstats[pid]["perfect_combo"] = 0
                self.conn.songstats[pid]["taps"] += 1
                if notesize > 1:
                    self.conn.songstats[pid]["jumps"] += 1
                    if notesize > 2:
                        self.conn.songstats[pid]["hands"] += 1

            self.conn.songstats[pid]["data"].append(stats)
            self.conn.songstats[pid]["dp"] += self.dp(stats["stepid"])
            self.conn.songstats[pid]["migsp"] += self.migsp(stats["stepid"])
            self.conn.songstats["data"]["grade"] = self.grade(self.conn.songstats[pid]["dp"] / (self.conn.songstats[pid]["taps"]*2))

            if best_score and self.conn.songstats[pid]["migsp"] > best_score:
                self.conn.songstats[self.packet["player_id"]]["best_score"] = None
                self.beat_best_score()

            if self.conn.songstats[pid]["perfect_combo"] != 0 and self.conn.songstats[pid]["perfect_combo"] % 250 == 0:
                self.conn.songstats[pid]["toasties"] += 1

    def beat_best_score(self):
        user = [user for user in self.users if user.pos == self.packet["player_id"]][0]

        message = "%s just beat the best score on %s(%s)" % (
            user.name,
            models.SongStat.DIFFICULTIES.get(self.conn.songstats[self.packet["player_id"]]["difficulty"]),
            self.conn.songstats[self.packet["player_id"]]["feet"]
        )

        self.sendroom(self.conn.room, smpacket.SMPacketServerNSCSU(message=message))


    def get_stepid(self, offset):
        smarv  = 0.02259;
        sperf  = 0.04509;
        sgreat = 0.09009;
        sgood  = 0.13509;
        sboo   = 0.18909;
        if (offset < smarv) and (offset > (smarv * -1.0)):
            return 8
        elif (offset < sperf) and (offset > (sperf * -1.0)):
            return 7
        elif (offset < sgreat) and (offset > (sgreat * -1.0)):
            return 6
        elif (offset < sgood) and (offset > (sgood * -1.0)):
            return 5
        else:
            return 4


    def dp(self, stepsid):
        if stepsid == 8 or stepsid == 7:
            return 2
        elif stepsid == 6:
            return 1
        elif stepsid == 5:
            return 0
        elif stepsid == 4:
            return -4
        elif stepsid == 3:
            return -8
        elif stepsid == 10:
            return 6
        else:
            return 0

    def migsp(self, stepsid):
        if stepsid == 8:
            return 3
        elif stepsid == 7:
            return 2
        elif stepsid == 6:
            return 1
        elif stepsid == 5:
            return 0
        elif stepsid == 4:
            return -4
        elif stepsid == 3:
            return -8
        elif stepsid == 10:
            return 6
        else:
            return 0


    def notesize(self, combo, data):
        if len(data) > 0:
            if combo > 0:
                return combo - data[-1]["combo"]
            else:
                return 1
        else:
            return 1


    def grade(self, score, data):
        if score >= 100.00:
            for note in data:
                if note["stepid"] > 2 and note["stepid"] < 9:
                    if note != 8:
                        return 1
            return 0
        elif score >= 93.00:
            return 2
        elif score >= 80.00:
            return 3
        elif score >= 65.00:
            return 4
        elif score >= 45.00:
            return 5
        return 6
