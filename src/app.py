import os
import random
import threading
import uuid

import flask


APP = flask.Flask(__name__)
METHODS = ("GET", "POST", "PUT", "PATCH", "DELETE")
GAME = {"players": {}, "buried_cards": []}
LOCK = threading.Lock()
UNICODE_CARDS = {
    "CLUBS": "\u2663",
    "DIAMONDS": "\u2666",
    "HEARTS": "\u2665",
    "SPADES": "\u2660",
}
DECK = (
    ("A", "CLUBS"),
    ("2", "CLUBS"),
    ("3", "CLUBS"),
    ("4", "CLUBS"),
    ("5", "CLUBS"),
    ("6", "CLUBS"),
    ("7", "CLUBS"),
    ("8", "CLUBS"),
    ("9", "CLUBS"),
    ("10", "CLUBS"),
    ("J", "CLUBS"),
    ("Q", "CLUBS"),
    ("K", "CLUBS"),
    ("A", "DIAMONDS"),
    ("2", "DIAMONDS"),
    ("3", "DIAMONDS"),
    ("4", "DIAMONDS"),
    ("5", "DIAMONDS"),
    ("6", "DIAMONDS"),
    ("7", "DIAMONDS"),
    ("8", "DIAMONDS"),
    ("9", "DIAMONDS"),
    ("10", "DIAMONDS"),
    ("J", "DIAMONDS"),
    ("Q", "DIAMONDS"),
    ("K", "DIAMONDS"),
    ("A", "HEARTS"),
    ("2", "HEARTS"),
    ("3", "HEARTS"),
    ("4", "HEARTS"),
    ("5", "HEARTS"),
    ("6", "HEARTS"),
    ("7", "HEARTS"),
    ("8", "HEARTS"),
    ("9", "HEARTS"),
    ("10", "HEARTS"),
    ("J", "HEARTS"),
    ("Q", "HEARTS"),
    ("K", "HEARTS"),
    ("A", "SPADES"),
    ("2", "SPADES"),
    ("3", "SPADES"),
    ("4", "SPADES"),
    ("5", "SPADES"),
    ("6", "SPADES"),
    ("7", "SPADES"),
    ("8", "SPADES"),
    ("9", "SPADES"),
    ("10", "SPADES"),
    ("J", "SPADES"),
    ("Q", "SPADES"),
    ("K", "SPADES"),
)


@APP.route("/favicon.ico", methods=("GET",))
def favicon():
    return flask.send_from_directory(
        os.path.join(APP.root_path, "static"),
        "favicon.ico",
        mimetype="image/vnd.microsoft.icon",
    )


def for_compare_cards(card):
    return DECK.index(card)


@APP.route("/player/<player_uuid>", methods=("GET",))
def player(player_uuid):
    with LOCK:
        # NOTE: Just let a `KeyError` happen here (and below).
        player = GAME["players"][player_uuid]
        name = player["name"]
        value, suit = GAME["top_card"]
        top_card = f"{value}{UNICODE_CARDS[suit]}"

        active_player_uuid = GAME["active_player"]
        active_player = GAME["players"][active_player_uuid]["name"]
        cards = [
            f"{value}{UNICODE_CARDS[suit]}"
            for value, suit in sorted(player["cards"], key=for_compare_cards)
        ]
        return flask.render_template(
            "player.html",
            name=name,
            top_card=top_card,
            active_player=active_player,
            cards=cards,
        )


@APP.route("/", defaults={"path": ""}, methods=METHODS)
@APP.route("/<path:path>", methods=METHODS)
def catch_all(path):
    return flask.jsonify({"path": path})


def start_game():
    players_str = os.environ.get("PLAYERS")
    if players_str is None:
        raise OSError("PLAYERS must be supplied")
    players = [player.strip() for player in players_str.upper().split(",")]
    num_players = len(players)
    if num_players <= 2:
        raise OSError("Must have at least two players")
    if len(set(players)) < num_players:
        raise OSError("Player names are not unique", players_str)

    with LOCK:
        reverse_map = {}
        for player in players:
            player_uuid = str(uuid.uuid4())
            reverse_map[player] = player_uuid
            GAME["players"][player_uuid] = {"name": player}
            print(f"{player_uuid} <-> {player}")

        new_deck = list(DECK)
        random.shuffle(new_deck)

        for _ in range(8):
            for player in players:
                player_uuid = reverse_map[player]
                cards = GAME["players"][player_uuid].setdefault("cards", [])
                dealt = new_deck.pop()
                cards.append(dealt)

        top_card = None
        # Bounded while loop
        for _ in range(1000):
            if top_card is not None:
                break

            top_card = new_deck.pop()
            value, _ = top_card
            if value in ("2", "4", "8"):
                new_deck.append(top_card)
                top_card = None
                random.shuffle(new_deck)

        GAME["top_card"] = top_card
        GAME["deck"] = new_deck
        GAME["active_player"] = reverse_map[players[0]]


if __name__ == "__main__":
    start_game()
    APP.run(host="0.0.0.0", port=15071, debug=True)
