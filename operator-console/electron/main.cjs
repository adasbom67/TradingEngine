const { app, BrowserWindow, dialog, shell } = require("electron");
const fs = require("node:fs");
const net = require("node:net");
const path = require("node:path");
const { spawn } = require("node:child_process");

const HOST = "127.0.0.1";
const STARTUP_TIMEOUT_MS = 45_000;

let mainWindow = null;
let backendProcess = null;
let backendUrl = null;
let shuttingDown = false;

function containsProjectMarker(directory) {
  return (
    fs.existsSync(path.join(directory, "VERSION")) &&
    fs.existsSync(path.join(directory, "app", "api", "operator_console.py"))
  );
}

function walkForProjectRoot(start) {
  let current = path.resolve(start);
  while (true) {
    if (containsProjectMarker(current)) return current;
    const parent = path.dirname(current);
    if (parent === current) return null;
    current = parent;
  }
}

function findExistingProjectRoot() {
  const candidates = [
    process.env.TRADINGENGINE_PROJECT_ROOT,
    process.cwd(),
    path.dirname(process.execPath),
    path.join(app.getPath("documents"), "Programming Projects", "Options Trading Engine"),
    path.join(app.getPath("home"), "TradingEngine"),
  ].filter(Boolean);

  for (const candidate of candidates) {
    const root = walkForProjectRoot(candidate);
    if (root) return root;
  }
  return null;
}

function ensureStandaloneWorkspace() {
  const workspace = path.join(app.getPath("userData"), "workspace");
  fs.mkdirSync(workspace, { recursive: true });

  const bundledConfig = path.join(process.resourcesPath, "default-config");
  const targetConfig = path.join(workspace, "config");
  if (!fs.existsSync(targetConfig) && fs.existsSync(bundledConfig)) {
    fs.cpSync(bundledConfig, targetConfig, { recursive: true });
  }

  for (const directory of ["data", "logs", "reports"]) {
    fs.mkdirSync(path.join(workspace, directory), { recursive: true });
  }

  const bundledVersion = path.join(process.resourcesPath, "VERSION");
  const targetVersion = path.join(workspace, "VERSION");
  if (!fs.existsSync(targetVersion) && fs.existsSync(bundledVersion)) {
    fs.copyFileSync(bundledVersion, targetVersion);
  }
  return workspace;
}

function getAvailablePort() {
  return new Promise((resolve, reject) => {
    const server = net.createServer();
    server.unref();
    server.on("error", reject);
    server.listen(0, HOST, () => {
      const address = server.address();
      const port = typeof address === "object" && address ? address.port : null;
      server.close(() => {
        if (port == null) reject(new Error("Could not allocate a desktop API port."));
        else resolve(port);
      });
    });
  });
}

function backendCommand(projectRoot) {
  if (app.isPackaged) {
    const executable = path.join(
      process.resourcesPath,
      "backend",
      "tradingengine-backend.exe",
    );
    if (!fs.existsSync(executable)) {
      throw new Error(`Packaged backend is missing: ${executable}`);
    }
    return { executable, args: [] };
  }

  const virtualEnvironmentPython = path.join(
    projectRoot,
    ".venv",
    "Scripts",
    "python.exe",
  );
  const executable = fs.existsSync(virtualEnvironmentPython)
    ? virtualEnvironmentPython
    : "python";
  return {
    executable,
    args: [path.join(projectRoot, "desktop_backend.py")],
  };
}

