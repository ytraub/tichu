import resources from "./resources.js";
import { CARD_MAP, ORIGIN_CARD_WIDTH, ORIGIN_CARD_HEIGHT } from "./cards.js";

const CANVAS_WIDTH = 800
const CANVAS_HEIGHT = 800

const CARD_WIDTH = 48
const CARD_HEIGHT = 64
const CARD_PADDING = 5
const CARD_BORDER = 2

const BACKSIDE_WIDTH = CARD_WIDTH * 0.7
const BACKSIDE_HEIGHT = CARD_HEIGHT * 0.7
const BACKSIDE_PADDING = CARD_PADDING * 0.7

const PADDING = 20

const SOCKET_PORT = 5400

class Game {
    constructor() {
        this.schupfenMode = undefined;
        this.schupfen = { "left": undefined, "team": undefined, "right": undefined }

        this.cards = undefined;
        this.backside = undefined;
        this.backsideVertical = undefined;

        this.state = undefined;
        this.hand = undefined;
        this.id = undefined;
        this.entityKeys = undefined;

        this.selfPublicState = undefined;
        this.matePublicState = undefined;
        this.leftOpponentPublicState = undefined;
        this.rightOpponentPublicState = undefined;

        this.gameState = undefined;
        this.teams = undefined;
        this.entityAtMoveKeys = undefined;
        this.entityAtMoveId = undefined;
        this.discardPile = undefined;

        this.debugMode = false;

        this.selectedCards = new Set();

        this.socket = new WebSocket(`ws://localhost:${SOCKET_PORT}`);

        this.socket.onopen = (event) => this.onSocketOpen(event);
        this.socket.onmessage = (event) => this.onSocketMessage(event);
        this.socket.onclose = (event) => this.onSocketClose(event);
        this.socket.onerror = (event) => this.onSocketError(event);

        this.canvas = document.getElementById("canvas");
        this.ctx = this.canvas.getContext("2d");

        this.lobbyButtons = document.getElementById("lobby_buttons");
        this.schupfenButtons = document.getElementById("schupfen_buttons");
        this.playingButtons = document.getElementById("playing_buttons");

        this.schupfenRightOpponentButton = document.getElementById("schupfen_right_opponent_btn");
        this.schupfenRightOpponentButton.onclick = () => this.schupfenMode = "right"
        this.schupfenTeammateButton = document.getElementById("schupfen_teammate_btn");
        this.schupfenTeammateButton.onclick = () => this.schupfenMode = "team"
        this.schupfenLeftOpponentButton = document.getElementById("schupfen_left_opponent_btn");
        this.schupfenLeftOpponentButton.onclick = () => this.schupfenMode = "left"

        this.schupfenSubmitButton = document.getElementById("schupfen_submit");

        this.startGameButton = document.getElementById("start_game_btn");
        this.startGameButton.onclick = (event) => this.startGame(event);

        this.playCardButton = document.getElementById("play_cards_btn");
        this.playCardButton.onclick = (event) => this.onPlayCards(event);

        this.passButton = document.getElementById("pass_btn");
        this.passButton.onclick = (event) => this.onPass(event);

        this.sortByValueButton = document.getElementById("sort_by_value_btn");
        this.sortByValueButton.onclick = (event) => this.onSortByValue(event);
        this.sortByColorButton = document.getElementById("sort_by_color_btn");
        this.sortByColorButton.onclick = (event) => this.onSortByColor(event);

        this.sortByFn = this.sortHandByValue

        this.teamsDebug = document.getElementById("teams_debug")
        this.entityAtMoveKeysDebug = document.getElementById("entity_at_move_keys_debug")
    }

    async onSocketOpen(event) {
        console.log("Connected");
    }

