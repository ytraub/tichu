import resources from "./resources.js";
import { CARD_MAP, ORIGIN_CARD_WIDTH, ORIGIN_CARD_HEIGHT } from "./cards.js";

const CANVAS_WIDTH = 800
const CANVAS_HEIGHT = 800

const CARD_WIDTH = 75
const CARD_HEIGHT = 100

const PADDING = 20
const CARD_PADDING = 5

const SOCKET_PORT = 5400

class Game {
    constructor() {
        this.canvas = document.getElementById("canvas");
        this.ctx = this.canvas.getContext("2d");

        this.running = false;
        this.state = undefined;

        this.selected_cards = [];

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
    }

    async onSocketClose(event) {
        console.log("Disconnected");
    }

    async onSocketError(event) {
        console.error(event);
    }

    async start() {
        await this.init();

        this.running = true;

        requestAnimationFrame((time) => {
            this.gameLoop(time);
        });
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
        console.log(card)
    }

    gameLoop(time) {
        if (!this.running) return;

        this.render();

        requestAnimationFrame((time) => {
            this.gameLoop(time);
        });
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

        const hand = this.state.player.hand
        const { x, y } = this.getHandOrigin(hand);

        for (const [i, id] of hand.entries()) {
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

        const hand = this.state.player.hand
        const { x, y } = this.getHandOrigin(hand)

        for (const [i, id] of hand.entries()) {
            this.renderCard(id, x + (i * (CARD_WIDTH + CARD_PADDING)), y)
        }
    }

    clearScreen() {
        this.ctx.clearRect(0, 0, this.canvas.width, this.canvas.height);
    }
}

(async () => {
    let game = new Game()
    game.start()
})()