function startBackend({ port, projectRoot, workspace }) {
  const command = backendCommand(projectRoot ?? workspace);
  const uiDirectory = app.isPackaged
    ? path.join(process.resourcesPath, "ui")
    : path.join(projectRoot, "operator-console", "dist");
  const logPath = path.join(app.getPath("userData"), "desktop-backend.log");
  const log = fs.createWriteStream(logPath, { flags: "a" });

  backendProcess = spawn(command.executable, command.args, {
    cwd: workspace,
    env: {
      ...process.env,
      TRADINGENGINE_DESKTOP: "1",
      TRADINGENGINE_HOST: HOST,
      TRADINGENGINE_PORT: String(port),
      TRADINGENGINE_UI_DIR: uiDirectory,
      PYTHONUNBUFFERED: "1",
    },
    windowsHide: true,
    stdio: ["ignore", "pipe", "pipe"],
  });

  backendProcess.stdout.pipe(log);
  backendProcess.stderr.pipe(log);
  backendProcess.once("error", (error) => {
    log.write(`\nDesktop backend launch error: ${error.stack ?? error}\n`);
  });
  backendProcess.once("exit", (code, signal) => {
    log.end(`\nDesktop backend exited (code=${code}, signal=${signal}).\n`);
    backendProcess = null;
    if (!shuttingDown && mainWindow) {
      dialog.showErrorBox(
        "TradingEngine service stopped",
        `The internal service exited unexpectedly. See ${logPath}`,
      );
      app.quit();
    }
  });
}

async function waitForBackend(url) {
  const deadline = Date.now() + STARTUP_TIMEOUT_MS;
  let lastError = null;

  while (Date.now() < deadline) {
    if (backendProcess?.exitCode != null) {
      throw new Error(`The internal service exited with code ${backendProcess.exitCode}.`);
    }
    try {
      const response = await fetch(`${url}/api/version`, {
        signal: AbortSignal.timeout(1500),
      });
      if (response.ok) return;
      lastError = new Error(`Health check returned HTTP ${response.status}.`);
    } catch (error) {
      lastError = error;
    }
    await new Promise((resolve) => setTimeout(resolve, 250));
  }
  throw new Error(
    `The internal service did not become ready within ${STARTUP_TIMEOUT_MS / 1000} seconds. ${lastError ?? ""}`,
  );
}

function createWindow(url) {
  mainWindow = new BrowserWindow({
    title: "TradingEngine",
    width: 1480,
    height: 940,
    minWidth: 1080,
    minHeight: 700,
    show: false,
    backgroundColor: "#0a0f1c",
    autoHideMenuBar: true,
    webPreferences: {
      contextIsolation: true,
      nodeIntegration: false,
      sandbox: true,
    },
  });

  mainWindow.once("ready-to-show", () => mainWindow?.show());
  mainWindow.webContents.setWindowOpenHandler(({ url: target }) => {
    if (/^https?:\/\//i.test(target)) void shell.openExternal(target);
    return { action: "deny" };
  });
  mainWindow.webContents.on("will-navigate", (event, target) => {
    if (!target.startsWith(url)) event.preventDefault();
  });
  mainWindow.on("closed", () => {
    mainWindow = null;
  });
  void mainWindow.loadURL(url);
}

function stopBackend() {
  shuttingDown = true;
  if (backendProcess && backendProcess.exitCode == null) {
    backendProcess.kill();
  }
  backendProcess = null;
}

const hasSingleInstanceLock = app.requestSingleInstanceLock();
if (!hasSingleInstanceLock) {
  app.quit();
} else {
  app.on("second-instance", () => {
    if (mainWindow) {
      if (mainWindow.isMinimized()) mainWindow.restore();
      mainWindow.focus();
    }
  });

  app.whenReady().then(async () => {
    try {
      const projectRoot = findExistingProjectRoot();
      const workspace = projectRoot ?? ensureStandaloneWorkspace();
      const port = await getAvailablePort();
      backendUrl = `http://${HOST}:${port}`;
      startBackend({ port, projectRoot, workspace });
      await waitForBackend(backendUrl);
      createWindow(backendUrl);
    } catch (error) {
      dialog.showErrorBox(
        "TradingEngine could not start",
        error instanceof Error ? error.message : String(error),
      );
      stopBackend();
      app.quit();
    }
  });

  app.on("before-quit", stopBackend);
  app.on("window-all-closed", () => app.quit());
}
