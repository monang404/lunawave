class WSAction:
    # Auth
    AUTH = "auth"
    LOGOUT = "logout"
    # Playback Actions
    PLAY_TRACK = "play_track"
    TOGGLE_PAUSE = "toggle_pause"
    NEXT = "next"
    PREV = "prev"
    STOP = "stop"
    SEEK = "seek"

    # Queue Actions
    QUEUE_SELECT = "queue_select"
    QUEUE_REMOVE = "queue_remove"
    QUEUE_ADD = "queue_add"
    QUEUE_REORDER = "queue_reorder"
    ENQUEUE_ARTIST_SONGS = "enqueue_artist_songs"
    ENQUEUE_GENRE_SONGS = "enqueue_genre_songs"

    # Radio Actions
    RADIO_RANDOMIZE = "radio_randomize"

    # Settings Actions
    VOLUME_UP = "volume_up"
    VOLUME_DOWN = "volume_down"
    VOLUME_SET = "volume_set"
    SET_MODE = "set_mode"
    SET_OUTPUT = "set_output"
    SET_SPONSORBLOCK = "set_sponsorblock"
    LYRICS_OFFSET = "lyrics_offset"

    # Download Actions
    DOWNLOAD = "download"
    DELETE_DOWNLOAD = "delete_download"

    # Discover Actions
    SEARCH = "search"
    DISCOVER = "discover"
    TOGGLE_FAVORITE = "toggle_favorite"
