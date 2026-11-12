const authView = document.querySelector("#auth-view");
const gameView = document.querySelector("#game-view");
const userMenu = document.querySelector("#user-menu");
const currentLoginElement = document.querySelector("#current-login");
const logoutButton = document.querySelector("#logout");

const authForm = document.querySelector("#auth-form");
const authTitle = document.querySelector("#auth-title");
const authSubmitButton = document.querySelector("#auth-submit");
const authStatusElement = document.querySelector("#auth-status");
const loginInput = document.querySelector("#login");
const passwordInput = document.querySelector("#password");
const modeButtons = [...document.querySelectorAll("[data-auth-mode]")];

const boardElement = document.querySelector("#board");
const cells = [...document.querySelectorAll(".cell")];
const statusElement = document.querySelector("#status");
const uuidElement = document.querySelector("#game-uuid");
const gameTypeElement = document.querySelector("#game-type");
const firstPlayerElement = document.querySelector("#first-player");
const secondPlayerElement = document.querySelector("#second-player");
const newGameButton = document.querySelector("#new-game");
const refreshGamesButton = document.querySelector("#refresh-games");
const availableGamesElement = document.querySelector("#available-games");

const POLL_INTERVAL_MS = 1500;

const errorMessages = {
    "Invalid request body": "Проверьте логин и пароль.",
    "Invalid login": "Логин должен содержать не менее трёх символов.",
    "Invalid password": "Пароль должен содержать не менее восьми символов.",
    "Login already exists": "Пользователь с таким логином уже существует.",
    Unauthorized: "Неверный логин или пароль.",
    "Game not found": "Игра не найдена.",
    "Cannot join your own game": "Нельзя присоединиться к собственной игре.",
    "Game is not available": "Эта игра уже недоступна.",
    "User is not a game participant": "Вы не являетесь участником этой игры.",
    "Game has not started": "Игра ещё ожидает второго игрока.",
    "Game is already finished": "Игра уже завершена.",
    "It is not your turn": "Сейчас ход другого игрока.",
    "ERROR: INVALID MOVE": "Некорректный ход.",
};

const appState = {
    authMode: "login",
    authHeader: null,
    currentUser: null,
    game: null,
    busy: false,
    pollTimer: null,
};

function emptyMatrix() {
    return Array.from({ length: 3 }, () => [0, 0, 0]);
}

function createBasicHeader(login, password) {
    const bytes = new TextEncoder().encode(`${login}:${password}`);
    const encoded = btoa(String.fromCharCode(...bytes));
    return `Basic ${encoded}`;
}

function translateError(data, status) {
    const rawMessage = data?.error || data?.game_status;
    return errorMessages[rawMessage] || rawMessage || `Ошибка сервера: ${status}`;
}

async function requestJson(url, options = {}, authorization = appState.authHeader) {
    const headers = new Headers(options.headers || {});
    if (authorization) {
        headers.set("Authorization", authorization);
    }

    let response;
    try {
        response = await fetch(url, { ...options, headers });
    } catch {
        throw new Error("Не удалось связаться с сервером. Попробуйте ещё раз.");
    }

    let data = {};
    try {
        data = await response.json();
    } catch {
        throw new Error("Сервер вернул ответ в неизвестном формате.");
    }

    if (!response.ok) {
        const error = new Error(translateError(data, response.status));
        error.status = response.status;
        error.data = data;
        throw error;
    }

    return data;
}

function setAuthStatus(message = "", isError = false) {
    authStatusElement.textContent = message;
    authStatusElement.classList.toggle("error", isError);
}

function setGameStatus(message, isError = false) {
    statusElement.textContent = message;
    statusElement.classList.toggle("error", isError);
}

function setAuthMode(mode) {
    appState.authMode = mode;
    const isSignup = mode === "signup";
    authTitle.textContent = isSignup ? "Создание аккаунта" : "Вход в игру";
    authSubmitButton.textContent = isSignup ? "Зарегистрироваться" : "Войти";
    passwordInput.autocomplete = isSignup ? "new-password" : "current-password";
    modeButtons.forEach((button) => {
        button.classList.toggle("is-active", button.dataset.authMode === mode);
    });
    setAuthStatus();
}

function showGameView() {
    authView.classList.add("is-hidden");
    gameView.classList.remove("is-hidden");
    userMenu.classList.remove("is-hidden");
    currentLoginElement.textContent = appState.currentUser.login;
}

function showAuthView() {
    authView.classList.remove("is-hidden");
    gameView.classList.add("is-hidden");
    userMenu.classList.add("is-hidden");
}

