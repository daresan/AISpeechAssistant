from loguru import logger
import time, pyttsx3
import multiprocessing
import multiprocessing.sharedctypes
import librosa
import numpy as np
from pathlib import Path
from synthesizer.inference import Synthesizer
from encoder import inference as encoder
from vocoder import inference as vocoder
import sounddevice as sd
import soundfile as sf
# Satztrennung
import re
import nltk; nltk.download('punkt_tab')
import os
		
class Voice:

	def __init__(self, fast_vocoding=True):
		self.process = None
		self.griffin_lim = fast_vocoding

		self.enc_model_fpath = Path("encoder/saved_models/german_encoder.pt")
		self.syn_model_fpath = Path("synthesizer/saved_models/german_synthesizer/german_synthesizer.pt")
		self.voc_model_fpath = Path("vocoder/saved_models/german_vocoder/german_vocoder.pt")
		
		self.voiceId = 'Daniel-germanvoice-DE-de'
		
		if self.enc_model_fpath.exists():
			encoder.load_model(self.enc_model_fpath)
		else:
			logger.warning("Encoder-Model existiert nicht. Bitte runterladen von https://github.com/padmalcom/Real-Time-Voice-Cloning-German/releases.")
			
		if self.syn_model_fpath.exists():
			self.synthesizer = Synthesizer(self.syn_model_fpath)
		else:
			logger.error("Synthesizer-Model existiert nicht. Bitte runterladen von https://github.com/padmalcom/Real-Time-Voice-Cloning-German/releases.")
			
		if self.voc_model_fpath.exists():
			vocoder.load_model(self.voc_model_fpath)
		else:
			logger.warning("Vocoder-Model existiert nicht. Bitte runterladen von https://github.com/padmalcom/Real-Time-Voice-Cloning-German/releases.")
	
	def split_text(self, text):
		paragraphs = text.split('\r\n')
		sentences = []

		for para in paragraphs:
			# Find all hyperlinks using a regular expression
			hyperlinks = re.findall(r'\bhttps?://\S+', para)
			
			# Tokenize the paragraph into sentences
			tokens = nltk.sent_tokenize(para)
			
			for token in tokens:
				# Check if the token contains a hyperlink and adjust accordingly
				for hyperlink in hyperlinks:
					if hyperlink in token:
						# Handle cases where the hyperlink is split across multiple tokens
						# # ... (implementation depends on specific requirements)
						break
				else:
					sentences.append(token)

		return sentences
	
	def __speak__(self, text, voiceId, record):
		logger.info("Starte Sprachausgabe.")
		texts = [text]
		embeds = [[0] * 256]
		result = self.split_text(text)
		
		if record == 1:
			for sentence in result:
				sentence = sentence.strip()
				texts = [sentence]
				
				if not self.syn_model_fpath.exists():
					logger.error("Synthesizer-Modell ist nicht geladen. TTS fehlgeschlagen.")
					return
					
				specs = self.synthesizer.synthesize_spectrograms(texts, embeds)
				spec = specs[0]
				
				if not self.griffin_lim and self.voc_model_fpath.exists():
					generated_wav = vocoder.infer_waveform(spec)
					generated_wav = np.pad(generated_wav, (0, self.synthesizer.sample_rate), mode="constant")
					
					if self.enc_model_fpath.exists():
						generated_wav = encoder.preprocess_wav(generated_wav)
					else:
						logger.warning("Kann Ausgabe nicht bereinigen, da Encoder-Modell nicht geladen werden kann.")
				else:
					if not self.voc_model_fpath.exists():
						logger.warning("Vocoder-Model existiert nicht. Fallback zu Griffin-Lim.")
					generated_wav = Synthesizer.griffin_lim(spec)
					
				audio_length = librosa.get_duration(generated_wav, sr = self.synthesizer.sample_rate)
				#turn generated wav into a np array float32
				sd.play(generated_wav.astype(np.float32), self.synthesizer.sample_rate)
				
				logger.info("Sprachausgabe für {} beendet.", texts)
				
				user_profile = os.path.expanduser('~')
				new_folder = "documents\\audio_output"
				folder_path = os.path.join(user_profile, new_folder)
				os.makedirs(folder_path, exist_ok=True)  # Erstellt den Ordner, falls er noch nicht existiert
				
				filename = f"output_{int(time.time())}.wav"
				file_path = os.path.join(folder_path, filename)
				logger.debug(f'Aufnahme wird als "{file_path}" gespeichert.')
				#with generated_wav as mydata:
				sf.write(file_path, generated_wav.astype(np.float32), self.synthesizer.sample_rate)
				time.sleep(round(audio_length+5.0))
				tex_name = f"{file_path[0:-4]}_txt.txt"
				with open(tex_name, 'w') as f:
					f.write(str(texts))
					f.write('\n')
				f.close()
			return []
		
		else:
			if not self.syn_model_fpath.exists():
				logger.error("Synthesizer-Modell ist nicht geladen. TTS fehlgeschlagen.")
				return
				
			specs = self.synthesizer.synthesize_spectrograms(texts, embeds)
			spec = specs[0]
			
			if not self.griffin_lim and self.voc_model_fpath.exists():
				generated_wav = vocoder.infer_waveform(spec)
				generated_wav = np.pad(generated_wav, (0, self.synthesizer.sample_rate), mode="constant")
				
				if self.enc_model_fpath.exists():
					generated_wav = encoder.preprocess_wav(generated_wav)
				else:
					logger.warning("Kann Ausgabe nicht bereinigen, da Encoder-Modell nicht geladen werden kann.")
			else:
				if not self.voc_model_fpath.exists():
					logger.warning("Vocoder-Model existiert nicht. Fallback zu Griffin-Lim.")
				generated_wav = Synthesizer.griffin_lim(spec)
				
			audio_length = librosa.get_duration(generated_wav, sr = self.synthesizer.sample_rate)
			#turn generated wav into a np array float32
			sd.play(generated_wav.astype(np.float32), self.synthesizer.sample_rate)
			
			logger.info("Sprachausgabe für {} beendet. Bereit für Eingabe.", texts)
			#num_frames = int(audio_length * self.synthesizer.sample_rate)
			
			# Save the generated WAV data to disk
			#if record == 1:
				# Speicher die Aufnahme hier:
			#	logger.debug('Aufnahme wird gespeichert.')
			#	filename = f"output_{int(time.time())}.wav"
			#	logger.debug(f'Aufnahme wird als "{filename}" gespeichert.')
				#mydata = sd.rec(generated_wav.astype(np.float32), self.synthesizer.sample_rate,channels=2, blocking=True)
				#sf.write(filename, generated_wav.astype(np.float32), self.synthesizer.sample_rate)
			#	with generated_wav as mydata:
			#		sf.write(filename, mydata.astype(np.float32), self.synthesizer.sample_rate)
			time.sleep(round(audio_length+5.0))
			return []
			# engine = pyttsx3.init()
			# engine.setProperty('Daniel-germanvoice-de-DE', voiceId)
			# engine.say(text)
			# engine.runAndWait()
		
	def say(self, text, record = None):
		if not record:
			self.record = 0
		else:
			self.record = 1
			
		if self.process:
			self.stop()
			
		# Create a shared array for the WAV data
		#self.shared_data = multiprocessing.sharedctypes.RawArray('f', 0)  # Initialize with a placeholder size
	
		p = multiprocessing.Process(target=self.__speak__, args=(text, self.voiceId, self.record))
		p.start()
		self.process = p
		
		# Wait for the child process to finish and retrieve the WAV data
		p.join()
	
		# Check if the WAV data was saved to the shared memory
		#if record:
		#	if self.shared_data:
		#		generated_wav = np.frombuffer(self.shared_data, dtype=np.float32)
		#		filename = f"output_{int(time.time())}.wav"
		#		logger.debug(f'Aufnahme wird als "{filename}" gespeichert.')
		#		mydata = sd.rec(generated_wav.astype(np.float32), self.synthesizer.sample_rate,channels=2, blocking=True)
		#		sf.write(filename, mydata, self.synthesizer.sample_rate)
		#	else:
		#		logger.warning("WAV data not available from child process.")
		
	def set_voice(self, voiceId):
		voiceId = self.voiceId
		print('VoiceID was set:', voiceId)
		
	def stop(self):
		if self.process:
			self.process.terminate()
	
	# Überprüfe, ob derzeit gesprochen wird
	def is_busy(self):
		if self.process:
			return self.process.is_alive()
		
	def get_voice_keys_by_language(self, language):
		#print('Die momentane Voice-ID: ', self.voiceId)
		result = self.voiceId
		# engine = pyttsx3.init()
		# voices = engine.getProperty('voices')
		
		# # Wir hängen ein "-" an die Sprache in Großschrift an, damit sie in der ID gefunden wird
		# lang_search_str = language.upper()+"-"
		# print('language:', lang_search_str)
		
		# for voice in voices:
		# 	print(voice.id)
		# 	# Die ID einer Sprache ist beispielsweise:
		# 	# HKEY_LOCAL_MACHINE\SOFTWARE\Microsoft\Speech\Voices\Tokens\TTS_MS_DE-DE_HEDDA_11.0
		# 	if language == '':
		# 		result.append(voice.id)
		# 	elif lang_search_str in voice.id:
		# 		result.append(voice.id)
		return result
	
if __name__ == "__main__":
    import sys
    say(str(sys.argv[1]))