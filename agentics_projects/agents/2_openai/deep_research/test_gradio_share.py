import gradio as gr

def greet(name):
    return f"Hello {name}! Gradio sharing is working!"

demo = gr.Interface(fn=greet, inputs="text", outputs="text")

print("Starting Gradio with share=True...")
demo.launch(share=True, debug=True)