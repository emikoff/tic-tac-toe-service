const boardElement = document.querySelector("#board");
const cells = [...document.querySelectorAll(".cell")];
const statusElement = document.querySelector("#status");
const uuidElement = document.querySelector("#game-uuid");
const newGameButton = document.querySelector("#new-game");

const statusMessages = {
    CREATED_NEW_GAME: "Ваш ход",
    GAME_CONTINUES: "Ваш ход",
    USER_WON: "Вы победили!",
    COMPUTER_WON: "Победил компьютер",
    DRAW: "Ничья",
    INVALID_MOVE: "Некорректный ход",
    GAME_NOT_FOUND: "Игра не найдена. Начните новую игру",
    INTERNAL_ERROR: "Внутренняя ошибка сервера",
    INVALID_WINNER: "Сервер вернул некорректный результат игры",
};

const finishedStatuses = new Set(["USER_WON", "COMPUTER_WON", "DRAW"]);

let gameUuid = null;
let matrix = emptyMatrix();
let isWaiting = false;
let isFinished = true;

function emptyMatrix() {
    return Array.from({ length: 3 }, () => [0, 0, 0]);
}

function setStatus(message, isError = false) {
    statusElement.textContent = message;
    statusElement.classList.toggle("error", isError);
}

function renderBoard() {
    cells.forEach((cell, index) => {
        const row = Math.floor(index / 3);
        const column = index % 3;
        const value = matrix[row][column];
        const symbol = value === 1 ? "X" : value === 2 ? "O" : "";

        cell.textContent = symbol;
        cell.classList.toggle("x", value === 1);
        cell.classList.toggle("o", value === 2);
        cell.setAttribute(
            "aria-label",
            symbol ? `Клетка ${index + 1}: ${symbol}` : `Пустая клетка ${index + 1}`,
        );
        cell.disabled = isWaiting || isFinished || value !== 0;
    });

    boardElement.classList.toggle("is-disabled", isWaiting || isFinished);
    boardElement.setAttribute("aria-busy", String(isWaiting));
}

async function readResponse(response) {
    let data;

    try {
        data = await response.json();
    } catch {
        throw new Error("Сервер вернул ответ в неизвестном формате");
    }

    if (!response.ok) {
        const message = statusMessages[data.game_status] || data.error;
        const error = new Error(message || `Ошибка сервера: ${response.status}`);
        error.gameStatus = data.game_status;
        throw error;
    }

    return data;
}

async function requestJson(url, options) {
    try {
        return await readResponse(await fetch(url, options));
    } catch (error) {
        if (error instanceof TypeError) {
            throw new Error("Не удалось связаться с сервером. Попробуйте ещё раз");
        }
        throw error;
    }
}

async function startNewGame() {
    isWaiting = true;
    isFinished = true;
    gameUuid = null;
    matrix = emptyMatrix();
    uuidElement.textContent = "—";
    newGameButton.disabled = true;
    setStatus("Создаём новую игру…");
    renderBoard();

    try {
        const data = await requestJson("/game", { method: "POST" });

        gameUuid = data.uuid;
        matrix = data.board.matrix;
        isFinished = false;
        uuidElement.textContent = gameUuid;
        setStatus(statusMessages[data.game_status] || "Ваш ход");
    } catch (error) {
        setStatus(
            error.message || "Не удалось связаться с сервером. Попробуйте ещё раз",
            true,
        );
    } finally {
        isWaiting = false;
        newGameButton.disabled = false;
        renderBoard();
    }
}

async function makeMove(index) {
    const row = Math.floor(index / 3);
    const column = index % 3;

    if (isWaiting || isFinished || !gameUuid || matrix[row][column] !== 0) {
        return;
    }

    const previousMatrix = matrix.map((line) => [...line]);
    matrix[row][column] = 1;
    isWaiting = true;
    setStatus("Компьютер думает…");
    renderBoard();

    try {
        const data = await requestJson(`/game/${gameUuid}`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ matrix }),
        });

        matrix = data.board.matrix;
        isFinished = finishedStatuses.has(data.game_status);
        setStatus(statusMessages[data.game_status] || "Получен неизвестный статус", false);
    } catch (error) {
        matrix = previousMatrix;
        isFinished = ["GAME_NOT_FOUND", "INTERNAL_ERROR", "INVALID_WINNER"].includes(
            error.gameStatus,
        );
        setStatus(
            error.message || "Не удалось связаться с сервером. Попробуйте ещё раз",
            true,
        );
    } finally {
        isWaiting = false;
        renderBoard();
    }
}

cells.forEach((cell) => {
    cell.addEventListener("click", () => makeMove(Number(cell.dataset.index)));
});

newGameButton.addEventListener("click", startNewGame);
startNewGame();