function currentPlayerMark(game = appState.game) {
    if (!game || !appState.currentUser) {
        return null;
    }
    if (game.first_player_uuid === appState.currentUser.uuid) {
        return { symbol: game.first_player_mark, value: 1 };
    }
    if (game.second_player_uuid === appState.currentUser.uuid) {
        return { symbol: game.second_player_mark, value: 2 };
    }
    return null;
}

function gameStatusText(game) {
    if (!game) {
        return "Создайте игру или присоединитесь к доступной партии.";
    }
    if (game.state === "WAITING_FOR_PLAYERS") {
        return "Ожидаем подключения второго игрока…";
    }
    if (game.state === "DRAW") {
        return "Игра завершена: ничья.";
    }
    if (game.state === "VICTORY") {
        if (game.winner_uuid === appState.currentUser.uuid) {
            return "Вы победили!";
        }
        if (game.opponent_type === "COMPUTER" && !game.winner_uuid) {
            return "Победил компьютер.";
        }
        return "Победил соперник.";
    }
    if (game.current_player_uuid === appState.currentUser.uuid) {
        return "Ваш ход.";
    }
    if (game.opponent_type === "COMPUTER") {
        return "Компьютер думает…";
    }
    return "Ход соперника…";
}

function playerLabel(prefix, mark, markClass) {
    return `${prefix} — <strong class="mark ${markClass}">${mark}</strong>`;
}

function renderPlayers(game) {
    if (!game) {
        firstPlayerElement.innerHTML = playerLabel("Вы", "X", "mark-x");
        secondPlayerElement.innerHTML = playerLabel("Компьютер", "O", "mark-o");
        return;
    }

    const userIsFirst = game.first_player_uuid === appState.currentUser.uuid;
    const firstPrefix = userIsFirst ? "Вы" : "Соперник";
    let secondPrefix = "Соперник";
    if (game.opponent_type === "COMPUTER") {
        secondPrefix = "Компьютер";
    } else if (!userIsFirst) {
        secondPrefix = "Вы";
    } else if (!game.second_player_uuid) {
        secondPrefix = "Ожидаем игрока";
    }

    firstPlayerElement.innerHTML = playerLabel(
        firstPrefix,
        game.first_player_mark,
        "mark-x",
    );
    secondPlayerElement.innerHTML = playerLabel(
        secondPrefix,
        game.second_player_mark,
        "mark-o",
    );
}

function renderGame() {
    const game = appState.game;
    const matrix = game?.board?.matrix || emptyMatrix();
    const mark = currentPlayerMark(game);
    const canMove = Boolean(
        game
        && mark
        && game.state === "PLAYER_TURN"
        && game.current_player_uuid === appState.currentUser.uuid
        && !appState.busy,
    );

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
        cell.disabled = !canMove || value !== 0;
    });

    boardElement.classList.toggle("is-disabled", !canMove);
    boardElement.setAttribute("aria-busy", String(appState.busy));
    uuidElement.textContent = game?.uuid || "—";
    gameTypeElement.textContent = game
        ? game.opponent_type === "COMPUTER" ? "Против компьютера" : "Два игрока"
        : "Нет игры";
    renderPlayers(game);
    setGameStatus(gameStatusText(game));
}

function stopPolling() {
    if (appState.pollTimer) {
        clearInterval(appState.pollTimer);
        appState.pollTimer = null;
    }
}

function shouldPollGame(game) {
    return Boolean(
        game
        && game.opponent_type === "USER"
        && !["DRAW", "VICTORY"].includes(game.state),
    );
}

function startPolling() {
    stopPolling();
    if (!shouldPollGame(appState.game)) {
        return;
    }
    appState.pollTimer = setInterval(refreshCurrentGame, POLL_INTERVAL_MS);
}

function setCurrentGame(game) {
    appState.game = game;
    renderGame();
    startPolling();
}

function renderAvailableGames(games) {
    const availableGames = games.filter(
        (game) => game.first_player_uuid !== appState.currentUser.uuid,
    );
    availableGamesElement.replaceChildren();

    if (availableGames.length === 0) {
        const empty = document.createElement("p");
        empty.className = "empty-list";
        empty.textContent = "Сейчас нет игр, к которым можно присоединиться.";
        availableGamesElement.append(empty);
        return;
    }

    availableGames.forEach((game, index) => {
        const item = document.createElement("div");
        item.className = "game-list-item";

        const description = document.createElement("div");
        const title = document.createElement("strong");
        title.textContent = `Игра №${index + 1}`;
        const uuid = document.createElement("small");
        uuid.textContent = game.uuid;
        description.append(title, uuid);

        const joinButton = document.createElement("button");
        joinButton.className = "join-button";
        joinButton.type = "button";
        joinButton.textContent = "Войти";
        joinButton.addEventListener("click", () => joinGame(game.uuid));

        item.append(description, joinButton);
        availableGamesElement.append(item);
    });
}

