import numpy as np
from pathlib import Path

import torch
from diffusers import DiffusionPipeline, DPMSolverMultistepScheduler
from diffusers.utils import export_to_video
from PIL import Image

class TTVideo:

	def __init__(self):
		self.process = None
		self.outpath = Path("txv/imagined_Video_")
		mem_all = torch.cuda.memory_allocated()
		print("Allocated Memory: ", str(mem_all))

		self.pipe = DiffusionPipeline.from_pretrained("./zeroscope_v2_576w", torch_dtype=torch.float16)
		self.pipe.scheduler = DPMSolverMultistepScheduler.from_config(self.pipe.scheduler.config)
		self.pipe.enable_model_cpu_offload()
		self.pipe.enable_vae_slicing()
		self.pipe.unet.enable_forward_chunking(chunk_size=1, dim=1) # disable if enough memory as this slows down significantly

	def __genVid__(self, text):
		outpath = self.__checkFilePath__("imagined_Video_",0)
		print("Generating ", outpath)
		self.video_frames = self.pipe(text, num_inference_steps=5, height=320, width=576, num_frames=36).frames[0]
		self.video_path = export_to_video(self.video_frames, output_video_path=outpath)
		print("Done.")
		mem_all = torch.cuda.memory_allocated()
		print("Allocated Memory: ", str(mem_all))
		print("Cleaning up ...")
		del self.pipe
		torch.cuda.empty_cache()

		mem_all = torch.cuda.memory_allocated()
		print("Allocated Memory: ", str(mem_all))
		
		self.video_path = None
		self.video_frames = None
		
		return []
		
	def __checkFilePath__(self, testString, currentCount):
		if os.path.exists(testString + str(currentCount) +".mp4"):
			return self.__checkFilePath__(testString, currentCount+1)
		else:
			return testString + str(currentCount) +".mp4"

	def imagine(self, text):
		if self.process:
			self.stop()
		p = multiprocessing.Process(target=self.__genVid__, args=(text))
		p.start()
		self.process = p
		
	def set_voice(self, voiceId):
		voiceId = self.voiceId
		print('VoiceID was set:', voiceId)
		
	def stop(self):
		if self.process:
			self.process.terminate()
	
	# Überprüfe, ob derzeit fantasiert wird
	def is_busy(self):
		if self.process:
			return self.process.is_alive()
		
if __name__ == "__main__":
    import sys
    imagine(str(sys.argv[1]))