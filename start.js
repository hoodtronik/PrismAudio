const path = require('path')
const fs = require('fs')

module.exports = async (kernel) => {
  let port = await kernel.port()

  // Read HF token from local .hf_token file (saved during install)
  const hfTokenPath = path.join(__dirname, '.hf_token')
  let hfToken = ''
  try {
    hfToken = fs.readFileSync(hfTokenPath, 'utf8').trim()
  } catch (e) {
    // Token file doesn't exist — will prompt during install
  }

  return {
    daemon: true,
    run: [
      {
        method: "shell.run",
        params: {
          venv: "env",
          env: {
            GRADIO_TEMP_DIR: "{{path.resolve(cwd, 'cache')}}",
            HF_TOKEN: hfToken,
          },
          path: "app",
          message: [
            `python app.py --server_port ${port}`,
          ],
          on: [{
            "event": "/http:\\/\\/[0-9.:]+/",
            "done": true
          }]
        }
      },
      {
        method: "local.set",
        params: {
          url: "{{input.event[0]}}"
        }
      }
    ]
  }
}