async function refreshAvailableGames() {
    if (!appState.authHeader) {
        return;
    }
    refreshGamesButton.disabled = true;
    try {
        const data = await requestJson("/game");
        renderAvailableGames(data.games);
    } catch (error) {
        availableGamesElement.replaceChildren();
        const message = document.createElement("p");
        message.className = "empty-list";
        message.textContent = error.message;
        availableGamesElement.append(message);
    } finally {
        refreshGamesButton.disabled = false;
    }
}

async function refreshCurrentGame() {
    if (!appState.game || appState.busy) {
        return;
    }
    try {
        const game = await requestJson(`/game/${appState.game.uuid}`);
        appState.game = game;
        renderGame();
        if (!shouldPollGame(game)) {
            stopPolling();
        }
    } catch (error) {
        setGameStatus(error.message, true);
    }
}

async function createGame() {
    const opponentType = document.querySelector("input[name='opponent']:checked").value;
    appState.busy = true;
    newGameButton.disabled = true;
    setGameStatus("Создаём новую игру…");
    renderGame();

    let failure = null;
    try {
        const game = await requestJson("/game", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ opponent_type: opponentType }),
        });
        setCurrentGame(game);
        await refreshAvailableGames();
    } catch (error) {
        failure = error;
    } finally {
        appState.busy = false;
        newGameButton.disabled = false;
        renderGame();
        if (failure) {
            setGameStatus(failure.message, true);
        }
    }
}

async function joinGame(gameUuid) {
    appState.busy = true;
    setGameStatus("Присоединяемся к игре…");
    renderGame();
    let failure = null;
    try {
        const game = await requestJson(`/game/${gameUuid}/join`, { method: "POST" });
        setCurrentGame(game);
        await refreshAvailableGames();
    } catch (error) {
        failure = error;
    } finally {
        appState.busy = false;
        renderGame();
        if (failure) {
            setGameStatus(failure.message, true);
        }
    }
}

async function makeMove(index) {
    const game = appState.game;
    const mark = currentPlayerMark(game);
    if (!game || !mark || appState.busy) {
        return;
    }

    const row = Math.floor(index / 3);
    const column = index % 3;
    if (game.board.matrix[row][column] !== 0) {
        return;
    }

    const previousGame = structuredClone(game);
    game.board.matrix[row][column] = mark.value;
    appState.busy = true;
    renderGame();
    setGameStatus(game.opponent_type === "COMPUTER" ? "Компьютер думает…" : "Отправляем ход…");

    let failure = null;
    try {
        const updatedGame = await requestJson(`/game/${game.uuid}`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ matrix: game.board.matrix }),
        });
        appState.game = updatedGame;
        startPolling();
    } catch (error) {
        appState.game = previousGame;
        failure = error;
    } finally {
        appState.busy = false;
        renderGame();
        if (failure) {
            setGameStatus(failure.message, true);
        }
    }
}

async function authenticate(login, password, mode) {
    const authorization = createBasicHeader(login, password);
    if (mode === "signup") {
        await requestJson(
            "/auth/signup",
            {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ login, password }),
            },
            null,
        );
    }

    const loginData = await requestJson(
        "/auth/login",
        { method: "POST" },
        authorization,
    );
    appState.authHeader = authorization;
    appState.currentUser = { uuid: loginData.user_uuid, login };
}

async function handleAuthSubmit(event) {
    event.preventDefault();
    const login = loginInput.value.trim();
    const password = passwordInput.value;
    authSubmitButton.disabled = true;
    setAuthStatus(appState.authMode === "signup" ? "Создаём аккаунт…" : "Проверяем данные…");

    try {
        await authenticate(login, password, appState.authMode);
        passwordInput.value = "";
        appState.game = null;
        showGameView();
        renderGame();
        await refreshAvailableGames();
    } catch (error) {
        setAuthStatus(error.message, true);
    } finally {
        authSubmitButton.disabled = false;
    }
}

function logout() {
    stopPolling();
    appState.authHeader = null;
    appState.currentUser = null;
    appState.game = null;
    appState.busy = false;
    loginInput.value = "";
    passwordInput.value = "";
    availableGamesElement.innerHTML = '<p class="empty-list">Войдите, чтобы увидеть игры.</p>';
    setAuthMode("login");
    showAuthView();
    renderGame();
}

modeButtons.forEach((button) => {
    button.addEventListener("click", () => setAuthMode(button.dataset.authMode));
});
authForm.addEventListener("submit", handleAuthSubmit);
logoutButton.addEventListener("click", logout);
newGameButton.addEventListener("click", createGame);
refreshGamesButton.addEventListener("click", refreshAvailableGames);
cells.forEach((cell) => {
    cell.addEventListener("click", () => makeMove(Number(cell.dataset.index)));
});

showAuthView();
renderGame();
