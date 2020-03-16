import os
import random
import threading
import uuid

import flask


PORT = 15071
APP = flask.Flask(__name__)
METHODS = ("GET", "POST", "PUT", "PATCH", "DELETE")
GAME = {
    "players": {},
    "buried_cards": [],
    "all_moves": [],
    "active_value": "",
    "active_suit": "",
    "consecutive_draw2": 0,
    "consecutive_skip4": 0,
    "winner": None,
}
LOCK = threading.Lock()
UNICODE_CARDS = {
    "CLUBS": "\u2663",
    "DIAMONDS": "\u2666",
    "SPADES": "\u2660",
    "HEARTS": "\u2665",
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
)


@APP.route("/favicon.ico", methods=("GET",))
def favicon():
    return flask.send_from_directory(
        os.path.join(APP.root_path, "static"),
        "favicon.ico",
        mimetype="image/vnd.microsoft.icon",
    )


@APP.route("/admin", methods=("GET",))
def admin():
    players = []
    for player_uuid, player in GAME["players"].items():
        url = f"/player/{player_uuid}"
        name = player["name"]
        players.append((name, url))

    return flask.render_template("admin.html", players=players)


def for_compare_cards(card):
    return DECK.index(card)


def can_play(card, player_uuid):
    # NOTE: This assumes the deck is locked.
    if player_uuid != GAME["active_player"]:
        return False

    value, suit = card

    # If a 4, need to check first if there is an active "skip streak" open.
    if GAME["active_value"] == "4" and GAME["consecutive_skip4"] > 0:
        return value == "4"

    # If a 2, need to check first if there is an active "draw 2 streak" open.
    if GAME["active_value"] == "2" and GAME["consecutive_draw2"] > 0:
        return value == "2"

    if value == "8":
        return True

    # If an 8 is showing, only the suit can match.
    if GAME["active_value"] == "8":
        return suit == GAME["active_suit"]

    return value == GAME["active_value"] or suit == GAME["active_suit"]


@APP.route("/player/<player_uuid>", methods=("GET",))
def player(player_uuid):
    with LOCK:
        # NOTE: Just let a `KeyError` happen here (and below).
        player = GAME["players"][player_uuid]
        name = player["name"]
        winner = GAME["winner"]
        if winner is not None:
            return flask.render_template(
                "over.html", name=name, winner=winner,
            )

        top_card_value, top_card_suit = GAME["top_card"]
        top_card_display = f"{top_card_value}{UNICODE_CARDS[top_card_suit]}"

        active_player_uuid = GAME["active_player"]
        active_player = GAME["players"][active_player_uuid]["name"]

        moves = []
        for card in sorted(player["cards"], key=for_compare_cards):
            value, suit = card
            as_display = f"{value}{UNICODE_CARDS[suit]}"
            can_play_here = can_play(card, player_uuid)
            if can_play_here and value == "8":
                for new_suit in ("CLUBS", "DIAMONDS", "SPADES", "HEARTS"):
                    extended = f"{as_display} becomes {new_suit}"
                    action = f"CHANGE-{new_suit}"
                    moves.append((suit, action, extended, True))
            else:
                moves.append((value, suit, as_display, can_play_here))

        if active_player_uuid == player_uuid:
            if GAME["consecutive_skip4"] > 0:
                moves.append(("0", "TAKESKIP", "Take Skip", True),)
            else:
                if GAME["consecutive_draw2"] > 0:
                    amount = 2 * GAME["consecutive_draw2"]
                    moves.append(
                        (str(amount), "DRAW", f"Draw {amount}", True),
                    )
                else:
                    moves.append(("1", "DRAW", "Draw 1", True),)

        return flask.render_template(
            "player.html",
            name=name,
            recent_moves=list(reversed(GAME["all_moves"][-3:])),
            top_card_suit=top_card_suit,
            top_card=top_card_display,
            active_player=active_player,
            moves=moves,
            player_uuid=player_uuid,
        )


