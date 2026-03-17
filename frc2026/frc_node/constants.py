class MatchConstants:
    # Periods (Seconds)
    AUTO_DURATION = 20
    TRANSITION_DURATION = 3
    TELEOP_TOTAL = 140

    # Manual 5.9.1 Shift Milestones (Relative to Teleop Start)
    # Format: { Milestone_Second: Sound_Key }
    TELEOP_SHIFTS = {
        10:  "SHIFT",
        35:  "SHIFT",
        60:  "SHIFT",
        85:  "SHIFT",
        110: "WHISTLE",
        140: "ENDGAME"
    }

    # ToDo: the following constants are not used yet
    # Broadcast Templates
    MSG_SCORE_UPDATE = "SCORE_UPDATE:{alliance}:{value}"
    MSG_SET_SHIFT    = "SET_SHIFT:{index}"
    MSG_PLAY_SOUND   = "PLAY:{key}"
    MSG_AUTO_RESULT  = "AUTO_RESULT:{winner}"
    
    # Hub Specific
    MSG_HUB_SCORE    = "HUB_SCORE:{alliance}:{value}"
    MSG_HUB_ACK      = "ACK_AUTO_SCORE"
