import gradio as gr
import sys

print("Starting simple Gradio test...", file=sys.stderr)

def greet(name):
    return f"Hello {name}!"

demo = gr.Interface(fn=greet, inputs="text", outputs="text")

print("\n" + "="*50, file=sys.stderr)
print("🚀 LAUNCHING TEST APP...", file=sys.stderr)
print("="*50 + "\n", file=sys.stderr)

# Launch and capture the URL
app, local_url, share_url = demo.launch(
    server_name="0.0.0.0",
    server_port=7861,
    share=False,
    show_api=False,
    prevent_thread_lock=True
)

print(f"\n✅ App is running at: {local_url}", file=sys.stderr)
print(f"   In Codespaces: Make port 7861 public in PORTS tab\n", file=sys.stderr)

# Keep the app running
demo.block_thread()