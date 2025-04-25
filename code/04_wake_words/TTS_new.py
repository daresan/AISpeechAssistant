import time, pyttsx3
import multiprocessing

def __speak__(text, voiceId):
	engine = pyttsx3.init()
	engine.setProperty('voice', voiceId)
	engine.say(text)
	engine.runAndWait()
		
class Voice:

	def __init__(self, fast_vocoding=True):
		self.process = None
		self.griffin_lim = fast_vocoding

		self.enc_model_fpath = Path("encoder/saved_models/german_encoder.pt")
		self.syn_model_fpath = Path("synthesizer/saved_models/german_synthesizer/german_synthesizer.pt")
		self.voc_model_fpath = Path("vocoder/saved_models/german_vocoder/german_vocoder.pt")
		
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
		
	def say(self, text):
		if self.process:
			self.stop()
		p = multiprocessing.Process(target=__speak__, args=(text, self.voiceId))
		p.start()
		self.process = p
		
	def set_voice(self, voiceId):
		self.voiceId = voiceId
		
	def stop(self):
		if self.process:
			self.process.terminate()
		
	def get_voice_keys_by_language(self, language=''):
		result = []
		engine = pyttsx3.init()
		voices = engine.getProperty('voices')
		
		# Wir hängen ein "-" an die Sprache in Großschrift an, damit sie in der ID gefunden wird
		lang_search_str = language.upper()+"-"
		
		for voice in voices:
			# Die ID einer Sprache ist beispielsweise:
			# HKEY_LOCAL_MACHINE\SOFTWARE\Microsoft\Speech\Voices\Tokens\TTS_MS_DE-DE_HEDDA_11.0
			if language == '':
				result.append(voice.id)
			elif lang_search_str in voice.id:
				result.append(voice.id)
		return result