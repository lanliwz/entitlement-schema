from pathlib import Path
from openai import OpenAI

client = OpenAI()

def text_to_speech_file(text_file: str, voice: str = "ash", model: str = "gpt-4o-mini-tts"):
    """
    Convert a text file into a speech mp3 file with the same name.

    Args:
        text_file (str): Path to the input text file.
        voice (str): Voice style for TTS (default: 'coral').
        model (str): TTS model to use (default: 'gpt-4o-mini-tts').
    """
    text_path = Path(text_file)
    if not text_path.exists():
        raise FileNotFoundError(f"File not found: {text_file}")

    # Read text from file
    input_text = text_path.read_text(encoding="utf-8")

    # Output path with same base name but .mp3
    mp3_path = text_path.with_suffix(".mp3")

    # Generate speech
    with client.audio.speech.with_streaming_response.create(
        model=model,
        voice=voice,
        speed=1.0,
        input=input_text,
    ) as response:
        response.stream_to_file(mp3_path)

    print(f"✅ Speech saved to {mp3_path}")
    return mp3_path


# text_to_speech_file("./speech_script/executive_pitch.txt")
# text_to_speech_file("./speech_script/introduction.txt")
text_to_speech_file("./speech_script/elevator_pitch.txt")