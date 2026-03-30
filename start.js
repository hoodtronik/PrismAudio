const os = require('os')
const path = require('path')
const fs = require('fs')

module.exports = async (kernel) => {
  let port = await kernel.port()

  // Read HF token from the standard cache location
  const hfTokenPath = path.join(os.homedir(), '.cache', 'huggingface', 'token')
  let hfToken = ''
  try {
    hfToken = fs.readFileSync(hfTokenPath, 'utf8').trim()
  } catch (e) {
    // Token file doesn't exist yet
  }
  const hfLoggedIn = !!hfToken

  return {
    daemon: true,
    run: [
      // If HF token missing, prompt user to set it up
      {
        when: "{{!self.hfLoggedIn}}",
        method: "input",
        params: {
          title: "🔑 HuggingFace Login Required",
          description: [
            "PrismAudio needs a HuggingFace token to download the T5Gemma model.",
            "",
            "📋 Follow these steps:",
            "",
            "Step 1️⃣  Create a free account at https://huggingface.co/join",
            "",
            "Step 2️⃣  Go to the model page and click 'Agree and access repository':",
            "   → https://huggingface.co/google/t5gemma-l-l-ul2-it",
            "",
            "Step 3️⃣  Create an access token:",
            "   → https://huggingface.co/settings/tokens",
            "   → Click 'Create new token' → Select 'Read' permission → Copy it",
            "",
            "Step 4️⃣  Paste your token below and click Submit",
          ].join("\n"),
          form: [{
            key: "hf_token",
            title: "HuggingFace Access Token",
            description: "Paste your token here (starts with hf_)",
            type: "password",
            required: true
          }]
        }
      },
      // Login with the provided token
      {
        when: "{{!self.hfLoggedIn}}",
        method: "shell.run",
        params: {
          venv: "env",
          path: "app",
          message: [
            "huggingface-cli login --token {{input.hf_token}} --add-to-git-credential",
          ]
        }
      },
      // Start the app — pass HF_TOKEN explicitly so Pinokio's conda shell can authenticate
      {
        method: "shell.run",
        params: {
          venv: "env",
          env: {
            GRADIO_TEMP_DIR: "{{path.resolve(cwd, 'cache')}}",
            HF_TOKEN: hfToken || "{{input.hf_token || ''}}",
          },
          path: "app",
          message: [
            `python app.py --server_port ${port}`,
          ],
          on: [{
            "event": "/(http:\\/\\/\\S+)/",
            "done": true
          }]
        }
      },
      {
        method: "local.set",
        params: {
          url: "{{input.event[1]}}"
        }
      }
    ],
    hfLoggedIn
  }
}