    handlePublicState(entities) {
        this.matePublicState = null;
        this.leftOpponentPublicState = null;
        this.rightOpponentPublicState = null;

        const { team_key: selfTeamKey, entity_key: selfPlayerKey } = this.entityKeys;

        const matePlayerKey = selfPlayerKey === "a" ? "b" : "a";
        const opponentTeamKey = selfTeamKey === "a" ? "b" : "a";

        const leftOpponentPlayerKey = selfPlayerKey === "a"
            ? (selfTeamKey === "a" ? "b" : "a")
            : (selfTeamKey === "a" ? "a" : "b");

        const rightOpponentPlayerKey = selfPlayerKey === "a"
            ? (selfTeamKey === "a" ? "a" : "b")
            : (selfTeamKey === "a" ? "b" : "a");

        for (const entity of entities) {
            const { team_key, entity_key } = entity;

            if (team_key === selfTeamKey && entity_key === matePlayerKey) {
                this.matePublicState = entity;
            } else if (team_key === opponentTeamKey && entity_key === leftOpponentPlayerKey) {
                this.leftOpponentPublicState = entity;
            } else if (team_key === opponentTeamKey && entity_key === rightOpponentPlayerKey) {
                this.rightOpponentPublicState = entity;
            }
        }
    }

    async onSocketMessage(event) {
        const state = JSON.parse(event.data);
        this.state = state;

        this.hand = state.player.hand;
        this.id = state.player.id;
        this.entityKeys = { team_key: state.player.team_key, player_key: state.player.entity_key }

        this.gameState = state.game.game_state;
        this.teams = state.game.teams;
        this.entityAtMoveKeys = state.game.entity_at_move_keys;
        this.entityAtMoveId = state.game.entity_at_move_id;
        this.discardPile = state.game.discard_pile;
        this.currentCombination = state.game.current_combination;

        this.handlePublicState(state.game.public)
        this.sortByFn()

        this.gameLoop()
    }

    async onSocketClose(event) {
        console.log("Disconnected");
    }

    async onSocketError(event) {
        console.error(event);
    }

    async onPlayCards(event) {
        const payload = {
            "played_cards": Array.from(this.selectedCards)
        }

        this.socket.send(JSON.stringify(payload))
        this.selectedCards.clear()
    }

    async onPass(event) {
        const payload = {
            "pass": true
        }

        this.socket.send(JSON.stringify(payload))
    }

    async onSubmitSchupfen(event) {

    }

    onSortByValue(event) {
        this.sortByFn = this.sortHandByValue
    }

    onSortByColor(event) {
        this.sortByFn = this.sortHandByColor
    }

    sortHandByValue(event) {
        if (!this.state) return;

        this.hand.sort((a, b) => CARD_MAP.get(a).value - CARD_MAP.get(b).value)
    }

    sortHandByColor(event) {
        if (!this.state) return;

        this.hand.sort((a, b) => {
            const card_a = CARD_MAP.get(a)
            const card_b = CARD_MAP.get(b)

            const cmp = card_a.color.localeCompare(card_b.color)

            if (cmp == 0) {
                return card_a.value - card_b.value
            }

            return cmp
        })
    }

    async startGame(event) {
        const payload = {
            "ready": true
        }

        this.socket.send(JSON.stringify(payload))
    }

    debug() {
        const { a, b } = this.teams;

        this.teamsDebug.innerText =
            `Team A: ${JSON.stringify(a, null, 2)}\n` +
            `Team B: ${JSON.stringify(b, null, 2)}`;


        this.entityAtMoveKeysDebug.innerText = this.entityAtMoveKeys;
    }

    async init() {
        const [cards] = await resources.load("/img/cards.png");
        this.cards = cards;

        const [backside] = await resources.load("/img/backside.png");
        this.backside = backside;

        const [backside_vertical] = await resources.load("/img/backside_vertical.png");
        this.backsideVertical = backside_vertical;

        this.canvas.height = CANVAS_HEIGHT;
        this.canvas.width = CANVAS_WIDTH;

        this.discardPileCenter = {
            x: this.canvas.width / 2,
            y: this.canvas.height / 2
        }

        this.playerHandCenter = {
            x: this.canvas.width / 2,
            y: this.canvas.height - 50 - PADDING
        };

        this.mateHandCenter = {
            x: this.canvas.width / 2,
            y: 50 + PADDING
        }

        this.leftOpponentHandCenter = {
            x: 50 + PADDING,
            y: this.canvas.height / 2
        }

        this.rightOpponentHandCenter = {
            x: this.canvas.width - 50 - PADDING,
            y: this.canvas.height / 2
        }

        this.initInput();

        /* requestAnimationFrame((time) => {
            this.gameLoop(time);
        }); */
    }

