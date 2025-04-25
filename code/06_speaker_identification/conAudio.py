import os
import wave

def concatenate_audio_wave(folder_path, output_path):
  """Concatenates all .wav files in a folder into one audio file using Python's built-in wav module
  and save it to `output_path`. Note that extension (wav) must be added to `output_path`"""
  wav_files = [os.path.join(folder_path, f) for f in os.listdir(folder_path) if f.endswith(".wav")]  # Get all .wav files

  if not wav_files:
      print(f"No .wav files found in directory: {folder_path}")
      return

  data = []
  for clip in wav_files:
      with wave.open(clip, "rb") as w:
          data.append([w.getparams(), w.readframes(w.getnframes())])

  if not data:  # Check if any data was read
      print("No data read from audio files. Exiting...")
      return

  # Print the output path before line 6 that's causing the error
  print(f"output_path: {output_path}")

  output = wave.open(output_path, "wb")
  output.setparams(data[0][0])
  for i in range(len(data)):
      output.writeframes(data[i][1])
  output.close()

if __name__ == "__main__":
  import argparse
  parser = argparse.ArgumentParser(description="Concatenate all .wav files in a folder")
  parser.add_argument("-f", "--folder", required=True, help="Path to the folder containing .wav files")
  parser.add_argument("-o", "--output", required=True, help="The output audio file, extension (wav) must be included")
  args = parser.parse_args()

  concatenate_audio_wave(args.folder, args.output)