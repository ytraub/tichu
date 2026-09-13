import resources from "./resources.js";
import { CARD_MAP, ORIGIN_CARD_WIDTH, ORIGIN_CARD_HEIGHT } from "./cards.js";

const CANVAS_WIDTH = 800
const CANVAS_HEIGHT = 800

const CARD_WIDTH = 48
const CARD_HEIGHT = 64

const PADDING = 20
const CARD_PADDING = 5
const CARD_BORDER = 2

const SOCKET_PORT = 5400

class Game {
    constructor() {
        this.canvas = document.getElementById("canvas");

        this.startGameButton = document.getElementById("start_game_btn");
        this.startGameButton.onclick = (event) => this.startGame(event);

        this.playCardButton = document.getElementById("play_cards_btn");
        this.playCardButton.onclick = (event) => this.onPlayCards(event);
            
        this.ctx = this.canvas.getContext("2d");

        this.state = undefined;
        this.isRunning = false;
        this.hand = undefined;

        this.selected_cards = new Set();

        this.socket = new WebSocket(`ws://localhost:${SOCKET_PORT}`);

        this.socket.onopen = (event) => this.onSocketOpen(event);
        this.socket.onmessage = (event) => this.onSocketMessage(event);
        this.socket.onclose = (event) => this.onSocketClose(event);
        this.socket.onerror = (event) => this.onSocketError(event);
    }

    async onSocketOpen(event) {
        console.log("Connected");
    }

    async onSocketMessage(event) {
        const state = JSON.parse(event.data);
        this.state = state;

        this.hand = state.player.hand;
        this.isRunning = state.game.is_running;
    }

    async onSocketClose(event) {
        console.log("Disconnected");
    }

    async onSocketError(event) {
        console.error(event);
    }

    async onPlayCards(event) {
        const payload = {
            "selected_cards": Array.from(this.selected_cards)
        }

        this.socket.send(JSON.stringify(payload))
    }

    async startGame(event) {
        const payload = {
            "ready": true
        }

        this.socket.send(JSON.stringify(payload))
    }

    async init() {
        const [cards] = await resources.load("/img/cards.png");

        this.cards = cards;

        this.canvas.width = CANVAS_HEIGHT;
        this.canvas.height = CANVAS_WIDTH;

        this.player_hand_center = {
            x: this.canvas.width / 2,
            y: this.canvas.height - 50 - PADDING
        };

        this.initInput();

        requestAnimationFrame((time) => {
            this.gameLoop(time);
        });
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

            if (this.selected_cards.has(id)) {
                this.selected_cards.delete(id)
            } else {
                this.selected_cards.add(id, CARD_MAP.get(id))
            }
        }

        console.log(this.selected_cards)
    }

    gameLoop(time) {
        this.update();
        this.render();

        requestAnimationFrame((time) => {
            this.gameLoop(time);
        });
    }

    update() {
        if (this.isRunning) {
            this.startGameButton.disabled = true;
            this.playCardButton.disabled = false;
        } else {
            this.startGameButton.disabled = false;
            this.playCardButton.disabled = true;
        }
    }

    render() {
        this.clearScreen()

        if (!this.state) return;

        this.renderHand()
    }

    getHandOrigin(hand) {
        const { x, y } = this.player_hand_center
        return { x: x - (hand.length / 2 * (CARD_WIDTH + CARD_PADDING)), y: y - CARD_HEIGHT / 2 }
    }

    getCardAt(mouseX, mouseY) {
        if (!this.state) return

        const { x, y } = this.getHandOrigin(this.hand);

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

    renderHand() {
        if (!this.state) return

        const { x, y } = this.getHandOrigin(this.hand)

        for (const [i, id] of this.hand.entries()) {
            const pos_x = x + (i * (CARD_WIDTH + CARD_PADDING))
            const pos_y = y

            if (this.selected_cards.has(id)) {
                this.renderCardBorder(pos_x, pos_y)
            }

            this.renderCard(id, pos_x, pos_y)
        }
    }

    clearScreen() {
        this.ctx.clearRect(0, 0, this.canvas.width, this.canvas.height);
    }
}

(async () => {
    let game = new Game()
    game.init()
})()

