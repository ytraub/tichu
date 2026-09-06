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
            y: this.canvas.height - 100 - 20
        };
    }

    gameLoop(time) {
        if (!this.running) {
            return;
        }

        this.render();

        requestAnimationFrame((time) => {
            this.gameLoop(time);
        });
    }

    clearScreen() {
        this.ctx.clearRect(0, 0, this.canvas.width, this.canvas.height);
    }

    render() {
        this.clearScreen()
    }

    renderCard(id, pos_x, pos_y) {
        const card = CARD_MAP.get(id);

        if (!card) {
            throw new Error(`Unknown card: ${id}`);
        }

        const { x, y } = card.get_origin()

        this.ctx.drawImage(this.cards, x, y, ORIGIN_CARD_WIDTH, ORIGIN_CARD_HEIGHT, pos_x, pos_y, CARD_WIDTH, CARD_HEIGHT);
    }

    renderHand(cardIds) {
        const { x, y } = this.player_hand_center

        const origin = x - (cardIds.length / 2 * (CARD_WIDTH + CARD_PADDING))

        for (const [i, id] of cardIds.entries()) {
            this.renderCard(id, origin + (i * (CARD_WIDTH + CARD_PADDING)), y)
        }
    }
}

(async () => {
    let game = new Game()
    game.start()
})()

