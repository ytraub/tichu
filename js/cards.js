export const ORIGIN_CARD_WIDTH = 56
export const ORIGIN_CARD_HEIGHT = 79.5

export class Card {
    constructor(color, value, row, col) {
        this.color = color
        this.value = value
        this.origin = {
            x: row,
            y: col
        }
    }

    get_origin() {
        return this.origin
    }
}

function row(n, offset = 1) {
    return ((n) * (ORIGIN_CARD_WIDTH + 5)) + offset
}

function col(n, offset = 1) {
    return ((n) * (ORIGIN_CARD_HEIGHT + 5)) + offset
}

export const CARD_MAP = new Map([
    ["black_2", new Card("black", 2, row(0), col(0))],
    ["black_3", new Card("black", 3, row(1), col(0))],
    ["black_4", new Card("black", 4, row(2), col(0))],
    ["black_5", new Card("black", 5, row(3), col(0))],
    ["black_6", new Card("black", 6, row(4), col(0))],
    ["black_7", new Card("black", 7, row(5), col(0))],
    ["black_8", new Card("black", 8, row(6), col(0))],
    ["black_9", new Card("black", 9, row(7), col(0))],
    ["black_10", new Card("black", 10, row(8), col(0))],
    ["black_j", new Card("black", 11, row(9), col(0))],
    ["black_q", new Card("black", 12, row(10), col(0))],
    ["black_k", new Card("black", 13, row(11), col(0))],
    ["black_a", new Card("black", 14, row(12), col(0))],
    ["green_2", new Card("green", 2, row(0), col(1))],
    ["green_3", new Card("green", 3, row(1), col(1))],
    ["green_4", new Card("green", 4, row(2), col(1))],
    ["green_5", new Card("green", 5, row(3), col(1))],
    ["green_6", new Card("green", 6, row(4), col(1))],
    ["green_7", new Card("green", 7, row(5), col(1))],
    ["green_8", new Card("green", 8, row(6), col(1))],
    ["green_9", new Card("green", 9, row(7), col(1))],
    ["green_10", new Card("green", 10, row(8), col(1))],
    ["green_j", new Card("green", 11, row(9), col(1))],
    ["green_q", new Card("green", 12, row(10), col(1))],
    ["green_k", new Card("green", 13, row(11), col(1))],
    ["green_a", new Card("green", 14, row(12), col(1))],
    ["blue_2", new Card("blue", 2, row(0), col(2))],
    ["blue_3", new Card("blue", 3, row(1), col(2))],
    ["blue_4", new Card("blue", 4, row(2), col(2))],
    ["blue_5", new Card("blue", 5, row(3), col(2))],
    ["blue_6", new Card("blue", 6, row(4), col(2))],
    ["blue_7", new Card("blue", 7, row(5), col(2))],
    ["blue_8", new Card("blue", 8, row(6), col(2))],
    ["blue_9", new Card("blue", 9, row(7), col(2))],
    ["blue_10", new Card("blue", 10, row(8), col(2))],
    ["blue_j", new Card("blue", 11, row(9), col(2))],
    ["blue_q", new Card("blue", 12, row(10), col(2))],
    ["blue_k", new Card("blue", 13, row(11), col(2))],
    ["blue_a", new Card("blue", 14, row(12), col(2))],
    ["red_2", new Card("red", 2, row(0), col(3))],
    ["red_3", new Card("red", 3, row(1), col(3))],
    ["red_4", new Card("red", 4, row(2), col(3))],
    ["red_5", new Card("red", 5, row(3), col(3))],
    ["red_6", new Card("red", 6, row(4), col(3))],
    ["red_7", new Card("red", 7, row(5), col(3))],
    ["red_8", new Card("red", 8, row(6), col(3))],
    ["red_9", new Card("red", 9, row(7), col(3))],
    ["red_10", new Card("red", 10, row(8), col(3))],
    ["red_j", new Card("red", 11, row(9), col(3))],
    ["red_q", new Card("red", 12, row(10), col(3))],
    ["red_k", new Card("red", 13, row(11), col(3))],
    ["red_a", new Card("red", 14, row(12), col(3))],
    ["dragon", new Card("special", 99, row(0, 275), col(4))],
    ["phoenix", new Card("special", 0.5, row(1, 275), col(4))],
    ["dog", new Card("special", 0, row(2, 275), col(4))],
    ["mahong", new Card("special", 1, row(3, 275), col(4))],
]);