    initInput() {
        this.canvas.addEventListener("click", (event) => {
            this.onCanvasClick(event);
        });
    }

    onCanvasClick(event) {
        const rect = this.canvas.getBoundingClientRect();

        const x = event.clientX - rect.left;
        const y = event.clientY - rect.top;

        const card = this.getCardAt(x, y);

        if (card) {
            const { id } = card;

            if (this.selectedCards.has(id)) {
                this.selectedCards.delete(id)
            } else {
                this.selectedCards.add(id, CARD_MAP.get(id))
            }
        }

        console.log(this.selectedCards)
    }

    gameLoop(time) {
        this.update();
        this.render();

        /* requestAnimationFrame((time) => {
            this.gameLoop(time);
        }); */
    }

    updateLobby() {
        this.lobbyButtons.style.display = "flex";

        this.startGameButton.disabled = false;
    }

    updatePlaying() {
        this.playingButtons.style.display = "flex";

        this.sortByColorButton.disabled = false;
        this.sortByValueButton.disabled = false;

        const isMyTurn = this.id === this.entityAtMoveId;

        this.playCardButton.disabled = !isMyTurn;
        this.passButton.disabled = !isMyTurn;
    }

    updateSchupfen() {
        this.schupfenButtons.style.display = "flex";

        const buttons = {
            left: this.schupfenLeftOpponentButton,
            team: this.schupfenTeammateButton,
            right: this.schupfenRightOpponentButton
        };

        for (const [mode, button] of Object.entries(buttons)) {
            button.innerText = this.schupfen[mode] ?? "Choose...";

            button.classList.toggle(
                "highlight_button",
                this.schupfenMode === mode
            );
        }
    }

    update() {
        this.lobbyButtons.style.display = "none";
        this.schupfenButtons.style.display = "none";
        this.playingButtons.style.display = "none";

        switch (this.gameState) {
            case "LOBBY":
                this.updateLobby()
                break
            case "SCHUPFEN":
                this.handleSchupfenSelection()
                this.updateSchupfen()
                break
            case "PLAYING":
                this.updatePlaying()
                break
        }
    }

    handleSchupfenSelection() {
        if (this.schupfenMode === undefined || this.selectedCards.size === 0) return;

        const selectedCard = this.selectedCards.values().next().value;

        this.schupfen[this.schupfenMode] = selectedCard;

        this.selectedCards.clear();
        this.schupfenMode = undefined;
    }

    render() {
        this.clearScreen();

        if (!this.state) return;

        this.renderCurrentCombination();
        this.renderPlayerHand();
        this.renderBacksides();
        this.renderDiscardPile();

        if (this.debugMode) {
            this.debug();
        }
    }

    getCardListOrigin(len, x, y) {
        return { x: x - (len / 2 * (CARD_WIDTH + CARD_PADDING)), y: y - CARD_HEIGHT / 2 }
    }

    getHandOrigin() {
        const { x, y } = this.playerHandCenter
        return this.getCardListOrigin(this.hand.length, x, y)
    }

    getDiscardPileOrigin() {
        const { x, y } = this.discardPileCenter
        return { x: x - (this.discardPile.length / 2 * (CARD_WIDTH + CARD_PADDING)), y: y - CARD_HEIGHT / 2 }
    }

    getCardAt(mouseX, mouseY) {
        if (!this.state) return

        const { x, y } = this.getHandOrigin();

        for (const [i, id] of this.hand.entries()) {
            const cardX = x + (i * (CARD_WIDTH + CARD_PADDING));
            const cardY = y;

            if (
                mouseX >= cardX &&
                mouseX <= cardX + CARD_WIDTH &&
                mouseY >= cardY &&
                mouseY <= cardY + CARD_HEIGHT
            ) {
                return {
                    id,
                    index: i
                };
            }
        }

        return null;
    }

