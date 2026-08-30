import resources from "./resources.js";

const canvas = document.getElementById("canvas");
const ctx = canvas.getContext("2d");

async function init() {
    const [cards] = await resources.load("/img/cards.png");

    console.log(cards)

    ctx.drawImage(
        cards,
        457, 339   ,       // source X, Y
        60, 80,     // source width, height
        0, 0,   // destination X, Y
        80, 60      // destination width, height
    );
}


init()