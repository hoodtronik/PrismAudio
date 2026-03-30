module.exports = {
  run: [{
    method: "shell.run",
    params: {
      message: "git pull --rebase --autostash"
    }
  }, {
    method: "shell.run",
    params: {
      path: "app",
      message: "git pull --rebase --autostash"
    }
  }, {
    method: "shell.run",
    params: {
      venv: "env",
      path: "app",
      message: [
        "uv pip install -r scripts/PrismAudio/setup/requirements.txt --index-strategy unsafe-best-match",
      ]
    }
  }]
}