    renderCurrentCombination() {
        if (!this.state || !this.currentCombination) return

        this.renderCardList(this.currentCombination, this.canvas.width / 2, this.canvas.height / 2);
    }

    // Draw a yellow highlight behind the card
    renderCardBorder(pos_x, pos_y) {
        this.ctx.fillStyle = "yellow"
        this.ctx.fillRect(pos_x - CARD_BORDER, pos_y - CARD_BORDER, CARD_WIDTH + CARD_BORDER * 2, CARD_HEIGHT + CARD_BORDER * 2)
    }

    renderCard(id, pos_x, pos_y) {
        const card = CARD_MAP.get(id);

        if (!card) {
            throw new Error(`Unknown card: ${id}`);
        }

        const { x, y } = card.getOrigin()

        this.ctx.drawImage(this.cards, x, y, ORIGIN_CARD_WIDTH, ORIGIN_CARD_HEIGHT, pos_x, pos_y, CARD_WIDTH, CARD_HEIGHT);
    }

    renderCardList(card_list, center_x, center_y) {
        const { x, y } = this.getCardListOrigin(card_list.length, center_x, center_y)

        for (const [i, id] of card_list.entries()) {
            const pos_x = x + (i * (CARD_WIDTH + CARD_PADDING))
            const pos_y = y

            if (this.selectedCards.has(id)) {
                this.renderCardBorder(pos_x, pos_y)
            }

            this.renderCard(id, pos_x, pos_y)
        }
    }

    renderPlayerHand() {
        if (!this.state) return

        const { x, y } = this.playerHandCenter

        this.renderCardList(this.hand, x, y)
    }

    renderDiscardPile() {
        if (!this.discardPile) return

        const { x, y } = this.getDiscardPileOrigin()

        this.renderCardList(this.discardPile, x, y)
    }

    getBacksideCardListOrigin(len, x, y, vertcial = false) {
        const width = (len / 2 * (BACKSIDE_WIDTH + BACKSIDE_PADDING))
        const height = BACKSIDE_HEIGHT / 2

        if (vertcial) {
            return { x: x - height, y: y - width }
        }

        return { x: x - width, y: y - height }
    }

    renderBacksideCard(pos_x, pos_y, vertical = false) {
        if (vertical) {
            this.ctx.drawImage(this.backsideVertical, 0, 0, 247, 160, pos_x, pos_y, BACKSIDE_HEIGHT, BACKSIDE_WIDTH);
            return;
        }

        this.ctx.drawImage(this.backside, 0, 0, 160, 247, pos_x, pos_y, BACKSIDE_WIDTH, BACKSIDE_HEIGHT);
    }

    renderBacksideCardList(amount, center_x, center_y, vertical = false) {
        const { x, y } = this.getBacksideCardListOrigin(amount, center_x, center_y, vertical)

        for (let i = 0; i < amount; i++) {
            const pos_x = !vertical ? x + (i * (BACKSIDE_WIDTH + BACKSIDE_PADDING)) : x
            const pos_y = !vertical ? y : y + (i * (BACKSIDE_WIDTH + BACKSIDE_PADDING))

            this.renderBacksideCard(pos_x, pos_y, vertical)
        }
    }

    renderBacksides() {
        //console.log(this.matePublicState, this.leftOpponentPublicState, this.rightOpponentPublicState)
        if (!(!!this.matePublicState && !!this.leftOpponentPublicState && !!this.rightOpponentPublicState)) return

        const { x: mate_x, y: mate_y } = this.mateHandCenter
        const { x: left_x, y: left_y } = this.leftOpponentHandCenter
        const { x: right_x, y: right_y } = this.rightOpponentHandCenter

        this.renderBacksideCardList(this.matePublicState.card_amount, mate_x, mate_y);
        this.renderBacksideCardList(this.leftOpponentPublicState.card_amount, left_x, left_y, true);
        this.renderBacksideCardList(this.rightOpponentPublicState.card_amount, right_x, right_y, true);
    }

    clearScreen() {
        this.ctx.clearRect(0, 0, this.canvas.width, this.canvas.height);
    }
}

(async () => {
    let game = new Game()
    game.init()
})()

