import resources from "./resources.js";
import { CARD_MAP, ORIGIN_CARD_WIDTH, ORIGIN_CARD_HEIGHT } from "./cards.js";

const CANVAS_WIDTH = 800
const CANVAS_HEIGHT = 800

const CARD_WIDTH = 75
const CARD_HEIGHT = 100

const PADDING = 20
const CARD_PADDING = 5

const UPDATE_RATE = 1000 / 30 // 30 times per second

class Game {
    constructor() {
        this.canvas = canvas = document.getElementById("canvas");
        this.ctx = canvas.getContext("2d");

        this.running = false
        this.lastTime = 0
        this.accumulator = 0

        this.x = 0
        this.y = 0
    }

    async start() {
        await this.init()

        this.running = true
        requestAnimationFrame((time) => this.gameLoop(time))
    }

    async init() {
        const [cards] = await resources.load("/img/cards.png");
        this.cards = cards

        this.canvas.width = CANVAS_WIDTH
        this.canvas.height = CANVAS_HEIGHT

        this.player_hand_center = { x: this.canvas.width / 2, y: this.canvas.height - CARD_HEIGHT - PADDING }
    }

    async gameLoop(time) {
        if (!this.running) return

        if (!this.lastTime) {
            this.lastTime = time
        }

        let frameTime = time - this.lastTime
        this.lastTime = time

        frameTime = Math.min(frameTime, 250)

        this.accumulator += frameTime

        while (this.accumulator >= UPDATE_RATE) {
            this.update(UPDATE_RATE)
            this.accumulator -= UPDATE_RATE
        }

        this.render()

        requestAnimationFrame((time) => this.gameLoop(time))
    }

    async update(dt) {
        if (this.y % 2 == 0) {

            this.x += 18
        } else {
            this.x -= 18
        }

        if (this.x > 800 | this.x < -100) {
            this.y += 25
        }
    }

    async render() {
        this.clearScreen()

        this.renderHand(["red_j", "red_2", "red_3", "red_4", "red_5", "dragon"])
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

    clearScreen() {
        this.ctx.clearRect(0, 0, this.canvas.width, this.canvas.height);
    }
}

(async () => {
    let game = new Game()
    game.start()
})()