@APP.route("/play/<player_uuid>/<value>/<action>", methods=("POST",))
def play(player_uuid, value, action):
    for change_suit in ("CLUBS", "DIAMONDS", "SPADES", "HEARTS"):
        target_action = f"CHANGE-{change_suit}"
        if action == target_action:
            with LOCK:
                # TODO: Check if a winner (here and elsewhere).

                if player_uuid != GAME["active_player"]:
                    raise RuntimeError(
                        "Only active player can play an 8 change",
                        player_uuid,
                        GAME["active_player"],
                    )

                old_suit = value
                if old_suit not in ("CLUBS", "DIAMONDS", "SPADES", "HEARTS"):
                    raise RuntimeError("Old suit invalid", old_suit)

                card = ("8", old_suit)
                if not can_play(card, player_uuid):
                    raise RuntimeError(
                        "Card cannot be played on top card for current player",
                        card,
                        GAME["top_card"],
                        player_uuid,
                    )

                top_card = GAME["top_card"]
                GAME["buried_cards"].append(top_card)
                GAME["top_card"] = card
                GAME["active_value"] = ""
                GAME["active_suit"] = change_suit
                player = GAME["players"][player_uuid]
                player["cards"].remove(card)
                GAME["active_player"] = player["next"]
                name = player["name"]
                as_display = f"8{UNICODE_CARDS[old_suit]}"
                GAME["all_moves"].append(
                    (
                        f"{name} changed to {change_suit} with",
                        as_display,
                        old_suit,
                    )
                )
                if not player["cards"]:
                    GAME["winner"] = name

                return flask.redirect(f"/player/{player_uuid}")

    if action == "TAKESKIP":
        with LOCK:
            if player_uuid != GAME["active_player"]:
                raise RuntimeError(
                    "Only active player can take a skip",
                    player_uuid,
                    GAME["active_player"],
                )

            if value != "0":
                raise RuntimeError("Take skip value should be 0", value)

            if GAME["consecutive_skip4"] == 0:
                raise RuntimeError("Must have active skip streak")

            player = GAME["players"][player_uuid]
            name = player["name"]
            GAME["all_moves"].append((f"{name} got", "skipped", ""),)
            GAME["consecutive_skip4"] = 0
            GAME["active_player"] = player["next"]

            return flask.redirect(f"/player/{player_uuid}")

    if action == "DRAW":
        with LOCK:
            if player_uuid != GAME["active_player"]:
                raise RuntimeError(
                    "Only active player can draw",
                    player_uuid,
                    GAME["active_player"],
                )

            player = GAME["players"][player_uuid]
            name = player["name"]
            if value == "1":
                if GAME["consecutive_draw2"] != 0:
                    raise RuntimeError(
                        "Invalid draw amount", value, GAME["consecutive_draw2"]
                    )

                drawn_card = GAME["deck"].pop()
                player["cards"].append(drawn_card)
                GAME["all_moves"].append((f"{name} drew", "a card", ""),)
            else:
                int_value = int(value)
                if int_value != 2 * GAME["consecutive_draw2"]:
                    raise RuntimeError(
                        "Invalid draw amount", value, GAME["consecutive_draw2"]
                    )
                for _ in range(int_value):
                    drawn_card = GAME["deck"].pop()
                    player["cards"].append(drawn_card)
                GAME["all_moves"].append(
                    (f"{name} drew", f"{value} cards", ""),
                )
                GAME["consecutive_draw2"] = 0

            GAME["active_player"] = player["next"]

            return flask.redirect(f"/player/{player_uuid}")

    suit = action
    card = value, suit
    if card not in DECK:
        raise RuntimeError("Invalid card", card)

    with LOCK:
        # NOTE: Just let a `KeyError` happen here (and below).
        player = GAME["players"][player_uuid]
        if card not in player["cards"]:
            raise RuntimeError("Player does not hold card", player, card)

        if not can_play(card, player_uuid):
            raise RuntimeError(
                "Card cannot be played on top card for current player",
                card,
                GAME["top_card"],
                player_uuid,
            )

        top_card = GAME["top_card"]
        GAME["buried_cards"].append(top_card)
        GAME["top_card"] = card
        GAME["active_value"] = value
        if value == "2":
            GAME["consecutive_draw2"] += 1
        if value == "4":
            GAME["consecutive_skip4"] += 1
        GAME["active_suit"] = suit
        player["cards"].remove(card)
        name = player["name"]
        if not player["cards"]:
            GAME["winner"] = name

        GAME["active_player"] = player["next"]
        as_display = f"{value}{UNICODE_CARDS[suit]}"
        GAME["all_moves"].append((f"{name} played", as_display, suit),)

        return flask.redirect(f"/player/{player_uuid}")


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

        for i, player in enumerate(players):
            player_uuid = reverse_map[player]
            next_index = (i + 1) % len(players)
            next_player_uuid = reverse_map[players[next_index]]
            GAME["players"][player_uuid]["next"] = next_player_uuid

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
        top_card_value, top_card_suit = top_card
        GAME["active_value"] = top_card_value
        GAME["active_suit"] = top_card_suit
        GAME["deck"] = new_deck
        GAME["active_player"] = reverse_map[players[0]]


if __name__ == "__main__":
    start_game()
    APP.run(host="0.0.0.0", port=PORT, debug=True)
