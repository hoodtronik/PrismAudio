module.exports = async (kernel) => {
  let port = await kernel.port()
  return {
    daemon: true,
    run: [
      {
        method: "shell.run",
        params: {
          venv: "env",
          env: {
            GRADIO_TEMP_DIR: "{{path.resolve(cwd, 'cache')}}",
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
